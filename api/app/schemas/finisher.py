from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDMixin


class FinisherGroupCreate(BaseModel):
    group_code: str = Field(..., max_length=30, description="그룹 코드 (예: FG-2026-001)")
    batch_name: str | None = Field(None, max_length=100)
    start_date: date
    head_count_in: int = Field(..., ge=1, description="입식 두수")
    avg_entry_weight_kg: float | None = Field(None, gt=0, description="평균 입식 체중 (kg)")
    building_id: UUID | None = None
    notes: str | None = None


class FinisherGroupShip(BaseModel):
    """출하 처리"""
    end_date: date
    head_count_out: int = Field(..., ge=1, description="출하 두수")
    avg_exit_weight_kg: float | None = Field(None, gt=0, description="평균 출하 체중 (kg)")
    notes: str | None = None


class FinisherGroupUpdate(BaseModel):
    """그룹 수정 (입식 정보)"""
    batch_name: str | None = Field(None, max_length=100)
    head_count_in: int | None = Field(None, ge=1)
    avg_entry_weight_kg: float | None = Field(None, gt=0)
    notes: str | None = None


class FinisherGroupResponse(UUIDMixin):
    farm_id: UUID
    group_code: str
    batch_name: str | None
    start_date: date
    end_date: date | None
    head_count_in: int
    head_count_out: int | None
    avg_entry_weight_kg: float | None
    avg_exit_weight_kg: float | None
    building_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_active(self) -> bool:
        return self.end_date is None

    @property
    def mortality(self) -> int | None:
        if self.head_count_out is None:
            return None
        return self.head_count_in - self.head_count_out
