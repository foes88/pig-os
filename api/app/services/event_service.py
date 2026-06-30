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

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, PeriodLockedError, ValidationError
from app.db.models.config import ComplianceProfile, RegionDefault
from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    PregnancyCheck,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import Removal
from app.db.models.master import MedicationCatalog
from app.db.models.platform import AuditLog
from app.db.models.sow import Boar, BreedingCycle, PigletGroup, Sow
from app.schemas.events import (
    FarrowingCreate,
    MatingCreate,
    PigletEventCreate,
    PregnancyCheckCreate,
    ReproductiveEventCreate,
    WeaningCreate,
)
from app.validators.cross_fostering import validate_cross_fostering
from app.validators.date_rules import (
    validate_event_within_sow_lifespan,
    validate_farrowing_after_mating,
    validate_mating_after_last_weaning,
    validate_piglet_event_date,
    validate_weaning_after_farrowing,
)
from app.validators.farrowing import validate_farrowing
from app.validators.mating import validate_mating
from app.validators.sow_state import validate_transition
from app.validators.weaning import validate_weaning

# 피그플랜 기준 상수
GESTATION_MIN_DAYS = 100
GESTATION_MAX_DAYS = 130
NURSING_MIN_DAYS = 10
NURSING_MAX_DAYS = 60
MAX_MATING_PER_CYCLE = 5
MAX_WEANED_COUNT = 30
MAX_NURSING_COUNT = 24  # 양자 후 한 모돈 포유두수 상한(과혼잡 방지, 유두수+간호모돈 현실 상한)

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

    # 교배 가능 상태 + 웅돈 순서 검증 (P0-BE-9: boar 슬롯 인자 전달)
    validate_mating(
        sow_status=sow.status,
        boar_1=req.boar_id,
        boar_2=getattr(req, "boar_id_2", None),
        boar_3=getattr(req, "boar_id_3", None),
    )

    # P0-BE-8: 웅돈은 ACTIVE 상태만 교배 사용 가능
    if req.boar_id:
        boar = await db.scalar(
            select(Boar).where(Boar.id == req.boar_id, Boar.farm_id == farm_id)
        )
        if not boar:
            raise NotFoundError(f"Boar {req.boar_id} not found in farm")
        if boar.status != "ACTIVE":
            raise ValidationError(
                f"Boar {boar.ear_tag} is '{boar.status}' and cannot be used for mating"
            )

    # P0-BE-7: 동일 날짜 중복 교배 방지
    dup = await db.scalar(
        select(Mating).where(
            Mating.sow_id == sow.id,
            Mating.mating_date == req.mating_date,
            Mating.deleted_at.is_(None),
        )
    )
    if dup:
        raise ConflictError("A mating is already recorded for this sow on this date")

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

    # 분만 입력값 한도 + 날짜 순서 검증 (app.validators) — P0-BE-6: 출생체중·암수 인자 완성
    validate_farrowing(
        total_born=req.total_born,
        born_alive=req.born_alive,
        stillborn=req.stillborn,
        mummified=req.mummified,
        avg_birth_weight_kg=getattr(req, "avg_birth_weight_kg", None),
        male=getattr(req, "born_alive_male", None),
        female=getattr(req, "born_alive_female", None),
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
        nursing_head=req.born_alive,  # P0-BE-4: 포유개시두수 초기값 = 실산 (양자 발생 시 갱신)
        avg_birth_weight_kg=getattr(req, "avg_birth_weight_kg", None),
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

    # 부분이유 모델: 잔여 포유두수 = 유효복당두수 - 기존 이유합
    foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
    effective_litter = max(0, farrowing.born_alive + foster_in - foster_out - deaths)
    prior_weaned = await db.scalar(
        select(func.coalesce(func.sum(Weaning.weaned_count), 0)).where(
            Weaning.farrowing_id == farrowing.id, Weaning.deleted_at.is_(None)
        )
    ) or 0
    remaining = effective_litter - int(prior_weaned)

    # 이미 전부 이유됨 → 더 이상 이유 불가 (기존 dedup 대체)
    if remaining <= 0:
        raise ConflictError(f"Litter already fully weaned for farrowing {farrowing.id}")

    # 상태전이 검증: 이유는 LACTATING(포유)에서만 (잔여 검사 뒤 = 더 구체적 에러 우선)
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

    # P0-BE-2: 이유체중 유효 범위 2~12kg
    if req.avg_weaning_weight_kg is not None and not (2.0 <= req.avg_weaning_weight_kg <= 12.0):
        raise ValidationError(
            f"Average weaning weight {req.avg_weaning_weight_kg}kg is outside the valid range (2~12kg)"
        )

    # 두수 상한 + 잔여 초과 검증
    if req.weaned_count > MAX_WEANED_COUNT:
        raise ValidationError(f"weaned_count exceeds maximum {MAX_WEANED_COUNT}")
    if req.weaned_count > remaining:
        raise ValidationError(
            f"weaned_count ({req.weaned_count}) > remaining nursing "
            f"(effective litter {effective_litter} - already weaned {int(prior_weaned)} = {remaining})"
        )

    # 최종이유(is_partial=False)는 잔여 전량 == weaned_count 항등식 강제.
    # 부분이유(is_partial=True)는 weaned_count <= remaining 허용(위에서 검증).
    # 출처: PigPlan DataValidationChk.java L747~752
    if not req.is_partial:
        validate_weaning(weaned=req.weaned_count, nursing_head=remaining)

    remaining_after = remaining - req.weaned_count

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

    # 잔여 포유두수 0 → 이유 완료(공태 복귀 + 사이클 종료). 잔여>0(부분이유) → LACTATING 유지.
    if remaining_after <= 0:
        sow.status = "OPEN"
        if farrowing.breeding_cycle_id:
            cycle = await db.get(BreedingCycle, farrowing.breeding_cycle_id)
            if cycle:
                cycle.cycle_status = "WEANED"
                cycle.ended_at = datetime.now(UTC)
    # else: 부분이유 — 모돈 LACTATING 유지, 사이클 FARROWED 유지

    # 데이터 정합성: 이유된 자돈을 그룹으로 추적(떠다니는 두수 방지, PSY→MSY 사슬 연결).
    # 이유 1건 = 자돈그룹 1개 자동 생성. 같은 날 부분이유 복수 대비 weaning id suffix로 충돌 방지.
    if req.weaned_count > 0:
        # group_code는 VARCHAR(30) — ear_tag 길이에 무관하게 길이 보장(INTEG-1).
        # weaning.id로 유일성 확보(같은 날 부분이유 복수 충돌 방지), ear_tag는 notes에 보존.
        code = f"WG-{req.weaning_date:%y%m%d}-{str(weaning.id)[:8]}"  # 18자 ≤ 30
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

    # P0-BE-10: 임신 중 도폐사(CULLED/DEAD) 시 사유(notes) 필수
    if sow.status == "PREGNANT" and req.event_type in ("CULLED", "DEAD") and not req.notes:
        raise ValidationError("A reason (notes) is required when culling/removing a pregnant sow")

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


async def record_pregnancy_check(
    db: AsyncSession,
    farm_id: UUID,
    user_id: UUID,
    req: PregnancyCheckCreate,
) -> PregnancyCheck:
    """임신감정 기록. PREGNANT 모돈만 대상. 음성(NEGATIVE)=공태 → ACCIDENT 전이(EMPTY와 동일)."""
    sow = await _get_active_sow(db, farm_id, req.sow_id)

    # 임신감정은 교배 후 PREGNANT 모돈에서만
    if sow.status != "PREGNANT":
        raise ValidationError(
            f"Pregnancy check requires a PREGNANT sow (current: {sow.status})"
        )

    validate_event_within_sow_lifespan(
        event_date=req.check_date,
        entry_date=_as_date(sow.entry_date),
        exit_date=_as_date(sow.exit_date),
        event_name="Pregnancy check",
    )

    event = PregnancyCheck(
        farm_id=farm_id,
        sow_id=req.sow_id,
        mating_id=req.mating_id,
        check_date=req.check_date,
        days_after_mating=req.days_after_mating,
        result=req.result,
        method=req.method,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(event)
    await db.flush()

    # 음성 = 공태(EMPTY) → ACCIDENT 전이 + 진행 사이클 FAILED (재교배 대기)
    if req.result == "NEGATIVE":
        await apply_terminal_reproductive(db, sow, "EMPTY", req.check_date, farm_id)

    await _audit(db, user_id, farm_id, "CREATE", "pregnancy_checks", event.id, req.model_dump(mode="json"))
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

    # V1 — 날짜 정합성: 자돈 이벤트는 분만일 이후, 이유 완료 시 이유일 이전. 미래일/입식전 금지.
    wean = await db.scalar(
        select(Weaning).where(Weaning.farrowing_id == farrowing.id, Weaning.deleted_at.is_(None))
    )
    validate_piglet_event_date(
        event_date=req.event_date,
        farrowing_date=farrowing.farrowing_date,
        weaning_date=wean.weaning_date if wean else None,
    )
    validate_event_within_sow_lifespan(
        event_date=req.event_date, entry_date=_as_date(sow.entry_date),
        exit_date=_as_date(sow.exit_date), event_name="Piglet event",
    )

    # 양자 이동 두수 한도 검증 (app.validators)
    if req.event_type in ("FOSTER_IN", "FOSTER_OUT"):
        validate_cross_fostering(transfer_count=req.piglet_count)
        # V2 — 양자 전입/전출은 상대 모돈(target_sow_id)이 명시되고, 포유 중(LACTATING)이어야
        # 고아 자돈/유령 참조를 방지.
        if not req.target_sow_id:
            raise ValidationError("Cross-foster requires target_sow_id (the counterpart sow)")
        if req.target_sow_id == sow.id:
            raise ValidationError("Cross-foster target must be a different sow (cannot foster to self)")
        target = await db.scalar(
            select(Sow).where(Sow.id == req.target_sow_id, Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        )
        if not target:
            raise ValidationError("target_sow_id is not a valid active sow in this farm")
        if target.status != "LACTATING":
            raise ValidationError(
                f"Cross-foster counterpart sow must be lactating (current: {target.status})"
            )
        # TENANT#1 — target_farrowing_id 주어지면 같은 농장 분만인지 검증(교차테넌트 dangling FK 방지)
        if req.target_farrowing_id:
            tgt_far = await db.scalar(
                select(Farrowing).where(
                    Farrowing.id == req.target_farrowing_id,
                    Farrowing.farm_id == farm_id,
                    Farrowing.deleted_at.is_(None),
                )
            )
            if not tgt_far:
                raise ValidationError("target_farrowing_id is not a valid farrowing in this farm")
        # V3 — 양자 전입(FOSTER_IN) 후 이 모돈 포유두수가 상한 초과 시 차단(과혼잡 방지)
        if req.event_type == "FOSTER_IN":
            fi, fo, dd = await _calc_piglet_adjustments(db, farrowing.id)
            nursing_after = farrowing.born_alive + fi + req.piglet_count - fo - dd
            if nursing_after > MAX_NURSING_COUNT:
                raise ValidationError(
                    f"Nursing count after foster-in ({nursing_after}) exceeds max {MAX_NURSING_COUNT}"
                )

    # 정합성: 포유 두수를 줄이는 이벤트(폐사·양자전출)는 현재 포유 두수 초과 불가.
    # (초과 시 포유두수가 음수 → 이유두수 공식이 깨져 두수 꼬임. C3: FOSTER_OUT도 가드)
    if req.event_type in ("DEATH", "FOSTER_OUT"):
        foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
        nursing = farrowing.born_alive + foster_in - foster_out - deaths
        if req.piglet_count > nursing:
            label = "Piglet deaths" if req.event_type == "DEATH" else "Foster-out count"
            raise ValidationError(
                f"{label} ({req.piglet_count}) exceed current nursing count "
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
        age_days=(req.event_date - farrowing.farrowing_date).days,  # P0-BE-5: 자돈 일령 자동계산
        reason=req.reason,
        target_sow_id=req.target_sow_id,
        target_farrowing_id=req.target_farrowing_id,
        notes=req.notes,
        created_by=user_id,
    )
    db.add(event)
    await db.flush()

    # P0-BE-3: 양자 거울 레코드 자동생성 — FOSTER_IN/OUT 반대편(target_sow)에 대칭 이벤트 생성.
    # 없으면 nursing_head 집계가 한쪽만 반영됨. 출처: MdYangjaWrMapper.xml L383~398
    if req.event_type in ("FOSTER_IN", "FOSTER_OUT") and req.target_sow_id:
        mirror_type = "FOSTER_IN" if req.event_type == "FOSTER_OUT" else "FOSTER_OUT"
        target_farrowing = await db.scalar(
            select(Farrowing)
            .where(Farrowing.sow_id == req.target_sow_id, Farrowing.deleted_at.is_(None))
            .order_by(Farrowing.farrowing_date.desc())
            .limit(1)
        )
        if target_farrowing:
            db.add(PigletEvent(
                farm_id=farm_id,
                farrowing_id=target_farrowing.id,
                sow_id=req.target_sow_id,
                event_date=req.event_date,
                event_type=mirror_type,
                piglet_count=req.piglet_count,
                age_days=(req.event_date - target_farrowing.farrowing_date).days,
                target_sow_id=sow.id,
                target_farrowing_id=farrowing.id,
                notes=f"auto-mirror:{event.id}",
                created_by=user_id,
            ))

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
        # 명명 예외(PeriodLockedError, HTTP 423)로 일관 — raw HTTPException/죽은 409 제거.
        raise PeriodLockedError(
            f"Period {d.year}-{d.month:02d} is locked; unlock it before editing."
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
    # 견고화: 수정도 생성(record_mating)과 동일 제약 재검증
    if "boar_id" in data and m.boar_id:
        boar = await db.scalar(select(Boar).where(Boar.id == m.boar_id, Boar.farm_id == farm_id))
        if not boar:
            raise NotFoundError(f"Boar {m.boar_id} not found in farm")
        if boar.status != "ACTIVE":
            raise ValidationError(f"Boar {boar.ear_tag} is '{boar.status}' and cannot be used for mating")
    if "mating_date" in data and data["mating_date"]:
        dup = await db.scalar(select(Mating).where(
            Mating.sow_id == m.sow_id, Mating.mating_date == m.mating_date,
            Mating.deleted_at.is_(None), Mating.id != m.id))
        if dup:
            raise ConflictError("A mating is already recorded for this sow on this date")
    # audit new_value는 JSONB — date 객체 직렬화 불가. mode="json"으로 ISO 문자열화(날짜수정 500 근인).
    await _audit(db, user_id, farm_id, "UPDATE", "matings", m.id, body.model_dump(mode="json", exclude_unset=True))
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
    # 견고화: 같은 사이클에 다른 교배(재교배)가 남아있으면 임신 유지 — 마지막 교배 삭제 때만 OPEN/FAILED 롤백.
    # ⚠️ 방금 삭제한 m을 명시적으로 제외(Mating.id != m.id) — deleted_at flush 타이밍에 의존하지 않게.
    remaining_matings = 0
    if m.breeding_cycle_id:
        remaining_matings = await db.scalar(select(func.count()).select_from(Mating).where(
            Mating.breeding_cycle_id == m.breeding_cycle_id,
            Mating.id != m.id,
            Mating.deleted_at.is_(None))) or 0
    if remaining_matings > 0:
        # 재교배 잔존 → 모돈 PREGNANT 유지, 사이클 MATED 유지, 교배횟수만 재계산
        if m.breeding_cycle_id:
            cycle = await db.get(BreedingCycle, m.breeding_cycle_id)
            if cycle:
                cycle.mating_count = int(remaining_matings)
    else:
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
    # P0-BE-13: 수정 시에도 출생체중 포함 재검증
    validate_farrowing(total_born=f.total_born, born_alive=f.born_alive,
                       stillborn=f.stillborn, mummified=f.mummified,
                       avg_birth_weight_kg=f.avg_birth_weight_kg)
    # 수정 시 날짜순서(INV4) 재검증 — 분만일을 교배 前으로 못 옮김(QA ws_update 발견: 등록은 검증, 수정은 누락).
    if "farrowing_date" in data and f.mating_id:
        _m = await db.get(Mating, f.mating_id)
        validate_farrowing_after_mating(farrowing_date=f.farrowing_date,
                                        mating_date=_m.mating_date if _m else None)
        # 수정 시에도 임신기간 범위(record_farrowing과 동일) 재검증 — 순서만으론 166일 같은
        # 비현실 임신기간이 통과해 KPI·코호트 오염(QA H1: 등록은 검증, 수정은 누락).
        if _m:
            _gest = (f.farrowing_date - _m.mating_date).days
            if not (GESTATION_MIN_DAYS <= _gest <= GESTATION_MAX_DAYS):
                raise ValidationError(
                    f"Gestation period {_gest} days is outside {GESTATION_MIN_DAYS}~{GESTATION_MAX_DAYS} range"
                )
    # 견고화: 실산 축소가 기존 이유두수 합/양자 정합성을 깨면 차단(두수 꼬임 방지)
    if "born_alive" in data:
        fi, fo, deaths = await _calc_piglet_adjustments(db, f.id)
        effective = max(0, f.born_alive + fi - fo - deaths)
        weaned_sum = await db.scalar(select(func.coalesce(func.sum(Weaning.weaned_count), 0)).where(
            Weaning.farrowing_id == f.id, Weaning.deleted_at.is_(None))) or 0
        if int(weaned_sum) > effective:
            raise ValidationError(
                f"born_alive too low: already weaned {int(weaned_sum)} exceeds effective litter {effective}"
            )
        f.nursing_head = f.born_alive  # 포유개시두수 동기화
    # audit new_value는 JSONB — date 객체 직렬화 불가. mode="json"으로 ISO 문자열화(날짜수정 500 근인).
    await _audit(db, user_id, farm_id, "UPDATE", "farrowings", f.id, body.model_dump(mode="json", exclude_unset=True))
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
    # V7 정합성: 수정 시에도 이유두수 재검증(유효 복당두수·상한 초과 차단)
    if w.weaned_count > MAX_WEANED_COUNT:
        raise ValidationError(f"weaned_count exceeds maximum {MAX_WEANED_COUNT}")
    # 수정 시에도 이유체중 유효범위(record_weaning과 동일) 재검증(QA H3: 등록은 검증, 수정은 누락).
    if w.avg_weaning_weight_kg is not None and not (2.0 <= w.avg_weaning_weight_kg <= 12.0):
        raise ValidationError(
            f"Average weaning weight {w.avg_weaning_weight_kg}kg is outside the valid range (2~12kg)"
        )
    if w.farrowing_id:
        farrowing = await db.get(Farrowing, w.farrowing_id)
        # 수정 시 날짜순서(INV4) 재검증 — 이유일을 분만 前으로 못 옮김(QA ws_update 발견).
        if "weaning_date" in data and farrowing:
            validate_weaning_after_farrowing(weaning_date=w.weaning_date,
                                             farrowing_date=farrowing.farrowing_date)
        if farrowing:
            # 수정 시에도 포유기간 범위·국가 컴플라이언스 재검증 + 파생 일령 재계산(QA H2:
            # 등록은 검증, 수정은 누락 → 포유 61일·법정 미달 이유가 통과하던 것 차단).
            _nursing = (w.weaning_date - farrowing.farrowing_date).days
            if not (NURSING_MIN_DAYS <= _nursing <= NURSING_MAX_DAYS):
                raise ValidationError(
                    f"Nursing period {_nursing} days is outside {NURSING_MIN_DAYS}~{NURSING_MAX_DAYS} range"
                )
            await _check_wean_compliance(db, farm_id, _nursing)
            w.weaning_age_days = _nursing
            foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
            effective = max(0, farrowing.born_alive + foster_in - foster_out - deaths)
            # 견고화: 부분이유 형제 합계까지 고려(이 이유 + 다른 이유들 ≤ 유효복당)
            others = await db.scalar(select(func.coalesce(func.sum(Weaning.weaned_count), 0)).where(
                Weaning.farrowing_id == farrowing.id, Weaning.deleted_at.is_(None),
                Weaning.id != w.id)) or 0
            if int(others) + w.weaned_count > effective:
                raise ValidationError(
                    f"total weaned ({int(others) + w.weaned_count}) > effective litter ({effective})"
                )
    # audit new_value는 JSONB — date 객체 직렬화 불가. mode="json"으로 ISO 문자열화(날짜수정 500 근인).
    await _audit(db, user_id, farm_id, "UPDATE", "weanings", w.id, body.model_dump(mode="json", exclude_unset=True))
    await db.commit(); await db.refresh(w)
    return w


async def delete_weaning(db, farm_id, user_id, weaning_id) -> None:
    w = await db.scalar(select(Weaning).where(
        Weaning.id == weaning_id, Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None)))
    if not w:
        raise NotFoundError(f"Weaning {weaning_id} not found")
    await _ensure_period_unlocked(db, farm_id, w.weaning_date)
    w.deleted_at = datetime.now(UTC)
    # BUG-3: 이유 시 자동생성된 자돈그룹(WG-...)도 soft-delete(유령 재고 방지). create와 동일 code.
    wg_code = f"WG-{w.weaning_date:%y%m%d}-{str(w.id)[:8]}"
    wg = await db.scalar(select(PigletGroup).where(
        PigletGroup.farm_id == farm_id, PigletGroup.group_code == wg_code,
        PigletGroup.deleted_at.is_(None)))
    if wg:
        wg.deleted_at = datetime.now(UTC)
    sow = await _get_active_sow(db, farm_id, w.sow_id)
    sow.status = rollback_status_on_delete("weaning")
    if w.breeding_cycle_id:
        cycle = await db.get(BreedingCycle, w.breeding_cycle_id)
        if cycle:
            cycle.cycle_status = "FARROWED"
            cycle.ended_at = None
    await _audit(db, user_id, farm_id, "DELETE", "weanings", w.id, {"id": str(w.id)})
    await db.commit()
