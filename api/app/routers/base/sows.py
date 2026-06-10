from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.core.exceptions import NotFoundError
from app.db.models.health import Removal
from app.db.models.platform import AuditLog
from app.db.models.sow import Sow
from app.schemas.common import PagedResponse, PageMeta
from app.schemas.sow import (
    RemovalResponse,
    SowCreate,
    SowCullRequest,
    SowResponse,
    SowUpdate,
)

router = APIRouter(prefix="/farms/{farm_id}/sows", tags=["Sows"])


@router.get("", response_model=PagedResponse[SowResponse])
async def list_sows(
    farm: FarmDep,
    db: DbDep,
    status: str | None = Query(None, description="GILT|OPEN|PREGNANT|LACTATING|ACCIDENT"),  # noqa: E501
    building_id: UUID | None = Query(None),
    parity_min: int | None = Query(None, ge=0),
    parity_max: int | None = Query(None, le=20),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200, alias="per_page"),
):
    q = select(Sow).where(Sow.farm_id == farm.id, Sow.deleted_at.is_(None))
    if status:
        q = q.where(Sow.status == status)
    if building_id:
        q = q.where(Sow.building_id == building_id)
    if parity_min is not None:
        q = q.where(Sow.parity >= parity_min)
    if parity_max is not None:
        q = q.where(Sow.parity <= parity_max)

    from sqlalchemy import func
    count_row = await db.scalar(select(func.count()).select_from(q.subquery()))
    total = count_row or 0
    pages = max(1, (total + per_page - 1) // per_page)

    q = q.order_by(Sow.ear_tag).offset((page - 1) * per_page).limit(per_page)
    rows = await db.scalars(q)
    sows = list(rows)

    return PagedResponse(
        items=[SowResponse.model_validate(s) for s in sows],
        meta=PageMeta(
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        ),
    )


@router.post("", response_model=SowResponse, status_code=201)
async def create_sow(body: SowCreate, farm: FarmDep, db: DbDep, current_user: CurrentUser):  # noqa: E501
    from datetime import UTC, datetime
    sow = Sow(
        farm_id=farm.id,
        ear_tag=body.ear_tag,
        rfid_tag=body.rfid_tag,
        entry_date=datetime.combine(body.entry_date, datetime.min.time()).replace(tzinfo=UTC),  # noqa: E501
        entry_type=body.entry_type,
        breed=body.breed,
        breed_company=body.breed_company,
        building_id=body.building_id,
        parity=body.parity,
        source_farm_id=body.source_farm_id,
        # 미경산(parity=0) → 후보돈, 경산돈 전입 → 공태로 입식
        status="GILT" if (body.parity or 0) == 0 else "OPEN",
    )
    db.add(sow)
    await db.commit()
    await db.refresh(sow)
    return SowResponse.model_validate(sow)


@router.get("/{sow_id}", response_model=SowResponse)
async def get_sow(sow_id: UUID, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    return SowResponse.model_validate(sow)


@router.patch("/{sow_id}", response_model=SowResponse)
async def update_sow(sow_id: UUID, body: SowUpdate, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(sow, k, v)
    await db.commit()
    await db.refresh(sow)
    return SowResponse.model_validate(sow)


@router.post("/{sow_id}/cull", response_model=RemovalResponse, status_code=201)
async def cull_sow(
    sow_id: UUID,
    body: SowCullRequest,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    """
    ?꾪룓???먮ℓ/?꾩텧 泥섎━.
    - 紐⑤룉 ?곹깭瑜?removal_type?쇰줈 ?꾪솚 + soft-delete
    - removals ?대젰 ?뚯씠釉붿뿉 ?곸꽭 湲곕줉
    - audit_log 湲곕줉
    """
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")

    now = datetime.now(UTC)

    # 紐⑤룉 ?곹깭 + soft-delete
    sow.status = body.removal_type
    sow.exit_date = now
    sow.deleted_at = now

    # removals ?대젰
    removal = Removal(
        farm_id=farm.id,
        sow_id=sow.id,
        removal_date=body.removal_date,
        removal_type=body.removal_type,
        reason_category=body.reason_category,
        reason_detail=body.reason_detail,
        body_weight_kg=body.body_weight_kg,
        sale_price=body.sale_price,
        sale_currency=body.sale_currency,
        created_by=current_user.id,
    )
    db.add(removal)

    # audit log
    db.add(AuditLog(
        user_id=current_user.id,
        farm_id=farm.id,
        action="CULL",
        entity_type="sows",
        entity_id=sow.id,
        new_value=body.model_dump(mode="json"),
    ))

    await db.commit()
    await db.refresh(removal)
    return RemovalResponse.model_validate(removal)


@router.get("/removals", response_model=list[RemovalResponse])
async def list_removals(
    farm: FarmDep,
    db: DbDep,
    removal_type: str | None = Query(None, description="CULLED|DEAD|SOLD|TRANSFER"),
    limit: int = Query(50, ge=1, le=200),
):
    """?꾪룓???먮ℓ ?대젰 紐⑸줉."""
    q = select(Removal).where(Removal.farm_id == farm.id)
    if removal_type:
        q = q.where(Removal.removal_type == removal_type)
    q = q.order_by(Removal.removal_date.desc()).limit(limit)
    rows = await db.scalars(q)
    return [RemovalResponse.model_validate(r) for r in rows]


@router.delete("/{sow_id}", status_code=204)
async def delete_sow(sow_id: UUID, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))  # noqa: E501
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    sow.deleted_at = datetime.now(UTC)
    await db.commit()
