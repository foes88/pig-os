"""M4 — 번식보고서가 이벤트 없는 기간도 연속으로 채우는지(트렌드와 정합)."""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Mating
from app.db.models.platform import Farm
from app.services import report_service
from app.services.report_service import enumerate_period_keys

pytestmark = pytest.mark.anyio


def test_enumerate_period_keys_monthly():
    assert enumerate_period_keys(date(2026, 1, 1), date(2026, 3, 31), "monthly") == \
        ["2026-01", "2026-02", "2026-03"]


def test_enumerate_period_keys_quarterly_cross_year():
    assert enumerate_period_keys(date(2025, 11, 1), date(2026, 2, 1), "quarterly") == \
        ["2025-Q4", "2026-Q1"]


def test_enumerate_period_keys_annual():
    assert enumerate_period_keys(date(2024, 5, 1), date(2026, 1, 1), "annual") == \
        ["2024", "2025", "2026"]


async def test_sparse_events_produce_contiguous_rows(db: AsyncSession, test_farm: Farm, test_sow):
    # 2026-02에만 교배 1건 → 1~3월 전부 행이 나오고 빈 달은 0.
    db.add(Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 2, 10),
                  mating_type="AI", mating_number=1))
    await db.flush()

    rows = await report_service.get_reproduction_report(
        db, test_farm.id, date(2026, 1, 1), date(2026, 3, 31), "monthly")
    periods = {r["period"]: r for r in rows}
    assert {"2026-01", "2026-02", "2026-03"} <= set(periods)   # 빈 달도 존재
    assert periods["2026-02"]["total_matings"] == 1
    assert periods["2026-01"]["total_matings"] == 0            # 빈 달은 0
    assert periods["2026-03"]["total_matings"] == 0
    assert periods["2026-01"]["fr"] is None                    # 분모 0 → None
