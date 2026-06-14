"""Schemas for the Reports endpoints."""
from pydantic import BaseModel


class ReproductionRow(BaseModel):
    period: str
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
