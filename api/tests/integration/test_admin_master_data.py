"""G4 — 관리자 코드/마스터 데이터 CRUD (disease/vaccine/medication/event-def)."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Organization, User

pytestmark = pytest.mark.anyio


async def _mk(db, org, role) -> User:
    u = User(org_id=org.id, username=f"{role.lower()}_{uuid.uuid4().hex[:6]}",
             email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@pigos.io", name=role,
             password_hash=hash_password("Test1234!"), role=role, system_role=role)
    db.add(u)
    await db.flush()
    return u


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def test_master_crud_lifecycle(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    h = _h(admin)
    code = f"QA-DIS-{uuid.uuid4().hex[:5].upper()}"

    # CREATE
    r = await client.post("/api/v1/admin/master/diseases", headers=h, json={
        "disease_code": code, "label_en": "QA Test Disease", "category": "VIRAL", "notifiable": True})
    assert r.status_code == 201, r.text
    assert r.json()["disease_code"] == code and r.json()["notifiable"] is True

    # LIST contains it
    lst = await client.get("/api/v1/admin/master/diseases", headers=h)
    assert lst.status_code == 200
    assert any(x["disease_code"] == code for x in lst.json())

    # UPDATE
    up = await client.patch(f"/api/v1/admin/master/diseases/{code}", headers=h,
                            json={"label_en": "QA Updated", "notifiable": False})
    assert up.status_code == 200
    assert up.json()["label_en"] == "QA Updated" and up.json()["notifiable"] is False

    # DELETE
    d = await client.delete(f"/api/v1/admin/master/diseases/{code}", headers=h)
    assert d.status_code == 204
    lst2 = await client.get("/api/v1/admin/master/diseases", headers=h)
    assert not any(x["disease_code"] == code for x in lst2.json())


async def test_master_unknown_field_rejected(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/diseases", headers=_h(admin), json={
        "disease_code": "X1", "label_en": "x", "category": "VIRAL", "bogus_col": "nope"})
    assert r.status_code == 422, r.text


async def test_master_unknown_kind_404(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.get("/api/v1/admin/master/nope", headers=_h(admin))
    assert r.status_code == 404


async def test_master_requires_super_admin(client: AsyncClient, db: AsyncSession, test_org: Organization):
    owner = await _mk(db, test_org, "FARM_OWNER")
    await db.flush()
    r = await client.get("/api/v1/admin/master/diseases", headers=_h(owner))
    assert r.status_code == 403


async def test_master_create_requires_pk(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/medications", headers=_h(admin),
                          json={"antibiotic_class": "PENICILLIN"})  # active_substance(PK) 누락
    assert r.status_code == 422
