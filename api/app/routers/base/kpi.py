"""
KPI endpoints — Base tier (free).

Domain access:
- PSY, NPD, alerts → Base (no Addon required)
- FCR → Addon #1 (ADDON_FCR) — handled in addons/fcr router
"""
from datetime import date

from fastapi import APIRouter, Query

from app.core.dependencies import DbDep, FarmDep
from app.schemas.kpi import DashboardKpi, KpiTrend, NpdBreakdown, PsyDetail
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
    """PSY (rolling 12개월, 해당 연도 말 기준 — 당해년도는 오늘까지)."""
    return await kpi_service.calculate_psy(db, farm.id, min(date(year, 12, 31), date.today()))


@router.get("/trend", response_model=list[KpiTrend])
async def trend(
    farm: FarmDep,
    db: DbDep,
    months: int = Query(default=6, ge=1, le=24, description="조회 개월 수"),
    kpi: str = Query(default="psy"),
):
    """Monthly KPI trend — last N months. All three KPIs returned per period."""
    return await kpi_service.get_trend(db, farm.id, months)


@router.get("/npd", response_model=NpdBreakdown)
async def npd(
    farm: FarmDep,
    db: DbDep,
    start: date = Query(default=None, description="Period start (default: Jan 1 this year)"),  # noqa: E501
    end: date = Query(default=None, description="Period end (default: today)"),
):
    """NPD breakdown: 비생산일수(여집합, rolling 12개월 as-of end) + 회전율 + WEI 참고값."""
    today = date.today()
    ref = end or today
    detail = await kpi_service.calculate_npd(db, farm.id, ref)
    if detail is None:
        # 재고 없음 → 빈 브레이크다운(계약 유지)
        return NpdBreakdown(
            farm_id=farm.id, period_start=start or (ref.replace(month=1, day=1)),
            period_end=ref, avg_npd=None, return_to_estrus_days=None,
            weaning_to_mating_days=None, empty_days=None, npd_target=None, benchmark_avg=None,
        )
    return detail
