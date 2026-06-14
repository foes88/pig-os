"""
Validation errors E2E (Phase 1/2 validators) — service-level, mirrors test_event_service.py.
Runs against the pigos_test DB (Docker). Each test is transaction-isolated.
"""
import pytest
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services import event_service
from app.schemas.events import (
    FarrowingCreate,
    MatingCreate,
    PigletEventCreate,
    WeaningCreate,
)


async def _mate(db, farm, sow, user, d=date(2026, 1, 1)):
    return await event_service.record_mating(
        db, farm.id, user.id, MatingCreate(sow_id=sow.id, mating_date=d, mating_type="AI")
    )


async def _farrow(db, farm, sow, user, mating_id, d=date(2026, 4, 25), ba=12, sb=1, mum=0):
    return await event_service.record_farrowing(
        db, farm.id, user.id,
        FarrowingCreate(sow_id=sow.id, mating_id=mating_id, farrowing_date=d,
                        born_alive=ba, stillborn=sb, mummified=mum),
    )


class TestMatingValidation:
    async def test_mating_from_pregnant_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        test_sow.status = "PREGNANT"
        await db.flush()
        with pytest.raises(ValidationError, match="only allowed|Mating"):
            await _mate(db, test_farm, test_sow, test_user)

    async def test_mating_before_entry_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        # entry_date fixture = 2024-01-01; mate before that
        with pytest.raises(ValidationError, match="entry date"):
            await _mate(db, test_farm, test_sow, test_user, d=date(2023, 12, 31))


class TestFarrowingValidation:
    async def test_total_born_over_35_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        m = await _mate(db, test_farm, test_sow, test_user)
        with pytest.raises(ValidationError, match="Total Born cannot exceed 35"):
            await _farrow(db, test_farm, test_sow, test_user, m.id, ba=36, sb=0, mum=0)

    async def test_stillborn_over_25_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        m = await _mate(db, test_farm, test_sow, test_user)
        with pytest.raises(ValidationError, match="Stillborn cannot exceed 25"):
            await _farrow(db, test_farm, test_sow, test_user, m.id, ba=4, sb=26, mum=0)

    async def test_farrowing_before_mating_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        m = await _mate(db, test_farm, test_sow, test_user, d=date(2026, 1, 10))
        with pytest.raises(ValidationError):
            await _farrow(db, test_farm, test_sow, test_user, m.id, d=date(2026, 1, 5))


class TestWeaningValidation:
    async def test_weaning_before_farrowing_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        m = await _mate(db, test_farm, test_sow, test_user)
        f = await _farrow(db, test_farm, test_sow, test_user, m.id, d=date(2026, 4, 25))
        with pytest.raises(ValidationError):
            await event_service.record_weaning(
                db, test_farm.id, test_user.id,
                WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id,
                              weaning_date=date(2026, 4, 24), weaned_count=10),
            )


class TestCrossFosteringValidation:
    async def test_foster_over_25_rejected(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        m = await _mate(db, test_farm, test_sow, test_user)
        f = await _farrow(db, test_farm, test_sow, test_user, m.id)
        with pytest.raises(ValidationError, match="cannot exceed 25 piglets per transfer"):
            await event_service.record_piglet_event(
                db, test_farm.id, test_user.id,
                PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id,
                                  event_date=date(2026, 4, 26), event_type="FOSTER_IN",
                                  piglet_count=26),
            )
