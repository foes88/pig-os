"""월마감 잠금 우회 결함 수정 — 적대적 헌터 P1/P2.

기존: _ensure_period_unlocked가 번식이벤트 create/PATCH/DELETE·feed·sync에는 걸려
있었으나 ① 모돈 도폐사(cull), ② 비육돈 그룹 create/ship/delete/update,
③ 분만·이유 PATCH의 '이동 도착월'은 검사하지 않아 잠긴 월로 백데이트 가능했음.
모두 확정 KPI(모돈수/PSY 분모, grow-finish ADG/FCR) 입력이라 잠금 대상.
"""
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PeriodLockedError
from app.core.security import create_access_token, hash_password
from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.ops import FinisherGroup, PeriodLock
from app.db.models.platform import Farm, Organization, User
from app.db.models.sow import Sow
from app.schemas.events import FarrowingUpdate, WeaningUpdate
from app.services import event_service

pytestmark = pytest.mark.anyio


async def _lock(db, farm, user, *, y, m):
    db.add(PeriodLock(farm_id=farm.id, period_year=y, period_month=m, locked_by=user.id))
    await db.flush()


async def _super(db, org) -> User:
    u = User(org_id=org.id, username=f"sa_{uuid.uuid4().hex[:6]}",
             email=f"sa-{uuid.uuid4().hex[:6]}@pigos.io", name="SA",
             password_hash=hash_password("Test1234!"),
             role="SUPER_ADMIN", system_role="SUPER_ADMIN")
    db.add(u)
    await db.flush()
    return u


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


# ── ① 모돈 도폐사(cull) ──────────────────────────────────────────────
async def test_cull_in_locked_period_blocked(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
    test_sow: Sow, test_user: User,
):
    await _lock(db, test_farm, test_user, y=2026, m=3)
    sa = await _super(db, test_org)
    await db.flush()
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull", headers=_h(sa),
        json={"removal_date": "2026-03-15", "removal_type": "CULLED",
              "reason_category": "AGE"})
    assert r.status_code == 423, r.text


async def test_cull_in_unlocked_period_ok(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
    test_sow: Sow, test_user: User,
):
    await _lock(db, test_farm, test_user, y=2026, m=3)
    sa = await _super(db, test_org)
    await db.flush()
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull", headers=_h(sa),
        json={"removal_date": "2026-04-15", "removal_type": "CULLED",
              "reason_category": "AGE"})
    assert r.status_code == 201, r.text


# ── ② 비육돈 그룹 ────────────────────────────────────────────────────
async def test_finisher_create_in_locked_period_blocked(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
    test_user: User,
):
    await _lock(db, test_farm, test_user, y=2026, m=3)
    sa = await _super(db, test_org)
    await db.flush()
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/finishers", headers=_h(sa),
        json={"group_code": f"FG-{uuid.uuid4().hex[:5]}", "start_date": "2026-03-05",
              "head_count_in": 100, "avg_entry_weight_kg": 25.0})
    assert r.status_code == 423, r.text


async def test_finisher_ship_in_locked_period_blocked(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
    test_user: User,
):
    # 입식은 잠기지 않은 5월, 출하 6월은 잠금 → 출하 차단
    group = FinisherGroup(farm_id=test_farm.id, group_code=f"FG-{uuid.uuid4().hex[:5]}",
                          start_date=date(2026, 5, 1), head_count_in=100,
                          avg_entry_weight_kg=25.0)
    db.add(group)
    await _lock(db, test_farm, test_user, y=2026, m=6)
    sa = await _super(db, test_org)
    await db.flush()
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/finishers/{group.id}/ship", headers=_h(sa),
        json={"end_date": "2026-06-10", "head_count_out": 90})
    assert r.status_code == 423, r.text


# ── ③ 분만/이유 PATCH 도착월 ─────────────────────────────────────────
async def _farrowing(db, farm, sow):
    m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2026, 1, 5),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=sow.id, mating_id=m.id,
                  farrowing_date=date(2026, 4, 20), total_born=10, born_alive=10,
                  stillborn=0, mummified=0, nursing_head=10)
    db.add(f)
    await db.flush()
    return f


async def test_update_farrowing_move_into_locked_blocked(
    db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user: User,
):
    f = await _farrowing(db, test_farm, test_sow)
    await _lock(db, test_farm, test_user, y=2026, m=3)  # 도착월 잠금
    with pytest.raises(PeriodLockedError) as ei:
        await event_service.update_farrowing(
            db, test_farm.id, test_user.id, f.id,
            FarrowingUpdate(farrowing_date=date(2026, 3, 15)))
    assert ei.value.status_code == 423


async def test_update_weaning_move_into_locked_blocked(
    db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user: User,
):
    f = await _farrowing(db, test_farm, test_sow)
    w = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                weaning_date=date(2026, 5, 10), weaned_count=8)
    db.add(w)
    await _lock(db, test_farm, test_user, y=2026, m=3)
    await db.flush()
    with pytest.raises(PeriodLockedError) as ei:
        await event_service.update_weaning(
            db, test_farm.id, test_user.id, w.id,
            WeaningUpdate(weaning_date=date(2026, 3, 1)))
    assert ei.value.status_code == 423


# ── ④ 자돈 그룹 — 코드리뷰 #4 (piglets 라우터 잠금 누락) ─────────────
async def test_piglet_group_create_in_locked_period_blocked(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
    test_user: User,
):
    await _lock(db, test_farm, test_user, y=2026, m=3)
    sa = await _super(db, test_org)
    await db.flush()
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/piglets", headers=_h(sa),
        json={"group_code": f"PG-{uuid.uuid4().hex[:5]}", "weaning_date": "2026-03-15",
              "head_count_in": 20})
    assert r.status_code == 423, r.text
