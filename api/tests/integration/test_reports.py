"""
Reports integration (Phase 10) — seed events, assert aggregation.
Runs on pigos_test (Docker).
"""
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
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
