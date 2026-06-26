"""사료 급여(Feed) 입력 스키마 — 수기 급이량 기록.

Core 누락 고리(handoff/FINDING_feed_input_gap.md) 해소: FCR 계산의 입력원.
대상은 선택(농장 전체/사bldg/그룹/모돈). quantity_kg는 필수(>0).
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FeedRecordCreate(BaseModel):
    record_date: date
    quantity_kg: float = Field(..., gt=0, le=100000, description="급여량(kg). 0 초과")
    feed_type: str | None = Field(None, max_length=50, description="사료 종류(예: 임신돈/포유돈/비육)")
    sow_id: UUID | None = None
    group_id: UUID | None = None        # finisher_group 등
    building_id: UUID | None = None
    unit_cost: float | None = Field(None, ge=0, description="kg당 단가(선택)")
    currency: str | None = Field(None, max_length=3)
    notes: str | None = None


class FeedRecordResponse(BaseModel):
    id: UUID
    farm_id: UUID
    record_date: date
    quantity_kg: float
    feed_type: str | None
    sow_id: UUID | None
    group_id: UUID | None
    building_id: UUID | None
    unit_cost: float | None
    currency: str | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
