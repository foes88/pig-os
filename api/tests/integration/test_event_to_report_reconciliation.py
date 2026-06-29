"""F8 — 이벤트 기록(실서비스) → 번식보고서/상태 수치 정합성 (end-to-end).

test_reports는 이벤트를 직접 insert하지만, 여기선 record_mating/farrowing/weaning
실서비스로 기록(사이클 생성·검증·상태전이 포함) → 보고서 수치가 실제 기록과
일치하는지 단언. 교배/분만/이유/폐사 → 보고서 정합성의 풀체인 검증.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform import Farm, User
from app.db.models.sow import Sow
from app.schemas.events import (
    FarrowingCreate,
    MatingCreate,
    PigletEventCreate,
    WeaningCreate,
)
from app.services import event_service, report_service

pytestmark = pytest.mark.anyio


async def _gilt(db, farm, tag) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=tag, parity=0, status="GILT",
            entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


async def _full_cycle(db, farm, user, sow, *, born_alive, weaned, deaths=0):
    """교배(2026-01-10)→분만(2026-05-05, 115일)→[폐사]→이유(2026-05-26, 21일)."""
    await event_service.record_mating(db, farm.id, user.id, MatingCreate(
        sow_id=sow.id, mating_date=date(2026, 1, 10), mating_type="AI"))
    f = await event_service.record_farrowing(db, farm.id, user.id, FarrowingCreate(
        sow_id=sow.id, farrowing_date=date(2026, 5, 5),
        total_born=born_alive + 1, born_alive=born_alive, stillborn=1, mummified=0))
    if deaths:
        await event_service.record_piglet_event(db, farm.id, user.id, PigletEventCreate(
            sow_id=sow.id, farrowing_id=f.id, event_date=date(2026, 5, 10),
            event_type="DEATH", piglet_count=deaths))
    await event_service.record_weaning(db, farm.id, user.id, WeaningCreate(
        sow_id=sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 26), weaned_count=weaned))
    return f


async def test_reproduction_report_matches_recorded_events(
    db: AsyncSession, test_farm: Farm, test_user: User
):
    # 3두: 실산 10/12/11, 폐사 0/2/0 → 이유 10/10/11
    s1 = await _gilt(db, test_farm, f"R-{uuid.uuid4().hex[:5]}")
    s2 = await _gilt(db, test_farm, f"R-{uuid.uuid4().hex[:5]}")
    s3 = await _gilt(db, test_farm, f"R-{uuid.uuid4().hex[:5]}")
    await _full_cycle(db, test_farm, test_user, s1, born_alive=10, weaned=10)
    await _full_cycle(db, test_farm, test_user, s2, born_alive=12, weaned=10, deaths=2)
    await _full_cycle(db, test_farm, test_user, s3, born_alive=11, weaned=11)

    rows = await report_service.get_reproduction_report(
        db, test_farm.id, date(2026, 1, 1), date(2026, 12, 31), "monthly")

    # 전 기간 합계 = 기록과 일치
    assert sum(r["total_matings"] for r in rows) == 3
    assert sum(r["total_farrowings"] for r in rows) == 3
    assert sum(r["total_weanings"] for r in rows) == 3

    # 분만/이유는 2026-05 버킷
    may = next(r for r in rows if r["period"] == "2026-05")
    assert may["total_farrowings"] == 3
    assert may["total_weanings"] == 3
    assert may["born_alive_sum"] == 33                 # 10+12+11
    assert may["avg_ba"] == pytest.approx(11.0)        # 33/3
    assert may["avg_tb"] == pytest.approx(12.0)        # (11+13+12)/3
    assert may["avg_weaned"] == pytest.approx(31 / 3, abs=0.01)  # 10+10+11
    assert may["total_stillborn"] == 3                 # 각 1

    # 교배는 2026-01 버킷
    jan = next(r for r in rows if r["period"] == "2026-01")
    assert jan["total_matings"] == 3


async def test_sow_status_after_full_cycle_all_open(
    db: AsyncSession, test_farm: Farm, test_user: User
):
    s1 = await _gilt(db, test_farm, f"S-{uuid.uuid4().hex[:5]}")
    await _full_cycle(db, test_farm, test_user, s1, born_alive=10, weaned=10)
    await db.refresh(s1)
    assert s1.status == "OPEN"           # 전량이유 후 공태 복귀
    assert s1.parity == 1                # 분만으로 산차 1
