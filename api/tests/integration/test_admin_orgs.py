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


# ─── B5: 계층 관리 (생성·수정·농장 재배정) ──────────────────────────────────────
async def test_create_org_under_parent(client: AsyncClient, db: AsyncSession):
    vendor = await _org(db, "Vendor", "VENDOR", 0)
    admin = await _admin_user(db, vendor, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/orgs", headers=_auth(admin), json={
        "name": "신규총판", "org_type": "DISTRIBUTOR", "parent_org_id": str(vendor.id), "country": "KR",
    })
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["org_type"] == "DISTRIBUTOR" and body["org_level"] == 1
    assert body["parent_org_id"] == str(vendor.id)


async def test_create_org_invalid_type_rejected(client: AsyncClient, db: AsyncSession):
    vendor = await _org(db, "V2", "VENDOR", 0)
    admin = await _admin_user(db, vendor, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/orgs", headers=_auth(admin), json={
        "name": "x", "org_type": "BOGUS", "country": "KR",
    })
    assert r.status_code == 422


async def test_update_org_rename_and_reparent(client: AsyncClient, db: AsyncSession):
    vendor = await _org(db, "V3", "VENDOR", 0)
    dist = await _org(db, "D3", "DISTRIBUTOR", 1, vendor)
    other = await _org(db, "V3b", "VENDOR", 0)
    admin = await _admin_user(db, vendor, "SUPER_ADMIN")
    await db.flush()
    r = await client.patch(f"/api/v1/admin/orgs/{dist.id}", headers=_auth(admin),
                           json={"name": "대리점이름", "parent_org_id": str(other.id)})
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "대리점이름"
    assert r.json()["parent_org_id"] == str(other.id)


async def test_update_org_cycle_rejected(client: AsyncClient, db: AsyncSession):
    vendor = await _org(db, "V4", "VENDOR", 0)
    dist = await _org(db, "D4", "DISTRIBUTOR", 1, vendor)
    admin = await _admin_user(db, vendor, "SUPER_ADMIN")
    await db.flush()
    # vendor의 부모를 자기 하위(dist)로 지정 → 사이클 → 409
    r = await client.patch(f"/api/v1/admin/orgs/{vendor.id}", headers=_auth(admin),
                           json={"parent_org_id": str(dist.id)})
    assert r.status_code == 409


async def test_reassign_farm_to_other_org(client: AsyncClient, db: AsyncSession):
    vendor = await _org(db, "V5", "VENDOR", 0)
    dealer1 = await _org(db, "DL5a", "DEALER", 2, vendor)
    dealer2 = await _org(db, "DL5b", "DEALER", 2, vendor)
    f = Farm(org_id=dealer1.id, farm_code=f"F-{uuid.uuid4().hex[:6]}", name="MoveMe",
             country="KR", timezone="Asia/Seoul", active=True)
    db.add(f)
    admin = await _admin_user(db, vendor, "SUPER_ADMIN")
    await db.flush()
    r = await client.patch(f"/api/v1/admin/farms/{f.id}/org", headers=_auth(admin),
                           json={"org_id": str(dealer2.id)})
    assert r.status_code == 200, r.text
    await db.refresh(f)
    assert str(f.org_id) == str(dealer2.id)
