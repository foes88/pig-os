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

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    PregnancyCheck,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import HealthEvent, Removal
from app.db.models.ops import PeriodLock, SyncLog
from app.db.models.platform import AuditLog, Farm
from app.db.models.sow import BreedingCycle, PigletGroup, Sow
from app.schemas.sync import (
    ServerChanges,
    SyncAccepted,
    SyncConflict,
    SyncFarrowing,
    SyncHealthEvent,
    SyncMating,
    SyncPigletEvent,
    SyncPregnancyCheck,
    SyncRejected,
    SyncReproductiveEvent,
    SyncRequest,
    SyncResponse,
    SyncWeaning,
)
from app.services.event_service import (
    _calc_piglet_adjustments,
    _get_open_cycle,
    apply_terminal_reproductive,
)
from app.validators.base import ValidationError
from app.validators.farrowing import validate_farrowing

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


def _dup_time_diff_seconds(client_dt: datetime, server_dt: datetime | None) -> float | None:
    """클라/서버 생성시각 차이(초). tz 안전: aware는 UTC로 변환(astimezone), naive는 UTC로 간주.
    server_dt=None(같은 배치 내 직전 삽입으로 server_default 미반영)이면 None → 비교 불가.
    과거 `.replace(tzinfo=UTC)`는 오프셋을 무시(relabel)해 +09:00을 9h 어긋나게 했음(#4)."""
    if server_dt is None:
        return None
    c = client_dt if client_dt.tzinfo else client_dt.replace(tzinfo=UTC)
    s = server_dt if server_dt.tzinfo else server_dt.replace(tzinfo=UTC)
    return abs((c.astimezone(UTC) - s.astimezone(UTC)).total_seconds())


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

    # 4b. Field validation — REST MatingCreate 규칙 미러 (finding #1 확장)
    invalid = _validate_mating_fields(item)
    if invalid:
        return None, SyncRejected(
            id=item.id, entity="mating", reason="VALIDATION_FAILED", detail=invalid,
        ), None

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

    # 6. Duplicate check (same sow, same date, SAME type, different UUID).
    # #3: mating_type까지 일치해야 중복. 같은 날 AI 후 NATURAL 백업교배(실제 관행)는
    # 서로 다른 교배라 둘 다 수용해야 함 — type을 빼면 무음 병합으로 데이터 손실.
    dup = await db.scalar(
        select(Mating).where(
            Mating.sow_id == item.sow_id,
            Mating.farm_id == farm_id,
            Mating.mating_date == event_date,
            Mating.mating_type == item.mating_type,
            Mating.deleted_at.is_(None),
        )
    )
    if dup:
        time_diff = _dup_time_diff_seconds(item.client_created_at, dup.created_at)
        if time_diff is not None and time_diff <= _DUPLICATE_MERGE_WINDOW_HOURS * 3600:
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
        # C4: REST record_mating 미러 — 활성 사이클 있으면 재사용, 없으면 신규 생성 후 연결.
        # breeding_cycle_id 누락 시 parity별 KPI(P1/P2 ABA 등)에서 동기화 데이터가 전량 누락됨.
        cycle = await _get_open_cycle(db, sow.id)
        if not cycle:
            cycle = BreedingCycle(
                farm_id=farm_id, sow_id=sow.id, parity=(sow.parity or 0) + 1,
                started_at=datetime.combine(event_date, datetime.min.time()).replace(tzinfo=UTC),
            )
            db.add(cycle)
            await db.flush()
        mating = Mating(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id,
            breeding_cycle_id=cycle.id,
            mating_date=event_date, mating_type=item.mating_type,
            boar_id=item.boar_id, semen_batch=item.semen_batch,
            mating_number=item.mating_number, notes=item.notes,
        )
        db.add(mating)
        db.add(_audit(farm_id, "mating", item.id, "CREATE", item.model_dump(mode="json")))
        sow.status = "PREGNANT"
        cycle.cycle_status = "MATED"

    return SyncAccepted(id=item.id, entity="mating", action="created"), None, None


# ── Farrowing validation ──────────────────────────────────────────────────────

# REST WeaningCreate(le=30)와 동일 상한 — 새 임계 도입 아님(기존 스키마 미러).
_MAX_WEANED_COUNT = 30


def _validate_mating_fields(item: SyncMating) -> dict | None:
    """동기화 교배 항목을 REST MatingCreate와 동일 규칙으로 검증 (finding #1 확장).
    REST: mating_type ∈ (AI|NATURAL), mating_number 1..5. 위반 시 detail(→ SyncRejected).
    스키마 하드제약 대신 항목별 처리(배치 전체 422 방지)."""
    if item.mating_type not in ("AI", "NATURAL"):
        return {"field": "mating_type",
                "message": "mating_type must be AI or NATURAL", "value": item.mating_type}
    if item.mating_number is not None and not (1 <= item.mating_number <= 5):
        return {"field": "mating_number",
                "message": "mating_number must be between 1 and 5", "value": item.mating_number}
    return None


def _validate_farrowing_counts(item: SyncFarrowing) -> dict | None:
    """동기화 분만 항목을 REST 생성경로와 동일 규칙으로 검증.
    위반 시 detail dict 반환(→ SyncRejected), 정상이면 None.
    배치 전체를 422로 떨구지 않도록 스키마 하드제약 대신 항목별로 처리한다."""
    for field, val in (
        ("total_born", item.total_born),
        ("born_alive", item.born_alive),
        ("born_dead", item.born_dead),
        ("mummies", item.mummies),
    ):
        if val is not None and val < 0:
            return {"field": field, "message": f"{field} cannot be negative", "value": val}
    try:
        validate_farrowing(
            total_born=item.total_born, born_alive=item.born_alive,
            stillborn=item.born_dead, mummified=item.mummies,
        )
    except ValidationError as e:
        return {"message": e.detail}
    return None


def _validate_weaning_counts(item: SyncWeaning) -> dict | None:
    """동기화 이유 항목 검증 — REST WeaningCreate(0 ≤ weaned_count ≤ 30)와 동일."""
    wc = item.weaned_count
    if wc is None:
        return None
    if wc < 0:
        return {"field": "weaned_count", "message": "weaned_count cannot be negative", "value": wc}
    if wc > _MAX_WEANED_COUNT:
        return {"field": "weaned_count",
                "message": f"weaned_count cannot exceed {_MAX_WEANED_COUNT}", "value": wc}
    return None


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
        time_diff = _dup_time_diff_seconds(item.client_created_at, dup.created_at)
        if time_diff is not None and time_diff <= _DUPLICATE_MERGE_WINDOW_HOURS * 3600:
            return SyncAccepted(id=item.id, entity="farrowing", action="merged"), None, None
        return None, None, SyncConflict(
            id=item.id, entity="farrowing", conflict_type="DUPLICATE_EVENT",
            client_record=item.model_dump(mode="json"),
            server_record={"id": str(dup.id), "farrowing_date": str(dup.farrowing_date),
                           "total_born": dup.total_born, "born_alive": dup.born_alive},
        )

    invalid = _validate_farrowing_counts(item)
    if invalid:
        return None, SyncRejected(id=item.id, entity="farrowing", reason="VALIDATION_FAILED",
                                   detail=invalid), None

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
        # C4: breeding_cycle_id 연결(교배의 사이클 상속) + nursing_head 초기화 — REST record_farrowing 미러.
        farrowing = Farrowing(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id, mating_id=mating.id,
            breeding_cycle_id=mating.breeding_cycle_id,
            farrowing_date=event_date, total_born=item.total_born,
            born_alive=item.born_alive, stillborn=item.born_dead,
            mummified=item.mummies, nursing_head=item.born_alive,
            farrowing_ease=item.farrowing_type, notes=item.notes,
        )
        db.add(farrowing)
        db.add(_audit(farm_id, "farrowing", item.id, "CREATE", item.model_dump(mode="json")))
        sow.status = "LACTATING"
        sow.parity = (sow.parity or 0) + 1
        if mating.breeding_cycle_id:
            cycle = await db.get(BreedingCycle, mating.breeding_cycle_id)
            if cycle:
                cycle.cycle_status = "FARROWED"

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
        time_diff = _dup_time_diff_seconds(item.client_created_at, dup.created_at)
        if time_diff is not None and time_diff <= _DUPLICATE_MERGE_WINDOW_HOURS * 3600:
            return SyncAccepted(id=item.id, entity="weaning", action="merged"), None, None
        return None, None, SyncConflict(
            id=item.id, entity="weaning", conflict_type="DUPLICATE_EVENT",
            client_record=item.model_dump(mode="json"),
            server_record={"id": str(dup.id), "weaning_date": str(dup.weaning_date),
                           "weaned_count": dup.weaned_count},
        )

    invalid = _validate_weaning_counts(item)
    if invalid:
        return None, SyncRejected(id=item.id, entity="weaning", reason="VALIDATION_FAILED",
                                   detail=invalid), None

    if not dry_run:
        # farrowing 은 NOT NULL FK — 해당 sow 최근 분만에 연결.
        # 세션 autoflush=False → 같은 sync 배치의 직전 farrowing/piglet_events(pending) 조회 위해 flush.
        # 처리순서 재정렬(piglet_events → weanings)로, 이 시점엔 같은 배치의 양자/폐사가 반영된다.
        await db.flush()
        farrowing = await db.scalar(
            select(Farrowing)
            .where(Farrowing.sow_id == item.sow_id, Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None))
            .order_by(Farrowing.farrowing_date.desc())
            .limit(1)
        )
        if not farrowing:
            return None, SyncRejected(
                id=item.id, entity="weaning", reason="NO_ACTIVE_FARROWING",
                detail={"sow_id": str(item.sow_id), "message": "No farrowing to attach weaning to"},
            ), None
        # B4: 이유두수 ≤ 잔여 유효복당 (born_alive + 양자전입 − 양자전출 − 폐사 − 기존이유합).
        # 직접 REST(event_service)와 동일 규칙. 처리순서 재정렬 덕에 같은 배치 양자/폐사가 먼저
        # 반영되어, 양자 받은 nurse sow가 자기 born_alive보다 많이 이유해도 오거부되지 않는다.
        foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
        effective_litter = max(0, farrowing.born_alive + foster_in - foster_out - deaths)
        prior_weaned = await db.scalar(
            select(func.coalesce(func.sum(Weaning.weaned_count), 0)).where(
                Weaning.farrowing_id == farrowing.id, Weaning.deleted_at.is_(None)
            )
        ) or 0
        remaining = effective_litter - int(prior_weaned)
        if item.weaned_count > remaining:
            return None, SyncRejected(
                id=item.id, entity="weaning", reason="VALIDATION_FAILED",
                detail={
                    "field": "weaned_count",
                    "message": (
                        f"weaned_count ({item.weaned_count}) > remaining nursing "
                        f"(effective litter {effective_litter} - already weaned {int(prior_weaned)} = {remaining})"
                    ),
                    "effective_litter": effective_litter,
                    "prior_weaned": int(prior_weaned),
                    "remaining": remaining,
                },
            ), None
        # 모델 컬럼명: avg_weaning_weight_kg (sync 입력은 avg_weight_kg).
        # H1/C4: breeding_cycle_id 연결 + 부분이유 상태머신 + PigletGroup 생성 — REST record_weaning 미러.
        nursing_days = (event_date - farrowing.farrowing_date).days
        weaning = Weaning(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id, farrowing_id=farrowing.id,
            breeding_cycle_id=farrowing.breeding_cycle_id,
            weaning_date=event_date, weaned_count=item.weaned_count,
            weaning_age_days=nursing_days if nursing_days >= 0 else None,
            avg_weaning_weight_kg=item.avg_weight_kg, notes=item.notes,
        )
        db.add(weaning)
        db.add(_audit(farm_id, "weaning", item.id, "CREATE", item.model_dump(mode="json")))
        await db.flush()

        # 잔여 포유두수 0 → 이유 완료(공태 복귀 + 사이클 종료). 잔여>0(부분이유) → LACTATING 유지.
        remaining_after = remaining - item.weaned_count
        if remaining_after <= 0:
            sow.status = "OPEN"
            if farrowing.breeding_cycle_id:
                cycle = await db.get(BreedingCycle, farrowing.breeding_cycle_id)
                if cycle:
                    cycle.cycle_status = "WEANED"
                    cycle.ended_at = datetime.now(UTC)
        # else: 부분이유 — 모돈 LACTATING 유지, 사이클 FARROWED 유지

        # 이유된 자돈을 그룹으로 추적(PSY→MSY 사슬 연결). 이유 1건 = 자돈그룹 1개.
        if item.weaned_count > 0:
            code = f"WG-{event_date:%y%m%d}-{str(item.id)[:8]}"  # VARCHAR(30) 안전
            exists = await db.scalar(
                select(PigletGroup).where(
                    PigletGroup.farm_id == farm_id, PigletGroup.group_code == code
                )
            )
            if not exists:
                db.add(PigletGroup(
                    farm_id=farm_id, group_code=code, weaning_date=event_date,
                    head_count_in=item.weaned_count, notes=f"auto: weaning {sow.ear_tag}",
                ))

    return SyncAccepted(id=item.id, entity="weaning", action="created"), None, None


# ── Reproductive event validation ─────────────────────────────────────────────

# REST ReproductiveEventCreate 패턴 미러 + sync 하위호환 별칭(CULL/DEATH)
_REPRODUCTIVE_EVENT_TYPES = frozenset({
    "RETURN_TO_ESTRUS", "ABORTION", "EMPTY", "INFERTILE",
    "CULLED", "DEAD", "TRANSFER_OUT", "SOLD", "HEAT_DETECTED", "CULL", "DEATH",
})
# REST PigletEventCreate 패턴 미러
_PIGLET_EVENT_TYPES = frozenset({"STILLBORN_REMOVAL", "DEATH", "FOSTER_IN", "FOSTER_OUT"})
_PIGLET_REASONS = frozenset({"CRUSHING", "SCOURS", "STARVATION", "CONGENITAL", "HYPOTHERMIA", "OTHER"})


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

    # 항목별 검증 — REST 규칙 미러(배치 전체 422 방지) — Codex P1
    if item.event_type not in _REPRODUCTIVE_EVENT_TYPES:
        return None, SyncRejected(
            id=item.id, entity="reproductive_event", reason="VALIDATION_FAILED",
            detail={"field": "event_type", "message": "invalid event_type", "value": item.event_type},
        ), None

    if not dry_run:
        event = ReproductiveEvent(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id,
            event_type=item.event_type, event_date=event_date, notes=item.notes,
        )
        db.add(event)
        db.add(_audit(farm_id, "reproductive_event", item.id, "CREATE", item.model_dump(mode="json")))
        # 상태 전이 — REST와 동일 공유 헬퍼(드리프트 방지, Codex P1).
        # 헬퍼가 SowStatus v2 매핑(TRANSFER_OUT→TRANSFER 등) + soft-delete + Removal 처리.
        await apply_terminal_reproductive(db, sow, item.event_type, event_date, farm_id)

    return SyncAccepted(id=item.id, entity="reproductive_event", action="created"), None, None


# ── Pregnancy check (임신감정) — REST record_pregnancy_check 미러(오프라인 큐 경로) ──────────
_PREGNANCY_RESULTS = frozenset({"POSITIVE", "NEGATIVE", "UNCERTAIN"})


async def _process_pregnancy_check(
    db: AsyncSession,
    farm_id: UUID,
    item: SyncPregnancyCheck,
    dry_run: bool,
) -> tuple[SyncAccepted | None, SyncRejected | None, SyncConflict | None]:

    check_date = _parse_date(item.check_date)

    if _is_future_date(check_date):
        return None, SyncRejected(id=item.id, entity="pregnancy_check", reason="FUTURE_DATE",
                                   detail={"check_date": item.check_date}), None

    lock = await _check_period_locked(db, farm_id, check_date)
    if lock:
        return None, SyncRejected(id=item.id, entity="pregnancy_check", reason="PERIOD_LOCKED",
                                   detail={"period": f"{check_date.year}-{check_date.month:02d}"}), None

    sow = await _get_sow(db, farm_id, item.sow_id)
    if not sow:
        return None, SyncRejected(id=item.id, entity="pregnancy_check", reason="SOW_NOT_FOUND",
                                   detail={"sow_id": str(item.sow_id)}), None

    existing_by_id = await db.get(PregnancyCheck, item.id)
    if existing_by_id:
        return SyncAccepted(id=item.id, entity="pregnancy_check", action="merged"), None, None

    if item.result not in _PREGNANCY_RESULTS:
        return None, SyncRejected(
            id=item.id, entity="pregnancy_check", reason="VALIDATION_FAILED",
            detail={"field": "result", "message": "invalid result", "value": item.result},
        ), None

    # 임신감정은 PREGNANT 모돈만(REST record_pregnancy_check와 동일) → 부적격은 영구거부(STATUS_CONFLICT).
    if sow.status != "PREGNANT":
        return None, SyncRejected(
            id=item.id, entity="pregnancy_check", reason="STATUS_CONFLICT",
            detail={"current": sow.status, "allowed": ["PREGNANT"]},
        ), None

    if not dry_run:
        event = PregnancyCheck(
            id=item.id, farm_id=farm_id, sow_id=item.sow_id, mating_id=item.mating_id,
            check_date=check_date, days_after_mating=item.days_after_mating,
            result=item.result, method=item.method, notes=item.notes,
        )
        db.add(event)
        db.add(_audit(farm_id, "pregnancy_check", item.id, "CREATE", item.model_dump(mode="json")))
        # 음성(NEGATIVE)=공태(EMPTY) → ACCIDENT 전이 + 사이클 FAILED(재교배 대기). REST와 동일 헬퍼.
        if item.result == "NEGATIVE":
            await apply_terminal_reproductive(db, sow, "EMPTY", check_date, farm_id)

    return SyncAccepted(id=item.id, entity="pregnancy_check", action="created"), None, None


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

    # 항목별 검증 — REST PigletEventCreate 규칙 미러(배치 전체 422 방지) — Codex P1
    if item.event_type not in _PIGLET_EVENT_TYPES:
        return None, SyncRejected(
            id=item.id, entity="piglet_event", reason="VALIDATION_FAILED",
            detail={"field": "event_type", "message": "invalid event_type", "value": item.event_type},
        ), None
    if item.piglet_count is None or item.piglet_count < 1:
        return None, SyncRejected(
            id=item.id, entity="piglet_event", reason="VALIDATION_FAILED",
            detail={"field": "piglet_count", "message": "piglet_count must be >= 1", "value": item.piglet_count},
        ), None
    if item.reason is not None and item.reason not in _PIGLET_REASONS:
        return None, SyncRejected(
            id=item.id, entity="piglet_event", reason="VALIDATION_FAILED",
            detail={"field": "reason", "message": "invalid reason", "value": item.reason},
        ), None

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
        len(req.changes.piglet_events) +
        len(req.changes.pregnancy_checks)
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
            # 처리 순서 = 의존관계 순서(B4 정공법, 2026-06-25):
            #   matings → farrowings → piglet_events(양자/폐사) → weanings → repro → health
            # 이유(weaning)의 유효복당 = born_alive + foster_in - foster_out - deaths 이므로,
            # piglet_events를 weanings보다 먼저 적용해야 양자 받은 nurse sow가 오거부되지 않는다.
            # (부가효과: 이유 후 sow=OPEN으로 바뀌므로, piglet_events를 먼저 처리해야 LACTATING
            #  상태에서 정상 기록됨 — 역순이면 뒤늦은 piglet_event가 STATUS 충돌로 거부될 수 있음.)
            processors = [
                (req.changes.matings,             _process_mating),
                (req.changes.farrowings,          _process_farrowing),
                (req.changes.piglet_events,       _process_piglet_event),
                (req.changes.weanings,            _process_weaning),
                (req.changes.reproductive_events, _process_reproductive),
                (req.changes.pregnancy_checks,    _process_pregnancy_check),
                (req.changes.health_events,       _process_health_event),
            ]

            for items, processor in processors:
                for item in items:
                    # #8: 항목별 savepoint — 한 항목의 DB에러(IntegrityError 등)가 트랜잭션을
                    # aborted 상태로 만들어 배치의 나머지 항목까지 연쇄 실패시키는 것을 차단
                    # (스펙의 '한 레코드 실패해도 나머지 정상 처리' 원자성 보장).
                    try:
                        async with db.begin_nested():
                            acc, rej, con = await processor(db, farm.id, item, req.dry_run)
                    except Exception as e:  # noqa: BLE001 — 항목 격리(savepoint 롤백 후 다음 항목 계속)
                        rejected.append(SyncRejected(
                            id=item.id,
                            entity=item.__class__.__name__,
                            reason="INTERNAL_ERROR",
                            detail={"error": str(e)},
                        ))
                        continue
                    if acc: accepted.append(acc)
                    if rej: rejected.append(rej)
                    if con: conflicts.append(con)

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
