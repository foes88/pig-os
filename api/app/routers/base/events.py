"""
Event recording endpoints.
All events are validated in event_service, which also handles:
- sow status transitions
- breeding cycle management
- audit logging
"""
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.db.models.events import Farrowing, Mating, PigletEvent, Weaning
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


@router.get("/matings", response_model=list[MatingResponse])
async def list_matings(
    farm: FarmDep,
    db: DbDep,
    sow_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(Mating).where(Mating.farm_id == farm.id)
    if sow_id:
        q = q.where(Mating.sow_id == sow_id)
    rows = await db.scalars(q.order_by(Mating.mating_date.desc()).limit(limit))
    return [MatingResponse.model_validate(r) for r in rows]


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


@router.get("/farrowings", response_model=list[FarrowingResponse])
async def list_farrowings(
    farm: FarmDep,
    db: DbDep,
    sow_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(Farrowing).where(Farrowing.farm_id == farm.id)
    if sow_id:
        q = q.where(Farrowing.sow_id == sow_id)
    rows = await db.scalars(q.order_by(Farrowing.farrowing_date.desc()).limit(limit))
    return [FarrowingResponse.model_validate(r) for r in rows]


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


@router.get("/weanings", response_model=list[WeaningResponse])
async def list_weanings(
    farm: FarmDep,
    db: DbDep,
    sow_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(Weaning).where(Weaning.farm_id == farm.id)
    if sow_id:
        q = q.where(Weaning.sow_id == sow_id)
    rows = await db.scalars(q.order_by(Weaning.weaning_date.desc()).limit(limit))
    return [WeaningResponse.model_validate(r) for r in rows]


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
    event = await event_service.record_reproductive_event(db, farm.id, current_user.id, body)  # noqa: E501
    return ReproductiveEventResponse.model_validate(event)


@router.get("/piglet_events", response_model=list[PigletEventResponse])
async def list_piglet_events(
    farm: FarmDep,
    db: DbDep,
    sow_id: UUID | None = Query(None),
    farrowing_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(PigletEvent).where(
        PigletEvent.farm_id == farm.id,
        PigletEvent.deleted_at.is_(None),
    )
    if sow_id:
        q = q.where(PigletEvent.sow_id == sow_id)
    if farrowing_id:
        q = q.where(PigletEvent.farrowing_id == farrowing_id)
    rows = await db.scalars(q.order_by(PigletEvent.event_date.desc()).limit(limit))
    return [PigletEventResponse.model_validate(r) for r in rows]


@router.post("/piglet_events", response_model=PigletEventResponse, status_code=201)
async def record_piglet_event(
    body: PigletEventCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    Record an in-lactation piglet event: death, foster in/out.
    farrowing_id is optional — auto-selects most recent farrowing if omitted.
    """
    event = await event_service.record_piglet_event(db, farm.id, current_user.id, body)
    return PigletEventResponse.model_validate(event)
