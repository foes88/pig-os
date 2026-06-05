from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.schemas.farm import FarmResponse, FarmUpdate
from app.services import farm_service

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.get("", response_model=list[FarmResponse])
async def list_farms(db: DbDep, current_user: CurrentUser):
    farms = await farm_service.list_farms(db, current_user)
    return [FarmResponse.model_validate(f) for f in farms]


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(farm: FarmDep):
    return FarmResponse.model_validate(farm)


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(body: FarmUpdate, farm: FarmDep, db: DbDep):
    updated = await farm_service.update_farm(db, farm, body)
    return FarmResponse.model_validate(updated)
