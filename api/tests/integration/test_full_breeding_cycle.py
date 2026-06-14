"""
Full breeding cycle E2E (Phase 10) — GILT→mate→farrow→wean→re-mate, 2 parities.
Asserts status transitions + parity + weaned formula. Runs on pigos_test (Docker).
"""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.schemas.events import FarrowingCreate, MatingCreate, WeaningCreate
from app.services import event_service


async def _cycle(db, farm, sow, user, mate_d, farrow_d, wean_d, ba=12, weaned=11):
    m = await event_service.record_mating(
        db, farm.id, user.id, MatingCreate(sow_id=sow.id, mating_date=mate_d, mating_type="AI"))
    await db.refresh(sow)
    assert sow.status == "PREGNANT"

    f = await event_service.record_farrowing(
        db, farm.id, user.id,
        FarrowingCreate(sow_id=sow.id, mating_id=m.id, farrowing_date=farrow_d,
                        born_alive=ba, stillborn=1, mummified=0))
    await db.refresh(sow)
    assert sow.status == "LACTATING"

    w = await event_service.record_weaning(
        db, farm.id, user.id,
        WeaningCreate(sow_id=sow.id, farrowing_id=f.id, weaning_date=wean_d, weaned_count=weaned))
    await db.refresh(sow)
    assert sow.status == "OPEN"
    return m, f, w


class TestFullBreedingCycle:
    async def test_two_parities(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        assert test_sow.status == "GILT"
        assert test_sow.parity == 0

        # Parity 1
        await _cycle(db, test_farm, test_sow, test_user,
                     date(2026, 1, 1), date(2026, 4, 25), date(2026, 5, 16))
        await db.refresh(test_sow)
        assert test_sow.parity == 1

        # Parity 2 (re-mate from OPEN after weaning)
        await _cycle(db, test_farm, test_sow, test_user,
                     date(2026, 5, 25), date(2026, 9, 16), date(2026, 10, 7))
        await db.refresh(test_sow)
        assert test_sow.parity == 2
        assert test_sow.status == "OPEN"

    async def test_weaned_not_exceeding_born_alive(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        import pytest

        from app.core.exceptions import ValidationError
        m = await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
        f = await event_service.record_farrowing(
            db, test_farm.id, test_user.id,
            FarrowingCreate(sow_id=test_sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 25),
                            born_alive=10, stillborn=0, mummified=0))
        with pytest.raises(ValidationError):
            await event_service.record_weaning(
                db, test_farm.id, test_user.id,
                WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id,
                              weaning_date=date(2026, 5, 16), weaned_count=12))
