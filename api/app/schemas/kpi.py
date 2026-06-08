from datetime import date
from uuid import UUID

from pydantic import BaseModel


class Alert(BaseModel):
    rule_id: str
    kpi: str
    severity: str  # OK / INFO / WARNING / CRITICAL
    message: str
    current_value: float | None = None
    target_value: float | None = None


class DashboardKpi(BaseModel):
    """Main KPI dashboard — Base tier (free). Flat structure for frontend."""
    farm_id: UUID
    as_of: date

    psy: float | None
    npd: float | None
    farrowing_rate: float | None

    active_sows: int
    gestating: int
    lactating: int
    weaned: int

    alerts: list[Alert]


class _KpiValueInternal(BaseModel):
    """Internal — rich KPI value with benchmarks. Not exposed in API responses."""
    value: float | None
    benchmark_avg: float | None
    benchmark_top25: float | None
    target_value: float | None
    unit: str
    status: str  # OK / WARNING / CRITICAL / NO_DATA


class PsyDetail(BaseModel):
    farm_id: UUID
    year: int
    avg_sow_count: int
    total_weaned: int
    psy: float | None
    benchmark_avg: float | None
    target_value: float | None


class NpdBreakdown(BaseModel):
    farm_id: UUID
    period_start: date
    period_end: date
    avg_npd: float | None
    return_to_estrus_days: float | None
    weaning_to_mating_days: float | None
    empty_days: float | None
    npd_target: float | None
    benchmark_avg: float | None


class KpiTrend(BaseModel):
    period: str        # "YYYY-MM"
    psy: float | None
    npd: float | None
    farrowing_rate: float | None
