"""운영자 어드민 콘솔 — Phase 0 게이트 검증.

SUPER_ADMIN 만 /admin/* 접근 가능. 비관리자·무토큰은 차단.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Organization, User

pytestmark = pytest.mark.anyio


async def _mk_user(db: AsyncSession, org: Organization, role: str) -> User:
    user = User(
        org_id=org.id,
        email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@pigos.io",
        name=f"{role} User",
        password_hash=hash_password("Test1234!"),
        role=role,
        system_role=role,  # 게이트 권위 필드 — role과 함께 설정해야 정확
    )
    db.add(user)
    await db.flush()
    return user


def _auth(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), str(user.org_id), [user.system_role])
    return {"Authorization": f"Bearer {token}"}


async def test_overview_forbidden_for_non_admin(client: AsyncClient, db: AsyncSession, test_org: Organization):
    owner = await _mk_user(db, test_org, "FARM_OWNER")
    r = await client.get("/api/v1/admin/overview", headers=_auth(owner))
    assert r.status_code == 403


async def test_overview_requires_auth(client: AsyncClient):
    r = await client.get("/api/v1/admin/overview")
    assert r.status_code in (401, 403)


async def test_overview_ok_for_super_admin(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    r = await client.get("/api/v1/admin/overview", headers=_auth(admin))
    assert r.status_code == 200
    body = r.json()
    # 전사 카운트 키 존재 + 음이 아닌 정수
    for key in ("organizations", "farms", "users", "sows"):
        assert key in body
        assert isinstance(body[key], int)
        assert body[key] >= 0
    # 최소 방금 만든 org 1개는 잡힘
    assert body["organizations"] >= 1


async def test_admin_me_returns_super_admin(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    r = await client.get("/api/v1/admin/me", headers=_auth(admin))
    assert r.status_code == 200
    assert r.json()["role"] == "SUPER_ADMIN"


async def test_admin_me_forbidden_for_viewer(client: AsyncClient, db: AsyncSession, test_org: Organization):
    viewer = await _mk_user(db, test_org, "VIEWER")
    r = await client.get("/api/v1/admin/me", headers=_auth(viewer))
    assert r.status_code == 403
