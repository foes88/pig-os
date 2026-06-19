"""
데이터 품질/정합성 리포트(#5) 통합 테스트.
검증이 막는 신규 입력 외, 직접 삽입한 부정합 행을 리포트가 잡아내는지.
"""
from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating
from app.db.models.sow import BreedingCycle, Sow
from app.schemas.events import MatingCreate
from app.services import report_service
from app.services.event_service import record_mating


async def _sow(db, farm, tag, status="OPEN"):
    s = Sow(farm_id=farm.id, ear_tag=tag, parity=1, status=status,
            entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


async def test_litter_mismatch_detected(db: AsyncSession, test_farm, test_user):
    sow = await _sow(db, test_farm, "DQ-LM")
    cyc = BreedingCycle(farm_id=test_farm.id, sow_id=sow.id, parity=1,
                        started_at=datetime(2026, 1, 1, tzinfo=UTC))
    db.add(cyc)
    await db.flush()
    m = Mating(farm_id=test_farm.id, sow_id=sow.id, breeding_cycle_id=cyc.id,
               mating_date=date(2026, 1, 1), mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    # 직접 삽입: total_born(20) ≠ BA(10)+SB(1)+MUM(0)
    db.add(Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=m.id,
                     breeding_cycle_id=cyc.id, farrowing_date=date(2026, 4, 25),
                     total_born=20, born_alive=10, stillborn=1, mummified=0))
    await db.flush()

    issues = await report_service.get_data_quality_report(db, test_farm.id, date(2026, 6, 19))
    lm = [i for i in issues if i["issue_type"] == "LITTER_MISMATCH" and i["ear_tag"] == "DQ-LM"]
    assert len(lm) == 1
    assert lm[0]["severity"] == "CRITICAL"


async def test_date_reversal_detected(db: AsyncSession, test_farm):
    sow = await _sow(db, test_farm, "DQ-DR")
    cyc = BreedingCycle(farm_id=test_farm.id, sow_id=sow.id, parity=1,
                        started_at=datetime(2026, 1, 1, tzinfo=UTC))
    db.add(cyc)
    await db.flush()
    m = Mating(farm_id=test_farm.id, sow_id=sow.id, breeding_cycle_id=cyc.id,
               mating_date=date(2026, 5, 1), mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    # 분만일(4/25) < 교배일(5/1)
    db.add(Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=m.id,
                     breeding_cycle_id=cyc.id, farrowing_date=date(2026, 4, 25),
                     total_born=11, born_alive=10, stillborn=1, mummified=0))
    await db.flush()

    issues = await report_service.get_data_quality_report(db, test_farm.id, date(2026, 6, 19))
    dr = [i for i in issues if i["issue_type"] == "DATE_REVERSAL" and i["ear_tag"] == "DQ-DR"]
    assert len(dr) == 1


async def test_missing_farrowing_overdue(db: AsyncSession, test_farm, test_sow, test_user):
    # PREGNANT인데 교배 후 200일 경과 → MISSING_FARROWING
    await record_mating(db, test_farm.id, test_user.id,
                        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
    await db.refresh(test_sow)
    assert test_sow.status == "PREGNANT"

    issues = await report_service.get_data_quality_report(db, test_farm.id, date(2026, 8, 1))
    mf = [i for i in issues if i["issue_type"] == "MISSING_FARROWING" and i["ear_tag"] == test_sow.ear_tag]
    assert len(mf) == 1
    assert mf[0]["severity"] == "WARNING"


async def test_clean_farm_no_issues(db: AsyncSession, test_farm):
    # 빈/정상 농장 — 이슈 없음
    issues = await report_service.get_data_quality_report(db, test_farm.id, date(2026, 6, 19))
    assert issues == []
