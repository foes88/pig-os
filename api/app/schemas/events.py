from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import UUIDMixin
from app.schemas.insight import EventInsight

# ── Event Definitions ────────────────────────────────────────────────────────

class EventDefinitionResponse(BaseModel):
    event_code: str
    category: str
    label_en: str
    label_ko: str | None
    label_vi: str | None
    required_fields: dict[str, Any] | None
    regional_applicability: str

    model_config = {"from_attributes": True}


# ── Mating ──────────────────────────────────────────────────────────────────

class MatingCreate(BaseModel):
    sow_id: UUID
    mating_date: date
    mating_type: str = Field(..., pattern="^(AI|NATURAL)$")
    boar_id: UUID | None = None
    semen_batch: str | None = None
    mating_number: int = Field(default=1, ge=1, le=5)
    notes: str | None = None


class MatingResponse(UUIDMixin):
    farm_id: UUID
    sow_id: UUID
    mating_date: date
    mating_type: str
    boar_id: UUID | None
    mating_number: int
    breeding_cycle_id: UUID | None
    created_at: datetime
    insights: list[EventInsight] = []  # 입력 즉시 분석 결과 (추가 필드, 기존 클라 비파괴)


# ── Farrowing ────────────────────────────────────────────────────────────────

class FarrowingCreate(BaseModel):
    sow_id: UUID
    mating_id: UUID | None = None  # optional — UI가 교배 선택 없이 기록 가능
    farrowing_date: date
    born_alive: int = Field(..., ge=0)
    stillborn: int = Field(default=0, ge=0)
    mummified: int = Field(default=0, ge=0)
    avg_birth_weight_kg: float | None = Field(None, gt=0, description="평균 출생체중(kg)")
    born_alive_male: int | None = Field(None, ge=0)
    born_alive_female: int | None = Field(None, ge=0)
    farrowing_ease: str | None = Field(None, pattern="^(EASY|ASSISTED|DIFFICULT)$")
    notes: str | None = None

    @model_validator(mode="after")
    def set_total_born(self) -> "FarrowingCreate":
        self.total_born = self.born_alive + self.stillborn + self.mummified
        return self

    total_born: int = 0  # model_validator가 자동 계산


class FarrowingResponse(UUIDMixin):
    farm_id: UUID
    sow_id: UUID
    mating_id: UUID
    farrowing_date: date
    total_born: int
    born_alive: int
    stillborn: int
    mummified: int
    nursing_head: int | None = None
    avg_birth_weight_kg: float | None = None
    farrowing_ease: str | None
    breeding_cycle_id: UUID | None
    created_at: datetime
    insights: list[EventInsight] = []


# ── Weaning ──────────────────────────────────────────────────────────────────

class WeaningCreate(BaseModel):
    sow_id: UUID
    farrowing_id: UUID | None = None  # optional — UI가 분만 선택 없이 기록 가능
    weaning_date: date
    weaned_count: int = Field(..., ge=0, le=30)
    avg_weaning_weight_kg: float | None = Field(None, gt=0)
    is_partial: bool = False  # 부분이유: 잔여 포유두수 > 0 허용, 모돈 LACTATING 유지
    notes: str | None = None


class WeaningResponse(UUIDMixin):
    farm_id: UUID
    sow_id: UUID
    farrowing_id: UUID
    weaning_date: date
    weaned_count: int
    weaning_age_days: int | None
    avg_weaning_weight_kg: float | None
    created_at: datetime
    insights: list[EventInsight] = []


# ── Reproductive event ────────────────────────────────────────────────────────

class ReproductiveEventCreate(BaseModel):
    sow_id: UUID
    event_date: date
    event_type: str = Field(
        ...,
        pattern="^(RETURN_TO_ESTRUS|ABORTION|EMPTY|INFERTILE|CULLED|DEAD|TRANSFER_OUT|SOLD|HEAT_DETECTED)$",
    )
    mating_id: UUID | None = None
    detected_method: str | None = Field(None, pattern="^(ULTRASOUND|VISUAL|BEHAVIOR|BLOOD_TEST)$")
    notes: str | None = None


class ReproductiveEventResponse(UUIDMixin):
    farm_id: UUID
    sow_id: UUID
    event_date: date
    event_type: str
    mating_id: UUID | None
    detected_method: str | None
    created_at: datetime


# ── Piglet event ──────────────────────────────────────────────────────────────

class PigletEventCreate(BaseModel):
    farrowing_id: UUID | None = None  # None → auto-lookup most recent farrowing
    sow_id: UUID
    event_date: date
    event_type: str = Field(..., pattern="^(STILLBORN_REMOVAL|DEATH|FOSTER_IN|FOSTER_OUT)$")
    piglet_count: int = Field(..., ge=1)
    reason: str | None = Field(
        None, pattern="^(CRUSHING|SCOURS|STARVATION|CONGENITAL|HYPOTHERMIA|OTHER)$"
    )
    target_sow_id: UUID | None = None
    target_farrowing_id: UUID | None = None
    notes: str | None = None


class PigletEventResponse(UUIDMixin):
    farm_id: UUID
    farrowing_id: UUID
    sow_id: UUID
    event_date: date
    event_type: str
    piglet_count: int
    reason: str | None
    created_at: datetime


# ── Update bodies (Phase 12 — edit/delete) ────────────────────────────────────

class MatingUpdate(BaseModel):
    mating_date: date | None = None
    boar_id: UUID | None = None
    notes: str | None = None


class FarrowingUpdate(BaseModel):
    farrowing_date: date | None = None
    born_alive: int | None = Field(None, ge=0)
    stillborn: int | None = Field(None, ge=0)
    mummified: int | None = Field(None, ge=0)
    avg_birth_weight_kg: float | None = Field(None, gt=0)
    notes: str | None = None


class WeaningUpdate(BaseModel):
    weaning_date: date | None = None
    weaned_count: int | None = Field(None, ge=0, le=30)
    avg_weaning_weight_kg: float | None = Field(None, gt=0)
    notes: str | None = None
