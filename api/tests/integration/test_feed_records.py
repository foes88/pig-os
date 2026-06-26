"""
Feed 입력 경로 테스트 (handoff/FINDING_feed_input_gap.md 해소).
create→영속·FCR 합산 입력원 / 다중대상 거부 / quantity_kg>0 / 월마감 잠금 423.
"""
from datetime import date, datetime, timezone

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
