"""
Integration test fixtures.
- 테스트 DB: pigos_test (Docker postgres 컨테이너 재활용)
- 각 테스트는 별도 트랜잭션 + rollback으로 격리
"""
import os
import uuid
from datetime import datetime, UTC
from typing import AsyncGenerator
from urllib.parse import urlparse, urlunparse

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.base import Base
from app.db.models import *  # noqa: F401,F403 — registers all models
from app.db.models.platform import Farm, Organization, User
from app.db.models.sow import Sow
from app.main import app
from app.core.dependencies import get_db

# ── Test DB URL ───────────────────────────────────────────────────────────────
def _make_test_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse(p._replace(path="/pigos_test"))


def _assert_test_database(url: str) -> None:
    database_name = urlparse(url).path.lstrip("/")
    if not database_name.lower().endswith("_test"):
        raise RuntimeError(f"Refusing to reset non-test database: {database_name}")


_ASYNC_TEST_URL = os.getenv("TEST_DATABASE_URL", _make_test_url(settings.database_url))
_SYNC_TEST_URL = _ASYNC_TEST_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")

# sync 엔진 — 테이블 생성 전용 (event loop 없이 session-scoped fixture에서 사용)
_sync_engine = create_engine(_SYNC_TEST_URL, echo=False)

# async 엔진 — 각 테스트 함수에서만 사용, NullPool로 독립 연결
_async_engine = create_async_engine(_ASYNC_TEST_URL, echo=False, future=True, poolclass=NullPool)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """세션 시작 시 한 번만 테이블 생성 (sync 엔진 사용)."""
    _assert_test_database(_SYNC_TEST_URL)
    with _sync_engine.begin() as conn:
        conn.exec_driver_sql("DROP VIEW IF EXISTS v_sow_npd, v_farm_psy CASCADE")
        conn.exec_driver_sql(
            "DROP FUNCTION IF EXISTS effective_metric_values(VARCHAR, VARCHAR, VARCHAR)"
        )
    Base.metadata.drop_all(_sync_engine)
    Base.metadata.create_all(_sync_engine)
    yield
    _sync_engine.dispose()


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    각 테스트마다 독립 트랜잭션.
    서비스의 commit()을 flush()로 대체 후 rollback → DB 격리.
    """
    async with _async_engine.begin() as conn:
        session = AsyncSession(bind=conn, expire_on_commit=False)

        async def mock_commit():
            await session.flush()

        session.commit = mock_commit  # type: ignore[method-assign]

        yield session

        await session.close()
        await conn.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI 테스트 클라이언트 — DB는 테스트 세션으로 오버라이드."""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Common entity fixtures ────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_org(db: AsyncSession) -> Organization:
    org = Organization(name="Test Corp", country="KR", timezone="Asia/Seoul")
    db.add(org)
    await db.flush()
    return org


@pytest_asyncio.fixture
async def test_farm(db: AsyncSession, test_org: Organization) -> Farm:
    farm = Farm(
        org_id=test_org.id,
        farm_code=f"TEST-{uuid.uuid4().hex[:6].upper()}",
        name="Test Farm",
        country="KR",
        timezone="Asia/Seoul",
    )
    db.add(farm)
    await db.flush()
    return farm


@pytest_asyncio.fixture
async def test_user(db: AsyncSession, test_org: Organization) -> User:
    from app.core.security import hash_password
    user = User(
        org_id=test_org.id,
        email=f"test-{uuid.uuid4().hex[:6]}@pigos.io",
        name="Test User",
        password_hash=hash_password("Test1234!"),
        role="FARM_OWNER",
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def test_sow(db: AsyncSession, test_farm: Farm) -> Sow:
    sow = Sow(
        farm_id=test_farm.id,
        ear_tag=f"SOW-{uuid.uuid4().hex[:6].upper()}",
        parity=0,
        status="ACTIVE",
        entry_date=datetime.now(UTC),
        entry_type="GILT",
    )
    db.add(sow)
    await db.flush()
    return sow
