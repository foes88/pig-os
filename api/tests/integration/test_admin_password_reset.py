"""운영자 비밀번호 재설정 — 임시 비번 발급 + 세션 폐기 + 권한(super_admin 전용)."""
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.platform import Organization, RefreshToken, User

pytestmark = pytest.mark.anyio


async def _user(db, org, role="FARM_OWNER") -> User:
    u = User(org_id=org.id, username=f"u_{uuid.uuid4().hex[:6]}",
             email=f"u-{uuid.uuid4().hex[:6]}@pigos.io", name="U",
             password_hash=hash_password("OldPass123!"), role="FARM_OWNER", system_role=role)
    db.add(u)
    await db.flush()
    return u


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def test_super_admin_resets_password_and_revokes_sessions(
    client: AsyncClient, db: AsyncSession, test_org: Organization,
):
    admin = await _user(db, test_org, "SUPER_ADMIN")
    target = await _user(db, test_org, "FARM_OWNER")
    # 대상의 활성 리프레시 토큰
    rt = RefreshToken(user_id=target.id, token_hash="h" + uuid.uuid4().hex,
                      expires_at=datetime.now(UTC) + timedelta(days=7), revoked=False)
    db.add(rt)
    await db.flush()

    r = await client.post(f"/api/v1/admin/members/{target.id}/reset-password", headers=_h(admin))
    assert r.status_code == 200, r.text
    temp = r.json()["temp_password"]
    assert temp and len(temp) >= 8

    await db.refresh(target)
    assert verify_password(temp, target.password_hash), "임시 비번으로 검증돼야 함"
    assert not verify_password("OldPass123!", target.password_hash), "옛 비번 무효"
    await db.refresh(rt)
    assert rt.revoked is True, "재설정 시 활성 세션 폐기"


async def test_non_super_admin_blocked(client: AsyncClient, db: AsyncSession, test_org: Organization):
    owner = await _user(db, test_org, "FARM_OWNER")
    target = await _user(db, test_org, "FARM_OWNER")
    await db.flush()
    r = await client.post(f"/api/v1/admin/members/{target.id}/reset-password", headers=_h(owner))
    assert r.status_code == 403, r.text


async def test_reset_unknown_member_404(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _user(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post(f"/api/v1/admin/members/{uuid.uuid4()}/reset-password", headers=_h(admin))
    assert r.status_code == 404, r.text
