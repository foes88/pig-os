"""
Event recording endpoints.
All events are validated in event_service, which also handles:
- sow status transitions
- breeding cycle management
- audit logging
"""
from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.schemas.events import (
    FarrowingCreate,
    FarrowingResponse,
    MatingCreate,
    MatingResponse,
    PigletEventCreate,
    PigletEventResponse,
    ReproductiveEventCreate,
    ReproductiveEventResponse,
    WeaningCreate,
    WeaningResponse,
)
from app.services import event_service

router = APIRouter(prefix="/farms/{farm_id}/events", tags=["Events"])


@router.post("/matings", response_model=MatingResponse, status_code=201)
async def record_mating(
    body: MatingCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    Record a mating event. Automatically:
    - Creates or reuses a BreedingCycle
    - Sets sow.status = GESTATING
    """
    event = await event_service.record_mating(db, farm.id, current_user.id, body)
    return MatingResponse.model_validate(event)


@router.post("/farrowings", response_model=FarrowingResponse, status_code=201)
async def record_farrowing(
    body: FarrowingCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    Record a farrowing. Validates gestation period (100–130 days).
    Sets sow.status = LACTATING, increments parity.
    """
    event = await event_service.record_farrowing(db, farm.id, current_user.id, body)
    return FarrowingResponse.model_validate(event)


@router.post("/weanings", response_model=WeaningResponse, status_code=201)
async def record_weaning(
    body: WeaningCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    Record a weaning. Validates nursing period (10–60 days).
    Sets sow.status = WEANED, closes BreedingCycle.
    """
    event = await event_service.record_weaning(db, farm.id, current_user.id, body)
    return WeaningResponse.model_validate(event)


@router.post("/reproductive", response_model=ReproductiveEventResponse, status_code=201)
async def record_reproductive_event(
    body: ReproductiveEventCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    Record non-productive event: return to estrus, abortion, empty, cull, death.
    Critical for accurate NPD calculation.
    """
    event = await event_service.record_reproductive_event(db, farm.id, current_user.id, body)
    return ReproductiveEventResponse.model_validate(event)
