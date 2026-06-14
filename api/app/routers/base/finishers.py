"""
비육돈 그룹 관리 — 입식/출하/목록
그룹 단위 관리 (개별 개체 추적 없음, FCR은 Phase 1.5)
"""
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.ops import FinisherGroup
from app.schemas.finisher import (
    FinisherGroupCreate,
    FinisherGroupResponse,
    FinisherGroupShip,
    FinisherGroupUpdate,
)

router = APIRouter(prefix="/farms/{farm_id}/finishers", tags=["Finishers"])


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


@router.post("", response_model=FinisherGroupResponse, status_code=201)
async def create_finisher_group(
    body: FinisherGroupCreate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """비육돈 그룹 입식 등록"""
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


@router.post("/{group_id}/ship", response_model=FinisherGroupResponse)
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

    group.end_date = body.end_date
    group.head_count_out = body.head_count_out
    group.avg_exit_weight_kg = body.avg_exit_weight_kg
    if body.notes:
        group.notes = body.notes
    await db.commit()
    await db.refresh(group)
    return FinisherGroupResponse.model_validate(group)


@router.delete("/{group_id}", status_code=204)
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


@router.patch("/{group_id}", response_model=FinisherGroupResponse)
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
    await db.commit()
    await db.refresh(group)
    return FinisherGroupResponse.model_validate(group)
