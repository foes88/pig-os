"""사료 급여(Feed) 입력 스키마 — 수기 급이량 기록.

Core 누락 고리(handoff/FINDING_feed_input_gap.md) 해소: FCR 계산의 입력원.
대상은 선택(농장 전체/사bldg/그룹/모돈). quantity_kg는 필수(>0).
"""
from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FeedRecordCreate(BaseModel):
    record_date: date
    quantity_kg: float = Field(..., gt=0, le=100000, description="급여량(kg). 0 초과")
    feed_type: str | None = Field(None, max_length=50, description="사료 종류(예: 임신돈/포유돈/비육)")
    sow_id: UUID | None = None
    group_id: UUID | None = None        # finisher_group 등
    building_id: UUID | None = None
    # DB unit_cost = Numeric(10,4) → 최대 999,999.9999. 상한 없으면 큰 값에 DB overflow(500) (M4).
    unit_cost: float | None = Field(None, ge=0, le=999999, description="kg당 단가(선택)")
    currency: str | None = Field(None, max_length=3)
    notes: str | None = None

    @field_validator("record_date")
    @classmethod
    def _no_future_date(cls, v: date) -> date:
        # 미래일자 사료는 기간 리포트 왜곡 → 거부 (M5). 오늘까지 허용.
        if v > datetime.now(UTC).date():
            raise ValueError("record_date cannot be in the future")
        return v


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
