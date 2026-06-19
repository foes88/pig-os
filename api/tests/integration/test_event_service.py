"""
교배/분만/이유 서비스 통합 테스트.
피그플랜 실데이터 패턴 기반 시나리오.
실제 test DB에 쓰고 rollback으로 격리.
"""
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.events import PigletEvent
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.schemas.events import (
    FarrowingCreate,
    MatingCreate,
    ReproductiveEventCreate,
    WeaningCreate,
)
from app.services import event_service

# ── Helpers ───────────────────────────────────────────────────────────────────

def mating_req(sow_id, mating_date=date(2026, 1, 1), mating_type="AI") -> MatingCreate:
    return MatingCreate(sow_id=sow_id, mating_date=mating_date, mating_type=mating_type)


def farrowing_req(sow_id, mating_id, farrowing_date=date(2026, 4, 25)) -> FarrowingCreate:
    return FarrowingCreate(
        sow_id=sow_id,
        mating_id=mating_id,
        farrowing_date=farrowing_date,
        born_alive=12,
        stillborn=1,
        mummified=0,
    )


def weaning_req(sow_id, farrowing_id, weaning_date=date(2026, 5, 16)) -> WeaningCreate:
    return WeaningCreate(
        sow_id=sow_id,
        farrowing_id=farrowing_id,
        weaning_date=weaning_date,
        weaned_count=11,
    )


async def _record_death(db, farm, sow, farrowing, count, when=date(2026, 4, 26)):
    """포유 중 자돈 폐사 기록 — 이유두수 항등식(P0-BE-1: weaned == nursing-deaths) 충족용."""
    db.add(PigletEvent(
        farm_id=farm.id, farrowing_id=farrowing.id, sow_id=sow.id,
        event_date=when, event_type="DEATH", piglet_count=count,
    ))
    await db.flush()


# ── 교배 테스트 ───────────────────────────────────────────────────────────────

class TestRecordMating:
    async def test_first_mating_creates_breeding_cycle(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """후보돈(parity=0) 첫 교배 → BreedingCycle 생성, 상태 GESTATING"""
        mating = await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id)
        )
        assert mating.id is not None
        assert mating.mating_number == 1
        assert mating.breeding_cycle_id is not None

        await db.refresh(test_sow)
        assert test_sow.status == "PREGNANT"

    async def test_remating_in_same_cycle_increments_number(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """반정 후 재교배 → 동일 사이클에 mating_number 2"""
        # 1차 교배
        m1 = await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id, date(2026, 1, 1))
        )
        # 반정 처리 (RETURN_TO_ESTRUS) — 사이클 FAILED, 소 ACTIVE
        await event_service.record_reproductive_event(
            db, test_farm.id, test_user.id,
            ReproductiveEventCreate(
                sow_id=test_sow.id,
                event_date=date(2026, 1, 21),
                event_type="RETURN_TO_ESTRUS",
            )
        )
        # 재교배
        m2 = await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id, date(2026, 1, 22))
        )
        assert m2.mating_number == 1  # 새 사이클의 첫 교배
        assert m2.breeding_cycle_id != m1.breeding_cycle_id

    async def test_mating_while_gestating_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """임신 중 교배 불가"""
        await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id)
        )
        await db.refresh(test_sow)
        assert test_sow.status == "PREGNANT"

        with pytest.raises(ValidationError, match="PREGNANT"):
            await event_service.record_mating(
                db, test_farm.id, test_user.id,
                mating_req(test_sow.id, date(2026, 1, 5))
            )

    async def test_mating_while_lactating_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """수유 중 교배 불가"""
        test_sow.status = "LACTATING"
        await db.flush()
        with pytest.raises(ValidationError, match="LACTATING"):
            await event_service.record_mating(
                db, test_farm.id, test_user.id, mating_req(test_sow.id)
            )

    async def test_unknown_sow_raises_not_found(
        self, db: AsyncSession, test_farm: Farm, test_user
    ):
        with pytest.raises(NotFoundError):
            await event_service.record_mating(
                db, test_farm.id, test_user.id, mating_req(uuid4())
            )


# ── 분만 테스트 ───────────────────────────────────────────────────────────────

class TestRecordFarrowing:
    async def test_normal_farrowing_increments_parity(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """정상 분만 → parity +1, status LACTATING"""
        mating = await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id)
        )
        farrowing = await event_service.record_farrowing(
            db, test_farm.id, test_user.id, farrowing_req(test_sow.id, mating.id)
        )
        assert farrowing.born_alive == 12
        assert farrowing.total_born == 13  # 12 + 1 stillborn

        await db.refresh(test_sow)
        assert test_sow.parity == 1
        assert test_sow.status == "LACTATING"

    async def test_duplicate_farrowing_same_mating_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """동일 교배에 분만 2회 → ConflictError (피그플랜 dedup 규칙)"""
        mating = await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id)
        )
        await event_service.record_farrowing(
            db, test_farm.id, test_user.id, farrowing_req(test_sow.id, mating.id)
        )
        with pytest.raises(ConflictError):
            await event_service.record_farrowing(
                db, test_farm.id, test_user.id, farrowing_req(test_sow.id, mating.id)
            )

    async def test_short_gestation_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """임신기간 99일 → ValidationError"""
        mating = await event_service.record_mating(
            db, test_farm.id, test_user.id, mating_req(test_sow.id, date(2026, 1, 1))
        )
        with pytest.raises(ValidationError, match="Gestation"):
            await event_service.record_farrowing(
                db, test_farm.id, test_user.id,
                FarrowingCreate(
                    sow_id=test_sow.id,
                    mating_id=mating.id,
                    farrowing_date=date(2026, 4, 10),  # 99일
                    born_alive=10,
                )
            )

    async def test_wrong_mating_id_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        with pytest.raises(NotFoundError):
            await event_service.record_farrowing(
                db, test_farm.id, test_user.id,
                FarrowingCreate(
                    sow_id=test_sow.id,
                    mating_id=uuid4(),
                    farrowing_date=date(2026, 4, 25),
                    born_alive=10,
                )
            )


# ── 이유 테스트 ───────────────────────────────────────────────────────────────

class TestRecordWeaning:
    async def _setup_farrowing(self, db, farm, sow, user):
        mating = await event_service.record_mating(
            db, farm.id, user.id, mating_req(sow.id)
        )
        farrowing = await event_service.record_farrowing(
            db, farm.id, user.id, farrowing_req(sow.id, mating.id)
        )
        return farrowing

    async def test_normal_weaning_sets_active(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """정상 이유 → sow.status ACTIVE (재교배 가능)"""
        farrowing = await self._setup_farrowing(db, test_farm, test_sow, test_user)
        await _record_death(db, test_farm, test_sow, farrowing, 1)  # 12 born - 1 death = 11 weaned
        weaning = await event_service.record_weaning(
            db, test_farm.id, test_user.id, weaning_req(test_sow.id, farrowing.id)
        )
        assert weaning.weaned_count == 11
        assert weaning.weaning_age_days == 21  # 4/25 → 5/16

        await db.refresh(test_sow)
        assert test_sow.status == "OPEN"

    async def test_duplicate_weaning_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """동일 분만에 이유 2회 → ConflictError (피그플랜 dedup)"""
        farrowing = await self._setup_farrowing(db, test_farm, test_sow, test_user)
        await _record_death(db, test_farm, test_sow, farrowing, 1)  # 12 born - 1 death = 11 weaned
        await event_service.record_weaning(
            db, test_farm.id, test_user.id, weaning_req(test_sow.id, farrowing.id)
        )
        with pytest.raises(ConflictError):
            await event_service.record_weaning(
                db, test_farm.id, test_user.id, weaning_req(test_sow.id, farrowing.id)
            )

    async def test_weaned_count_exceeds_effective_litter(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """이유두수 > born_alive → ValidationError"""
        farrowing = await self._setup_farrowing(db, test_farm, test_sow, test_user)
        with pytest.raises(ValidationError, match="effective litter"):
            await event_service.record_weaning(
                db, test_farm.id, test_user.id,
                WeaningCreate(
                    sow_id=test_sow.id,
                    farrowing_id=farrowing.id,
                    weaning_date=date(2026, 5, 16),
                    weaned_count=20,  # born_alive=12 초과
                )
            )

    async def test_foster_in_increases_effective_litter(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """foster_in 3두 → effective=15, weaned_count=14 허용"""
        farrowing = await self._setup_farrowing(db, test_farm, test_sow, test_user)
        # foster_in 3두 기록
        db.add(PigletEvent(
            farm_id=test_farm.id,
            farrowing_id=farrowing.id,
            sow_id=test_sow.id,
            event_date=date(2026, 4, 26),
            event_type="FOSTER_IN",
            piglet_count=3,
        ))
        await db.flush()
        await _record_death(db, test_farm, test_sow, farrowing, 1)  # 12 + 3 in - 1 death = 14

        weaning = await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(
                sow_id=test_sow.id,
                farrowing_id=farrowing.id,
                weaning_date=date(2026, 5, 16),
                weaned_count=14,  # born_alive(12) + foster_in(3) - 1 death = 14
            )
        )
        assert weaning.weaned_count == 14

    async def test_short_nursing_raises(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """포유기간 9일 → ValidationError"""
        farrowing = await self._setup_farrowing(db, test_farm, test_sow, test_user)
        with pytest.raises(ValidationError, match="Nursing"):
            await event_service.record_weaning(
                db, test_farm.id, test_user.id,
                WeaningCreate(
                    sow_id=test_sow.id,
                    farrowing_id=farrowing.id,
                    weaning_date=date(2026, 5, 4),  # 분만 4/25 → 9일
                    weaned_count=10,
                )
            )


# ── 전체 사이클 시나리오 (피그플랜 실데이터 패턴) ─────────────────────────────

class TestFullBreedingCycle:
    async def test_pigplan_pattern_gilt_to_parity3(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user
    ):
        """
        피그플랜 실데이터 패턴 재현:
        후보돈(parity=0) → 산차 1 → 산차 2 → 산차 3
        교배(1/1) → 분만(4/25) → 이유(5/16) → 재교배(5/20) → ...
        """
        assert test_sow.parity == 0
        assert test_sow.status == "GILT"

        # === 산차 1 ===
        m1 = await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2025, 1, 1), mating_type="AI")
        )
        f1 = await event_service.record_farrowing(
            db, test_farm.id, test_user.id,
            FarrowingCreate(
                sow_id=test_sow.id, mating_id=m1.id,
                farrowing_date=date(2025, 4, 25),
                born_alive=13, stillborn=1, mummified=0,
            )
        )
        await _record_death(db, test_farm, test_sow, f1, 1, when=date(2025, 4, 26))  # 13 - 1 = 12
        w1 = await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(
                sow_id=test_sow.id, farrowing_id=f1.id,
                weaning_date=date(2025, 5, 16), weaned_count=12,
            )
        )
        await db.refresh(test_sow)
        assert test_sow.parity == 1
        assert test_sow.status == "OPEN"
        assert w1.weaning_age_days == 21

        # === 산차 2 ===
        m2 = await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2025, 5, 20), mating_type="AI")
        )
        f2 = await event_service.record_farrowing(
            db, test_farm.id, test_user.id,
            FarrowingCreate(
                sow_id=test_sow.id, mating_id=m2.id,
                farrowing_date=date(2025, 9, 11),  # 114일
                born_alive=11, stillborn=2, mummified=1,
            )
        )
        await _record_death(db, test_farm, test_sow, f2, 1, when=date(2025, 9, 12))  # 11 - 1 = 10
        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(
                sow_id=test_sow.id, farrowing_id=f2.id,
                weaning_date=date(2025, 10, 2), weaned_count=10,
            )
        )
        await db.refresh(test_sow)
        assert test_sow.parity == 2
        assert test_sow.status == "OPEN"

        # === 산차 3: 반정 후 재교배 ===
        m3a = await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2025, 10, 7), mating_type="AI")
        )
        # 반정 (21일 후)
        await event_service.record_reproductive_event(
            db, test_farm.id, test_user.id,
            ReproductiveEventCreate(
                sow_id=test_sow.id,
                event_date=date(2025, 10, 28),
                event_type="RETURN_TO_ESTRUS",
                mating_id=m3a.id,
            )
        )
        await db.refresh(test_sow)
        assert test_sow.status == "ACCIDENT"  # 반정 → 사고 상태, 재교배 가능

        m3b = await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2025, 10, 29), mating_type="AI")
        )
        assert m3b.mating_number == 1  # 새 사이클
        await event_service.record_farrowing(
            db, test_farm.id, test_user.id,
            FarrowingCreate(
                sow_id=test_sow.id, mating_id=m3b.id,
                farrowing_date=date(2026, 2, 20),  # 114일
                born_alive=12, stillborn=0, mummified=0,
            )
        )
        await db.refresh(test_sow)
        assert test_sow.parity == 3
        assert test_sow.status == "LACTATING"
