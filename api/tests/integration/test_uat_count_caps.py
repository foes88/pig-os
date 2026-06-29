"""UAT 후속 — 두수/날짜 상한 검증 + 크로스테넌트 + 조직롤 서브트리.

이번 UAT(3갈래 헌터)에서 발견한 결함의 회귀 방지:
- H1 비육 출하일 < 입식일 / H5 비육 PATCH head_in < head_out
- H2 자돈 폐사 > 보유 / H3 자돈 전출 > 잔여 / H4 양자 > 실산
- M2 모돈이력 크로스테넌트 / F1 조직롤 서브트리 강제
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.permissions import effective_farm_role
from app.core.security import create_access_token, hash_password
from app.db.models.events import Farrowing, Mating
from app.db.models.ops import FinisherGroup
from app.db.models.platform import Farm, Organization, User, UserFarm
from app.db.models.sow import PigletGroup, Sow
from app.services import report_service

pytestmark = pytest.mark.anyio


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role or u.role])}"}


async def _owner(db, farm):
    u = User(org_id=farm.org_id, username=f"o_{uuid.uuid4().hex[:6]}",
             email=f"o-{uuid.uuid4().hex[:6]}@pigos.io", name="O",
             password_hash=hash_password("Test1234!"), role="FARM_OWNER", system_role="FARM_OWNER")
    db.add(u)
    await db.flush()
    db.add(UserFarm(user_id=u.id, farm_id=farm.id, role_override="FARM_OWNER"))
    await db.flush()
    return u


# ── H2/H3: 자돈 그룹 두수 상한 ────────────────────────────────────────────────
async def test_piglet_deaths_exceed_capacity_blocked(client: AsyncClient, db, test_farm, test_user):
    owner = await _owner(db, test_farm)
    g = PigletGroup(farm_id=test_farm.id, group_code="PG-CAP1", weaning_date=date(2026, 6, 1), head_count_in=30)
    db.add(g)
    await db.flush()
    r = await client.post(f"/api/v1/farms/{test_farm.id}/piglets/{g.id}/deaths",
                          headers=_h(owner), json={"head_count_dead": 500})
    assert r.status_code == 422, r.text


async def test_piglet_transfer_exceed_remaining_blocked(client: AsyncClient, db, test_farm):
    owner = await _owner(db, test_farm)
    g = PigletGroup(farm_id=test_farm.id, group_code="PG-CAP2", weaning_date=date(2026, 6, 1),
                    head_count_in=20, head_count_dead=5)
    db.add(g)
    await db.flush()
    r = await client.post(f"/api/v1/farms/{test_farm.id}/piglets/{g.id}/transfer",
                          headers=_h(owner),
                          json={"transfer_date": "2026-07-01", "transfer_type": "SOLD", "head_count_out": 100})
    assert r.status_code == 422, r.text


# ── H4: 양자 > 실산 ──────────────────────────────────────────────────────────
async def test_cross_foster_exceeds_born_alive_blocked(client: AsyncClient, db, test_farm, test_sow):
    owner = await _owner(db, test_farm)
    dest = Sow(farm_id=test_farm.id, ear_tag="DEST-1", parity=1, status="LACTATING",
               entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(dest)
    m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 1, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id,
                  farrowing_date=date(2026, 4, 25), total_born=9, born_alive=8, stillborn=1, mummified=0)
    db.add(f)
    await db.flush()
    r = await client.post(f"/api/v1/farms/{test_farm.id}/piglets/transfers", headers=_h(owner),
                          json={"source_sow_id": str(test_sow.id), "dest_sow_id": str(dest.id),
                                "transfer_date": "2026-05-01", "piglet_count": 20,
                                "source_farrowing_id": str(f.id)})
    assert r.status_code == 422, r.text


# ── H1/H5: 비육 그룹 ─────────────────────────────────────────────────────────
async def test_finisher_ship_end_before_start_blocked(client: AsyncClient, db, test_farm):
    owner = await _owner(db, test_farm)
    g = FinisherGroup(farm_id=test_farm.id, group_code="FG-H1", start_date=date(2026, 6, 1),
                      head_count_in=100)
    db.add(g)
    await db.flush()
    r = await client.post(f"/api/v1/farms/{test_farm.id}/finishers/{g.id}/ship", headers=_h(owner),
                          json={"end_date": "2026-05-01", "head_count_out": 90})
    assert r.status_code == 422, r.text


async def test_finisher_patch_head_in_below_out_blocked(client: AsyncClient, db, test_farm):
    owner = await _owner(db, test_farm)
    g = FinisherGroup(farm_id=test_farm.id, group_code="FG-H5", start_date=date(2026, 1, 1),
                      end_date=date(2026, 5, 1), head_count_in=100, head_count_out=100)
    db.add(g)
    await db.flush()
    r = await client.patch(f"/api/v1/farms/{test_farm.id}/finishers/{g.id}", headers=_h(owner),
                           json={"head_count_in": 10})
    assert r.status_code == 422, r.text


# ── M2: 모돈이력 크로스테넌트 ─────────────────────────────────────────────────
async def test_sow_history_cross_tenant_blocked(db: AsyncSession, test_farm, test_org):
    # 다른 농장의 모돈
    other_farm = Farm(org_id=test_org.id, farm_code="OF-1", name="Other", country="KR", timezone="Asia/Seoul")
    db.add(other_farm)
    await db.flush()
    sow = Sow(farm_id=other_farm.id, ear_tag="X-1", parity=0, status="GILT",
              entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(sow)
    await db.flush()
    # test_farm 컨텍스트로 다른 농장 모돈 이력 요청 → 차단
    with pytest.raises(NotFoundError):
        await report_service.get_sow_history(db, test_farm.id, sow.id)


# ── F1: 조직롤 서브트리 강제 ──────────────────────────────────────────────────
async def test_org_role_blocked_outside_subtree(db: AsyncSession, test_org):
    # 총판(org A) — 자기 서브트리 농장만. 무관한 org B의 농장엔 None.
    farm_in = Farm(org_id=test_org.id, farm_code="IN-1", name="In", country="KR", timezone="Asia/Seoul")
    other_org = Organization(name="Other Co", country="KR", timezone="Asia/Seoul")
    db.add_all([farm_in, other_org])
    await db.flush()
    farm_out = Farm(org_id=other_org.id, farm_code="OUT-1", name="Out", country="KR", timezone="Asia/Seoul")
    db.add(farm_out)
    dist = User(org_id=test_org.id, username=f"d_{uuid.uuid4().hex[:6]}",
                email=f"d-{uuid.uuid4().hex[:6]}@pigos.io", name="D",
                password_hash=hash_password("Test1234!"), role="DISTRIBUTOR_ADMIN",
                system_role="DISTRIBUTOR_ADMIN")
    db.add(dist)
    await db.flush()
    assert await effective_farm_role(dist, farm_in.id, db) == "DISTRIBUTOR_ADMIN"
    assert await effective_farm_role(dist, farm_out.id, db) is None  # 서브트리 밖 → 권한 없음
