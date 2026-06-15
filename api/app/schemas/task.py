"""Task(자동배정 작업) 스키마 — Phase 2."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import UUIDMixin


class TaskResponse(UUIDMixin):
    farm_id: UUID
    sow_id: UUID | None
    ear_tag: str | None = None      # join으로 채움 (편의)
    task_type: str
    title: str
    action: str | None
    status: str
    priority: int
    overdue_days: int | None
    due_date: date | None
    assigned_to: UUID | None
    completed_at: datetime | None
    created_at: datetime


class TaskGenerateResult(BaseModel):
    created: int
    closed: int          # 더 이상 해당되지 않아 자동 종료된 OPEN task 수
    open_total: int


class TaskUpdate(BaseModel):
    status: str | None = None        # DONE | DISMISSED | OPEN
    assigned_to: UUID | None = None
