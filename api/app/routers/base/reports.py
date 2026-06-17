"""
Reports router — reproduction & grow-finish performance, sow breeding history.

Reference: docs/SCREEN_MENU_SPEC.md → Reports.
Aggregation lives in app.services.report_service (pure builders + DB wrappers).
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.dependencies import DbDep, FarmDep
from app.schemas.report import (
    GrowFinishRow,
    ProductionSummary,
    ReproductionRow,
    SowHistoryCycle,
)
from app.services import report_service

router = APIRouter(prefix="/farms/{farm_id}/reports", tags=["Reports"])

MAX_RANGE_DAYS = 731  # ~2 years


def _check_range(start: date, end: date) -> None:
    if end < start:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")
    if (end - start).days > MAX_RANGE_DAYS:
        raise HTTPException(status_code=400, detail="date range cannot exceed 2 years")


@router.get("/reproduction", response_model=list[ReproductionRow])
async def reproduction_report(
    farm: FarmDep,
    db: DbDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    period: str = Query("monthly", pattern="^(monthly|quarterly|annual)$"),
    group_by: str = Query("period", pattern="^(period|breed)$"),
):
    _check_range(start_date, end_date)
    return await report_service.get_reproduction_report(
        db, farm.id, start_date, end_date, period, group_by
    )


@router.get("/production-summary", response_model=ProductionSummary)
async def production_summary(
    farm: FarmDep,
    db: DbDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    period: str = Query("monthly", pattern="^(monthly|quarterly|annual)$"),
    group_by: str = Query("period", pattern="^(period|breed)$"),
):
    """피그플랜식 통합표: 번식성적 + 농장 country 기준값(target/avg/top25) 동봉."""
    _check_range(start_date, end_date)
    return await report_service.get_production_summary(
        db, farm, start_date, end_date, period, group_by
    )


@router.get("/grow-finish", response_model=list[GrowFinishRow])
async def grow_finish_report(
    farm: FarmDep,
    db: DbDep,
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_id: UUID | None = Query(None),
):
    _check_range(start_date, end_date)
    return await report_service.get_grow_finish_report(db, farm.id, start_date, end_date, group_id)


@router.get("/sows/{sow_id}/history", response_model=list[SowHistoryCycle])
async def sow_history(farm: FarmDep, db: DbDep, sow_id: UUID):
    return await report_service.get_sow_history(db, farm.id, sow_id)
