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
