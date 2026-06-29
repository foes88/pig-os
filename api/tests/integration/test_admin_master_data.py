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


# --- G4 하드닝: 제네릭 CRUD 타입/제약 위반은 500이 아닌 422 (버그헌터 P1) ---

async def test_master_string_into_numeric_422(client: AsyncClient, db: AsyncSession, test_org: Organization):
    """숫자 컬럼에 문자열 → 과거 raw 500. 이제 422."""
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/diseases", headers=_h(admin), json={
        "disease_code": f"QA-{uuid.uuid4().hex[:5]}", "label_en": "x", "category": "VIRAL",
        "typical_mortality_pct": "not-a-number"})
    assert r.status_code == 422, r.text


async def test_master_string_into_integer_422(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/vaccines", headers=_h(admin), json={
        "vaccine_code": f"QA-{uuid.uuid4().hex[:5]}", "label_en": "x", "withdrawal_days": "abc"})
    assert r.status_code == 422, r.text


async def test_master_missing_not_null_422(client: AsyncClient, db: AsyncSession, test_org: Organization):
    """NOT NULL(category) 누락 → 과거 IntegrityError 500. 이제 commit 캐치로 422."""
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/diseases", headers=_h(admin), json={
        "disease_code": f"QA-{uuid.uuid4().hex[:5]}", "label_en": "x"})  # category 누락
    assert r.status_code == 422, r.text


async def test_master_numeric_overflow_422(client: AsyncClient, db: AsyncSession, test_org: Organization):
    """Numeric 자릿수 초과 → 과거 500. 이제 422."""
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/diseases", headers=_h(admin), json={
        "disease_code": f"QA-{uuid.uuid4().hex[:5]}", "label_en": "x", "category": "VIRAL",
        "typical_mortality_pct": 999999999})
    assert r.status_code == 422, r.text


async def test_master_jsonb_must_be_object_422(client: AsyncClient, db: AsyncSession, test_org: Organization):
    """JSONB 컬럼에 bare 문자열 → 과거 201 저장(손상). 이제 422."""
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/diseases", headers=_h(admin), json={
        "disease_code": f"QA-{uuid.uuid4().hex[:5]}", "label_en": "x", "category": "VIRAL",
        "regional_prevalence": "justastring"})
    assert r.status_code == 422, r.text


async def test_master_array_must_be_list_422(client: AsyncClient, db: AsyncSession, test_org: Organization):
    """ARRAY 컬럼에 dict → 과거 201(키만 추출 저장). 이제 422."""
    admin = await _mk(db, test_org, "SUPER_ADMIN")
    await db.flush()
    r = await client.post("/api/v1/admin/master/vaccines", headers=_h(admin), json={
        "vaccine_code": f"QA-{uuid.uuid4().hex[:5]}", "label_en": "x",
        "approved_regions": {"not": "a list"}})
    assert r.status_code == 422, r.text
