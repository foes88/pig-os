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
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.config import ComplianceProfile, RegionDefault
from app.db.models.master import MedicationCatalog
from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.platform import AuditLog
from app.db.models.sow import BreedingCycle, Sow
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

    # 교배 기록 검증
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

    # 중복 분만 검증 (피그플랜: 동일 교배에 분만 1회)
    existing_farrowing = await db.scalar(
        select(Farrowing).where(
            Farrowing.mating_id == req.mating_id,
            Farrowing.deleted_at.is_(None),
        )
    )
    if existing_farrowing:
        raise ConflictError(f"Farrowing already recorded for mating {req.mating_id}")

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
        mating_id=req.mating_id,
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

    terminal_map = {
        "CULLED": "CULLED",
        "DEAD": "DEAD",
        # 번식사고 → ACCIDENT (재교배 대기). SCREEN_MENU_SPEC: RTS → Accident
        "RETURN_TO_ESTRUS": "ACCIDENT",
        "EMPTY": "ACCIDENT",
        "INFERTILE": "ACCIDENT",
        "ABORTION": "ACCIDENT",
    }
    if req.event_type in terminal_map:
        sow.status = terminal_map[req.event_type]
        if req.event_type in ("CULLED", "DEAD"):
            sow.exit_date = datetime.combine(req.event_date, datetime.min.time()).replace(tzinfo=UTC)

        # 비생산 이벤트 → 현재 사이클 FAILED 처리
        if req.event_type in ("RETURN_TO_ESTRUS", "ABORTION", "EMPTY", "INFERTILE"):
            cycle = await _get_open_cycle(db, sow.id)
            if cycle:
                cycle.cycle_status = "FAILED"
                cycle.ended_at = datetime.now(UTC)

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
