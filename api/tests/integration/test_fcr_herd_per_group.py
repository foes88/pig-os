"""FCR 대시보드(herd) 경로 — 스펙 §5: CLOSED 그룹의 그룹당 전생애 사료 / 그룹당 증체.

기존: 사료를 record_date 윈도우로 '농장 전체'(group_id NULL 포함) 합산해, gain(end_date
윈도우의 CLOSED 그룹)과 대상·기간이 어긋났음(미출하 그룹 사료가 gain 없이 포함 → 상향편향).
이제 gain과 같은 CLOSED 그룹에 group_id로 귀속된 사료만 합산.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.health import FeedRecord
from app.db.models.ops import FinisherGroup
from app.db.models.platform import Farm
from app.services.kpi_service import build_herd_kpis

pytestmark = pytest.mark.anyio


async def _closed_group(db, farm) -> FinisherGroup:
    g = FinisherGroup(farm_id=farm.id, group_code=f"FG-{uuid.uuid4().hex[:5]}",
                      start_date=date(2026, 1, 10), end_date=date(2026, 3, 20),
                      head_count_in=100, head_count_out=95,
                      avg_entry_weight_kg=25.0, avg_exit_weight_kg=115.0)
    db.add(g)
    await db.flush()
    return g


async def test_fcr_uses_group_linked_feed_only(db: AsyncSession, test_farm: Farm):
    g = await _closed_group(db, test_farm)  # gain = (115-25)*95 = 8550
    # 그룹 귀속 사료(전생애) 합 23085
    for d, q in ((date(2026, 1, 20), 7255), (date(2026, 2, 15), 9234), (date(2026, 3, 10), 6596)):
        db.add(FeedRecord(farm_id=test_farm.id, group_id=g.id, record_date=d, quantity_kg=q))
    # 농장단위(미태깅) 사료 5000 — 귀속 불가라 FCR에서 제외돼야 함(과거엔 포함돼 상향)
    db.add(FeedRecord(farm_id=test_farm.id, group_id=None, record_date=date(2026, 2, 1), quantity_kg=5000))
    await db.flush()

    kpis = await build_herd_kpis(db, test_farm)
    # 23085 / 8550 = 2.700 (미태깅 5000 제외). 과거처럼 포함되면 28085/8550=3.285
    assert kpis["FCR"] == pytest.approx(2.7, abs=0.01), kpis["FCR"]


async def test_fcr_none_when_no_group_linked_feed(db: AsyncSession, test_farm: Farm):
    await _closed_group(db, test_farm)
    # 미태깅 사료만 있음 → 귀속 불가 → FCR None(오도값 대신 정직하게 None)
    db.add(FeedRecord(farm_id=test_farm.id, group_id=None, record_date=date(2026, 2, 1), quantity_kg=9000))
    await db.flush()
    kpis = await build_herd_kpis(db, test_farm)
    assert kpis["FCR"] is None
