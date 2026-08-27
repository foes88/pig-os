"""트렌드 PSY 정정(#2) — 분자=이유 자돈수 합계, 분모=월별 활성 재고(스펙 §1).

기존 get_trend는 분자를 COUNT(*)(이유 건수)로, 분모를 전체 sows COUNT로 계산해
PSY가 ~복당두수배 과소이고 대시보드 PSY와도 불일치했음.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import get_trend

pytestmark = pytest.mark.anyio


async def test_trend_psy_uses_weaned_count_and_monthly_inventory(db: AsyncSession, test_farm: Farm):
    # 활성 10두(1년 전 입식). 당월 이유 자돈수 합계 40(4건×10). PSY=(40/10)×12=48.0.
    sows = [
        Sow(farm_id=test_farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=1,
            status="OPEN", entry_date=datetime(2025, 6, 1, tzinfo=UTC), entry_type="GILT")
        for _ in range(10)
    ]
    for s in sows:
        db.add(s)
    await db.flush()
    m = Mating(farm_id=test_farm.id, sow_id=sows[0].id, mating_date=date(2026, 2, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=test_farm.id, sow_id=sows[0].id, mating_id=m.id,
                  farrowing_date=date(2026, 5, 20), total_born=12, born_alive=12,
                  stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    # 오늘(2026-06-30) 기준 당월 이유 4건 × 10두 = 40
    for _ in range(4):
        db.add(Weaning(farm_id=test_farm.id, sow_id=sows[0].id, farrowing_id=f.id,
                       weaning_date=date(2026, 6, 15), weaned_count=10))
    await db.flush()

    trend = await get_trend(db, test_farm.id, months=3)
    jun = next((t for t in trend if t.period == "2026-06"), None)
    assert jun is not None, [t.period for t in trend]
    assert jun.psy == pytest.approx(48.0, abs=0.1), \
        f"당월 이유자돈 40/활성 10 ×12 = 48.0 이어야 함(옛 건수기반이면 4.8), got {jun.psy}"
    # HOTFIX(2026-08-27): 트렌드 npd는 WEI 오노출이라 응답에서 항상 null. 실호출로 억제 확인.
    assert all(t.npd is None for t in trend), \
        f"트렌드 npd는 전 기간 null이어야 함(WEI 오노출 억제), got {[(t.period, t.npd) for t in trend]}"
