from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDMixin


class PigletGroupCreate(BaseModel):
    group_code: str = Field(..., max_length=30, description="그룹 코드 (예: PG-2026-001)")
    batch_name: str | None = Field(None, max_length=100)
    weaning_date: date
    head_count_in: int = Field(..., ge=1, description="이유 두수")
    avg_entry_weight_kg: float | None = Field(None, gt=0, description="평균 이유 체중 (kg)")
    building_id: UUID | None = None
    notes: str | None = None


class PigletGroupTransferOut(BaseModel):
    """전출/판매 처리"""
    transfer_date: date
    transfer_type: str = Field(..., pattern="^(FINISHER_TRANSFER|SOLD|CULLED)$")
    head_count_out: int = Field(..., ge=1)
    avg_exit_weight_kg: float | None = Field(None, gt=0)
    notes: str | None = None


class PigletGroupDeathRecord(BaseModel):
    """자돈 폐사 기록 (누적)"""
    head_count_dead: int = Field(..., ge=1, description="폐사 두수 추가")
    notes: str | None = None


class PigletGroupResponse(UUIDMixin):
    farm_id: UUID
    group_code: str
    batch_name: str | None
    weaning_date: date
    transfer_date: date | None
    transfer_type: str | None
    head_count_in: int
    head_count_dead: int
    head_count_out: int | None
    avg_entry_weight_kg: float | None
    avg_exit_weight_kg: float | None
    building_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PigletTransferCreate(BaseModel):
    """양자/대리모 이벤트"""
    source_sow_id: UUID
    dest_sow_id: UUID
    transfer_date: date
    piglet_count: int = Field(..., ge=1)
    source_farrowing_id: UUID | None = None
    dest_farrowing_id: UUID | None = None
    reason: str | None = None
    notes: str | None = None


class PigletTransferResponse(UUIDMixin):
    farm_id: UUID
    source_sow_id: UUID
    dest_sow_id: UUID
    transfer_date: date
    piglet_count: int
    source_farrowing_id: UUID | None
    dest_farrowing_id: UUID | None
    reason: str | None
    created_at: datetime
