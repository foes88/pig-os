"""사료 급여(Feed) 서비스 — 수기 급이량 CRUD.

FCR(kpi_service)·grow-finish 리포트가 SUM(feed_records.quantity_kg)을 읽으므로, 본 입력이 그 입력원.
검증: quantity_kg>0(스키마) + 월마감 잠금(period_locks) 시 423. soft-delete.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models.health import FeedRecord
from app.db.models.ops import FinisherGroup
from app.db.models.sow import Building, Sow
from app.schemas.feed import FeedRecordCreate
from app.services.event_service import _ensure_period_unlocked


async def _ensure_target_in_farm(db: AsyncSession, farm_id: UUID, body: FeedRecordCreate) -> None:
    """사료 대상(sow/group/building)이 해당 농장 소속인지 검증 — 크로스테넌트 오염 차단."""
    if body.sow_id is not None:
        ok = await db.scalar(
            select(Sow.id).where(Sow.id == body.sow_id, Sow.farm_id == farm_id)
        )
        if not ok:
            raise NotFoundError(f"Sow {body.sow_id} not found in this farm")
    if body.group_id is not None:
        ok = await db.scalar(
            select(FinisherGroup.id).where(
                FinisherGroup.id == body.group_id, FinisherGroup.farm_id == farm_id
            )
        )
        if not ok:
            raise NotFoundError(f"Finisher group {body.group_id} not found in this farm")
    if body.building_id is not None:
        ok = await db.scalar(
            select(Building.id).where(
                Building.id == body.building_id, Building.farm_id == farm_id
            )
        )
        if not ok:
            raise NotFoundError(f"Building {body.building_id} not found in this farm")


async def create_feed_record(
    db: AsyncSession, farm_id: UUID, user_id: UUID, body: FeedRecordCreate
) -> FeedRecord:
    # 대상 중복 지정 방지(있으면 1종만)
    targets = [t for t in (body.sow_id, body.group_id, body.building_id) if t is not None]
    if len(targets) > 1:
        raise ValidationError("Specify at most one target among sow_id / group_id / building_id")
    # 대상이 해당 농장 소속인지 검증 (크로스테넌트 차단)
    await _ensure_target_in_farm(db, farm_id, body)
    # 월마감 잠금 검사 (잠긴 기간이면 PeriodLockedError → 423)
    await _ensure_period_unlocked(db, farm_id, body.record_date)

    rec = FeedRecord(
        farm_id=farm_id, record_date=body.record_date, quantity_kg=body.quantity_kg,
        feed_type=body.feed_type, sow_id=body.sow_id, group_id=body.group_id,
        building_id=body.building_id, unit_cost=body.unit_cost, currency=body.currency,
        notes=body.notes, created_by=user_id,
    )
    db.add(rec)
    await db.flush()
    await db.commit()
    await db.refresh(rec)
    return rec


async def list_feed_records(
    db: AsyncSession, farm_id: UUID, *, limit: int = 50, offset: int = 0
) -> list[FeedRecord]:
    rows = await db.scalars(
        select(FeedRecord)
        .where(FeedRecord.farm_id == farm_id, FeedRecord.deleted_at.is_(None))
        .order_by(FeedRecord.record_date.desc(), FeedRecord.created_at.desc())
        .limit(limit).offset(offset)
    )
    return list(rows)


async def delete_feed_record(db: AsyncSession, farm_id: UUID, record_id: UUID) -> None:
    rec = await db.scalar(
        select(FeedRecord).where(
            FeedRecord.id == record_id, FeedRecord.farm_id == farm_id,
            FeedRecord.deleted_at.is_(None),
        )
    )
    if not rec:
        raise NotFoundError("Feed record not found")
    await _ensure_period_unlocked(db, farm_id, rec.record_date)
    from datetime import UTC, datetime
    rec.deleted_at = datetime.now(UTC)
    await db.commit()
