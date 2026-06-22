"""운영자 콘솔 Phase 4 — 활동 로그 뷰어 검증."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Organization, User

pytestmark = pytest.mark.anyio


async def _mk_user(db: AsyncSession, org: Organization, role: str) -> User:
    u = User(
        org_id=org.id, email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@pigos.io",
        name=f"{role} User", password_hash=hash_password("Test1234!"), role=role, system_role=role,
    )
    db.add(u)
    await db.flush()
    return u


def _auth(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def test_audit_gate(client: AsyncClient, db: AsyncSession, test_org: Organization):
    owner = await _mk_user(db, test_org, "FARM_OWNER")
    await db.flush()
    assert (await client.get("/api/v1/admin/audit-log", headers=_auth(owner))).status_code == 403


async def test_audit_records_admin_action(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    await db.flush()
    # 운영 작업 발생(공지 작성 → AuditLog CREATE)
    cr = await client.post("/api/v1/admin/announcements", headers=_auth(admin),
                           json={"title": "Audit me", "body": "x"})
    assert cr.status_code == 201
    # 활동 로그에 반영
    log = await client.get("/api/v1/admin/audit-log?entity_type=announcement", headers=_auth(admin))
    assert log.status_code == 200
    body = log.json()
    assert body["meta"]["total"] >= 1
    assert any(r["action"] == "CREATE" and r["entity_type"] == "announcement" for r in body["items"])
    assert body["items"][0]["actor_name"] is not None
