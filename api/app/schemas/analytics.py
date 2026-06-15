"""Analytics 스키마 — PRRS 유전자 성과 추적 (Phase 2)."""
from uuid import UUID

from pydantic import BaseModel


class PrrsGeneticsRow(BaseModel):
    breed: str | None
    breed_company: str | None
    genetics_id: str | None
    total_sows: int
    affected_sows: int
    prrs_events: int
    incidence_rate: float


class PrrsByGeneticsResponse(BaseModel):
    farm_id: UUID
    rows: list[PrrsGeneticsRow]
    total_sows: int
    total_affected: int
    total_events: int
