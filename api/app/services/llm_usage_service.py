"""LLM usage tracking (Addon #1) — monthly count for quota enforcement."""
from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ops import LlmUsageLog


async def monthly_count(db: AsyncSession, farm_id: UUID, today: date | None = None) -> int:
    today = today or datetime.now(UTC).date()
    return await db.scalar(
        select(func.count()).select_from(LlmUsageLog).where(
            LlmUsageLog.farm_id == farm_id,
            LlmUsageLog.year == today.year,
            LlmUsageLog.month == today.month,
        )
    ) or 0


async def record_call(
    db: AsyncSession, farm_id: UUID, intent: str | None = None,
    tokens: int | None = None, today: date | None = None,
) -> None:
    today = today or datetime.now(UTC).date()
    db.add(LlmUsageLog(farm_id=farm_id, year=today.year, month=today.month, intent=intent, tokens=tokens))
    await db.flush()
