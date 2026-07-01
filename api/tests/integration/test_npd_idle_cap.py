"""#3 — NPD가 60일 넘게 미재교배한 유휴 모돈을 포함(스펙 §3 엣지: 60 cap).

기존 v_sow_npd는 이유 후 60일 내 재교배가 있어야 wei_days를 내고 없으면 NULL →
가장 오래 놀린 모돈이 AVG에서 통째로 빠져 NPD 과소·경고 무력(감사 F3).
이제 60일 넘게 미재교배면 60으로 포함(아직 60일 미경과는 정상 WEI라 NULL 유지).
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import calculate_npd_breakdown

pytestmark = pytest.mark.anyio
# 오늘 2026-06-30 기준: today-60 = 2026-05-01


async def _sow_wean(db, farm, wdate, *, remate_after=None) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=2,
            status="OPEN", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    from app.db.models.events import Farrowing
    m0 = Mating(farm_id=farm.id, sow_id=s.id, mating_date=wdate.replace(month=1),
                mating_type="AI", mating_number=1)
    db.add(m0)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=s.id, mating_id=m0.id,
                  farrowing_date=date(wdate.year, wdate.month, 1), total_born=12, born_alive=12,
                  stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    db.add(Weaning(farm_id=farm.id, sow_id=s.id, farrowing_id=f.id, weaning_date=wdate, weaned_count=11))
    if remate_after is not None:
        from datetime import timedelta
        db.add(Mating(farm_id=farm.id, sow_id=s.id, mating_date=wdate + timedelta(days=remate_after),
                      mating_type="AI", mating_number=2))
    await db.flush()
    return s


async def test_npd_includes_idle_sow_at_cap60(db: AsyncSession, test_farm: Farm):
    # A: 이유 4/01(90일 전), 미재교배 → 60(유휴 포함)
    await _sow_wean(db, test_farm, date(2026, 4, 1))
    # B: 이유 6/01, 7일 후 재교배 → 7
    await _sow_wean(db, test_farm, date(2026, 6, 1), remate_after=7)
    # C: 이유 6/20(10일 전), 미재교배 → NULL(정상 WEI, 제외)
    await _sow_wean(db, test_farm, date(2026, 6, 20))

    npd = await calculate_npd_breakdown(db, test_farm.id, date(2026, 1, 1), date(2026, 12, 31))
    # AVG(60, 7) = 33.5 (C는 NULL 제외). 옛 뷰면 A 제외 → 7.0
    assert npd.avg_npd == pytest.approx(33.5, abs=0.1), \
        f"유휴 모돈(60)이 포함돼 33.5여야 함(옛 뷰면 7.0), got {npd.avg_npd}"
