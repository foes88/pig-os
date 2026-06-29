"""
비육돈 그룹 관리 — 입식/출하/목록
그룹 단위 관리 (개별 개체 추적 없음, FCR은 Phase 1.5)
"""
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.ops import FinisherGroup
from app.schemas.finisher import (
    FinisherGroupCreate,
    FinisherGroupResponse,
    FinisherGroupShip,
    FinisherGroupUpdate,
)
from app.validators.finisher import (
    validate_finisher_entry,
    validate_finisher_event_count,
    validate_finisher_exit_weight,
    validate_finisher_not_shipped,
)

router = APIRouter(prefix="/farms/{farm_id}/finishers", tags=["Finishers"])

_MANAGE_ROLES = ("FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")  # 파괴적 작업 한정 (Section D)

_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")  # 일상입력 WORKER+ (VIEWER/VET 차단)


@router.get("", response_model=list[FinisherGroupResponse])
async def list_finisher_groups(
    farm: FarmDep,
    db: DbDep,
    active_only: bool = Query(False, description="True = 출하 전 그룹만"),
    limit: int = Query(50, ge=1, le=200),
):
    q = select(FinisherGroup).where(
        FinisherGroup.farm_id == farm.id,
        FinisherGroup.deleted_at.is_(None),
    )
    if active_only:
        q = q.where(FinisherGroup.end_date.is_(None))
    q = q.order_by(FinisherGroup.start_date.desc()).limit(limit)
    rows = await db.scalars(q)
    return [FinisherGroupResponse.model_validate(r) for r in rows]


@router.post("", response_model=FinisherGroupResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def create_finisher_group(
    body: FinisherGroupCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """비육돈 그룹 입식 등록"""
    # P0-BE-12: 입식 두수·체중 검증
    validate_finisher_entry(
        entry_count=body.head_count_in,
        avg_entry_weight_kg=body.avg_entry_weight_kg,
    )
    existing = await db.scalar(
        select(FinisherGroup).where(
            FinisherGroup.farm_id == farm.id,
            FinisherGroup.group_code == body.group_code,
            FinisherGroup.deleted_at.is_(None),
        )
    )
    if existing:
        raise ConflictError(f"Group code '{body.group_code}' already exists")

    group = FinisherGroup(
        farm_id=farm.id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return FinisherGroupResponse.model_validate(group)


@router.post("/{group_id}/ship", response_model=FinisherGroupResponse,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def ship_finisher_group(
    group_id: UUID,
    body: FinisherGroupShip,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """출하 처리 — 그룹 종료"""
    group = await db.scalar(
        select(FinisherGroup).where(
            FinisherGroup.id == group_id,
            FinisherGroup.farm_id == farm.id,
            FinisherGroup.deleted_at.is_(None),
        )
    )
    if not group:
        raise NotFoundError(f"Finisher group {group_id} not found")
    if group.end_date is not None:
        raise ConflictError("Group already shipped")

    # H1: 출하일은 입식일 이후여야 함(음수 사육일수 → 음수 ADG/일수로 KPI 오염 방지).
    if group.start_date is not None and body.end_date < group.start_date:
        raise ValidationError(
            f"end_date ({body.end_date}) cannot be before start_date ({group.start_date})"
        )

    # P0-BE-12: 출하 두수 ≤ 잔여(입식) 두수, 출하체중 범위·입식체중 초과 검증
    validate_finisher_not_shipped(shipped_at=group.end_date)
    validate_finisher_event_count(
        action_count=body.head_count_out,
        remaining_head=group.head_count_in or 0,
        label="Shipped head count",
    )
    if body.avg_exit_weight_kg:
        validate_finisher_exit_weight(
            avg_exit_weight_kg=body.avg_exit_weight_kg,
            avg_entry_weight_kg=group.avg_entry_weight_kg,
        )

    group.end_date = body.end_date
    group.head_count_out = body.head_count_out
    group.avg_exit_weight_kg = body.avg_exit_weight_kg
    if body.notes:
        group.notes = body.notes
    await db.commit()
    await db.refresh(group)
    return FinisherGroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=204,
               dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def delete_finisher_group(group_id: UUID, farm: FarmDep, db: DbDep):
    group = await db.scalar(
        select(FinisherGroup).where(
            FinisherGroup.id == group_id,
            FinisherGroup.farm_id == farm.id,
            FinisherGroup.deleted_at.is_(None),
        )
    )
    if not group:
        raise NotFoundError(f"Finisher group {group_id} not found")
    group.deleted_at = datetime.now(UTC)
    await db.commit()


@router.patch("/{group_id}", response_model=FinisherGroupResponse,
              dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def update_finisher_group(group_id: UUID, body: FinisherGroupUpdate, farm: FarmDep, db: DbDep):
    group = await db.scalar(
        select(FinisherGroup).where(
            FinisherGroup.id == group_id,
            FinisherGroup.farm_id == farm.id,
            FinisherGroup.deleted_at.is_(None),
        )
    )
    if not group:
        raise NotFoundError(f"Finisher group {group_id} not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(group, k, v)
    # H5: 수정 후 정합성 — 입식두수 < 출하두수(이미 출하됨)면 음수 폐사율 발생 → 차단.
    if group.head_count_out is not None and group.head_count_in is not None \
            and group.head_count_in < group.head_count_out:
        raise ValidationError(
            f"head_count_in ({group.head_count_in}) cannot be lower than "
            f"shipped head_count_out ({group.head_count_out})"
        )
    if group.end_date is not None and group.start_date is not None and group.end_date < group.start_date:
        raise ValidationError("end_date cannot be before start_date")
    await db.commit()
    await db.refresh(group)
    return FinisherGroupResponse.model_validate(group)
