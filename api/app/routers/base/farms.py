from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.schemas.farm import (
    FarmLocalConfig,
    FarmReproConfig,
    FarmReproConfigUpdate,
    FarmResponse,
    FarmUpdate,
)
from app.services import farm_service

router = APIRouter(prefix="/farms", tags=["Farms"])

_MANAGE_ROLES = ("FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN")  # 농장 설정 변경 한정 (Section D)


@router.get("", response_model=list[FarmResponse])
async def list_farms(db: DbDep, current_user: CurrentUser):
    farms = await farm_service.list_farms(db, current_user)
    return [FarmResponse.model_validate(f) for f in farms]


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(farm: FarmDep):
    return FarmResponse.model_validate(farm)


@router.get("/{farm_id}/config", response_model=FarmLocalConfig)
async def get_farm_local_config(farm: FarmDep, db: DbDep):
    """Resolved unit/currency/compliance config for this farm's country."""
    return await farm_service.get_local_config(db, farm)


@router.patch("/{farm_id}", response_model=FarmResponse,
              dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def update_farm(body: FarmUpdate, farm: FarmDep, db: DbDep):
    updated = await farm_service.update_farm(db, farm, body)
    return FarmResponse.model_validate(updated)


@router.get("/{farm_id}/config/repro", response_model=FarmReproConfig)
async def get_repro_config(farm: FarmDep, db: DbDep):
    """Resolved reproductive parameters (gestation/lactation/WSI/gilt age/slaughter age)."""
    return await farm_service.get_repro_config(db, farm.id)


@router.patch("/{farm_id}/config/repro", response_model=FarmReproConfig,
              dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def update_repro_config(body: FarmReproConfigUpdate, farm: FarmDep, db: DbDep):
    """Upsert reproductive parameters; alert thresholds take effect immediately."""
    return await farm_service.set_repro_config(db, farm.id, body)
