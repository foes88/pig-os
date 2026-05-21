"""
Integration test fixtures.
- 테스트 DB: pigos_test (Docker postgres 컨테이너 재활용)
- 각 테스트는 savepoint로 감싸고 rollback → 격리 보장
"""
import os
import uuid
from datetime import datetime, UTC
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.models import *  # noqa: F401,F403 — registers all models
from app.db.models.platform import Farm, Organization, User
from app.db.models.sow import Sow
from app.main import app
from app.core.dependencies import get_db

# ── Test DB URL ───────────────────────────────────────────────────────────────
# pigos_test DB는 docker exec로 미리 생성 필요:
#   docker exec pigos-postgres psql -U pigos -c "CREATE DATABASE pigos_test;"
_TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    settings.database_url.replace("/pigos", "/pigos_test"),
)

_engine = create_async_engine(_TEST_DB_URL, echo=False, future=True)
_TestSession = async_sessionmaker(_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    """세션 시작 시 한 번만 테이블 생성."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 테스트 세션 종료 후 전체 드랍 (선택적)
    # async with _engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    각 테스트마다 savepoint 트랜잭션으로 격리.
    테스트 종료 시 rollback → DB 상태 초기화.
    """
    async with _engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested()  # savepoint

        session = AsyncSession(bind=conn, expire_on_commit=False)

        async def mock_commit():
            # commit 대신 flush만 — savepoint 안에서 유지
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
