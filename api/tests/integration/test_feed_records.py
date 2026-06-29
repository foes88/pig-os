"""
Feed 입력 경로 테스트 (handoff/FINDING_feed_input_gap.md 해소).
create→영속·FCR 합산 입력원 / 다중대상 거부 / quantity_kg>0 / 월마감 잠금 423.
"""
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PeriodLockedError, ValidationError
from app.db.models.health import FeedRecord
from app.db.models.ops import PeriodLock
from app.db.models.platform import Farm, User
from app.schemas.feed import FeedRecordCreate
from app.services import feed_service

pytestmark = pytest.mark.anyio


async def test_create_feed_record(db: AsyncSession, test_farm: Farm, test_user: User):
    rec = await feed_service.create_feed_record(
        db, test_farm.id, test_user.id,
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=1200.5, feed_type="비육"))
    assert rec.id is not None and float(rec.quantity_kg) == 1200.5
    got = await db.scalar(select(FeedRecord).where(FeedRecord.id == rec.id))
    assert got is not None and got.deleted_at is None


async def test_feed_sum_is_fcr_input(db: AsyncSession, test_farm: Farm, test_user: User):
    """여러 급여 기록 SUM(quantity_kg) = FCR 분자 입력원."""
    for q in (1000.0, 500.0, 250.0):
        await feed_service.create_feed_record(
            db, test_farm.id, test_user.id,
            FeedRecordCreate(record_date=date(2026, 6, 2), quantity_kg=q))
    total = await db.scalar(
        select(func.coalesce(func.sum(FeedRecord.quantity_kg), 0)).where(
            FeedRecord.farm_id == test_farm.id, FeedRecord.deleted_at.is_(None)))
    assert float(total) == 1750.0


async def test_multiple_targets_rejected(db: AsyncSession, test_farm: Farm, test_user: User):
    from uuid import uuid4
    with pytest.raises(ValidationError):
        await feed_service.create_feed_record(
            db, test_farm.id, test_user.id,
            FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=10,
                             sow_id=uuid4(), group_id=uuid4()))


def test_quantity_must_be_positive():
    """quantity_kg <= 0 → 스키마 거부."""
    with pytest.raises(Exception):
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=0)
    with pytest.raises(Exception):
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=-5)


def test_unit_cost_upper_bound():
    """M4: unit_cost가 DB Numeric(10,4) 상한 초과 → 스키마 422(500 방지)."""
    with pytest.raises(Exception):
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=10, unit_cost=2_000_000)


def test_future_record_date_rejected():
    """M5: 미래일자 record_date → 스키마 거부."""
    from datetime import timedelta
    future = date.today() + timedelta(days=2)
    with pytest.raises(Exception):
        FeedRecordCreate(record_date=future, quantity_kg=10)


async def test_period_lock_blocks_feed(db: AsyncSession, test_farm: Farm, test_user: User):
    db.add(PeriodLock(farm_id=test_farm.id, period_year=2026, period_month=3,
                      locked_by=test_user.id))
    await db.flush()
    with pytest.raises(PeriodLockedError) as ei:
        await feed_service.create_feed_record(
            db, test_farm.id, test_user.id,
            FeedRecordCreate(record_date=date(2026, 3, 15), quantity_kg=100))
    assert ei.value.status_code == 423


async def test_delete_soft(db: AsyncSession, test_farm: Farm, test_user: User):
    rec = await feed_service.create_feed_record(
        db, test_farm.id, test_user.id,
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=50))
    await feed_service.delete_feed_record(db, test_farm.id, rec.id)
    got = await db.scalar(select(FeedRecord).where(FeedRecord.id == rec.id))
    assert got.deleted_at is not None


# ── C6: 대상 농장 소속 검증 (크로스테넌트 차단) ────────────────────────────────
async def _make_group(db, farm, code="FG-T1") -> "FinisherGroup":  # noqa: F821
    from app.db.models.ops import FinisherGroup
    g = FinisherGroup(farm_id=farm.id, group_code=code, start_date=date(2026, 1, 1),
                      head_count_in=100)
    db.add(g)
    await db.flush()
    return g


async def test_feed_valid_group_in_farm_passes(db: AsyncSession, test_farm: Farm, test_user: User):
    g = await _make_group(db, test_farm)
    rec = await feed_service.create_feed_record(
        db, test_farm.id, test_user.id,
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=300, group_id=g.id))
    assert rec.group_id == g.id


async def test_feed_nonexistent_group_rejected(db: AsyncSession, test_farm: Farm, test_user: User):
    from uuid import uuid4

    from app.core.exceptions import NotFoundError
    with pytest.raises(NotFoundError):
        await feed_service.create_feed_record(
            db, test_farm.id, test_user.id,
            FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=300, group_id=uuid4()))


async def test_feed_cross_tenant_group_rejected(
    db: AsyncSession, test_farm: Farm, test_org, test_user: User
):
    """타 농장 group_id로 사료 입력 시 NotFoundError — 크로스테넌트 오염 차단."""
    from app.core.exceptions import NotFoundError
    from app.db.models.platform import Farm as FarmModel
    other = FarmModel(org_id=test_org.id, farm_code="OTHER-1", name="Other Farm",
                      country="KR", timezone="Asia/Seoul")
    db.add(other)
    await db.flush()
    other_group = await _make_group(db, other, code="FG-OTHER")
    with pytest.raises(NotFoundError):
        await feed_service.create_feed_record(
            db, test_farm.id, test_user.id,
            FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=300,
                             group_id=other_group.id))


async def test_feed_sow_in_farm_passes(db: AsyncSession, test_farm: Farm, test_sow, test_user: User):
    rec = await feed_service.create_feed_record(
        db, test_farm.id, test_user.id,
        FeedRecordCreate(record_date=date(2026, 6, 1), quantity_kg=10, sow_id=test_sow.id))
    assert rec.sow_id == test_sow.id
