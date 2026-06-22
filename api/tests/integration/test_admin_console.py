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


# ─── Phase 1: 회원/가입승인 ────────────────────────────────────────────────────
async def test_members_list_forbidden_for_owner(client: AsyncClient, db: AsyncSession, test_org: Organization):
    owner = await _mk_user(db, test_org, "FARM_OWNER")
    r = await client.get("/api/v1/admin/members", headers=_auth(owner))
    assert r.status_code == 403


async def test_members_list_and_search(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    await _mk_user(db, test_org, "FARM_OWNER")
    await db.flush()
    r = await client.get("/api/v1/admin/members", headers=_auth(admin))
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "meta" in body
    assert body["meta"]["total"] >= 2
    # 상태 필터 유효성
    bad = await client.get("/api/v1/admin/members?status=BOGUS", headers=_auth(admin))
    assert bad.status_code == 422


async def test_member_status_approve_reject(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    target = await _mk_user(db, test_org, "FARM_OWNER")
    await db.flush()
    # 반려
    r = await client.patch(
        f"/api/v1/admin/members/{target.id}/status",
        headers=_auth(admin), json={"approval_status": "REJECTED", "active": False},
    )
    assert r.status_code == 200
    assert r.json()["approval_status"] == "REJECTED"
    assert r.json()["active"] is False
    # 재승인
    r2 = await client.patch(
        f"/api/v1/admin/members/{target.id}/status",
        headers=_auth(admin), json={"approval_status": "APPROVED", "active": True},
    )
    assert r2.json()["approval_status"] == "APPROVED"
    # 잘못된 상태
    bad = await client.patch(
        f"/api/v1/admin/members/{target.id}/status",
        headers=_auth(admin), json={"approval_status": "NOPE"},
    )
    assert bad.status_code == 422


async def test_pilot_signup_list_and_approve(client: AsyncClient, db: AsyncSession, test_org: Organization):
    from app.db.models.pilot_signup import PilotSignup
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    signup = PilotSignup(
        name="Nguyen Farm", email=f"pilot-{uuid.uuid4().hex[:6]}@ex.com",
        farm_size="500_1000", country="Vietnam", role="owner", lang="vi", status="pending",
    )
    db.add(signup)
    await db.flush()

    lst = await client.get("/api/v1/admin/pilot-signups", headers=_auth(admin))
    assert lst.status_code == 200
    assert lst.json()["meta"]["total"] >= 1

    appr = await client.post(
        f"/api/v1/admin/pilot-signups/{signup.id}/approve",
        headers=_auth(admin), json={"initial_password": "pilot1234!", "system_role": "FARM_OWNER"},
    )
    assert appr.status_code == 200, appr.text
    assert appr.json()["email"] == signup.email
    # 중복 승인 차단
    again = await client.post(
        f"/api/v1/admin/pilot-signups/{signup.id}/approve",
        headers=_auth(admin), json={"initial_password": "pilot1234!"},
    )
    assert again.status_code == 409


async def test_pilot_signup_forbidden_for_viewer(client: AsyncClient, db: AsyncSession, test_org: Organization):
    viewer = await _mk_user(db, test_org, "VIEWER")
    r = await client.get("/api/v1/admin/pilot-signups", headers=_auth(viewer))
    assert r.status_code == 403
