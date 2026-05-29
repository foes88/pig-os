"""
KPI endpoints — Base tier (free).

Domain access:
- PSY, NPD, alerts → Base (no Addon required)
- FCR → Addon #1 (ADDON_FCR) — handled in addons/fcr router
"""
from datetime import date

from fastapi import APIRouter, Query

from app.core.dependencies import DbDep, FarmDep
from app.schemas.kpi import DashboardKpi, NpdBreakdown, PsyDetail
from app.services import kpi_service

router = APIRouter(prefix="/farms/{farm_id}/kpi", tags=["KPI"])


@router.get("/dashboard", response_model=DashboardKpi)
async def dashboard(farm: FarmDep, db: DbDep):
    """
    Main KPI dashboard.
    Returns PSY, NPD, sow counts, and Rule Engine alerts.
    No Addon subscription required.
    """
    return await kpi_service.get_dashboard(db, farm)


@router.get("/psy", response_model=PsyDetail | None)
async def psy(
    farm: FarmDep,
    db: DbDep,
    year: int = Query(default=date.today().year, ge=2000, le=2099),
):
    """Annual PSY breakdown for the specified year."""
    return await kpi_service.calculate_psy(db, farm.id, year)


@router.get("/npd", response_model=NpdBreakdown)
async def npd(
    farm: FarmDep,
    db: DbDep,
    start: date = Query(default=None, description="Period start (default: Jan 1 this year)"),
    end: date = Query(default=None, description="Period end (default: today)"),
):
    """NPD breakdown: WEI days + return/empty days."""
    today = date.today()
    period_start = start or today.replace(month=1, day=1)
    period_end = end or today
    return await kpi_service.calculate_npd_breakdown(db, farm.id, period_start, period_end)
