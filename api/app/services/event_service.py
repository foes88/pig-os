"""
Event recording service.
All events flow through here for consistent validation + audit logging.

PigPlan 로직 기반 핵심 규칙:
- 임신기간: 100~130일 (정상 114±3일)
- 포유기간: 10~60일 (정상 19~23일)
- 교배횟수: 사이클당 최대 5회 (gyobae_cnt)
- 분만 중복: 동일 mating_id로 분만 1회만 허용
- 이유 중복: 동일 farrowing_id로 이유 1회만 허용 (dedup)
- 이유두수: born_alive + foster_in - foster_out - deaths 이하
- 산차: 분만 완료 시 sow.parity += 1
"""
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.config import ComplianceProfile, RegionDefault
from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import Removal
from app.db.models.master import MedicationCatalog
from app.db.models.platform import AuditLog
from app.db.models.sow import BreedingCycle, PigletGroup, Sow
from app.schemas.events import (
    FarrowingCreate,
    MatingCreate,
    PigletEventCreate,
    ReproductiveEventCreate,
    WeaningCreate,
)
from app.validators.cross_fostering import validate_cross_fostering
from app.validators.date_rules import (
    validate_event_within_sow_lifespan,
    validate_farrowing_after_mating,
    validate_mating_after_last_weaning,
    validate_weaning_after_farrowing,
)
from app.validators.farrowing import validate_farrowing
from app.validators.mating import validate_mating
from app.validators.sow_state import validate_transition

# 피그플랜 기준 상수
GESTATION_MIN_DAYS = 100
GESTATION_MAX_DAYS = 130
NURSING_MIN_DAYS = 10
NURSING_MAX_DAYS = 60
MAX_MATING_PER_CYCLE = 5
MAX_WEANED_COUNT = 30

# 교배 가능 상태 — docs/SCREEN_MENU_SPEC.md 상태 정의 기준
# GILT(후보돈) / OPEN(공태) / ACCIDENT(번식사고 후 재교배 대기)
MATABLE_STATUSES = {"GILT", "OPEN", "ACCIDENT"}


async def _get_compliance(db: AsyncSession, farm_id: UUID) -> ComplianceProfile | None:
    """Resolve compliance profile for a farm via region_defaults chain."""
    from app.db.models.platform import Farm as FarmModel
    farm = await db.get(FarmModel, farm_id)
    if not farm or not farm.country:
        return None
    region = await db.scalar(
        select(RegionDefault).where(RegionDefault.region_code == farm.country.upper())
    )
    if not region or not region.compliance_profile_code:
        return None
    return await db.scalar(
        select(ComplianceProfile).where(
            ComplianceProfile.profile_code == region.compliance_profile_code
        )
    )


async def _check_wean_compliance(db: AsyncSession, farm_id: UUID, nursing_days: int) -> None:
    """Raise ValidationError if weaning is below the country's minimum legal wean age."""
    compliance = await _get_compliance(db, farm_id)
    if compliance and compliance.min_wean_period and nursing_days < compliance.min_wean_period:
        raise ValidationError(
            f"Weaning at {nursing_days} days is below the minimum {compliance.min_wean_period} days "
            f"required by compliance profile '{compliance.profile_code}'"
        )


async def _check_vfd_compliance(
    db: AsyncSession, farm_id: UUID, drug_code: str | None
) -> None:
    """
    US: Raise ValidationError if the medication requires a VFD (Veterinary Feed Directive)
    and no override flag is provided.
    """
    if not drug_code:
        return
    from app.db.models.platform import Farm as FarmModel
    farm = await db.get(FarmModel, farm_id)
    if not farm or farm.country.upper() != "US":
        return
    med = await db.scalar(
        select(MedicationCatalog).where(MedicationCatalog.active_substance == drug_code)
    )
    if med and med.vfd_required_us:
        raise ValidationError(
            f"Medication '{drug_code}' requires a Veterinary Feed Directive (VFD) in the US. "
            "Ensure a signed VFD is on file before recording this treatment."
        )


def _as_date(value):
    """Coerce a (timezone-aware) datetime column to a plain ``date`` for validators."""
    if value is None:
        return None
    return value.date() if isinstance(value, datetime) else value


async def _last_weaning_date(db: AsyncSession, sow_id: UUID):
    """Most recent weaning date for a sow (None if never weaned)."""
    return await db.scalar(
        select(Weaning.weaning_date)
        .where(Weaning.sow_id == sow_id, Weaning.deleted_at.is_(None))
        .order_by(Weaning.weaning_date.desc())
        .limit(1)
    )


async def _get_active_sow(db: AsyncSession, farm_id: UUID, sow_id: UUID) -> Sow:
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found in farm")
    return sow


async def _audit(
    db: AsyncSession,
    user_id: UUID,
    farm_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID,
    new_value: dict,
) -> None:
    db.add(AuditLog(
        user_id=user_id,
        farm_id=farm_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        new_value=new_value,
    ))


async def _get_open_cycle(db: AsyncSession, sow_id: UUID) -> BreedingCycle | None:
    return await db.scalar(
        select(BreedingCycle).where(
            BreedingCycle.sow_id == sow_id,
            BreedingCycle.cycle_status.notin_(["WEANED", "FAILED"]),
        )
    )


async def record_mating(
    db: AsyncSession,
    farm_id: UUID,
    user_id: UUID,
    req: MatingCreate,
) -> Mating:
    sow = await _get_active_sow(db, farm_id, req.sow_id)

    # 교배 가능 상태 + 날짜 검증 (app.validators)
    validate_mating(sow_status=sow.status)
    validate_event_within_sow_lifespan(
        event_date=req.mating_date,
        entry_date=_as_date(sow.entry_date),
        exit_date=_as_date(sow.exit_date),
        event_name="Mating",
    )
    validate_mating_after_last_weaning(
        mating_date=req.mating_date,
        last_weaning_date=await _last_weaning_date(db, sow.id),
    )

    cycle = await _get_open_cycle(db, sow.id)

    if cycle:
        # 기존 사이클에 재교배 — 교배횟수 상한 검증
        existing_matings = await db.scalar(
            select(func.count()).select_from(Mating).where(
                Mating.breeding_cycle_id == cycle.id,
                Mating.deleted_at.is_(None),
            )
        ) or 0
        if existing_matings >= MAX_MATING_PER_CYCLE:
            raise ValidationError(
                f"Cannot record more than {MAX_MATING_PER_CYCLE} matings per breeding cycle"
            )
        mating_number = existing_matings + 1
    else:
        # 새 사이클 시작
        cycle = BreedingCycle(
            farm_id=farm_id,
            sow_id=sow.id,
            parity=sow.parity + 1,
            started_at=datetime.combine(req.mating_date, datetime.min.time()).replace(tzinfo=UTC),
        )
        db.add(cycle)
        await db.flush()
        mating_number = 1

    mating = Mating(
        farm_id=farm_id,
        sow_id=req.sow_id,
        boar_id=req.boar_id,
        breeding_cycle_id=cycle.id,
        mating_date=req.mating_date,
        mating_type=req.mating_type,
        mating_number=mating_number,  # 자동 계산 (피그플랜 gyobae_cnt 방식)
        semen_batch=req.semen_batch,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(mating)
    await db.flush()

    sow.status = "PREGNANT"
    cycle.cycle_status = "MATED"
    cycle.mating_count = mating_number

    await _audit(db, user_id, farm_id, "CREATE", "matings", mating.id, req.model_dump(mode="json"))
    await db.commit()
    await db.refresh(mating)
    return mating


async def record_farrowing(
    db: AsyncSession,
    farm_id: UUID,
    user_id: UUID,
    req: FarrowingCreate,
) -> Farrowing:
    sow = await _get_active_sow(db, farm_id, req.sow_id)

    # 교배 기록 검증 — mating_id 미지정 시 해당 모돈의 '최근 미분만 교배' 자동 조회
    # (UI 계약: 분만 탭에서 교배 선택 없이 저장 가능)
    if req.mating_id is not None:
        mating = await db.scalar(
            select(Mating).where(
                Mating.id == req.mating_id,
                Mating.sow_id == sow.id,
                Mating.farm_id == farm_id,
                Mating.deleted_at.is_(None),
            )
        )
        if not mating:
            raise NotFoundError(f"Mating {req.mating_id} not found for this sow")
    else:
        # 분만 기록이 아직 없는 최근 교배 1건
        mating = await db.scalar(
            select(Mating)
            .outerjoin(
                Farrowing,
                (Farrowing.mating_id == Mating.id) & (Farrowing.deleted_at.is_(None)),
            )
            .where(
                Mating.sow_id == sow.id,
                Mating.farm_id == farm_id,
                Mating.deleted_at.is_(None),
                Farrowing.id.is_(None),
            )
            .order_by(Mating.mating_date.desc())
            .limit(1)
        )
        if not mating:
            raise NotFoundError("No open mating found for this sow to record farrowing")

    # 중복 분만 검증 (피그플랜: 동일 교배에 분만 1회)
    existing_farrowing = await db.scalar(
        select(Farrowing).where(
            Farrowing.mating_id == mating.id,
            Farrowing.deleted_at.is_(None),
        )
    )
    if existing_farrowing:
        raise ConflictError(f"Farrowing already recorded for mating {mating.id}")

    # 상태전이 검증: 분만은 PREGNANT(임신)에서만 (중복·미발견 검사 뒤 = 더 구체적 에러 우선)
    validate_transition(event="farrowing", current_status=sow.status)

    # 임신기간 검증 (100~130일)
    gestation = (req.farrowing_date - mating.mating_date).days
    if not (GESTATION_MIN_DAYS <= gestation <= GESTATION_MAX_DAYS):
        raise ValidationError(
            f"Gestation period {gestation} days is outside {GESTATION_MIN_DAYS}~{GESTATION_MAX_DAYS} range"
        )

    # total_born 일관성 검증
    expected_total = req.born_alive + req.stillborn + req.mummified
    if req.total_born != expected_total:
        raise ValidationError(
            f"total_born ({req.total_born}) != born_alive + stillborn + mummified ({expected_total})"
        )

    # 분만 입력값 한도 + 날짜 순서 검증 (app.validators)
    validate_farrowing(
        total_born=req.total_born,
        born_alive=req.born_alive,
        stillborn=req.stillborn,
        mummified=req.mummified,
    )
    validate_event_within_sow_lifespan(
        event_date=req.farrowing_date,
        entry_date=_as_date(sow.entry_date),
        exit_date=_as_date(sow.exit_date),
        event_name="Farrowing",
    )
    validate_farrowing_after_mating(
        farrowing_date=req.farrowing_date, mating_date=mating.mating_date
    )

    farrowing = Farrowing(
        farm_id=farm_id,
        sow_id=req.sow_id,
        mating_id=mating.id,
        breeding_cycle_id=mating.breeding_cycle_id,
        farrowing_date=req.farrowing_date,
        total_born=req.total_born,
        born_alive=req.born_alive,
        stillborn=req.stillborn,
        mummified=req.mummified,
        farrowing_ease=req.farrowing_ease,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(farrowing)
    await db.flush()

    # 산차 증가 + 상태 변경
    sow.status = "LACTATING"
    sow.parity = sow.parity + 1

    if mating.breeding_cycle_id:
        cycle = await db.get(BreedingCycle, mating.breeding_cycle_id)
        if cycle:
            cycle.cycle_status = "FARROWED"

    await _audit(db, user_id, farm_id, "CREATE", "farrowings", farrowing.id, req.model_dump(mode="json"))
    await db.commit()
    await db.refresh(farrowing)
    return farrowing


async def record_weaning(
    db: AsyncSession,
    farm_id: UUID,
    user_id: UUID,
    req: WeaningCreate,
) -> Weaning:
    sow = await _get_active_sow(db, farm_id, req.sow_id)

    if req.farrowing_id:
        farrowing = await db.scalar(
            select(Farrowing).where(
                Farrowing.id == req.farrowing_id,
                Farrowing.sow_id == sow.id,
                Farrowing.deleted_at.is_(None),
            )
        )
        if not farrowing:
            raise NotFoundError(f"Farrowing {req.farrowing_id} not found for this sow")
    else:
        # farrowing_id 미전달 시 가장 최근 미이유 분만 자동 조회
        farrowing = await db.scalar(
            select(Farrowing)
            .where(Farrowing.sow_id == sow.id, Farrowing.deleted_at.is_(None))
            .order_by(Farrowing.farrowing_date.desc())
            .limit(1)
        )
        if not farrowing:
            raise NotFoundError("No farrowing found for this sow")

    # 중복 이유 검증 (피그플랜 dedup: 동일 farrowing_id로 이유 1회만)
    existing_weaning = await db.scalar(
        select(Weaning).where(
            Weaning.farrowing_id == req.farrowing_id,
            Weaning.deleted_at.is_(None),
        )
    )
    if existing_weaning:
        raise ConflictError(f"Weaning already recorded for farrowing {req.farrowing_id}")

    # 상태전이 검증: 이유는 LACTATING(포유)에서만 (중복 검사 뒤 = 더 구체적 에러 우선)
    validate_transition(event="weaning", current_status=sow.status)

    # 이유일 > 분만일 순서 검증 (app.validators)
    validate_weaning_after_farrowing(
        weaning_date=req.weaning_date, farrowing_date=farrowing.farrowing_date
    )

    # 포유기간 검증 (10~60일)
    nursing_days = (req.weaning_date - farrowing.farrowing_date).days
    if not (NURSING_MIN_DAYS <= nursing_days <= NURSING_MAX_DAYS):
        raise ValidationError(
            f"Nursing period {nursing_days} days is outside {NURSING_MIN_DAYS}~{NURSING_MAX_DAYS} range"
        )

    # 컴플라이언스: 국가별 최소 이유일령 검증
    await _check_wean_compliance(db, farm_id, nursing_days)

    # 이유두수 검증: foster 이벤트 반영
    foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
    effective_litter = max(0, farrowing.born_alive + foster_in - foster_out - deaths)
    if req.weaned_count > MAX_WEANED_COUNT:
        raise ValidationError(f"weaned_count exceeds maximum {MAX_WEANED_COUNT}")
    if req.weaned_count > effective_litter:
        raise ValidationError(
            f"weaned_count ({req.weaned_count}) > effective litter "
            f"({farrowing.born_alive} born_alive + {foster_in} foster_in "
            f"- {foster_out} foster_out - {deaths} deaths = {effective_litter})"
        )

    weaning = Weaning(
        farm_id=farm_id,
        sow_id=req.sow_id,
        farrowing_id=farrowing.id,
        breeding_cycle_id=farrowing.breeding_cycle_id,
        weaning_date=req.weaning_date,
        weaned_count=req.weaned_count,
        weaning_age_days=nursing_days,
        avg_weaning_weight_kg=req.avg_weaning_weight_kg,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(weaning)
    await db.flush()

    # 이유 → 공태 복귀 (SCREEN_MENU_SPEC: Weaning = Lactating → Open)
    sow.status = "OPEN"

    if farrowing.breeding_cycle_id:
        cycle = await db.get(BreedingCycle, farrowing.breeding_cycle_id)
        if cycle:
            cycle.cycle_status = "WEANED"
            cycle.ended_at = datetime.now(UTC)

    # 데이터 정합성: 이유된 자돈을 그룹으로 추적(떠다니는 두수 방지, PSY→MSY 사슬 연결).
    # 이유 1건 = 자돈그룹 1개 자동 생성(head_count_in = weaned_count).
    if req.weaned_count > 0:
        code = f"WG-{req.weaning_date:%y%m%d}-{sow.ear_tag}"
        exists = await db.scalar(
            select(PigletGroup).where(PigletGroup.farm_id == farm_id, PigletGroup.group_code == code)
        )
        if not exists:
            db.add(PigletGroup(
                farm_id=farm_id, group_code=code, weaning_date=req.weaning_date,
                head_count_in=req.weaned_count, created_by=user_id,
                notes=f"auto: weaning {sow.ear_tag}",
            ))

    await _audit(db, user_id, farm_id, "CREATE", "weanings", weaning.id, req.model_dump(mode="json"))
    await db.commit()
    await db.refresh(weaning)
    return weaning


async def _calc_piglet_adjustments(
    db: AsyncSession, farrowing_id: UUID
) -> tuple[int, int, int]:
    """farrowing_id 기준 foster_in / foster_out / deaths 합계 반환."""
    rows = list(await db.scalars(
        select(PigletEvent).where(
            PigletEvent.farrowing_id == farrowing_id,
            PigletEvent.deleted_at.is_(None),
        )
    ))
    foster_in = sum(r.piglet_count for r in rows if r.event_type == "FOSTER_IN")
    foster_out = sum(r.piglet_count for r in rows if r.event_type == "FOSTER_OUT")
    deaths = sum(r.piglet_count for r in rows if r.event_type == "DEATH")
    return foster_in, foster_out, deaths


# 번식사고/종료 이벤트의 모돈 상태 전이 — REST·sync 공유(드리프트 방지, Codex P1)
_REPRO_ALIAS = {"CULL": "CULLED", "DEATH": "DEAD"}
_REPRO_TERMINAL = ("CULLED", "DEAD", "SOLD", "TRANSFER_OUT")
_REPRO_ACCIDENT = ("RETURN_TO_ESTRUS", "EMPTY", "INFERTILE", "ABORTION")
# 종료 event_type → 유효 SowStatus v2 매핑. "TRANSFER_OUT"은 SowStatus가 아니므로 TRANSFER로.
# (removal_type에는 원래 event_type을 그대로 기록)
_REPRO_TERMINAL_STATUS = {"CULLED": "CULLED", "DEAD": "DEAD", "SOLD": "SOLD", "TRANSFER_OUT": "TRANSFER"}


async def apply_terminal_reproductive(
    db: AsyncSession, sow: Sow, event_type: str, event_date: date, farm_id: UUID,
) -> None:
    """번식사고/종료 이벤트 → 모돈 상태 전이 (REST·sync 동일 동작).
    - 종료(CULLED/DEAD/SOLD/TRANSFER_OUT): status 전이 + exit_date + soft-delete + Removal 기록.
    - 사고(RTS/EMPTY/INFERTILE/ABORTION): status=ACCIDENT + 진행 사이클 FAILED.
    """
    ev = _REPRO_ALIAS.get(event_type, event_type)
    if ev in _REPRO_TERMINAL:
        now = datetime.now(UTC)
        sow.status = _REPRO_TERMINAL_STATUS[ev]  # 유효 SowStatus v2 (TRANSFER_OUT→TRANSFER)
        sow.exit_date = datetime.combine(event_date, datetime.min.time()).replace(tzinfo=UTC)
        sow.deleted_at = now
        db.add(Removal(farm_id=farm_id, sow_id=sow.id, removal_date=event_date, removal_type=ev))
    elif ev in _REPRO_ACCIDENT:
        sow.status = "ACCIDENT"
        cycle = await _get_open_cycle(db, sow.id)
        if cycle:
            cycle.cycle_status = "FAILED"
            cycle.ended_at = datetime.now(UTC)


async def record_reproductive_event(
    db: AsyncSession,
    farm_id: UUID,
    user_id: UUID,
    req: ReproductiveEventCreate,
) -> ReproductiveEvent:
    sow = await _get_active_sow(db, farm_id, req.sow_id)

    event = ReproductiveEvent(
        farm_id=farm_id,
        sow_id=req.sow_id,
        mating_id=req.mating_id,
        event_date=req.event_date,
        event_type=req.event_type,
        detected_method=req.detected_method,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(event)
    await db.flush()

    # 상태 전이 — REST·sync 공유 헬퍼(드리프트 방지). SOLD/TRANSFER_OUT 포함 종료 일관 처리.
    await apply_terminal_reproductive(db, sow, req.event_type, req.event_date, farm_id)

    await _audit(db, user_id, farm_id, "CREATE", "reproductive_events", event.id, req.model_dump(mode="json"))
    await db.commit()
    await db.refresh(event)
    return event


async def record_piglet_event(
    db: AsyncSession,
    farm_id: UUID,
    user_id: UUID,
    req: PigletEventCreate,
) -> PigletEvent:
    sow = await _get_active_sow(db, farm_id, req.sow_id)

    if req.farrowing_id:
        farrowing = await db.scalar(
            select(Farrowing).where(
                Farrowing.id == req.farrowing_id,
                Farrowing.sow_id == sow.id,
                Farrowing.deleted_at.is_(None),
            )
        )
        if not farrowing:
            raise NotFoundError(f"Farrowing {req.farrowing_id} not found for this sow")
    else:
        farrowing = await db.scalar(
            select(Farrowing)
            .where(Farrowing.sow_id == sow.id, Farrowing.deleted_at.is_(None))
            .order_by(Farrowing.farrowing_date.desc())
            .limit(1)
        )
        if not farrowing:
            raise NotFoundError("No active farrowing found for this sow")

    # 양자 이동 두수 한도 검증 (app.validators)
    if req.event_type in ("FOSTER_IN", "FOSTER_OUT"):
        validate_cross_fostering(transfer_count=req.piglet_count)

    # 정합성: 자돈 폐사 두수는 현재 포유 두수(생존+양자in-양자out-기존폐사) 초과 불가.
    # (초과 시 이유두수 공식이 음수로 깨져 두수가 안 맞음)
    if req.event_type == "DEATH":
        foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
        nursing = farrowing.born_alive + foster_in - foster_out - deaths
        if req.piglet_count > nursing:
            raise ValidationError(
                f"Piglet deaths ({req.piglet_count}) exceed current nursing count "
                f"({farrowing.born_alive} born_alive + {foster_in} in - {foster_out} out "
                f"- {deaths} prior deaths = {nursing})"
            )

    event = PigletEvent(
        farm_id=farm_id,
        farrowing_id=farrowing.id,
        sow_id=req.sow_id,
        event_date=req.event_date,
        event_type=req.event_type,
        piglet_count=req.piglet_count,
        reason=req.reason,
        target_sow_id=req.target_sow_id,
        target_farrowing_id=req.target_farrowing_id,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(event)
    await _audit(db, user_id, farm_id, "CREATE", "piglet_events", event.id, req.model_dump(mode="json"))
    await db.commit()
    await db.refresh(event)
    return event


# ── Event edit / delete (Phase 12) ────────────────────────────────────────────

# Sow status to restore when an event is deleted (undo its forward transition).
ROLLBACK_STATUS_ON_DELETE: dict[str, str] = {
    "mating": "OPEN",         # PREGNANT → OPEN
    "farrowing": "PREGNANT",  # LACTATING → PREGNANT
    "weaning": "LACTATING",   # OPEN → LACTATING
}


def rollback_status_on_delete(event_type: str) -> str:
    """Pure: the sow status to restore after deleting ``event_type``."""
    try:
        return ROLLBACK_STATUS_ON_DELETE[event_type]
    except KeyError as e:
        raise ValidationError(f"Cannot roll back unknown event type '{event_type}'") from e


async def _ensure_period_unlocked(db: AsyncSession, farm_id: UUID, d: date) -> None:
    """Raise 423 if the month containing ``d`` is closed in period_locks."""
    from app.db.models.ops import PeriodLock
    lock = await db.scalar(
        select(PeriodLock).where(
            PeriodLock.farm_id == farm_id,
            PeriodLock.period_year == d.year,
            PeriodLock.period_month == d.month,
            PeriodLock.unlocked_at.is_(None),
        )
    )
    if lock:
        raise HTTPException(
            status_code=423,
            detail=f"Period {d.year}-{d.month:02d} is locked; unlock it before editing.",
        )


async def update_mating(db, farm_id, user_id, mating_id, body) -> Mating:
    m = await db.scalar(select(Mating).where(
        Mating.id == mating_id, Mating.farm_id == farm_id, Mating.deleted_at.is_(None)))
    if not m:
        raise NotFoundError(f"Mating {mating_id} not found")
    await _ensure_period_unlocked(db, farm_id, m.mating_date)
    data = body.model_dump(exclude_unset=True)
    if "mating_date" in data and data["mating_date"]:
        await _ensure_period_unlocked(db, farm_id, data["mating_date"])
    for k, v in data.items():
        setattr(m, k, v)
    await _audit(db, user_id, farm_id, "UPDATE", "matings", m.id, data)
    await db.commit(); await db.refresh(m)
    return m


async def delete_mating(db, farm_id, user_id, mating_id) -> None:
    m = await db.scalar(select(Mating).where(
        Mating.id == mating_id, Mating.farm_id == farm_id, Mating.deleted_at.is_(None)))
    if not m:
        raise NotFoundError(f"Mating {mating_id} not found")
    await _ensure_period_unlocked(db, farm_id, m.mating_date)
    if await db.scalar(select(Farrowing).where(
            Farrowing.mating_id == m.id, Farrowing.deleted_at.is_(None))):
        raise ConflictError("Cannot delete a mating that already has a farrowing")
    m.deleted_at = datetime.now(UTC)
    sow = await _get_active_sow(db, farm_id, m.sow_id)
    sow.status = rollback_status_on_delete("mating")
    if m.breeding_cycle_id:
        cycle = await db.get(BreedingCycle, m.breeding_cycle_id)
        if cycle:
            cycle.cycle_status = "FAILED"
            cycle.ended_at = datetime.now(UTC)
    await _audit(db, user_id, farm_id, "DELETE", "matings", m.id, {"id": str(m.id)})
    await db.commit()


async def update_farrowing(db, farm_id, user_id, farrowing_id, body) -> Farrowing:
    f = await db.scalar(select(Farrowing).where(
        Farrowing.id == farrowing_id, Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None)))
    if not f:
        raise NotFoundError(f"Farrowing {farrowing_id} not found")
    await _ensure_period_unlocked(db, farm_id, f.farrowing_date)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(f, k, v)
    f.total_born = f.born_alive + f.stillborn + f.mummified
    validate_farrowing(total_born=f.total_born, born_alive=f.born_alive,
                       stillborn=f.stillborn, mummified=f.mummified)
    await _audit(db, user_id, farm_id, "UPDATE", "farrowings", f.id, data)
    await db.commit(); await db.refresh(f)
    return f


async def delete_farrowing(db, farm_id, user_id, farrowing_id) -> None:
    f = await db.scalar(select(Farrowing).where(
        Farrowing.id == farrowing_id, Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None)))
    if not f:
        raise NotFoundError(f"Farrowing {farrowing_id} not found")
    await _ensure_period_unlocked(db, farm_id, f.farrowing_date)
    if await db.scalar(select(Weaning).where(
            Weaning.farrowing_id == f.id, Weaning.deleted_at.is_(None))):
        raise ConflictError("Cannot delete a farrowing that already has a weaning")
    f.deleted_at = datetime.now(UTC)
    sow = await _get_active_sow(db, farm_id, f.sow_id)
    sow.status = rollback_status_on_delete("farrowing")
    sow.parity = max(0, sow.parity - 1)  # undo the increment from record_farrowing
    if f.breeding_cycle_id:
        cycle = await db.get(BreedingCycle, f.breeding_cycle_id)
        if cycle:
            cycle.cycle_status = "MATED"
    await _audit(db, user_id, farm_id, "DELETE", "farrowings", f.id, {"id": str(f.id)})
    await db.commit()


async def update_weaning(db, farm_id, user_id, weaning_id, body) -> Weaning:
    w = await db.scalar(select(Weaning).where(
        Weaning.id == weaning_id, Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None)))
    if not w:
        raise NotFoundError(f"Weaning {weaning_id} not found")
    await _ensure_period_unlocked(db, farm_id, w.weaning_date)
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(w, k, v)
    await _audit(db, user_id, farm_id, "UPDATE", "weanings", w.id, data)
    await db.commit(); await db.refresh(w)
    return w


async def delete_weaning(db, farm_id, user_id, weaning_id) -> None:
    w = await db.scalar(select(Weaning).where(
        Weaning.id == weaning_id, Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None)))
    if not w:
        raise NotFoundError(f"Weaning {weaning_id} not found")
    await _ensure_period_unlocked(db, farm_id, w.weaning_date)
    w.deleted_at = datetime.now(UTC)
    sow = await _get_active_sow(db, farm_id, w.sow_id)
    sow.status = rollback_status_on_delete("weaning")
    if w.breeding_cycle_id:
        cycle = await db.get(BreedingCycle, w.breeding_cycle_id)
        if cycle:
            cycle.cycle_status = "FARROWED"
            cycle.ended_at = None
    await _audit(db, user_id, farm_id, "DELETE", "weanings", w.id, {"id": str(w.id)})
    await db.commit()
