"""
Event recording endpoints.
All events are validated in event_service, which also handles:
- sow status transitions
- breeding cycle management
- audit logging
"""
from uuid import UUID

from fastapi import APIRouter, Query, Response
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.db.models.events import Farrowing, Mating, PigletEvent, Weaning
from app.db.models.master import EventDefinition
from app.schemas.events import (
    EventDefinitionResponse,
    FarrowingCreate,
    FarrowingResponse,
    FarrowingUpdate,
    MatingCreate,
    MatingResponse,
    MatingUpdate,
    PigletEventCreate,
    PigletEventResponse,
    ReproductiveEventCreate,
    ReproductiveEventResponse,
    WeaningCreate,
    WeaningResponse,
    WeaningUpdate,
)
from app.services import event_service, insight_service

router = APIRouter(prefix="/farms/{farm_id}/events", tags=["Events"])


async def _attach_insights(db, farm, event_type: str, event) -> list:
    """이벤트 분석 → WARNING↑ 알림 적재 → insight 리스트 반환.
    분석 실패가 입력(이미 커밋됨)을 깨지 않게 격리."""
    try:
        insights = await insight_service.analyze_event(db, farm, event_type, event)
        if insights:
            await insight_service.persist_insights(db, farm, event.sow_id, insights)
        return insights
    except Exception:  # noqa: BLE001 — 분석 실패는 무시(입력은 성공 유지)
        return []


@router.get("/definitions", response_model=list[EventDefinitionResponse])
async def list_event_definitions(farm: FarmDep, db: DbDep):
    """
    Return event types applicable to this farm's country.
    Filters regional_applicability: ALL always included;
    comma-separated ISO codes included only if farm.country matches.
    Phase filter: MVP only.
    """
    rows = list(await db.scalars(
        select(EventDefinition)
        .where(EventDefinition.phase == "MVP")
        .order_by(EventDefinition.sort_order)
    ))
    country = (farm.country or "").upper()

    def _applicable(ev: EventDefinition) -> bool:
        ra = (ev.regional_applicability or "ALL").upper()
        if ra == "ALL":
            return True
        return country in [c.strip() for c in ra.split(",")]

    return [
        EventDefinitionResponse.model_validate(r)
        for r in rows if _applicable(r)
    ]


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
    resp = MatingResponse.model_validate(event)
    resp.insights = await _attach_insights(db, farm, "mating", event)
    return resp


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
    resp = FarrowingResponse.model_validate(event)
    resp.insights = await _attach_insights(db, farm, "farrowing", event)
    return resp


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
    resp = WeaningResponse.model_validate(event)
    resp.insights = await _attach_insights(db, farm, "weaning", event)
    return resp


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



# ── Edit / delete (Phase 12) — status rollback + period-lock guard ────────────

@router.patch("/matings/{mating_id}", response_model=MatingResponse)
async def update_mating(mating_id: UUID, body: MatingUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    ev = await event_service.update_mating(db, farm.id, current_user.id, mating_id, body)
    return MatingResponse.model_validate(ev)


@router.delete("/matings/{mating_id}", status_code=204)
async def delete_mating(mating_id: UUID, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    await event_service.delete_mating(db, farm.id, current_user.id, mating_id)
    return Response(status_code=204)


@router.patch("/farrowings/{farrowing_id}", response_model=FarrowingResponse)
async def update_farrowing(farrowing_id: UUID, body: FarrowingUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    ev = await event_service.update_farrowing(db, farm.id, current_user.id, farrowing_id, body)
    return FarrowingResponse.model_validate(ev)


@router.delete("/farrowings/{farrowing_id}", status_code=204)
async def delete_farrowing(farrowing_id: UUID, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    await event_service.delete_farrowing(db, farm.id, current_user.id, farrowing_id)
    return Response(status_code=204)


@router.patch("/weanings/{weaning_id}", response_model=WeaningResponse)
async def update_weaning(weaning_id: UUID, body: WeaningUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    ev = await event_service.update_weaning(db, farm.id, current_user.id, weaning_id, body)
    return WeaningResponse.model_validate(ev)


@router.delete("/weanings/{weaning_id}", status_code=204)
async def delete_weaning(weaning_id: UUID, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    await event_service.delete_weaning(db, farm.id, current_user.id, weaning_id)
    return Response(status_code=204)
