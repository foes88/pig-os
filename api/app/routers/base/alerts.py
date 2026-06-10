"""
Alerts / Tasks router — overdue sows + cull recommendations.

Reference: docs/SCREEN_MENU_SPEC.md → "Alerts / Tasks".
"""
from app.core.dependencies import DbDep, FarmDep
from app.schemas.alert import CullCandidate, OverdueSow, OverdueSummary
from app.services import alert_service
from fastapi import APIRouter

router = APIRouter(prefix="/farms/{farm_id}/alerts", tags=["Alerts"])


@router.get("/overdue", response_model=OverdueSummary)
async def list_overdue_sows(farm: FarmDep, db: DbDep) -> OverdueSummary:
    rows = await alert_service.get_overdue_sows(db, farm.id)
    counts = {t: 0 for t in alert_service.OVERDUE_TYPES}
    for r in rows:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    return OverdueSummary(
        total=len(rows),
        counts=counts,
        items=[OverdueSow(**r) for r in rows],
    )


@router.get("/cull-candidates", response_model=list[CullCandidate])
async def list_cull_candidates(farm: FarmDep, db: DbDep) -> list[CullCandidate]:
    rows = await alert_service.get_cull_candidates(db, farm.id)
    return [CullCandidate(**r) for r in rows]
