"""
자돈 그룹 관리 + 양자/대리모 이벤트
- 자돈그룹: 이유 후 자돈을 그룹 단위로 관리 (피그플랜 P03 자돈관리)
- 양자: 모돈 간 자돈 이동 (분만 기록과 별도 모델 유지 — 데이터 무결성)
"""
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.sow import PigletGroup, PigletTransfer, Sow
from app.schemas.piglet import (
    PigletGroupCreate,
    PigletGroupDeathRecord,
    PigletGroupResponse,
    PigletGroupTransferOut,
    PigletTransferCreate,
    PigletTransferResponse,
)
from app.validators.cross_fostering import (
    validate_cross_foster_distinct,
    validate_cross_fostering,
)

router = APIRouter(prefix="/farms/{farm_id}/piglets", tags=["Piglets"])

_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")  # 일상입력 WORKER+ (VIEWER/VET 차단)


# ── Piglet Groups ─────────────────────────────────────────────────────────────

@router.get("", response_model=list[PigletGroupResponse])
async def list_piglet_groups(
    farm: FarmDep,
    db: DbDep,
    active_only: bool = Query(False, description="True = 전출 전 그룹만"),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(PigletGroup).where(
        PigletGroup.farm_id == farm.id,
        PigletGroup.deleted_at.is_(None),
    )
    if active_only:
        q = q.where(PigletGroup.transfer_date.is_(None))
    q = q.order_by(PigletGroup.weaning_date.desc()).limit(limit)
    rows = await db.scalars(q)
    return [PigletGroupResponse.model_validate(r) for r in rows]


@router.post("", response_model=PigletGroupResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def create_piglet_group(
    body: PigletGroupCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """자돈 그룹 시작 (이유 후 그룹 등록) — 피그플랜 P03010100 자돈그룹시작"""
    existing = await db.scalar(
        select(PigletGroup).where(
            PigletGroup.farm_id == farm.id,
            PigletGroup.group_code == body.group_code,
            PigletGroup.deleted_at.is_(None),
        )
    )
    if existing:
        raise ConflictError(f"Group code '{body.group_code}' already exists")

    group = PigletGroup(
        farm_id=farm.id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return PigletGroupResponse.model_validate(group)


@router.post("/{group_id}/deaths", response_model=PigletGroupResponse,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def record_deaths(
    group_id: UUID,
    body: PigletGroupDeathRecord,
    farm: FarmDep,
    db: DbDep,
):
    """자돈 폐사 누적 기록"""
    group = await db.scalar(
        select(PigletGroup).where(
            PigletGroup.id == group_id,
            PigletGroup.farm_id == farm.id,
            PigletGroup.deleted_at.is_(None),
        )
    )
    if not group:
        raise NotFoundError(f"Piglet group {group_id} not found")

    # H2: 누적 폐사 + 전출이 그룹 보유두수를 넘지 못함(음수 재고 방지).
    new_dead = (group.head_count_dead or 0) + body.head_count_dead
    if new_dead + (group.head_count_out or 0) > group.head_count_in:
        raise ValidationError(
            f"Total deaths ({new_dead}) + transferred ({group.head_count_out or 0}) "
            f"cannot exceed group head count ({group.head_count_in})"
        )
    group.head_count_dead = new_dead
    if body.notes:
        group.notes = body.notes
    await db.commit()
    await db.refresh(group)
    return PigletGroupResponse.model_validate(group)


@router.post("/{group_id}/transfer", response_model=PigletGroupResponse,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def transfer_out_piglet_group(
    group_id: UUID,
    body: PigletGroupTransferOut,
    farm: FarmDep,
    db: DbDep,
):
    """전출/판매 처리 — 피그플랜 P03010400 자돈전출/출하기록"""
    group = await db.scalar(
        select(PigletGroup).where(
            PigletGroup.id == group_id,
            PigletGroup.farm_id == farm.id,
            PigletGroup.deleted_at.is_(None),
        )
    )
    if not group:
        raise NotFoundError(f"Piglet group {group_id} not found")
    if group.transfer_date is not None:
        raise ConflictError("Group already transferred out")

    # H3: 전출 두수가 잔여(보유 - 폐사)를 넘지 못함.
    available = group.head_count_in - (group.head_count_dead or 0)
    if body.head_count_out > available:
        raise ValidationError(
            f"head_count_out ({body.head_count_out}) exceeds remaining ({available} "
            f"= in {group.head_count_in} - dead {group.head_count_dead or 0})"
        )

    group.transfer_date = body.transfer_date
    group.transfer_type = body.transfer_type
    group.head_count_out = body.head_count_out
    group.avg_exit_weight_kg = body.avg_exit_weight_kg
    if body.notes:
        group.notes = body.notes
    await db.commit()
    await db.refresh(group)
    return PigletGroupResponse.model_validate(group)


# ── Piglet Transfers (양자/대리모) ─────────────────────────────────────────────

@router.post("/transfers", response_model=PigletTransferResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def create_piglet_transfer(
    body: PigletTransferCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    양자/대리모 기록.
    분만 기록과 별도 — PSY는 생물학적 산자 기준, 이유두수는 양자 반영 수 기준.
    """
    # B6: 동일 모돈 양자 차단 + 1회 이전 두수 상한(양자 validator). piglet_count≥1은 스키마가 강제.
    # 직접 piglet_events 경로엔 self-check가 있었으나 이 transfers 엔드포인트엔 누락이었음.
    validate_cross_foster_distinct(body.source_sow_id, body.dest_sow_id)
    validate_cross_fostering(transfer_count=body.piglet_count)
    # 데이터 정합성: 출처/대상 모돈이 이 농장 소속인지 검증(외부 UUID가 자기 행에 박히는 것 차단)
    for label, sid in (("source_sow_id", body.source_sow_id), ("dest_sow_id", body.dest_sow_id)):
        ok = await db.scalar(select(Sow.id).where(
            Sow.id == sid, Sow.farm_id == farm.id, Sow.deleted_at.is_(None)))
        if not ok:
            raise NotFoundError(f"{label} not found in this farm")
    # H4: 양자 출처 분만이 지정되면, 실산두수보다 많이 양자 보낼 수 없음(말도 안 되는 입력 차단).
    if body.source_farrowing_id is not None:
        from app.db.models.events import Farrowing
        src = await db.scalar(
            select(Farrowing).where(
                Farrowing.id == body.source_farrowing_id,
                Farrowing.farm_id == farm.id,
                Farrowing.deleted_at.is_(None),
            )
        )
        if not src:
            raise NotFoundError("source_farrowing_id not found in this farm")
        if body.piglet_count > src.born_alive:
            raise ValidationError(
                f"piglet_count ({body.piglet_count}) exceeds source litter born_alive ({src.born_alive})"
            )
    transfer = PigletTransfer(
        farm_id=farm.id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return PigletTransferResponse.model_validate(transfer)


@router.get("/transfers", response_model=list[PigletTransferResponse])
async def list_piglet_transfers(
    farm: FarmDep,
    db: DbDep,
    sow_id: UUID | None = Query(None, description="특정 모돈 필터"),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(PigletTransfer).where(PigletTransfer.farm_id == farm.id)
    if sow_id:
        q = q.where(
            (PigletTransfer.source_sow_id == sow_id) |
            (PigletTransfer.dest_sow_id == sow_id)
        )
    q = q.order_by(PigletTransfer.transfer_date.desc()).limit(limit)
    rows = await db.scalars(q)
    return [PigletTransferResponse.model_validate(r) for r in rows]
