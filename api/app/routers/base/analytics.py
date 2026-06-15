"""
Analytics router — 심화 분석 (Phase 2).

GET /api/v1/farms/{farm_id}/analytics/prrs-by-genetics — 품종/유전자별 PRRS 발생률.
"""
from fastapi import APIRouter

from app.core.dependencies import DbDep, FarmDep
from app.schemas.analytics import PrrsByGeneticsResponse
from app.services import analytics_service

router = APIRouter(prefix="/farms/{farm_id}/analytics", tags=["Analytics"])


@router.get("/prrs-by-genetics", response_model=PrrsByGeneticsResponse)
async def prrs_by_genetics(farm: FarmDep, db: DbDep) -> PrrsByGeneticsResponse:
    data = await analytics_service.prrs_by_genetics(db, farm.id)
    return PrrsByGeneticsResponse(**data)
