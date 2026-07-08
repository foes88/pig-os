"""
Reports integration (Phase 10) — seed events, assert aggregation.
Runs on pigos_test (Docker).
"""
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.health import FeedRecord, Removal
from app.db.models.ops import FinisherGroup
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services import report_service


async def _sow(db, farm):
    s = Sow(farm_id=farm.id, ear_tag=f"R-{uuid.uuid4().hex[:6].upper()}", parity=1,
            status="OPEN", entry_date=date(2024, 1, 1), entry_type="GILT")
    db.add(s); await db.flush()
    return s


class TestReproductionReport:
    async def test_monthly_aggregation(self, db: AsyncSession, test_farm: Farm):
        sow = await _sow(db, test_farm)
        db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2026, 1, 5), mating_type="AI", mating_number=1))
        db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2026, 1, 20), mating_type="AI", mating_number=1))
        f = Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=None, farrowing_date=date(2026, 1, 10),
                      total_born=14, born_alive=13, stillborn=1, mummified=0)
        # mating_id is required (NOT NULL); attach a throwaway mating
        m0 = Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2025, 9, 18), mating_type="AI", mating_number=1)
        db.add(m0); await db.flush()
        f.mating_id = m0.id
        db.add(f)
        await db.flush()
        db.add(Weaning(farm_id=test_farm.id, sow_id=sow.id, farrowing_id=f.id, weaning_date=date(2026, 1, 28),
                       weaned_count=11, weaning_age_days=18))
        await db.flush()

        rows = await report_service.get_reproduction_report(
            db, test_farm.id, date(2026, 1, 1), date(2026, 3, 1), "monthly")
        jan = next((r for r in rows if r["period"] == "2026-01"), None)
        assert jan is not None
        # Sep throwaway mating is out of [Jan,Mar] window → only the 2 Jan matings count
        assert jan["total_matings"] == 2
        assert jan["total_farrowings"] == 1
        assert jan["avg_tb"] == 14.0


class TestReproductionExtended:
    async def test_group_by_breed(self, db: AsyncSession, test_farm: Farm):
        ly = Sow(farm_id=test_farm.id, ear_tag=f"LY-{uuid.uuid4().hex[:6]}", parity=1,
                 status="OPEN", entry_date=date(2024, 1, 1), entry_type="GILT", breed="LY")
        du = Sow(farm_id=test_farm.id, ear_tag=f"DU-{uuid.uuid4().hex[:6]}", parity=1,
                 status="OPEN", entry_date=date(2024, 1, 1), entry_type="GILT", breed="Duroc")
        db.add_all([ly, du]); await db.flush()
        db.add(Mating(farm_id=test_farm.id, sow_id=ly.id, mating_date=date(2026, 2, 1), mating_type="AI", mating_number=1))
        db.add(Mating(farm_id=test_farm.id, sow_id=ly.id, mating_date=date(2026, 3, 1), mating_type="NATURAL", mating_number=2))
        db.add(Mating(farm_id=test_farm.id, sow_id=du.id, mating_date=date(2026, 2, 5), mating_type="AI", mating_number=1))
        await db.flush()

        rows = await report_service.get_reproduction_report(
            db, test_farm.id, date(2026, 1, 1), date(2026, 6, 1), "monthly", "breed")
        by = {r["period"]: r for r in rows}
        assert by["LY"]["total_matings"] == 2
        assert by["Duroc"]["total_matings"] == 1
        # 교배 방식/회차 분해
        assert by["LY"]["ai_count"] == 1
        assert by["LY"]["natural_count"] == 1
        assert by["LY"]["mating_2_count"] == 1

    async def test_stillborn_mummified_rates(self, db: AsyncSession, test_farm: Farm):
        sow = await _sow(db, test_farm)
        m0 = Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2025, 10, 1), mating_type="AI", mating_number=1)
        db.add(m0); await db.flush()
        db.add(Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=m0.id,
                         farrowing_date=date(2026, 2, 2), total_born=16, born_alive=14, stillborn=1, mummified=1))
        await db.flush()
        rows = await report_service.get_reproduction_report(
            db, test_farm.id, date(2026, 2, 1), date(2026, 2, 28), "monthly")
        feb = next(r for r in rows if r["period"] == "2026-02")
        assert feb["total_stillborn"] == 1
        assert feb["total_mummified"] == 1
        assert feb["stillborn_rate"] == 6.2   # 1/16*100 → 6.25 round1 = 6.2
        assert feb["birth_loss_rate"] == 12.5  # 2/16*100

    async def test_production_summary_envelope(self, db: AsyncSession, test_farm: Farm):
        sow = await _sow(db, test_farm)
        db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2026, 1, 5), mating_type="AI", mating_number=1))
        await db.flush()
        out = await report_service.get_production_summary(
            db, test_farm, date(2026, 1, 1), date(2026, 3, 1), "monthly", "period")
        assert out["group_by"] == "period"
        assert isinstance(out["rows"], list)
        assert isinstance(out["benchmarks"], list)  # 시드 없으면 [], 비교만 — 봉투 구조 검증
        assert any(r["period"] == "2026-01" for r in out["rows"])


class TestGrowFinishReport:
    async def test_group_metrics(self, db: AsyncSession, test_farm: Farm):
        db.add(FinisherGroup(
            farm_id=test_farm.id, group_code=f"FG-{uuid.uuid4().hex[:4]}",
            start_date=date(2026, 1, 1), end_date=date(2026, 4, 1),
            head_count_in=100, head_count_out=96,
            avg_entry_weight_kg=25.0, avg_exit_weight_kg=115.0))
        await db.flush()
        rows = await report_service.get_grow_finish_report(
            db, test_farm.id, date(2026, 1, 1), date(2026, 6, 1))
        assert len(rows) == 1
        r = rows[0]
        assert r["adg_g"] == 1000.0          # (115-25)/90*1000
        assert r["mortality_rate"] == 4.0    # (100-96)/100


class TestCostSummaryReport:
    async def test_feed_cost_and_revenue(self, db: AsyncSession, test_farm: Farm):
        # 사료: 1월 원가입력행(100kg×0.5) + 원가미입력행(200kg, coverage 검증용)
        db.add(FeedRecord(farm_id=test_farm.id, record_date=date(2026, 1, 10),
                          quantity_kg=100, unit_cost=0.5, currency="USD"))
        db.add(FeedRecord(farm_id=test_farm.id, record_date=date(2026, 1, 20),
                          quantity_kg=200))  # unit_cost/currency NULL → 기본통화 USD, cost 제외
        # 판매: 2두, 총 700 USD, 체중 240kg
        sow = await _sow(db, test_farm)
        sow2 = await _sow(db, test_farm)
        db.add(Removal(farm_id=test_farm.id, sow_id=sow.id, removal_date=date(2026, 1, 15),
                       removal_type="SOLD", sale_price=300, sale_currency="USD", body_weight_kg=110))
        db.add(Removal(farm_id=test_farm.id, sow_id=sow2.id, removal_date=date(2026, 1, 25),
                       removal_type="SOLD", sale_price=400, sale_currency="USD", body_weight_kg=130))
        # 도태(SOLD 아님) → 수익 제외
        sow3 = await _sow(db, test_farm)
        db.add(Removal(farm_id=test_farm.id, sow_id=sow3.id, removal_date=date(2026, 1, 26),
                       removal_type="CULL", sale_price=None))
        await db.flush()

        out = await report_service.get_cost_summary(
            db, test_farm, date(2026, 1, 1), date(2026, 3, 1), "monthly")
        usd = next(c for c in out["by_currency"] if c["currency"] == "USD")
        assert usd["feed_cost"] == 50.0          # 100×0.5 (200kg행은 원가 없음 → 제외)
        assert usd["feed_qty_kg"] == 300.0       # 물량엔 미입력분 포함
        assert usd["sale_revenue"] == 700.0
        assert usd["sale_head"] == 2             # CULL 제외
        assert usd["net"] == 650.0               # 700 - 50
        assert out["feed_records_total"] == 2
        assert out["feed_records_with_cost"] == 1
        assert out["feed_cost_coverage"] == 50.0
        assert any(r["period"] == "2026-01" for r in out["rows"])
