"""
Event recording endpoints.
All events are validated in event_service, which also handles:
- sow status transitions
- breeding cycle management
- audit logging
"""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query, Response
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    PregnancyCheck,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import Removal
from app.db.models.master import EventDefinition
from app.db.models.sow import Sow
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
    PregnancyCheckCreate,
    PregnancyCheckResponse,
    ReproductiveEventCreate,
    ReproductiveEventResponse,
    WeaningCreate,
    WeaningResponse,
    WeaningUpdate,
)
from app.schemas.report import LedgerEntry
from app.services import event_service, insight_service

router = APIRouter(prefix="/farms/{farm_id}/events", tags=["Events"])

# 이벤트 삭제(상태 롤백 동반)는 OWNER/MANAGER만. 일상 입력(POST)·수정(PATCH)은 WORKER 허용. (Section D)
_MANAGE_ROLES = ("FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")
# 일상 입력/수정 = WORKER 이상 (VIEWER/VET/API_CLIENT 읽기전용 차단) — Section D2
_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")


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
    q = select(Mating).where(Mating.farm_id == farm.id, Mating.deleted_at.is_(None))
    if sow_id:
        q = q.where(Mating.sow_id == sow_id)
    rows = await db.scalars(q.order_by(Mating.mating_date.desc()).limit(limit))
    return [MatingResponse.model_validate(r) for r in rows]


@router.post("/matings", response_model=MatingResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
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
    q = select(Farrowing).where(Farrowing.farm_id == farm.id, Farrowing.deleted_at.is_(None))
    if sow_id:
        q = q.where(Farrowing.sow_id == sow_id)
    rows = await db.scalars(q.order_by(Farrowing.farrowing_date.desc()).limit(limit))
    return [FarrowingResponse.model_validate(r) for r in rows]


@router.post("/farrowings", response_model=FarrowingResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
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
    q = select(Weaning).where(Weaning.farm_id == farm.id, Weaning.deleted_at.is_(None))
    if sow_id:
        q = q.where(Weaning.sow_id == sow_id)
    rows = await db.scalars(q.order_by(Weaning.weaning_date.desc()).limit(limit))
    return [WeaningResponse.model_validate(r) for r in rows]


@router.get("/ledger", response_model=list[LedgerEntry])
async def event_ledger(
    farm: FarmDep,
    db: DbDep,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    kind: str | None = Query(None, pattern="^(mating|farrowing|weaning|reproductive|piglet|removal)$"),
    limit: int = Query(200, ge=1, le=1000),
):
    """작업대장 — 전 이벤트 유형(교배/분만/이유/사고/자돈/도폐사)을 한 목록으로 통합.
    날짜 범위·유형 필터, 최신순. soft-delete 제외."""
    def _in_range(d: date) -> bool:
        return (start_date is None or d >= start_date) and (end_date is None or d <= end_date)

    # sow_id → ear_tag 매핑(한 번 조회)
    tag_rows = await db.execute(select(Sow.id, Sow.ear_tag).where(Sow.farm_id == farm.id))
    tags = {sid: tag for sid, tag in tag_rows.all()}

    entries: list[LedgerEntry] = []

    if kind in (None, "mating"):
        for m in await db.scalars(select(Mating).where(Mating.farm_id == farm.id, Mating.deleted_at.is_(None))):
            if _in_range(m.mating_date):
                entries.append(LedgerEntry(id=str(m.id), kind="mating", event_date=m.mating_date.isoformat(),
                                           sow_id=str(m.sow_id), ear_tag=tags.get(m.sow_id),
                                           summary=f"{m.mating_type} #{m.mating_number}"))
    if kind in (None, "farrowing"):
        for f in await db.scalars(select(Farrowing).where(Farrowing.farm_id == farm.id, Farrowing.deleted_at.is_(None))):
            if _in_range(f.farrowing_date):
                entries.append(LedgerEntry(id=str(f.id), kind="farrowing", event_date=f.farrowing_date.isoformat(),
                                           sow_id=str(f.sow_id), ear_tag=tags.get(f.sow_id),
                                           summary=f"TB {f.total_born} / BA {f.born_alive}"))
    if kind in (None, "weaning"):
        for w in await db.scalars(select(Weaning).where(Weaning.farm_id == farm.id, Weaning.deleted_at.is_(None))):
            if _in_range(w.weaning_date):
                entries.append(LedgerEntry(id=str(w.id), kind="weaning", event_date=w.weaning_date.isoformat(),
                                           sow_id=str(w.sow_id), ear_tag=tags.get(w.sow_id),
                                           summary=f"weaned {w.weaned_count}"))
    if kind in (None, "reproductive"):
        for r in await db.scalars(select(ReproductiveEvent).where(ReproductiveEvent.farm_id == farm.id, ReproductiveEvent.deleted_at.is_(None))):
            if _in_range(r.event_date):
                entries.append(LedgerEntry(id=str(r.id), kind="reproductive", event_date=r.event_date.isoformat(),
                                           sow_id=str(r.sow_id), ear_tag=tags.get(r.sow_id), summary=r.event_type))
    if kind in (None, "piglet"):
        for p in await db.scalars(select(PigletEvent).where(PigletEvent.farm_id == farm.id, PigletEvent.deleted_at.is_(None))):
            if _in_range(p.event_date):
                entries.append(LedgerEntry(id=str(p.id), kind="piglet", event_date=p.event_date.isoformat(),
                                           sow_id=str(p.sow_id), ear_tag=tags.get(p.sow_id),
                                           summary=f"{p.event_type} {p.piglet_count}"))
    if kind in (None, "removal"):
        for rm in await db.scalars(select(Removal).where(Removal.farm_id == farm.id)):
            if _in_range(rm.removal_date):
                entries.append(LedgerEntry(id=str(rm.id), kind="removal", event_date=rm.removal_date.isoformat(),
                                           sow_id=str(rm.sow_id), ear_tag=tags.get(rm.sow_id), summary=rm.removal_type))

    entries.sort(key=lambda e: e.event_date, reverse=True)
    return entries[:limit]


@router.post("/weanings", response_model=WeaningResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
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


@router.post("/reproductive", response_model=ReproductiveEventResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
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


@router.post("/piglet_events", response_model=PigletEventResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
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


@router.get("/pregnancy_checks", response_model=list[PregnancyCheckResponse])
async def list_pregnancy_checks(
    farm: FarmDep,
    db: DbDep,
    sow_id: UUID | None = Query(None),
):
    """List pregnancy-check records (optionally filtered by sow)."""
    q = select(PregnancyCheck).where(
        PregnancyCheck.farm_id == farm.id, PregnancyCheck.deleted_at.is_(None)
    )
    if sow_id:
        q = q.where(PregnancyCheck.sow_id == sow_id)
    rows = (await db.scalars(q.order_by(PregnancyCheck.check_date.desc()))).all()
    return [PregnancyCheckResponse.model_validate(r) for r in rows]


@router.post("/pregnancy_checks", response_model=PregnancyCheckResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def record_pregnancy_check(
    body: PregnancyCheckCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    Record a pregnancy check on a PREGNANT sow.
    NEGATIVE result = empty/open → sow transitions to ACCIDENT (re-breeding wait).
    """
    event = await event_service.record_pregnancy_check(db, farm.id, current_user.id, body)
    resp = PregnancyCheckResponse.model_validate(event)
    resp.insights = await _attach_insights(db, farm, "pregnancy_check", event)
    return resp



# ── Edit / delete (Phase 12) — status rollback + period-lock guard ────────────

@router.patch("/matings/{mating_id}", response_model=MatingResponse,
              dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def update_mating(mating_id: UUID, body: MatingUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    ev = await event_service.update_mating(db, farm.id, current_user.id, mating_id, body)
    return MatingResponse.model_validate(ev)


@router.delete("/matings/{mating_id}", status_code=204,
               dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def delete_mating(mating_id: UUID, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    await event_service.delete_mating(db, farm.id, current_user.id, mating_id)
    return Response(status_code=204)


@router.patch("/farrowings/{farrowing_id}", response_model=FarrowingResponse,
              dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def update_farrowing(farrowing_id: UUID, body: FarrowingUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    ev = await event_service.update_farrowing(db, farm.id, current_user.id, farrowing_id, body)
    return FarrowingResponse.model_validate(ev)


@router.delete("/farrowings/{farrowing_id}", status_code=204,
               dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def delete_farrowing(farrowing_id: UUID, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    await event_service.delete_farrowing(db, farm.id, current_user.id, farrowing_id)
    return Response(status_code=204)


@router.patch("/weanings/{weaning_id}", response_model=WeaningResponse,
              dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def update_weaning(weaning_id: UUID, body: WeaningUpdate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    ev = await event_service.update_weaning(db, farm.id, current_user.id, weaning_id, body)
    return WeaningResponse.model_validate(ev)


@router.delete("/weanings/{weaning_id}", status_code=204,
               dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def delete_weaning(weaning_id: UUID, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    await event_service.delete_weaning(db, farm.id, current_user.id, weaning_id)
    return Response(status_code=204)
