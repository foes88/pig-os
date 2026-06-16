"""
임계값 관리 라우터 (#4) — 농장 KPI 임계값 조회/override.

override는 OWNER/MANAGER만. 삭제 시 국가/글로벌 값으로 복귀.
"""
from fastapi import APIRouter

from app.core.dependencies import DbDep, FarmDep, require_farm_role
from app.schemas.threshold import ThresholdOverride, ThresholdRow
from app.services import threshold_service

router = APIRouter(prefix="/farms/{farm_id}/thresholds", tags=["Thresholds"])

_ROLES = ("FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN")


@router.get("", response_model=list[ThresholdRow])
async def list_thresholds(farm: FarmDep, db: DbDep) -> list[ThresholdRow]:
    rows = await threshold_service.list_effective(db, farm)
    return [ThresholdRow(**r) for r in rows]


@router.patch(
    "/{metric_code}", response_model=ThresholdRow,
    dependencies=[require_farm_role(*_ROLES)],
)
async def set_threshold(metric_code: str, body: ThresholdOverride, farm: FarmDep, db: DbDep) -> ThresholdRow:
    row = await threshold_service.set_override(db, farm, metric_code, body.warning, body.critical)
    return ThresholdRow(**row)


@router.delete(
    "/{metric_code}", status_code=204,
    dependencies=[require_farm_role(*_ROLES)],
)
async def clear_threshold(metric_code: str, farm: FarmDep, db: DbDep) -> None:
    await threshold_service.clear_override(db, farm, metric_code)
