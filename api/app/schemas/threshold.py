"""임계값 관리 스키마 (#4)."""
from pydantic import BaseModel, Field


class ThresholdRow(BaseModel):
    metric_code: str
    warning: float | None
    critical: float | None
    avg: float | None
    top25: float | None
    target: float | None
    direction: str
    unit: str
    confidence: str | None
    is_proxy: bool
    source: str | None
    scope: str          # farm | country | global
    is_override: bool   # 농장이 직접 설정한 값인가


class ThresholdOverride(BaseModel):
    warning: float | None = Field(None)
    critical: float | None = Field(None)
