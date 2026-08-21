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
    """국가별 벤치마크 (농장 country 기준 effective_metric_values에서 해석).
    ※ 판정용 threshold(warning/critical/direction)는 여기 담지 않는다 — ADR-KPI-08 §9.1.
    benchmark(비교 표시용) ≠ threshold(판정 정책) ≠ status(판정 결과)."""
    avg: float | None = None      # 국가 평균
    top25: float | None = None    # 국가 상위 25%
    target: float | None = None   # 목표값


class KpiStatus(BaseModel):
    """ADR-KPI-08 canonical status. 백엔드(Rule Engine)가 국가별 정책으로 판정한 결과.

    status: normal | warning | critical | insufficient
    reason: 항상 존재(없으면 None). optional로 두면 프론트가 유무로 분기 → 판단 로직의 입구가 됨.
            어휘: no_data · insufficient_sample · out_of_valid_range · no_policy ·
                  policy_pending · evaluation_skipped · rule_disabled · context_missing
    """
    status: str
    reason: str | None = None


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

    # 정본 kpi_code → 값. 카드를 하나 늘릴 때마다 스키마를 고치지 않기 위한 일반 맵.
    # ★ 룰엔진이 판정에 쓰는 것과 "같은 dict" 를 그대로 노출한다 — 화면에 보이는 숫자와
    #   경고를 낸 숫자가 갈라지지 않게 하려는 것이다.
    # 위 psy/npd/farrowing_rate/sow_turnover 는 기존 계약 유지를 위해 남긴 중복이다.
    metrics: dict[str, float | None] = {}

    # ADR-KPI-08 Phase 1 — 백엔드 소유 KPI 상태(국가별 Rule Engine 판정 결과).
    # 키 = metric_code(benchmarks와 동일 키). 프론트는 이 값을 렌더만 하고 자체 판정 금지.
    kpi_status: dict[str, KpiStatus] = {}

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
    # ※ display_order/local_label 은 여기 없다 — 표현 축은 GET /kpi/presentation 소관.
    #    country_kpi_policy = 써도 되는가 / country_kpi_presentation = 뭐라 부르고 몇 번째인가.


class KpiPresentationItem(BaseModel):
    """표시 KPI 1건 — 거버넌스(CKP) ⨝ 표현(CKPRES) 합성 결과.
    Presentation row 가 없어도 CKP 가 visible 이면 포함되며, 이때 표현값만 null 이다."""
    kpi_code: str
    display_order: int | None = None
    local_label: str | None = None      # 현지 용어(i18n 번역 아님). null=공용 라벨 사용
    priority_class: str | None = None
    display_role: str | None = None


class KpiPresentationOut(BaseModel):
    """국가별 KPI 표현 정책. 순서는 백엔드가 확정한 것이며 프론트 재정렬 금지."""
    country: str | None = None
    headline_kpi: str | None = None     # priority_class='NORTH_STAR' (국가당 1개)
    items: list[KpiPresentationItem] = []
