"""
KPI aggregation jobs — run by ARQ worker.

Scheduled (see WorkerSettings.cron_jobs):
  daily_kpi_aggregation   — 매일 00:05 UTC
  weekly_kpi_aggregation  — 매주 월요일 00:10 UTC
  monthly_kpi_aggregation — 매월 1일 00:15 UTC

On-demand (triggered after event write):
  recalculate_farm_kpi(farm_id, period_start, period_end)
"""
from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.ops import KpiSnapshot
from app.db.models.platform import Farm
from app.db.models.sow import Sow

log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _period_bounds(period_type: str, ref: date) -> tuple[date, date]:
    if period_type == "DAILY":
        return ref, ref
    if period_type == "WEEKLY":
        start = ref - timedelta(days=ref.weekday())
        return start, start + timedelta(days=6)
    if period_type == "MONTHLY":
        start = ref.replace(day=1)
        next_month = (start + timedelta(days=32)).replace(day=1)
        return start, next_month - timedelta(days=1)
    # ANNUAL
    return ref.replace(month=1, day=1), ref.replace(month=12, day=31)


async def _calculate_farm_kpi(
    db: AsyncSession,
    farm_id: UUID,
    period_type: str,
    period_start: date,
    period_end: date,
) -> dict:
    """Calculate KPI values for a farm/period. Returns dict ready for KpiSnapshot."""

    # Active sow counts
    active = await db.scalar(
        select(func.count()).select_from(Sow).where(
            Sow.farm_id == farm_id,
            Sow.deleted_at.is_(None),
            Sow.status.notin_(["CULLED", "DEAD"]),
        )
    ) or 0
    gestating = await db.scalar(
        select(func.count()).select_from(Sow).where(
            Sow.farm_id == farm_id, Sow.status == "PREGNANT", Sow.deleted_at.is_(None)
        )
    ) or 0
    lactating = await db.scalar(
        select(func.count()).select_from(Sow).where(
            Sow.farm_id == farm_id, Sow.status == "LACTATING", Sow.deleted_at.is_(None)
        )
    ) or 0

    # Farrowings in period
    farrowings = list(await db.scalars(
        select(Farrowing).where(
            Farrowing.farm_id == farm_id,
            Farrowing.farrowing_date >= period_start,
            Farrowing.farrowing_date <= period_end,
            Farrowing.deleted_at.is_(None),
        )
    ))

    # Matings in period
    matings_count = await db.scalar(
        select(func.count()).select_from(Mating).where(
            Mating.farm_id == farm_id,
            Mating.mating_date >= period_start,
            Mating.mating_date <= period_end,
            Mating.deleted_at.is_(None),
        )
    ) or 0

    # Weanings in period — for PSY calculation
    weanings = list(await db.scalars(
        select(Weaning).where(
            Weaning.farm_id == farm_id,
            Weaning.weaning_date >= period_start,
            Weaning.weaning_date <= period_end,
            Weaning.deleted_at.is_(None),
        )
    ))

    # PSY = (total_weaned / active_sows) * (365 / days_in_period)
    days = max((period_end - period_start).days + 1, 1)
    total_weaned = sum(w.weaned_count for w in weanings)
    psy = round((total_weaned / active * (365 / days)), 2) if active > 0 else None

    # Farrowing rate = farrowings / matings (same period)
    farrowing_rate = (
        round(len(farrowings) / matings_count * 100, 1) if matings_count > 0 else None
    )

    return {
        "psy": psy,
        "farrowing_rate": farrowing_rate,
        "active_sow_count": active,
        "gestating_count": gestating,
        "lactating_count": lactating,
    }


async def _upsert_snapshot(
    db: AsyncSession,
    farm_id: UUID,
    period_type: str,
    period_start: date,
    period_end: date,
    kpi: dict,
) -> None:
    existing = await db.scalar(
        select(KpiSnapshot).where(
            KpiSnapshot.farm_id == farm_id,
            KpiSnapshot.period_type == period_type,
            KpiSnapshot.period_start == period_start,
        )
    )
    if existing:
        for k, v in kpi.items():
            setattr(existing, k, v)
        existing.is_stale = False
        existing.calculated_at = datetime.now(UTC)
    else:
        db.add(KpiSnapshot(
            farm_id=farm_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            is_stale=False,
            **kpi,
        ))
    await db.commit()


# ── ARQ job functions ─────────────────────────────────────────────────────────

async def daily_kpi_aggregation(ctx: dict) -> str:
    """Aggregate daily KPI snapshots for all active farms."""
    today = date.today()
    period_start, period_end = _period_bounds("DAILY", today - timedelta(days=1))

    async with AsyncSessionLocal() as db:
        farm_ids = list(await db.scalars(
            select(Farm.id).where(Farm.deleted_at.is_(None))
        ))

    processed = 0
    errors = 0
    for farm_id in farm_ids:
        try:
            async with AsyncSessionLocal() as db:
                kpi = await _calculate_farm_kpi(db, farm_id, "DAILY", period_start, period_end)
                await _upsert_snapshot(db, farm_id, "DAILY", period_start, period_end, kpi)
            processed += 1
        except Exception as e:
            log.error("daily_kpi farm=%s error=%s", farm_id, e)
            errors += 1

    result = f"daily KPI done: {processed} farms, {errors} errors, period={period_start}"
    log.info(result)
    return result


async def weekly_kpi_aggregation(ctx: dict) -> str:
    """Aggregate weekly KPI snapshots."""
    today = date.today()
    last_week = today - timedelta(weeks=1)
    period_start, period_end = _period_bounds("WEEKLY", last_week)

    async with AsyncSessionLocal() as db:
        farm_ids = list(await db.scalars(
            select(Farm.id).where(Farm.deleted_at.is_(None))
        ))

    processed = 0
    for farm_id in farm_ids:
        try:
            async with AsyncSessionLocal() as db:
                kpi = await _calculate_farm_kpi(db, farm_id, "WEEKLY", period_start, period_end)
                await _upsert_snapshot(db, farm_id, "WEEKLY", period_start, period_end, kpi)
            processed += 1
        except Exception as e:
            log.error("weekly_kpi farm=%s error=%s", farm_id, e)

    return f"weekly KPI done: {processed} farms, period={period_start}~{period_end}"


async def monthly_kpi_aggregation(ctx: dict) -> str:
    """Aggregate monthly KPI snapshots."""
    today = date.today()
    last_month = (today.replace(day=1) - timedelta(days=1))
    period_start, period_end = _period_bounds("MONTHLY", last_month)

    async with AsyncSessionLocal() as db:
        farm_ids = list(await db.scalars(
            select(Farm.id).where(Farm.deleted_at.is_(None))
        ))

    processed = 0
    for farm_id in farm_ids:
        try:
            async with AsyncSessionLocal() as db:
                kpi = await _calculate_farm_kpi(db, farm_id, "MONTHLY", period_start, period_end)
                await _upsert_snapshot(db, farm_id, "MONTHLY", period_start, period_end, kpi)
            processed += 1
        except Exception as e:
            log.error("monthly_kpi farm=%s error=%s", farm_id, e)

    return f"monthly KPI done: {processed} farms, period={period_start}~{period_end}"


async def recalculate_farm_kpi(ctx: dict, farm_id: str, period_start: str, period_end: str) -> str:
    """
    On-demand recalculation triggered after event write (mating/farrowing/weaning).
    Marks matching snapshots as stale and recalculates.
    """
    fid = UUID(farm_id)
    ps = date.fromisoformat(period_start)
    pe = date.fromisoformat(period_end)

    for period_type in ("DAILY", "WEEKLY", "MONTHLY"):
        try:
            async with AsyncSessionLocal() as db:
                kpi = await _calculate_farm_kpi(db, fid, period_type, ps, pe)
                await _upsert_snapshot(db, fid, period_type, ps, pe, kpi)
        except Exception as e:
            log.error("recalc_kpi farm=%s period=%s error=%s", farm_id, period_type, e)

    return f"recalculated KPI farm={farm_id} period={period_start}~{period_end}"
