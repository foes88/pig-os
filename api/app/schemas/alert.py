"""Schemas for the Alerts / Tasks endpoints."""
from uuid import UUID

from pydantic import BaseModel


class OverdueSow(BaseModel):
    type: str  # one of alert_service.OVERDUE_TYPES
    sow_id: UUID
    ear_tag: str
    status: str
    parity: int
    overdue_days: int


class OverdueSummary(BaseModel):
    total: int
    counts: dict[str, int]  # type → count (all 6 keys present, 0 when none)
    items: list[OverdueSow]


class CullCandidate(BaseModel):
    sow_id: UUID
    ear_tag: str
    status: str
    parity: int
    reasons: list[str]  # repeat_rts / aged_low_performer / overdue_gilt
    last_weaned: int | None = None
