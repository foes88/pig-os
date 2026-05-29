from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.core.exceptions import NotFoundError
from app.db.models.sow import Sow
from app.schemas.common import PageMeta, PagedResponse
from app.schemas.sow import SowCreate, SowResponse, SowUpdate

router = APIRouter(prefix="/farms/{farm_id}/sows", tags=["Sows"])


@router.get("", response_model=PagedResponse[SowResponse])
async def list_sows(
    farm: FarmDep,
    db: DbDep,
    status: str | None = Query(None, description="ACTIVE|GESTATING|LACTATING|WEANED|DRY"),
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

    total_q = q.with_only_columns(select(Sow.id).where(Sow.farm_id == farm.id, Sow.deleted_at.is_(None)).subquery().c.id)
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
async def create_sow(body: SowCreate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    from datetime import datetime, UTC
    sow = Sow(
        farm_id=farm.id,
        ear_tag=body.ear_tag,
        rfid_tag=body.rfid_tag,
        entry_date=datetime.combine(body.entry_date, datetime.min.time()).replace(tzinfo=UTC),
        entry_type=body.entry_type,
        breed=body.breed,
        breed_company=body.breed_company,
        building_id=body.building_id,
        parity=body.parity,
        source_farm_id=body.source_farm_id,
    )
    db.add(sow)
    await db.commit()
    await db.refresh(sow)
    return SowResponse.model_validate(sow)


@router.get("/{sow_id}", response_model=SowResponse)
async def get_sow(sow_id: UUID, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    return SowResponse.model_validate(sow)


@router.patch("/{sow_id}", response_model=SowResponse)
async def update_sow(sow_id: UUID, body: SowUpdate, farm: FarmDep, db: DbDep):
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(sow, k, v)
    await db.commit()
    await db.refresh(sow)
    return SowResponse.model_validate(sow)


@router.delete("/{sow_id}", status_code=204)
async def delete_sow(sow_id: UUID, farm: FarmDep, db: DbDep):
    from datetime import datetime, UTC
    sow = await db.scalar(
        select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id, Sow.deleted_at.is_(None))
    )
    if not sow:
        raise NotFoundError(f"Sow {sow_id} not found")
    sow.deleted_at = datetime.now(UTC)
    await db.commit()
