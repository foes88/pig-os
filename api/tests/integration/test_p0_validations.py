"""
P0 백엔드 검증 회귀 테스트 (DEV_GUIDE §5 P0-BE-1~13).
새로 추가/연결된 정합성 가드를 락인한다. pigos_test(Docker)에서 실행.
"""
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.db.models.events import PigletEvent
from app.db.models.sow import Boar, Sow
from app.schemas.events import (
    FarrowingCreate,
    MatingCreate,
    PigletEventCreate,
    ReproductiveEventCreate,
    WeaningCreate,
)
from app.services import event_service
from app.validators.finisher import (
    calc_remaining_head,
    validate_finisher_entry,
    validate_finisher_exit_weight,
)


async def _farrow(db, farm, sow, user, ba=12, mate_d=date(2026, 1, 1), farrow_d=date(2026, 4, 25)):
    m = await event_service.record_mating(
        db, farm.id, user.id, MatingCreate(sow_id=sow.id, mating_date=mate_d, mating_type="AI"))
    f = await event_service.record_farrowing(
        db, farm.id, user.id,
        FarrowingCreate(sow_id=sow.id, mating_id=m.id, farrowing_date=farrow_d,
                        born_alive=ba, stillborn=0, mummified=0))
    return m, f


async def _new_sow(db, farm, tag):
    sow = Sow(farm_id=farm.id, ear_tag=tag, parity=0, status="GILT",
              entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(sow)
    await db.flush()
    return sow


# ── P0-BE-7 동일 날짜 중복 교배 ────────────────────────────────────────────────

async def test_duplicate_mating_same_date_raises(db: AsyncSession, test_farm, test_sow, test_user):
    await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
    # 같은 모돈·같은 날짜 재교배 → Conflict (상태도 PREGNANT라 어차피 차단되지만 날짜 가드 우선)
    sow2 = await _new_sow(db, test_farm, "DUP-SOW")
    await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=sow2.id, mating_date=date(2026, 2, 1), mating_type="AI"))
    # sow2를 OPEN으로 되돌려 같은 날짜 재교배 시도
    sow2.status = "OPEN"
    await db.flush()
    with pytest.raises(ConflictError, match="already recorded"):
        await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=sow2.id, mating_date=date(2026, 2, 1), mating_type="AI"))


# ── P0-BE-8 웅돈 ACTIVE 상태 ───────────────────────────────────────────────────

async def test_inactive_boar_blocks_mating(db: AsyncSession, test_farm, test_sow, test_user):
    boar = Boar(farm_id=test_farm.id, ear_tag="BOAR-CULL", status="CULLED",
                entry_date=datetime(2024, 1, 1, tzinfo=UTC))
    db.add(boar)
    await db.flush()
    with pytest.raises(ValidationError, match="cannot be used for mating"):
        await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1),
                         mating_type="NATURAL", boar_id=boar.id))


# ── P0-BE-1 이유두수 항등식 / P0-BE-2 이유체중 범위 ────────────────────────────

async def test_weaning_identity_mismatch_raises(db: AsyncSession, test_farm, test_sow, test_user):
    _, f = await _farrow(db, test_farm, test_sow, test_user, ba=12)
    # 폐사 미기록인데 11두만 이유 → 항등식 위반 (12 != 11)
    with pytest.raises(ValidationError):
        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id,
                          weaning_date=date(2026, 5, 16), weaned_count=11))


async def test_weaning_weight_out_of_range_raises(db: AsyncSession, test_farm, test_sow, test_user):
    _, f = await _farrow(db, test_farm, test_sow, test_user, ba=10)
    with pytest.raises(ValidationError, match="valid range"):
        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id, weaning_date=date(2026, 5, 16),
                          weaned_count=10, avg_weaning_weight_kg=15.0))


# ── P0-BE-4 nursing_head / P0-BE-5 age_days ───────────────────────────────────

async def test_farrowing_sets_nursing_head_and_piglet_age_days(
    db: AsyncSession, test_farm, test_sow, test_user
):
    _, f = await _farrow(db, test_farm, test_sow, test_user, ba=12)
    assert f.nursing_head == 12  # 초기값 = born_alive
    ev = await event_service.record_piglet_event(
        db, test_farm.id, test_user.id,
        PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id, event_date=date(2026, 5, 1),
                          event_type="DEATH", piglet_count=1, reason="CRUSHING"))
    assert ev.age_days == (date(2026, 5, 1) - date(2026, 4, 25)).days == 6


# ── P0-BE-3 양자 거울 레코드 자동생성 ─────────────────────────────────────────

async def test_cross_foster_creates_mirror(db: AsyncSession, test_farm, test_sow, test_user):
    # 두 모돈 모두 분만(LACTATING) 상태로
    _, fa = await _farrow(db, test_farm, test_sow, test_user, ba=12)
    sow_b = await _new_sow(db, test_farm, "FOSTER-B")
    _, fb = await _farrow(db, test_farm, sow_b, test_user, ba=10,
                          mate_d=date(2026, 1, 2), farrow_d=date(2026, 4, 26))
    # A → B 로 2두 전출(FOSTER_OUT)
    await event_service.record_piglet_event(
        db, test_farm.id, test_user.id,
        PigletEventCreate(sow_id=test_sow.id, farrowing_id=fa.id, event_date=date(2026, 5, 1),
                          event_type="FOSTER_OUT", piglet_count=2, target_sow_id=sow_b.id))
    # B 쪽에 거울 FOSTER_IN 자동 생성됐는지
    mirror = await db.scalar(
        select(PigletEvent).where(
            PigletEvent.sow_id == sow_b.id, PigletEvent.event_type == "FOSTER_IN"))
    assert mirror is not None
    assert mirror.piglet_count == 2
    assert mirror.farrowing_id == fb.id


# ── P0-BE-10 임신 중 도폐사 사유 필수 ─────────────────────────────────────────

async def test_pregnant_cull_requires_reason(db: AsyncSession, test_farm, test_sow, test_user):
    await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 1), mating_type="AI"))
    await db.refresh(test_sow)
    assert test_sow.status == "PREGNANT"
    with pytest.raises(ValidationError, match="reason"):
        await event_service.record_reproductive_event(
            db, test_farm.id, test_user.id,
            ReproductiveEventCreate(sow_id=test_sow.id, event_date=date(2026, 2, 1),
                                    event_type="CULLED"))


# ── P0-BE-11/12 비육돈 검증 ───────────────────────────────────────────────────

def test_finisher_entry_weight_range():
    with pytest.raises(ValidationError):
        validate_finisher_entry(entry_count=10, avg_entry_weight_kg=80.0)  # >50
    validate_finisher_entry(entry_count=10, avg_entry_weight_kg=25.0)  # ok


def test_finisher_exit_weight_must_exceed_entry():
    with pytest.raises(ValidationError):
        validate_finisher_exit_weight(avg_exit_weight_kg=20.0, avg_entry_weight_kg=25.0)


def test_finisher_remaining_head():
    class _G:
        head_count_in = 100
        head_count_out = 30
    assert calc_remaining_head(_G()) == 70
