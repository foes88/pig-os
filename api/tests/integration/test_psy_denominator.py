"""PSY 분모 정정 — 스펙 §1: PSY = SUM(weaned_count) / AVG(활성 모돈 재고).

기존 v_farm_psy 뷰는 분모를 '그 해 이유한 모돈수'(COUNT DISTINCT, LEFT JOIN weanings)로
계산해 사육두수가 아니라 이유 실적 모돈수로 나눴음 → PSY 심각 과대(라이브: 20두 농장 9/1=9.0).
스펙대로 월별 활성 재고(entry~exit 윈도우) 12개월 평균으로 정정.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import calculate_psy

pytestmark = pytest.mark.anyio


async def _sow(db, farm, *, entry, exit_=None, deleted=None) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=1,
            status="OPEN", entry_date=entry, exit_date=exit_, deleted_at=deleted, entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


async def test_psy_uses_average_inventory_not_weaning_sows(db: AsyncSession, test_farm: Farm):
    # 활성 10두(2025-06 입식, 미퇴출) — 2026 전월 재고=10 → 평균 10
    sows = [await _sow(db, test_farm, entry=datetime(2025, 6, 1, tzinfo=UTC)) for _ in range(10)]
    # 이유 실적은 단 1두(sow[0])에 몰림, 합계 200 (옛 뷰라면 200/1=200으로 왜곡)
    m = Mating(farm_id=test_farm.id, sow_id=sows[0].id, mating_date=date(2025, 11, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=test_farm.id, sow_id=sows[0].id, mating_id=m.id,
                  farrowing_date=date(2026, 2, 20), total_born=12, born_alive=12,
                  stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    for wc in (50, 50, 50, 50):
        db.add(Weaning(farm_id=test_farm.id, sow_id=sows[0].id, farrowing_id=f.id,
                       weaning_date=date(2026, 3, 15), weaned_count=wc))
    await db.flush()

    detail = await calculate_psy(db, test_farm.id, 2026)
    assert detail is not None
    assert detail.total_weaned == 200
    assert detail.avg_sow_count == pytest.approx(10, abs=0.001), \
        "분모는 사육 모돈 평균(10)이어야 함(이유 실적 모돈수 1 아님)"
    assert detail.psy == pytest.approx(20.0, abs=0.05)


async def test_psy_zero_weanings_is_zero_not_none(db: AsyncSession, test_farm: Farm):
    await _sow(db, test_farm, entry=datetime(2025, 6, 1, tzinfo=UTC))
    detail = await calculate_psy(db, test_farm.id, 2026)
    assert detail is not None and detail.total_weaned == 0
    assert detail.psy == 0.0, "분만/이유 0건이면 PSY=0 (스펙 엣지: NULL 아님)"


async def test_psy_no_inventory_is_none(db: AsyncSession, test_farm: Farm):
    # 활성 모돈 0두 → PSY None
    detail = await calculate_psy(db, test_farm.id, 2026)
    assert detail is None or detail.psy is None
