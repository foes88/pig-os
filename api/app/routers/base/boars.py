from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.models.platform import AuditLog
from app.db.models.sow import Boar
from app.schemas.boar import BoarCreate, BoarResponse, BoarUpdate

router = APIRouter(prefix="/farms/{farm_id}/boars", tags=["Boars"])

_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN")  # 일상입력 WORKER+ (VIEWER/VET 차단)


@router.get("", response_model=list[BoarResponse])
async def list_boars(
    farm: FarmDep,
    db: DbDep,
    status: str | None = Query(None, description="ACTIVE|CULLED|DEAD|TRANSFERRED"),
    limit: int = Query(100, ge=1, le=500),
):
    q = select(Boar).where(Boar.farm_id == farm.id)
    if status:
        q = q.where(Boar.status == status)
    rows = await db.scalars(q.order_by(Boar.ear_tag).limit(limit))
    return [BoarResponse.model_validate(r) for r in rows]


@router.post("", response_model=BoarResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def create_boar(body: BoarCreate, farm: FarmDep, db: DbDep, current_user: CurrentUser):
    existing = await db.scalar(
        select(Boar).where(Boar.farm_id == farm.id, Boar.ear_tag == body.ear_tag)
    )
    if existing:
        raise ConflictError(f"Boar with ear_tag '{body.ear_tag}' already exists")
    # 미래 입식일 거부(QA UAT) — 아직 오지 않은 날짜에 웅돈 입식 불가.
    if body.entry_date > date.today():
        raise ValidationError(f"entry_date {body.entry_date} cannot be in the future")

    boar = Boar(
        farm_id=farm.id,
        ear_tag=body.ear_tag,
        breed=body.breed,
        breed_company=body.breed_company,
        entry_date=datetime.combine(body.entry_date, datetime.min.time()).replace(tzinfo=UTC),
        entry_type=body.entry_type,
        semen_quality=body.semen_quality,
    )
    db.add(boar)
    db.add(AuditLog(
        user_id=current_user.id,
        farm_id=farm.id,
        action="CREATE",
        entity_type="boars",
        entity_id=boar.id,
        new_value=body.model_dump(mode="json"),
    ))
    await db.commit()
    await db.refresh(boar)
    return BoarResponse.model_validate(boar)


@router.get("/{boar_id}", response_model=BoarResponse)
async def get_boar(boar_id: UUID, farm: FarmDep, db: DbDep):
    boar = await db.scalar(
        select(Boar).where(Boar.id == boar_id, Boar.farm_id == farm.id)
    )
    if not boar:
        raise NotFoundError(f"Boar {boar_id} not found")
    return BoarResponse.model_validate(boar)


@router.patch("/{boar_id}", response_model=BoarResponse,
              dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def update_boar(
    boar_id: UUID,
    body: BoarUpdate,
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
):
    boar = await db.scalar(
        select(Boar).where(Boar.id == boar_id, Boar.farm_id == farm.id)
    )
    if not boar:
        raise NotFoundError(f"Boar {boar_id} not found")

    updated = body.model_dump(exclude_none=True)
    # ear_tag 변경 시 유니크 재검증(create와 동일) — 미검증 시 UniqueConstraint 위반이 409 아닌 500 누설(QA 웅돈리뷰 High).
    if "ear_tag" in updated and updated["ear_tag"] != boar.ear_tag:
        dup = await db.scalar(select(Boar).where(
            Boar.farm_id == farm.id, Boar.ear_tag == updated["ear_tag"], Boar.id != boar.id))
        if dup:
            raise ConflictError(f"Boar with ear_tag '{updated['ear_tag']}' already exists")
    for k, v in updated.items():
        setattr(boar, k, v)

    db.add(AuditLog(
        user_id=current_user.id,
        farm_id=farm.id,
        action="UPDATE",
        entity_type="boars",
        entity_id=boar.id,
        new_value=updated,
    ))
    await db.commit()
    await db.refresh(boar)
    return BoarResponse.model_validate(boar)
