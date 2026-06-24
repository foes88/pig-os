from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import UUIDMixin

CURRENCY_SYMBOLS: dict[str, str] = {
    "KRW": "₩", "USD": "$", "CNY": "¥", "BRL": "R$", "VND": "₫",
    "EUR": "€", "GBP": "£", "THB": "฿", "PHP": "₱", "IDR": "Rp",
    "MXN": "Mex$",
}


class FarmLocalConfig(BaseModel):
    """Resolved market/region defaults for this farm — used by frontend for unit display."""
    weight_unit: str                       # kg | lb
    currency_code: str                     # KRW / USD / CNY …
    currency_symbol: str                   # ₩ / $ / ¥ …
    min_wean_period: int | None            # compliance minimum weaning age (days)
    requires_traceability: bool
    requires_antibiotic_tracking: bool
    slaughter_weight_target_kg: float | None   # country-typical target, converted for display
    market_code: str | None


class FarmCreate(BaseModel):
    name: str = Field(..., max_length=200)
    country: str = Field(..., min_length=2, max_length=2)
    region: str | None = None
    timezone: str = "UTC"
    language: str = "en"
    currency: str = Field(default="USD", max_length=3)
    unit_system: str = Field(default="METRIC", pattern="^(METRIC|IMPERIAL)$")
    farm_scale: str = Field(default="COMMERCIAL", pattern="^(COMMERCIAL|SMALL|BACKYARD)$")
    internet_reliability: str = Field(default="HIGH", pattern="^(HIGH|LOW|NONE)$")
    notification_channel: str = Field(default="EMAIL")


class FarmUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    timezone: str | None = None
    language: str | None = None
    currency: str | None = None
    notification_channel: str | None = None


class FarmResponse(UUIDMixin):
    org_id: UUID
    farm_code: str
    name: str
    country: str
    region: str | None
    timezone: str
    language: str
    currency: str
    unit_system: str
    farm_scale: str
    internet_reliability: str
    active: bool
    created_at: datetime


class FarmConfigSet(BaseModel):
    """Bulk upsert farm configs (onboarding step)."""
    gestation_days: int | None = Field(None, ge=100, le=130, description="임신 기간 (기본 114일)")
    lactation_days: int | None = Field(None, ge=10, le=40, description="포유 기간 (기본 21일)")
    wei_target_days: int | None = Field(None, ge=1, le=30, description="이유→교배 목표 간격 (기본 7일)")
    pregnancy_check_day: int | None = Field(None, ge=21, le=35, description="임신 확인 시점: 교배 후 N일")
    npd_alert_threshold: int | None = Field(None, ge=1, le=90, description="NPD 경보 기준값 (일)")
    sow_cull_parity_threshold: int | None = Field(None, ge=1, le=15, description="도태 권고 산차")


class OnboardingStatus(BaseModel):
    farm_id: UUID
    has_farm_config: bool
    has_sows: bool
    has_buildings: bool
    onboarding_complete: bool
    completion_pct: int


class FarmReproConfig(BaseModel):
    """Resolved reproductive parameters (defaults applied) for the Farm settings page."""
    gestation_days: int
    lactation_days: int
    wei_target_days: int
    gilt_first_mating_age: int
    slaughter_age: int


class FarmReproConfigUpdate(BaseModel):
    """Partial update of reproductive parameters; only provided fields are upserted."""
    gestation_days: int | None = Field(None, ge=100, le=130)
    lactation_days: int | None = Field(None, ge=10, le=40)
    wei_target_days: int | None = Field(None, ge=1, le=30)
    gilt_first_mating_age: int | None = Field(None, ge=180, le=400)
    slaughter_age: int | None = Field(None, ge=120, le=300)
