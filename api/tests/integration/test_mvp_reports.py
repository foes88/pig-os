"""
MVP 보고서 #1(모돈 상태표) / #3(분만·포유·이유 성적) / #4(도폐사·포유폐사) 통합 테스트.
"""
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import PigletEvent
from app.db.models.health import Removal
from app.db.models.sow import Sow
from app.schemas.events import FarrowingCreate, MatingCreate, PigletEventCreate, WeaningCreate
from app.services import event_service, report_service


async def _new_sow(db, farm, tag, status="GILT", parity=0):
    s = Sow(farm_id=farm.id, ear_tag=tag, parity=parity, status=status,
            entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


# ── #1 모돈 상태표 ────────────────────────────────────────────────────────────
async def test_sow_status_report_counts(db: AsyncSession, test_farm, test_sow):
    # test_sow = GILT(1). 추가로 OPEN 1, PREGNANT 1
    await _new_sow(db, test_farm, "ST-OPEN", status="OPEN")
    await _new_sow(db, test_farm, "ST-PREG", status="PREGNANT")
    rep = await report_service.get_sow_status_report(db, test_farm.id)
    assert rep["total"] == 3
    assert rep["by_status"]["GILT"] == 1
    assert rep["by_status"]["OPEN"] == 1
    assert rep["by_status"]["PREGNANT"] == 1
    assert len(rep["sows"]) == 3


# ── #3 분만·포유·이유 성적표 ──────────────────────────────────────────────────
async def test_farrowing_report_by_parity(db: AsyncSession, test_farm, test_sow, test_user):
    # 교배→분만(BA 12)→폐사 2→이유 10
    m = await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
    f = await event_service.record_farrowing(
        db, test_farm.id, test_user.id,
        FarrowingCreate(sow_id=test_sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 25),
                        born_alive=12, stillborn=1, mummified=0))
    db.add(PigletEvent(farm_id=test_farm.id, farrowing_id=f.id, sow_id=test_sow.id,
                       event_date=date(2026, 4, 26), event_type="DEATH", piglet_count=2))
    await db.flush()
    await event_service.record_weaning(
        db, test_farm.id, test_user.id,
        WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 16),
                      weaned_count=10))

    rows = await report_service.get_farrowing_report(db, test_farm.id, date(2026, 1, 1), date(2026, 12, 31))
    assert len(rows) == 1
    r = rows[0]
    assert r["parity"] == 1  # 분만 시 parity 1로 증가
    assert r["farrowings"] == 1
    assert r["avg_total_born"] == 13
    assert r["avg_born_alive"] == 12
    assert r["avg_weaned"] == 10
    assert r["avg_lactation_days"] == 21


# ── #4 도폐사/포유폐사 리포트 ─────────────────────────────────────────────────
async def test_mortality_report(db: AsyncSession, test_farm, test_sow, test_user):
    # 분만(BA 10) + 포유폐사 2(원인 CRUSHING)
    m = await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
    f = await event_service.record_farrowing(
        db, test_farm.id, test_user.id,
        FarrowingCreate(sow_id=test_sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 25),
                        born_alive=10, stillborn=0, mummified=0))
    await event_service.record_piglet_event(
        db, test_farm.id, test_user.id,
        PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id, event_date=date(2026, 5, 1),
                          event_type="DEATH", piglet_count=2, reason="CRUSHING"))
    # 모돈 도태(REPRODUCTIVE) 1건
    db.add(Removal(farm_id=test_farm.id, sow_id=test_sow.id, removal_date=date(2026, 5, 20),
                   removal_type="CULLED", reason_category="REPRODUCTIVE"))
    await db.flush()

    rep = await report_service.get_mortality_report(db, test_farm.id, date(2026, 1, 1), date(2026, 12, 31))
    assert rep["total_piglet_deaths"] == 2
    assert rep["total_removals"] == 1
    assert rep["born_alive_in_period"] == 10
    assert rep["preweaning_mortality_rate"] == 20.0  # 2/10*100
    assert any(x["key"] == "CRUSHING" and x["piglets"] == 2 for x in rep["piglet_deaths_by_reason"])
    assert any(x["key"] == "REPRODUCTIVE" for x in rep["removals_by_reason"])


async def test_mortality_report_empty(db: AsyncSession, test_farm):
    rep = await report_service.get_mortality_report(db, test_farm.id, date(2026, 1, 1), date(2026, 12, 31))
    assert rep["total_removals"] == 0
    assert rep["preweaning_mortality_rate"] is None
