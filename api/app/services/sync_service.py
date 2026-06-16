"""
Offline sync service — the most critical validation layer in PigOS.

Design contract:
  - Per-item atomicity: one failure never blocks others
  - Idempotency: re-sending the same UUID = same result (merge, not error)
  - dry_run=True: validate everything, write nothing
  - All unresolved conflicts → sync_conflict_queue table (never silently dropped)
  - Every sync run → sync_logs (full audit trail for debugging)
  - Farm-level advisory lock → no concurrent sync race conditions

Conflict resolution matrix (see docs/specs/2026-05-19_offline-sync-spec.md):
  DUPLICATE_EVENT  (<1h, same date)  → LWW merge (ACCEPTED)
  DUPLICATE_EVENT  (different date)  → CONFLICT (user decision)
  PERIOD_LOCKED                      → REJECTED
  SOW_NOT_FOUND                      → REJECTED
  STATUS_CONFLICT                    → REJECTED + server state returned
  CYCLE_CONFLICT   (same batch)      → LWW merge (ACCEPTED)
  CYCLE_CONFLICT   (different batch) → CONFLICT
  FUTURE_DATE      (>1 day ahead)    → REJECTED
  STALE_CLIENT     (>30 days)        → require_full_sync flag
"""
from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import HealthEvent, Removal
from app.db.models.ops import PeriodLock, SyncLog
from app.db.models.platform import AuditLog, Farm
from app.db.models.sow import Sow
from app.schemas.sync import (
    ServerChanges,
    SyncAccepted,
    SyncConflict,
    SyncFarrowing,
    SyncHealthEvent,
    SyncMating,
    SyncPigletEvent,
    SyncRejected,
    SyncReproductiveEvent,
    SyncRequest,
    SyncResponse,
    SyncWeaning,
)

_FULL_SYNC_THRESHOLD_DAYS = 30
_FUTURE_DATE_TOLERANCE_DAYS = 1
_DUPLICATE_MERGE_WINDOW_HOURS = 1
_MAX_ITEMS_PER_REQUEST = 500


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(s: str) -> date:
    return date.fromisoformat(s)


async def _check_period_locked(db: AsyncSession, farm_id: UUID, event_date: date) -> PeriodLock | None:
    return await db.scalar(
        select(PeriodLock).where(
            PeriodLock.farm_id == farm_id,
            PeriodLock.period_year == event_date.year,
            PeriodLock.period_month == event_date.month,
            PeriodLock.unlocked_at.is_(None),
        )
    )


async def _get_sow(db: AsyncSession, farm_id: UUID, sow_id: UUID) -> Sow | None:
    return await db.scalar(
        select(Sow).where(
            Sow.id == sow_id,
            Sow.farm_id == farm_id,
            Sow.deleted_at.is_(None),
        )
    )


def _is_future_date(event_date: date) -> bool:
    return event_date > date.today() + timedelta(days=_FUTURE_DATE_TOLERANCE_DAYS)


def _audit(farm_id: UUID, entity_type: str, entity_id: UUID, action: str, new_value: dict) -> AuditLog:
    return AuditLog(
        farm_id=farm_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        new_value=new_value,
    )


# ── Mating validation ─────────────────────────────────────────────────────────

async def _process_mating(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncMating,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    event_date = _parse_date(item.mating_date)

    # 1. Future date
    if _is_future_date(event_date):
        return None, SyncRejected(
            id=item.id, entity="mating", reason="FUTURE_DATE",
            detail={"event_date": item.mating_date, "server_date": str(date.today())},
        ), None

    # 2. Period lock
    lock = await _check_period_locked(db, farm_id, event_date)
    if lock:
        return None, SyncRejected(
            id=item.id, entity="mating", reason="PERIOD_LOCKED",
            detail={"period": f"{event_date.year}-{event_date.month:02d}"},
        ), None

    # 3. Sow exists
    sow = await _get_sow(db, farm_id, item.sow_id)
    if not sow:
        return None, SyncRejected(
            id=item.id, entity="mating", reason="SOW_NOT_FOUND",
            detail={"sow_id": str(item.sow_id)},
        ), None

    # 4. Idempotency — same UUID already exists
    existing_by_id = await db.get(Mating, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="mating", action="merged"), None, None

    # 5. Sow status check — valid states for mating (SCREEN_MENU_SPEC 상태 정의)
    valid_for_mating = ("GILT", "OPEN", "ACCIDENT")
    if sow.status not in valid_for_mating:
        return None, SyncRejected(
            id=item.id, entity="mating", reason="STATUS_CONFLICT",
            detail={
                "sow_id": str(item.sow_id),
                "current_status": sow.status,
                "allowed_statuses": list(valid_for_mating),
                "message": f"Cannot record mating for sow in {sow.status} status",
            },
        ), None

    # 6. Duplicate check (same sow, same date, different UUID)
    dup = await db.scalar(
        select(Mating).where(
            Mating.sow_id == item.sow_id,
            Mating.farm_id == farm_id,
            Mating.mating_date == event_date,
            Mating.deleted_at.is_(None),
        )
    )
    if dup:
        time_diff = abs((item.client_created_at.replace(tzinfo=UTC) - dup.created_at).total_seconds())
        if time_diff <= _DUPLICATE_MERGE_WINDOW_HOURS * 3600:
            return SyncAccepted(id=item.id, entity="mating", action="merged"), None, None
        return None, None, SyncConflict(
            id=item.id, entity="mating", conflict_type="DUPLICATE_EVENT",
            client_record=item.model_dump(mode="json"),
            server_record={
                "id": str(dup.id),
                "sow_id": str(dup.sow_id),
                "mating_date": str(dup.mating_date),
                "mating_type": dup.mating_type,
                "semen_batch": dup.semen_batch,
            },
        )

    # 7. All checks passed — write (unless dry_run)
    if not dry_run:
        mating = Mating(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id,
            mating_date=event_date, mating_type=item.mating_type,
            boar_id=item.boar_id, semen_batch=item.semen_batch,
            mating_number=item.mating_number, notes=item.notes,
        )
        db.add(mating)
        db.add(_audit(farm_id, "mating", item.id, "CREATE", item.model_dump(mode="json")))
        sow.status = "PREGNANT"

    return SyncAccepted(id=item.id, entity="mating", action="created"), None, None


# ── Farrowing validation ──────────────────────────────────────────────────────

async def _process_farrowing(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncFarrowing,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    event_date = _parse_date(item.farrowing_date)

    if _is_future_date(event_date):
        return None, SyncRejected(id=item.id, entity="farrowing", reason="FUTURE_DATE",
                                   detail={"event_date": item.farrowing_date}), None

    lock = await _check_period_locked(db, farm_id, event_date)
    if lock:
        return None, SyncRejected(id=item.id, entity="farrowing", reason="PERIOD_LOCKED",
                                   detail={"period": f"{event_date.year}-{event_date.month:02d}"}), None

    sow = await _get_sow(db, farm_id, item.sow_id)
    if not sow:
        return None, SyncRejected(id=item.id, entity="farrowing", reason="SOW_NOT_FOUND",
                                   detail={"sow_id": str(item.sow_id)}), None

    existing_by_id = await db.get(Farrowing, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="farrowing", action="merged"), None, None

    if sow.status != "PREGNANT":
        return None, SyncRejected(
            id=item.id, entity="farrowing", reason="STATUS_CONFLICT",
            detail={
                "sow_id": str(item.sow_id), "current_status": sow.status,
                "allowed_statuses": ["PREGNANT"],
                "message": f"Cannot record farrowing for sow in {sow.status} status",
            },
        ), None

    dup = await db.scalar(
        select(Farrowing).where(
            Farrowing.sow_id == item.sow_id, Farrowing.farm_id == farm_id,
            Farrowing.farrowing_date == event_date, Farrowing.deleted_at.is_(None),
        )
    )
    if dup:
        time_diff = abs((item.client_created_at.replace(tzinfo=UTC) - dup.created_at).total_seconds())
        if time_diff <= _DUPLICATE_MERGE_WINDOW_HOURS * 3600:
            return SyncAccepted(id=item.id, entity="farrowing", action="merged"), None, None
        return None, None, SyncConflict(
            id=item.id, entity="farrowing", conflict_type="DUPLICATE_EVENT",
            client_record=item.model_dump(mode="json"),
            server_record={"id": str(dup.id), "farrowing_date": str(dup.farrowing_date),
                           "total_born": dup.total_born, "born_alive": dup.born_alive},
        )

    if not dry_run:
        # mating_id 는 NOT NULL FK — 해당 sow 최근 교배에 연결.
        # 세션 autoflush=False → 같은 sync 배치의 직전 mating(pending) 조회 위해 flush.
        await db.flush()
        mating = await db.scalar(
            select(Mating)
            .where(Mating.sow_id == item.sow_id, Mating.farm_id == farm_id, Mating.deleted_at.is_(None))
            .order_by(Mating.mating_date.desc())
            .limit(1)
        )
        if not mating:
            return None, SyncRejected(
                id=item.id, entity="farrowing", reason="MATING_NOT_FOUND",
                detail={"sow_id": str(item.sow_id), "message": "No mating to attach farrowing to"},
            ), None
        # 모델 컬럼명: stillborn / mummified / farrowing_ease (sync 입력은 born_dead / mummies / farrowing_type).
        farrowing = Farrowing(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id, mating_id=mating.id,
            farrowing_date=event_date, total_born=item.total_born,
            born_alive=item.born_alive, stillborn=item.born_dead,
            mummified=item.mummies, farrowing_ease=item.farrowing_type, notes=item.notes,
        )
        db.add(farrowing)
        db.add(_audit(farm_id, "farrowing", item.id, "CREATE", item.model_dump(mode="json")))
        sow.status = "LACTATING"
        sow.parity = (sow.parity or 0) + 1

    return SyncAccepted(id=item.id, entity="farrowing", action="created"), None, None


# ── Weaning validation ────────────────────────────────────────────────────────

async def _process_weaning(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncWeaning,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    event_date = _parse_date(item.weaning_date)

    if _is_future_date(event_date):
        return None, SyncRejected(id=item.id, entity="weaning", reason="FUTURE_DATE",
                                   detail={"event_date": item.weaning_date}), None

    lock = await _check_period_locked(db, farm_id, event_date)
    if lock:
        return None, SyncRejected(id=item.id, entity="weaning", reason="PERIOD_LOCKED",
                                   detail={"period": f"{event_date.year}-{event_date.month:02d}"}), None

    sow = await _get_sow(db, farm_id, item.sow_id)
    if not sow:
        return None, SyncRejected(id=item.id, entity="weaning", reason="SOW_NOT_FOUND",
                                   detail={"sow_id": str(item.sow_id)}), None

    existing_by_id = await db.get(Weaning, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="weaning", action="merged"), None, None

    if sow.status != "LACTATING":
        return None, SyncRejected(
            id=item.id, entity="weaning", reason="STATUS_CONFLICT",
            detail={
                "sow_id": str(item.sow_id), "current_status": sow.status,
                "allowed_statuses": ["LACTATING"],
                "message": f"Cannot record weaning for sow in {sow.status} status",
            },
        ), None

    dup = await db.scalar(
        select(Weaning).where(
            Weaning.sow_id == item.sow_id, Weaning.farm_id == farm_id,
            Weaning.weaning_date == event_date, Weaning.deleted_at.is_(None),
        )
    )
    if dup:
        time_diff = abs((item.client_created_at.replace(tzinfo=UTC) - dup.created_at).total_seconds())
        if time_diff <= _DUPLICATE_MERGE_WINDOW_HOURS * 3600:
            return SyncAccepted(id=item.id, entity="weaning", action="merged"), None, None
        return None, None, SyncConflict(
            id=item.id, entity="weaning", conflict_type="DUPLICATE_EVENT",
            client_record=item.model_dump(mode="json"),
            server_record={"id": str(dup.id), "weaning_date": str(dup.weaning_date),
                           "weaned_count": dup.weaned_count},
        )

    if not dry_run:
        # farrowing_id 는 NOT NULL FK — 해당 sow 최근 분만에 연결.
        # 세션 autoflush=False → 같은 sync 배치의 직전 farrowing(pending) 조회 위해 flush.
        await db.flush()
        farrowing_id = await db.scalar(
            select(Farrowing.id)
            .where(Farrowing.sow_id == item.sow_id, Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None))
            .order_by(Farrowing.farrowing_date.desc())
            .limit(1)
        )
        if not farrowing_id:
            return None, SyncRejected(
                id=item.id, entity="weaning", reason="NO_ACTIVE_FARROWING",
                detail={"sow_id": str(item.sow_id), "message": "No farrowing to attach weaning to"},
            ), None
        # 모델 컬럼명: avg_weaning_weight_kg (sync 입력은 avg_weight_kg).
        weaning = Weaning(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id, farrowing_id=farrowing_id,
            weaning_date=event_date, weaned_count=item.weaned_count,
            avg_weaning_weight_kg=item.avg_weight_kg, notes=item.notes,
        )
        db.add(weaning)
        db.add(_audit(farm_id, "weaning", item.id, "CREATE", item.model_dump(mode="json")))
        sow.status = "OPEN"

    return SyncAccepted(id=item.id, entity="weaning", action="created"), None, None


# ── Reproductive event validation ─────────────────────────────────────────────

async def _process_reproductive(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncReproductiveEvent,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    event_date = _parse_date(item.event_date)

    if _is_future_date(event_date):
        return None, SyncRejected(id=item.id, entity="reproductive_event", reason="FUTURE_DATE",
                                   detail={"event_date": item.event_date}), None

    lock = await _check_period_locked(db, farm_id, event_date)
    if lock:
        return None, SyncRejected(id=item.id, entity="reproductive_event", reason="PERIOD_LOCKED",
                                   detail={"period": f"{event_date.year}-{event_date.month:02d}"}), None

    sow = await _get_sow(db, farm_id, item.sow_id)
    if not sow:
        return None, SyncRejected(id=item.id, entity="reproductive_event", reason="SOW_NOT_FOUND",
                                   detail={"sow_id": str(item.sow_id)}), None

    existing_by_id = await db.get(ReproductiveEvent, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="reproductive_event", action="merged"), None, None

    if not dry_run:
        event = ReproductiveEvent(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id,
            event_type=item.event_type, event_date=event_date, notes=item.notes,
        )
        db.add(event)
        db.add(_audit(farm_id, "reproductive_event", item.id, "CREATE", item.model_dump(mode="json")))

        # Normalise legacy aliases (CULL→CULLED, DEATH→DEAD)
        _alias = {"CULL": "CULLED", "DEATH": "DEAD"}
        normalised = _alias.get(item.event_type, item.event_type)

        # Sow status transitions → SowStatus v2 종료/활성값만 사용.
        # (event_type TRANSFER_OUT → 상태 TRANSFER. "TRANSFER_OUT"은 유효 SowStatus 아님 → 422 방지)
        _status_map = {
            "CULLED": "CULLED", "DEAD": "DEAD", "SOLD": "SOLD",
            "TRANSFER_OUT": "TRANSFER",
            "RETURN_TO_ESTRUS": "ACCIDENT",
            "EMPTY": "ACCIDENT",
            "INFERTILE": "ACCIDENT",
            "ABORTION": "ACCIDENT",
        }
        if normalised in _status_map:
            sow.status = _status_map[normalised]

        # Soft-delete + Removal record for terminal exits
        if normalised in ("CULLED", "DEAD", "SOLD", "TRANSFER_OUT"):
            now_utc = datetime.now(UTC)
            sow.exit_date = now_utc
            sow.deleted_at = now_utc
            db.add(Removal(
                farm_id=farm_id,
                sow_id=sow.id,
                removal_date=event_date,
                removal_type=normalised,
            ))

    return SyncAccepted(id=item.id, entity="reproductive_event", action="created"), None, None


# ── Health event validation ────────────────────────────────────────────────────

async def _process_health_event(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncHealthEvent,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    event_date = _parse_date(item.event_date)

    if _is_future_date(event_date):
        return None, SyncRejected(id=item.id, entity="health_event", reason="FUTURE_DATE",
                                   detail={"event_date": item.event_date}), None

    lock = await _check_period_locked(db, farm_id, event_date)
    if lock:
        return None, SyncRejected(id=item.id, entity="health_event", reason="PERIOD_LOCKED",
                                   detail={"period": f"{event_date.year}-{event_date.month:02d}"}), None

    # sow_id is optional for health events (None = herd-level)
    if item.sow_id:
        sow = await _get_sow(db, farm_id, item.sow_id)
        if not sow:
            return None, SyncRejected(id=item.id, entity="health_event", reason="SOW_NOT_FOUND",
                                       detail={"sow_id": str(item.sow_id)}), None

    existing_by_id = await db.get(HealthEvent, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="health_event", action="merged"), None, None

    if not dry_run:
        event = HealthEvent(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id,
            event_date=event_date, disease_code=item.disease_code,
            vaccine_code=item.vaccine_code, active_substance=item.active_substance,
            dose_mg=item.dose_mg, severity=item.severity, notes=item.notes,
        )
        db.add(event)
        db.add(_audit(farm_id, "health_event", item.id, "CREATE", item.model_dump(mode="json")))

    return SyncAccepted(id=item.id, entity="health_event", action="created"), None, None


# ── Piglet event validation ───────────────────────────────────────────────────

async def _process_piglet_event(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncPigletEvent,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    event_date = _parse_date(item.event_date)

    if _is_future_date(event_date):
        return None, SyncRejected(id=item.id, entity="piglet_event", reason="FUTURE_DATE",
                                   detail={"event_date": item.event_date}), None

    lock = await _check_period_locked(db, farm_id, event_date)
    if lock:
        return None, SyncRejected(id=item.id, entity="piglet_event", reason="PERIOD_LOCKED",
                                   detail={"period": f"{event_date.year}-{event_date.month:02d}"}), None

    sow = await _get_sow(db, farm_id, item.sow_id)
    if not sow:
        return None, SyncRejected(id=item.id, entity="piglet_event", reason="SOW_NOT_FOUND",
                                   detail={"sow_id": str(item.sow_id)}), None

    existing_by_id = await db.get(PigletEvent, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="piglet_event", action="merged"), None, None

    if not dry_run:
        # Resolve farrowing_id: explicit or auto-lookup latest for this sow.
        # 세션 autoflush=False → 같은 sync 배치의 직전 farrowing(pending) 조회 위해 flush.
        farrowing_id = item.farrowing_id
        if farrowing_id is None:
            await db.flush()
            farrowing = await db.scalar(
                select(Farrowing)
                .where(Farrowing.sow_id == sow.id, Farrowing.deleted_at.is_(None))
                .order_by(Farrowing.farrowing_date.desc())
                .limit(1)
            )
            if not farrowing:
                return None, SyncRejected(
                    id=item.id, entity="piglet_event", reason="NO_ACTIVE_FARROWING",
                    detail={"sow_id": str(item.sow_id)},
                ), None
            farrowing_id = farrowing.id

        event = PigletEvent(
            id=item.id, farm_id=farm_id, sow_id=sow.id,
            farrowing_id=farrowing_id,
            event_date=event_date, event_type=item.event_type,
            piglet_count=item.piglet_count, reason=item.reason,
            target_sow_id=item.target_sow_id, notes=item.notes,
        )
        db.add(event)
        db.add(_audit(farm_id, "piglet_event", item.id, "CREATE", item.model_dump(mode="json")))

    return SyncAccepted(id=item.id, entity="piglet_event", action="created"), None, None


# ── Server pull ───────────────────────────────────────────────────────────────

async def _pull_server_changes(
    db: AsyncSession,
    farm_id: UUID,
    since: datetime | None,
) -> ServerChanges:
    """Return all records changed on server since `since`."""
    if since is None:
        return ServerChanges()

    # 일부 이벤트 모델(Mating/PigletEvent 등)은 updated_at 없이 created_at만 가짐 → 모델별 컬럼 선택.
    def _sync_col(model):
        return model.updated_at if hasattr(model, "updated_at") else model.created_at

    def q(model, extra=None):
        stmt = select(model).where(model.farm_id == farm_id, _sync_col(model) >= since)
        if extra is not None:
            stmt = stmt.where(extra)
        return stmt

    sows       = list(await db.scalars(q(Sow)))
    matings    = list(await db.scalars(q(Mating)))
    farrowings = list(await db.scalars(q(Farrowing)))
    weanings   = list(await db.scalars(q(Weaning)))
    repro      = list(await db.scalars(q(ReproductiveEvent)))
    health     = list(await db.scalars(q(HealthEvent)))
    piglet_evs = list(await db.scalars(q(PigletEvent)))
    removals   = list(await db.scalars(
        select(Removal).where(Removal.farm_id == farm_id, Removal.created_at >= since)
    ))
    locks      = list(await db.scalars(
        select(PeriodLock).where(PeriodLock.farm_id == farm_id, PeriodLock.locked_at >= since)
    ))

    def to_dict(obj, fields: list[str]) -> dict:
        # getattr default None: 모델에 없는 필드(updated_at 등)도 크래시 없이 null로.
        out: dict = {}
        for f in fields:
            v = getattr(obj, f, None)
            out[f] = str(v) if isinstance(v, UUID) else v
        return out

    deleted = (
        [str(s.id) for s in sows if s.deleted_at and s.deleted_at >= since] +
        [str(m.id) for m in matings if m.deleted_at and m.deleted_at >= since] +
        [str(f.id) for f in farrowings if f.deleted_at and f.deleted_at >= since] +
        [str(w.id) for w in weanings if w.deleted_at and w.deleted_at >= since]
    )

    return ServerChanges(
        sows=       [to_dict(s, ["id","ear_tag","status","parity","updated_at"]) for s in sows if not s.deleted_at],
        matings=    [to_dict(m, ["id","sow_id","mating_date","mating_type","created_at"]) for m in matings if not m.deleted_at],
        farrowings= [to_dict(f, [
            "id","sow_id","mating_id","breeding_cycle_id",
            "farrowing_date","total_born","born_alive",
            "stillborn","mummified","farrowing_ease",
            "notes","updated_at",
        ]) for f in farrowings if not f.deleted_at],
        weanings=   [to_dict(w, [
            "id","sow_id","farrowing_id","breeding_cycle_id",
            "weaning_date","weaned_count","weaning_age_days",
            "avg_weaning_weight_kg","notes","updated_at",
        ]) for w in weanings if not w.deleted_at],
        reproductive_events=[to_dict(r, [
            "id","sow_id","mating_id","event_type","event_date","notes","updated_at",
        ]) for r in repro if not r.deleted_at],
        health_events=[to_dict(h, ["id","sow_id","event_date","updated_at"]) for h in health if not h.deleted_at],
        piglet_events=[to_dict(p, [
            "id","sow_id","farrowing_id","event_date","event_type",
            "piglet_count","reason","target_sow_id","notes","created_at",
        ]) for p in piglet_evs if not p.deleted_at],
        removals=[to_dict(r, [
            "id","sow_id","removal_date","removal_type",
            "reason_category","reason_detail","body_weight_kg",
            "sale_price","sale_currency","created_at",
        ]) for r in removals],
        period_locks=[to_dict(l, ["id","period_year","period_month","locked_at"]) for l in locks],
        deleted_ids=deleted,
    )


# ── Main entry point ──────────────────────────────────────────────────────────

async def process_sync(
    db: AsyncSession,
    farm: Farm,
    req: SyncRequest,
) -> SyncResponse:
    now = datetime.now(UTC)
    started_at = now

    # Stale client check
    require_full_sync = False
    if req.last_sync_at:
        age = (now - req.last_sync_at.replace(tzinfo=UTC)).days
        if age > _FULL_SYNC_THRESHOLD_DAYS:
            require_full_sync = True

    # Item count guard (before any DB work)
    total_items = (
        len(req.changes.matings) +
        len(req.changes.farrowings) +
        len(req.changes.weanings) +
        len(req.changes.reproductive_events) +
        len(req.changes.health_events) +
        len(req.changes.piglet_events)
    )
    if total_items > _MAX_ITEMS_PER_REQUEST:
        return SyncResponse(
            sync_token=now.isoformat().replace("+00:00", "Z"),
            dry_run=req.dry_run,
            rejected=[
                SyncRejected(
                    id=uuid4(),
                    entity="batch",
                    reason="BATCH_TOO_LARGE",
                    detail={"count": total_items, "max": _MAX_ITEMS_PER_REQUEST,
                            "message": f"Split into batches of ≤{_MAX_ITEMS_PER_REQUEST} items"},
                )
            ],
            stats={"pushed": total_items, "accepted": 0, "rejected": 1, "conflicts": 0, "pulled": 0},
        )

    accepted:  list[SyncAccepted]  = []
    rejected:  list[SyncRejected]  = []
    conflicts: list[SyncConflict]  = []

    # Farm-level advisory lock — prevents concurrent sync from same farm causing race conditions.
    # pg_advisory_xact_lock blocks until lock is available; released when outer transaction ends.
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:farm_id))"),
        {"farm_id": str(farm.id)},
    )

    try:
        async with db.begin_nested():  # savepoint for dry_run rollback
            processors = [
                (req.changes.matings,             _process_mating),
                (req.changes.farrowings,          _process_farrowing),
                (req.changes.weanings,            _process_weaning),
                (req.changes.reproductive_events, _process_reproductive),
                (req.changes.health_events,       _process_health_event),
                (req.changes.piglet_events,       _process_piglet_event),
            ]

            for items, processor in processors:
                for item in items:
                    try:
                        acc, rej, con = await processor(db, farm.id, item, req.dry_run)
                        if acc: accepted.append(acc)
                        if rej: rejected.append(rej)
                        if con: conflicts.append(con)
                    except Exception as e:
                        rejected.append(SyncRejected(
                            id=item.id,
                            entity=item.__class__.__name__,
                            reason="INTERNAL_ERROR",
                            detail={"error": str(e)},
                        ))

            # Persist conflict queue for unresolved conflicts
            if conflicts and not req.dry_run:
                for con in conflicts:
                    await db.execute(
                        text("""
                            INSERT INTO sync_conflict_queue
                                (farm_id, client_id, entity, conflict_type, client_record, server_record)
                            VALUES (:farm_id, :client_id, :entity, :conflict_type, :client_record, :server_record)
                        """),
                        {
                            "farm_id":        str(farm.id),
                            "client_id":      str(req.client_id),
                            "entity":         con.entity,
                            "conflict_type":  con.conflict_type,
                            "client_record":  json.dumps(con.client_record),
                            "server_record":  json.dumps(con.server_record),
                        },
                    )

            if req.dry_run:
                raise _DryRunRollback()   # rolls back the savepoint, keeps outer tx open

    except _DryRunRollback:
        pass  # savepoint rolled back; proceed to build response without committing

    # Pull server changes (runs regardless of dry_run)
    server_changes = await _pull_server_changes(db, farm.id, req.last_sync_at)

    # Write sync log and commit (live sync only)
    completed_at = datetime.now(UTC)
    if not req.dry_run:
        log = SyncLog(
            farm_id=farm.id,
            device_id=str(req.client_id),
            sync_direction="BIDIRECTIONAL",
            started_at=started_at,
            completed_at=completed_at,
            records_pushed=total_items,
            records_pulled=(
                len(server_changes.sows) +
                len(server_changes.matings) +
                len(server_changes.farrowings) +
                len(server_changes.weanings) +
                len(server_changes.reproductive_events) +
                len(server_changes.health_events) +
                len(server_changes.piglet_events) +
                len(server_changes.removals)
            ),
            conflicts_found=len(conflicts),
            conflicts_resolved=len([c for c in accepted if c.action == "merged"]),
            duration_ms=int((completed_at - started_at).total_seconds() * 1000),
        )
        db.add(log)
        await db.commit()

    sync_token = now.isoformat().replace("+00:00", "Z")
    pulled_count = (
        len(server_changes.sows) + len(server_changes.matings) +
        len(server_changes.farrowings) + len(server_changes.weanings) +
        len(server_changes.reproductive_events) + len(server_changes.health_events) +
        len(server_changes.piglet_events) + len(server_changes.removals)
    )

    return SyncResponse(
        sync_token=sync_token,
        dry_run=req.dry_run,
        accepted=accepted,
        rejected=rejected,
        conflicts=conflicts,
        server_changes=server_changes,
        require_full_sync=require_full_sync,
        stats={
            "pushed":    total_items,
            "accepted":  len(accepted),
            "rejected":  len(rejected),
            "conflicts": len(conflicts),
            "pulled":    pulled_count,
        },
    )


class _DryRunRollback(Exception):
    """Sentinel used to roll back a dry_run savepoint."""
