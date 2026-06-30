"""R2 관리자 콘솔 보안 결함 — pilot 권한상승(P1)·마지막 super_admin 락아웃(P1)·
pilot 감사 권한기록(P2)·orgs UUID 파싱 500→422(P2).
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.pilot_signup import PilotSignup
from app.db.models.platform import AuditLog, Organization, User

pytestmark = pytest.mark.anyio


async def _admin(db, org) -> User:
    u = User(org_id=org.id, username=f"sa_{uuid.uuid4().hex[:6]}",
             email=f"sa-{uuid.uuid4().hex[:6]}@pigos.io", name="SA",
             password_hash=hash_password("Test1234!"), role="FARM_OWNER", system_role="SUPER_ADMIN")
    db.add(u)
    await db.flush()
    return u


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def _signup(db) -> PilotSignup:
    p = PilotSignup(name="Pilot", email=f"p-{uuid.uuid4().hex[:6]}@x.io",
                    farm_size="under_100", country="Vietnam", role="owner", lang="en", status="pending")
    db.add(p)
    await db.flush()
    return p


# ── P1: pilot 승인으로 SUPER_ADMIN 발급 차단 ────────────────────────
async def test_pilot_approve_cannot_grant_super_admin(client: AsyncClient, db: AsyncSession, test_org):
    admin = await _admin(db, test_org)
    p = await _signup(db)
    await db.flush()
    r = await client.post(f"/api/v1/admin/pilot-signups/{p.id}/approve", headers=_h(admin),
                          json={"initial_password": "escalate123", "system_role": "SUPER_ADMIN"})
    assert r.status_code == 422, r.text


async def test_pilot_approve_farm_owner_ok_and_audits_role(client: AsyncClient, db: AsyncSession, test_org):
    admin = await _admin(db, test_org)
    p = await _signup(db)
    await db.flush()
    r = await client.post(f"/api/v1/admin/pilot-signups/{p.id}/approve", headers=_h(admin),
                          json={"initial_password": "welcome123", "system_role": "FARM_OWNER"})
    assert r.status_code == 200, r.text
    new_uid = r.json()["user_id"]
    # P2: 감사에 부여 권한 기록
    audit = await db.scalar(select(AuditLog).where(
        AuditLog.entity_type == "pilot_approval", AuditLog.entity_id == uuid.UUID(new_uid)))
    assert audit is not None and audit.new_value.get("granted_system_role") == "FARM_OWNER"


# ── P1: 마지막/자기자신 super_admin 비활성화 차단 ───────────────────
async def test_cannot_deactivate_self_super_admin(client: AsyncClient, db: AsyncSession, test_org):
    admin = await _admin(db, test_org)
    await db.flush()
    r = await client.patch(f"/api/v1/admin/members/{admin.id}/status", headers=_h(admin),
                           json={"active": False})
    assert r.status_code == 422, r.text


async def test_can_deactivate_other_super_admin_when_another_remains(
    client: AsyncClient, db: AsyncSession, test_org,
):
    # 과도차단 방지: 다른 활성 super_admin이 남아 있으면 한 명 비활성화는 허용돼야 함.
    actor = await _admin(db, test_org)
    other = await _admin(db, test_org)
    await db.flush()
    r = await client.patch(f"/api/v1/admin/members/{other.id}/status", headers=_h(actor),
                           json={"active": False})
    assert r.status_code == 200, r.text


# ── P2: orgs UUID 파싱 500→422 ──────────────────────────────────────
async def test_create_org_bad_parent_uuid_422(client: AsyncClient, db: AsyncSession, test_org):
    admin = await _admin(db, test_org)
    await db.flush()
    r = await client.post("/api/v1/admin/orgs", headers=_h(admin),
                          json={"name": "X", "org_type": "DISTRIBUTOR", "country": "KR",
                                "parent_org_id": "not-a-uuid"})
    assert r.status_code == 422, r.text


async def test_update_org_bad_parent_uuid_422(client: AsyncClient, db: AsyncSession, test_org):
    admin = await _admin(db, test_org)
    org = Organization(name="O", org_type="VENDOR", org_level=0, country="KR", timezone="UTC")
    db.add(org)
    await db.flush()
    r = await client.patch(f"/api/v1/admin/orgs/{org.id}", headers=_h(admin),
                           json={"parent_org_id": "not-a-uuid"})
    assert r.status_code == 422, r.text


async def test_reassign_farm_bad_org_uuid_422(client: AsyncClient, db: AsyncSession, test_org, test_farm):
    admin = await _admin(db, test_org)
    await db.flush()
    r = await client.patch(f"/api/v1/admin/farms/{test_farm.id}/org", headers=_h(admin),
                           json={"org_id": "not-a-uuid"})
    assert r.status_code == 422, r.text
