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


class KpiBenchmark(BaseModel):
    """국가별 벤치마크 (농장 country 기준 effective_metric_values에서 해석)."""
    avg: float | None = None      # 국가 평균
    top25: float | None = None    # 국가 상위 25%
    target: float | None = None   # 목표값


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

    # 이번주(월요일~오늘) 이벤트 건수 — 대시보드 파이프라인 카드용
    week_matings: int = 0
    week_farrowings: int = 0
    week_weanings: int = 0

    # 국가별 벤치마크 — "내 KPI vs 국가평균/상위25%" 비교용 (웹/모바일 공용)
    country: str | None = None
    benchmarks: dict[str, KpiBenchmark] = {}  # "PSY" | "NPD" | "FARROWING_RATE"

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
