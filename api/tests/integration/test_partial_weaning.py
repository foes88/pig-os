"""
부분이유(Partial Weaning, P1 #1) 통합 테스트.
잔여 포유두수 모델 + 부분이유 시 LACTATING 유지 + 최종이유 시 OPEN 전이.
"""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.schemas.events import FarrowingCreate, MatingCreate, WeaningCreate
from app.services import event_service


async def _farrow(db, farm, sow, user, ba=12):
    m = await event_service.record_mating(
        db, farm.id, user.id,
        MatingCreate(sow_id=sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
    f = await event_service.record_farrowing(
        db, farm.id, user.id,
        FarrowingCreate(sow_id=sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 25),
                        born_alive=ba, stillborn=0, mummified=0))
    return f


async def test_partial_then_final_weaning(db: AsyncSession, test_farm, test_sow, test_user):
    f = await _farrow(db, test_farm, test_sow, test_user, ba=12)

    # 부분이유 5두 → 모돈 LACTATING 유지
    await event_service.record_weaning(
        db, test_farm.id, test_user.id,
        WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 10),
                      weaned_count=5, is_partial=True))
    await db.refresh(test_sow)
    assert test_sow.status == "LACTATING"

    # 최종이유 7두(잔여 전량) → 모돈 OPEN
    await event_service.record_weaning(
        db, test_farm.id, test_user.id,
        WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 16),
                      weaned_count=7))
    await db.refresh(test_sow)
    assert test_sow.status == "OPEN"


async def test_partial_weaning_exceeding_remaining_raises(db: AsyncSession, test_farm, test_sow, test_user):
    f = await _farrow(db, test_farm, test_sow, test_user, ba=12)
    await event_service.record_weaning(
        db, test_farm.id, test_user.id,
        WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 10),
                      weaned_count=5, is_partial=True))
    # 잔여 7인데 8 시도 → 422
    with pytest.raises(ValidationError, match="remaining nursing"):
        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 16),
                          weaned_count=8, is_partial=True))


async def test_weaning_after_fully_weaned_raises(db: AsyncSession, test_farm, test_sow, test_user):
    f = await _farrow(db, test_farm, test_sow, test_user, ba=10)
    # 최종이유 전량
    await event_service.record_weaning(
        db, test_farm.id, test_user.id,
        WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 16),
                      weaned_count=10))
    # 추가 이유 시도 → 잔여 0 → 409
    with pytest.raises(ConflictError, match="fully weaned"):
        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 17),
                          weaned_count=1, is_partial=True))


async def test_final_weaning_must_equal_remaining(db: AsyncSession, test_farm, test_sow, test_user):
    f = await _farrow(db, test_farm, test_sow, test_user, ba=12)
    # 최종이유인데 잔여(12)와 불일치(10) → 항등식 422
    with pytest.raises(ValidationError):
        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 16),
                          weaned_count=10))
