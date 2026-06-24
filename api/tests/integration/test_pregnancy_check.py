"""
임신감정(D1) 통합 — PREGNANT 모돈에서만, 음성=ACCIDENT 전이. (pigos_test, Docker)
"""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.schemas.events import MatingCreate, PregnancyCheckCreate
from app.services import event_service


async def _mate(db, farm, sow, user, d=date(2026, 1, 1)):
    await event_service.record_mating(
        db, farm.id, user.id, MatingCreate(sow_id=sow.id, mating_date=d, mating_type="AI"))
    await db.refresh(sow)
    assert sow.status == "PREGNANT"


class TestPregnancyCheck:
    async def test_positive_keeps_pregnant(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        await _mate(db, test_farm, test_sow, test_user)
        ev = await event_service.record_pregnancy_check(
            db, test_farm.id, test_user.id,
            PregnancyCheckCreate(sow_id=test_sow.id, check_date=date(2026, 1, 25),
                                 result="POSITIVE", days_after_mating=24, method="ULTRASOUND"))
        await db.refresh(test_sow)
        assert ev.result == "POSITIVE"
        assert test_sow.status == "PREGNANT"   # 확진 — 유지

    async def test_negative_transitions_to_accident(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        await _mate(db, test_farm, test_sow, test_user)
        await event_service.record_pregnancy_check(
            db, test_farm.id, test_user.id,
            PregnancyCheckCreate(sow_id=test_sow.id, check_date=date(2026, 1, 28), result="NEGATIVE"))
        await db.refresh(test_sow)
        assert test_sow.status == "ACCIDENT"   # 공태 → 재교배 대기

    async def test_requires_pregnant_sow(self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user):
        # test_sow는 GILT(미교배) → 임신감정 불가
        assert test_sow.status == "GILT"
        with pytest.raises(ValidationError):
            await event_service.record_pregnancy_check(
                db, test_farm.id, test_user.id,
                PregnancyCheckCreate(sow_id=test_sow.id, check_date=date(2026, 1, 25), result="POSITIVE"))
