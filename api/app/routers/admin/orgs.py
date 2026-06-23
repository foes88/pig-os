"""운영자 어드민 — 조직 트리 (업체→총판→대리점→농장) 드릴다운.

SUPER_ADMIN 전용. 전사 조직 목록 + 조직별 농장 카운트. 프론트가 parent_org_id로 트리 구성.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import NotFoundError
from app.db.models.platform import Farm, Organization, User

router = APIRouter(
    prefix="/admin",
    tags=["Admin · Orgs"],
    dependencies=[Depends(require_super_admin)],
)


class AdminOrgRow(BaseModel):
    id: str
    name: str
    org_type: str
    org_level: int
    parent_org_id: str | None
    country: str
    farm_count: int
    user_count: int


class AdminOrgFarm(BaseModel):
    id: str
    name: str
    farm_code: str
    country: str
    active: bool


@router.get("/orgs", response_model=list[AdminOrgRow])
async def list_orgs(db: DbDep, _admin: SuperAdmin) -> list[AdminOrgRow]:
    """전사 조직 목록(트리 구성용). parent_org_id로 프론트에서 업체→총판→대리점 계층화."""
    orgs = (await db.execute(select(Organization))).scalars().all()

    farm_counts: dict[UUID, int] = {}
    for oid, cnt in (
        await db.execute(
            select(Farm.org_id, func.count()).where(Farm.active.is_(True)).group_by(Farm.org_id)
        )
    ).all():
        farm_counts[oid] = cnt

    user_counts: dict[UUID, int] = {}
    for oid, cnt in (
        await db.execute(select(User.org_id, func.count()).group_by(User.org_id))
    ).all():
        if oid is not None:
            user_counts[oid] = cnt

    rows = [
        AdminOrgRow(
            id=str(o.id), name=o.name, org_type=o.org_type, org_level=o.org_level,
            parent_org_id=str(o.parent_org_id) if o.parent_org_id else None,
            country=o.country, farm_count=farm_counts.get(o.id, 0), user_count=user_counts.get(o.id, 0),
        )
        for o in orgs
    ]
    rows.sort(key=lambda r: (r.org_level, r.name))
    return rows


@router.get("/orgs/{org_id}/farms", response_model=list[AdminOrgFarm])
async def list_org_farms(org_id: UUID, db: DbDep, _admin: SuperAdmin) -> list[AdminOrgFarm]:
    """해당 조직에 직접 속한 농장 목록(드릴다운 말단)."""
    org = await db.get(Organization, org_id)
    if not org:
        raise NotFoundError("Org not found")
    farms = (
        await db.execute(select(Farm).where(Farm.org_id == org_id).order_by(Farm.name))
    ).scalars().all()
    return [
        AdminOrgFarm(id=str(f.id), name=f.name, farm_code=f.farm_code, country=f.country, active=f.active)
        for f in farms
    ]
