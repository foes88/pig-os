"""Schemas for the Reports endpoints."""
from pydantic import BaseModel


class ReproductionRow(BaseModel):
    period: str  # group label: 기간(YYYY-MM 등) 또는 group_by=breed 시 품종명
    total_matings: int
    total_farrowings: int
    total_weanings: int
    fr: float | None = None
    avg_tb: float | None = None
    avg_ba: float | None = None
    avg_weaned: float | None = None
    avg_lactation_days: float | None = None
    pwmr_a: float | None = None
    pwmr_b: float | None = None
    rts_rate: float | None = None
    # ── 확장 지표 (R3) — 미집계 시 0/None ──
    total_born_sum: int | None = None
    born_alive_sum: int | None = None
    total_stillborn: int | None = None
    total_mummified: int | None = None
    stillborn_rate: float | None = None
    mummified_rate: float | None = None
    birth_loss_rate: float | None = None
    mating_1_count: int | None = None
    mating_2_count: int | None = None
    mating_3plus_count: int | None = None
    ai_count: int | None = None
    natural_count: int | None = None


class BenchmarkValue(BaseModel):
    """농장 country 기준값 — 프론트는 비교만(판정 재구현 금지)."""
    metric_code: str
    target: float | None = None
    benchmark_avg: float | None = None
    benchmark_top25: float | None = None
    warning: float | None = None
    critical: float | None = None
    alert_direction: str | None = None
    unit: str | None = None
    source_ref: str | None = None
    confidence: str | None = None


class ProductionSummary(BaseModel):
    """피그플랜식 통합표: rows + 해당 농장 country 기준값 동봉."""
    group_by: str
    period: str
    country_scope: str | None = None
    benchmarks: list[BenchmarkValue] = []
    rows: list[ReproductionRow] = []


class DailyHerd(BaseModel):
    active_sows: int
    gilts: int
    open: int
    pregnant: int
    lactating: int
    accident: int


class DailyCount(BaseModel):
    count: int
    # 분만: total_born/born_alive, 이유: weaned, 자돈폐사: piglets (해당 없으면 0)
    total_born: int = 0
    born_alive: int = 0
    weaned: int = 0
    piglets: int = 0


class DailyReport(BaseModel):
    """일일 사육현황 — PigPlan '일일보고서' 대응."""
    date: str
    herd: DailyHerd
    matings: int
    farrowings: DailyCount
    weanings: DailyCount
    accidents: int
    piglet_deaths: DailyCount
    removals: int


class LedgerEntry(BaseModel):
    """작업대장(Work Ledger) 통합 항목 — 전 이벤트 유형을 한 줄로."""
    id: str
    kind: str            # mating | farrowing | weaning | reproductive | piglet | removal
    event_date: str      # ISO date
    sow_id: str | None = None
    ear_tag: str | None = None
    summary: str


class GrowFinishRow(BaseModel):
    group_code: str
    start_date: str
    end_date: str | None = None
    head_in: int
    head_out: int | None = None
    avg_entry_weight_kg: float | None = None
    avg_exit_weight_kg: float | None = None
    adg_g: float | None = None
    fcr: float | None = None
    mortality_rate: float | None = None


class SowHistoryCycle(BaseModel):
    parity: int
    mating_date: str | None = None
    boar_ids: list[str] = []
    farrowing_date: str | None = None
    tb: int | None = None
    ba: int | None = None
    sb: int | None = None
    mum: int | None = None
    weaned: int | None = None
    weaning_date: str | None = None
    lactation_days: int | None = None
    status: str
