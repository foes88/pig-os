"""
Onboarding flow (quick start):
  POST /onboarding/complete  → one-step: creates org + user + farm, returns tokens

Extended flow (advanced):
  Step 1: POST /auth/register       → creates org + user
  Step 2: POST /onboarding/farm     → creates farm, links user
  Step 3: POST /onboarding/farm/{id}/config → set farm params
  Step 4: POST /farms/{id}/sows     → add first sows
  GET  /onboarding/farm/{id}/status → completion check
"""
from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.schemas.auth import OnboardingCompleteRequest, OnboardingCompleteResponse
from app.schemas.farm import FarmConfigSet, FarmCreate, FarmResponse, OnboardingStatus
from app.services import auth_service, farm_service

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post("/complete", response_model=OnboardingCompleteResponse, status_code=201)
async def onboarding_complete(body: OnboardingCompleteRequest, db: DbDep):
    """
    One-step onboarding: create org + user + farm in a single call.
    Returns tokens immediately — no follow-up steps required.
    """
    return await auth_service.complete_onboarding(db, body)


@router.post("/farm", response_model=FarmResponse, status_code=201)
async def create_farm(body: FarmCreate, db: DbDep, current_user: CurrentUser):
    """
    Create a farm and link it to the current user.
    farm_code is auto-generated: FARM-{COUNTRY}-{ORG_PREFIX}
    """
    farm = await farm_service.create_farm(db, current_user.org_id, current_user.id, body)
    return FarmResponse.model_validate(farm)


@router.post("/farm/{farm_id}/config", response_model=dict)
async def set_farm_config(
    farm_id: UUID,
    body: FarmConfigSet,
    db: DbDep,
    farm: FarmDep,  # validates access
):
    """
    Upsert reproductive parameters. All fields optional — only provided keys are saved.
    Default values (gestation=114, lactation=21) apply until overridden.
    """
    await farm_service.set_farm_configs(db, farm_id, body)
    return {"saved": True}


@router.get("/farm/{farm_id}/status", response_model=OnboardingStatus)
async def onboarding_status(farm_id: UUID, db: DbDep, farm: FarmDep):
    """Returns completion % and which onboarding steps are done."""
    return await farm_service.get_onboarding_status(db, farm_id)
