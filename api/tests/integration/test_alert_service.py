"""
Alert service integration (Phase 2) — deterministic via today= param.
Seeds event rows directly, then asserts overdue/cull classification.
Runs on pigos_test (Docker).
"""
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services import alert_service

TODAY = date(2026, 6, 10)


async def _new_sow(db, farm, status, entry_days_ago=400, ear=None):
    sow = Sow(
        farm_id=farm.id,
        ear_tag=ear or f"S-{uuid.uuid4().hex[:6].upper()}",
        parity=0,
        status=status,
        entry_date=datetime(TODAY.year, TODAY.month, TODAY.day, tzinfo=UTC) - timedelta(days=entry_days_ago),
        entry_type="GILT",
    )
    db.add(sow)
    await db.flush()
    return sow


class TestOverdue:
    async def test_pregnant_overdue_farrowing(self, db: AsyncSession, test_farm: Farm):
        sow = await _new_sow(db, test_farm, "PREGNANT")
        db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=TODAY - timedelta(days=120),
                      mating_type="AI", mating_number=1))
        await db.flush()
        rows = await alert_service.get_overdue_sows(db, test_farm.id, today=TODAY)
        mine = [r for r in rows if r["sow_id"] == sow.id]
        assert mine and mine[0]["type"] == "pregnant_overdue_farrowing"

    async def test_open_overdue_mating(self, db: AsyncSession, test_farm: Farm):
        sow = await _new_sow(db, test_farm, "OPEN")
        m = Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=TODAY - timedelta(days=160),
                   mating_type="AI", mating_number=1)
        db.add(m); await db.flush()
        f = Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=m.id,
                      farrowing_date=TODAY - timedelta(days=45), total_born=13, born_alive=12,
                      stillborn=1, mummified=0)
        db.add(f); await db.flush()
        db.add(Weaning(farm_id=test_farm.id, sow_id=sow.id, farrowing_id=f.id,
                       weaning_date=TODAY - timedelta(days=20), weaned_count=11))
        await db.flush()
        rows = await alert_service.get_overdue_sows(db, test_farm.id, today=TODAY)
        mine = [r for r in rows if r["sow_id"] == sow.id]
        assert mine and mine[0]["type"] == "open_overdue_mating"

    async def test_on_schedule_not_flagged(self, db: AsyncSession, test_farm: Farm):
        sow = await _new_sow(db, test_farm, "PREGNANT")
        db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=TODAY - timedelta(days=30),
                      mating_type="AI", mating_number=1))
        await db.flush()
        rows = await alert_service.get_overdue_sows(db, test_farm.id, today=TODAY)
        assert not [r for r in rows if r["sow_id"] == sow.id]


class TestCull:
    async def test_overdue_gilt(self, db: AsyncSession, test_farm: Farm):
        sow = await _new_sow(db, test_farm, "GILT", entry_days_ago=320)
        rows = await alert_service.get_cull_candidates(db, test_farm.id, today=TODAY)
        mine = [r for r in rows if r["sow_id"] == sow.id]
        assert mine and "overdue_gilt" in mine[0]["reasons"]
