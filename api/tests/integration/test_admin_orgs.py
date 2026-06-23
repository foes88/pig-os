"""운영자 콘솔 — 조직 트리(업체→총판→대리점→농장) 드릴다운 API 검증."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Farm, Organization, User

pytestmark = pytest.mark.anyio


async def _org(db, name, otype, level, parent=None):
    o = Organization(name=name, org_type=otype, org_level=level,
                     parent_org_id=parent.id if parent else None, country="KR", timezone="Asia/Seoul")
    db.add(o); await db.flush(); return o


async def _admin_user(db, org, role):
    u = User(org_id=org.id, email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@pigos.io", name=role,
             password_hash=hash_password("Test1234!"), role="FARM_OWNER", system_role=role)
    db.add(u); await db.flush(); return u


def _auth(u):
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def test_orgs_gate_and_tree(client: AsyncClient, db: AsyncSession):
    vendor = await _org(db, "V", "VENDOR", 0)
    dist = await _org(db, "D", "DISTRIBUTOR", 1, vendor)
    dealer = await _org(db, "DL", "DEALER", 2, dist)
    f = Farm(org_id=dealer.id, farm_code=f"F-{uuid.uuid4().hex[:6]}", name="FarmX", country="KR", timezone="Asia/Seoul", active=True)
    db.add(f); await db.flush()
    admin = await _admin_user(db, vendor, "SUPER_ADMIN")
    owner = await _admin_user(db, dealer, "FARM_OWNER")
    await db.flush()

    # 비관리자 차단
    assert (await client.get("/api/v1/admin/orgs", headers=_auth(owner))).status_code == 403

    # 전사 조직 목록 + 계층 필드
    r = await client.get("/api/v1/admin/orgs", headers=_auth(admin))
    assert r.status_code == 200
    by_name = {o["name"]: o for o in r.json()}
    assert by_name["V"]["parent_org_id"] is None
    assert by_name["D"]["parent_org_id"] == str(vendor.id)
    assert by_name["DL"]["parent_org_id"] == str(dist.id)
    assert by_name["DL"]["farm_count"] == 1

    # 조직 농장 드릴다운
    fr = await client.get(f"/api/v1/admin/orgs/{dealer.id}/farms", headers=_auth(admin))
    assert fr.status_code == 200
    assert any(x["name"] == "FarmX" for x in fr.json())
