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
    npd: float | None            # 비생산일수(여집합, 모돈-년) — PigPlan 정합
    sow_turnover: float | None = None  # 모돈회전율 = 분만복수 / 평균 상시모돈(경산)
    farrowing_rate: float | None  # percent(0~100) 단일 SSOT — 시드 benchmarks와 동일 스케일. ratio 변환 금지.

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

    # LOSS_CALC — 올해 누적 손실 추정 {amount, currency, lost_pigs, basis, demo} | None
    estimated_loss: dict | None = None


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
    avg_sow_count: float  # 월별 활성 모돈 재고 평균(소수 가능) — 스펙 §1
    total_weaned: int
    psy: float | None
    benchmark_avg: float | None
    target_value: float | None


class NpdBreakdown(BaseModel):
    farm_id: UUID
    period_start: date
    period_end: date
    avg_npd: float | None            # 비생산일수(여집합, 모돈-년 기준) — PigPlan 정합 headline
    return_to_estrus_days: float | None
    weaning_to_mating_days: float | None  # WEI(이유→교배) 참고값
    empty_days: float | None
    npd_target: float | None
    benchmark_avg: float | None
    # rolling 12개월 파생(PigPlan 대조용) — 없으면 None
    sow_turnover: float | None = None       # 모돈회전율 = 분만복수 / 평균 상시모돈(경산)
    avg_gestation_days: float | None = None
    avg_lactation_days: float | None = None


class KpiTrend(BaseModel):
    period: str        # "YYYY-MM"
    psy: float | None
    npd: float | None
    farrowing_rate: float | None  # percent(0~100) — DashboardKpi와 동일 스케일 SSOT.


class KpiPolicyOut(BaseModel):
    """resolved 정책 벡터(리졸버 결과) — 대시보드/룰엔진 구성용. (COUNTRY_KPI_RULE_SPEC v0.4)"""
    kpi_code: str
    compute_enabled: bool | None = None
    display_role: str | None = None
    priority_class: str | None = None
    rule_enabled: bool | None = None
    benchmark_exposure: str | None = None
    evidence_status: str | None = None
