"""C2 — NPD가 도태(소프트삭제) 모돈의 과거 이유 이력을 포함.
C4 — 대시보드 분만율이 코호트(build_herd_kpis/룰엔진과 동일)로 통일.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import _cohort_farrowing_rate, calculate_npd_breakdown, get_dashboard

pytestmark = pytest.mark.anyio


async def test_npd_includes_culled_sow_history(db: AsyncSession, test_farm: Farm):
    now = datetime.now(UTC)
    # 이유→7일후 재교배 사이클을 마친 뒤 도태(소프트삭제)된 모돈
    s = Sow(farm_id=test_farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=3,
            status="CULLED", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT",
            exit_date=now, deleted_at=now)
    db.add(s)
    await db.flush()  # s.id 확정 후 참조
    m0 = Mating(farm_id=test_farm.id, sow_id=s.id, mating_date=date(2026, 1, 5),
                mating_type="AI", mating_number=1)
    db.add(m0)
    await db.flush()
    f = Farrowing(farm_id=test_farm.id, sow_id=s.id, mating_id=m0.id, farrowing_date=date(2026, 4, 20),
                  total_born=12, born_alive=12, stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    db.add(Weaning(farm_id=test_farm.id, sow_id=s.id, farrowing_id=f.id,
                   weaning_date=date(2026, 5, 11), weaned_count=11))
    db.add(Mating(farm_id=test_farm.id, sow_id=s.id, mating_date=date(2026, 5, 18),  # 이유 7일 후 재교배
                  mating_type="AI", mating_number=1))
    await db.flush()

    npd = await calculate_npd_breakdown(db, test_farm.id, date(2026, 1, 1), date(2026, 12, 31))
    # 도태 모돈이지만 이유→재교배 7일이 NPD에 잡혀야 함(옛 뷰는 deleted_at 필터로 제외 → None)
    assert npd.avg_npd == pytest.approx(7.0, abs=0.01), npd.avg_npd


async def test_dashboard_farrowing_rate_is_cohort(db: AsyncSession, test_farm: Farm):
    # 코호트 창(오늘-150~-110) 안 초교배 5건 중 4건 분만 → 80%
    ref = date.today()
    from datetime import timedelta
    win = ref - timedelta(days=130)
    for i in range(5):
        sow = Sow(farm_id=test_farm.id, ear_tag=f"C-{uuid.uuid4().hex[:6].upper()}", parity=1,
                  status="OPEN", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
        db.add(sow)
        await db.flush()
        m = Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=win, mating_type="AI", mating_number=1)
        db.add(m)
        await db.flush()
        if i < 4:
            db.add(Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=m.id,
                             farrowing_date=ref - timedelta(days=10), total_born=12, born_alive=11,
                             stillborn=1, mummified=0, nursing_head=11))
    await db.flush()

    cohort = await _cohort_farrowing_rate(db, test_farm.id, ref)
    assert cohort == pytest.approx(80.0)
    dash = await get_dashboard(db, test_farm)
    assert dash.farrowing_rate == pytest.approx(cohort), (dash.farrowing_rate, cohort)
