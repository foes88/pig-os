"""운영자 어드민 — 조직 트리 (업체→총판→대리점→농장) 드릴다운.

SUPER_ADMIN 전용. 전사 조직 목록 + 조직별 농장 카운트. 프론트가 parent_org_id로 트리 구성.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import MAX_ORG_TREE_DEPTH, ORG_TREE_CTE
from app.db.models.platform import AuditLog, Farm, Organization, User

router = APIRouter(
    prefix="/admin",
    tags=["Admin · Orgs"],
    dependencies=[Depends(require_super_admin)],
)

_ORG_TYPES = {"VENDOR", "DISTRIBUTOR", "DEALER", "INDEPENDENT"}
_ORG_LEVEL = {"VENDOR": 0, "DISTRIBUTOR": 1, "DEALER": 2, "INDEPENDENT": 3}


class AdminOrgRow(BaseModel):
    id: str
    name: str
    org_type: str
    org_level: int
    parent_org_id: str | None
    country: str
    farm_count: int
    user_count: int


class AdminOrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    org_type: str = Field(..., description="VENDOR|DISTRIBUTOR|DEALER|INDEPENDENT")
    parent_org_id: str | None = None
    country: str = Field(..., min_length=2, max_length=2)
    timezone: str = Field(default="UTC")


class AdminOrgUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    org_type: str | None = None
    parent_org_id: str | None = None  # exclude_unset로 '미변경' 구분(없으면 변경 안 함)


class FarmReassign(BaseModel):
    org_id: str  # 농장을 옮길 대상 조직


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


# ─── 계층 관리 (생성·수정·농장 재배정) ────────────────────────────────────────────
async def _descendant_ids(db, org_id: UUID) -> set[UUID]:
    """org_id 자신 + 모든 하위 조직 id (사이클 가드용)."""
    rows = await db.execute(
        text(f"{ORG_TREE_CTE} SELECT id FROM org_tree"),
        {"root_org_id": org_id, "max_depth": MAX_ORG_TREE_DEPTH},
    )
    return {r[0] for r in rows.fetchall()}


def _row(o: Organization, fc: int = 0, uc: int = 0) -> AdminOrgRow:
    return AdminOrgRow(
        id=str(o.id), name=o.name, org_type=o.org_type, org_level=o.org_level,
        parent_org_id=str(o.parent_org_id) if o.parent_org_id else None,
        country=o.country, farm_count=fc, user_count=uc,
    )


@router.post("/orgs", response_model=AdminOrgRow, status_code=201)
async def create_org(body: AdminOrgCreate, db: DbDep, admin: SuperAdmin) -> AdminOrgRow:
    """조직 생성 (업체→총판→대리점 계층 구성)."""
    if body.org_type not in _ORG_TYPES:
        raise ValidationError(f"Invalid org_type. Allowed: {', '.join(sorted(_ORG_TYPES))}")
    parent_id: UUID | None = None
    if body.parent_org_id:
        parent_id = UUID(body.parent_org_id)
        if not await db.get(Organization, parent_id):
            raise NotFoundError("Parent org not found")
    org = Organization(
        name=body.name, org_type=body.org_type, org_level=_ORG_LEVEL.get(body.org_type, 0),
        parent_org_id=parent_id, country=body.country.upper(), timezone=body.timezone,
    )
    db.add(org)
    await db.flush()
    db.add(AuditLog(user_id=admin.id, farm_id=None, action="CREATE", entity_type="organization",
                    entity_id=org.id, new_value=body.model_dump(mode="json")))
    await db.commit()
    await db.refresh(org)
    return _row(org)


@router.patch("/orgs/{org_id}", response_model=AdminOrgRow)
async def update_org(org_id: UUID, body: AdminOrgUpdate, db: DbDep, admin: SuperAdmin) -> AdminOrgRow:
    """조직 수정 — 이름/유형/상위조직(계층 이동). 사이클(자기 자신·하위로 이동) 차단."""
    org = await db.get(Organization, org_id)
    if not org:
        raise NotFoundError("Org not found")
    data = body.model_dump(exclude_unset=True)
    before = {"name": org.name, "org_type": org.org_type,
              "parent_org_id": str(org.parent_org_id) if org.parent_org_id else None}

    if "org_type" in data:
        if data["org_type"] not in _ORG_TYPES:
            raise ValidationError(f"Invalid org_type. Allowed: {', '.join(sorted(_ORG_TYPES))}")
        org.org_type = data["org_type"]
        org.org_level = _ORG_LEVEL.get(data["org_type"], org.org_level)
    if "name" in data:
        org.name = data["name"]
    if "parent_org_id" in data:
        new_parent = data["parent_org_id"]
        if new_parent is None:
            org.parent_org_id = None
        else:
            pid = UUID(new_parent)
            if pid == org_id or pid in await _descendant_ids(db, org_id):
                raise ConflictError("Cannot set parent to self or a descendant (cycle)")
            if not await db.get(Organization, pid):
                raise NotFoundError("Parent org not found")
            org.parent_org_id = pid

    db.add(AuditLog(user_id=admin.id, farm_id=None, action="UPDATE", entity_type="organization",
                    entity_id=org.id, old_value=before, new_value=data))
    await db.commit()
    await db.refresh(org)
    return _row(org)


@router.patch("/farms/{farm_id}/org", response_model=AdminOrgFarm)
async def reassign_farm(farm_id: UUID, body: FarmReassign, db: DbDep, admin: SuperAdmin) -> AdminOrgFarm:
    """농장을 다른 조직으로 재배정 (총판/대리점 산하 이동)."""
    farm = await db.get(Farm, farm_id)
    if not farm:
        raise NotFoundError("Farm not found")
    target = UUID(body.org_id)
    if not await db.get(Organization, target):
        raise NotFoundError("Target org not found")
    before = str(farm.org_id)
    farm.org_id = target
    db.add(AuditLog(user_id=admin.id, farm_id=farm.id, action="UPDATE", entity_type="farm_org",
                    entity_id=farm.id, old_value={"org_id": before}, new_value={"org_id": body.org_id}))
    await db.commit()
    await db.refresh(farm)
    return AdminOrgFarm(id=str(farm.id), name=farm.name, farm_code=farm.farm_code,
                        country=farm.country, active=farm.active)
