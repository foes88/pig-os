"""Organization management API."""
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, DbDep
from app.core.permissions import (
    MAX_ORG_TREE_DEPTH,
    ORG_LEVEL_ROLES,
    ORG_TREE_CTE,
    effective_system_role,
    get_accessible_org_ids as permission_accessible_org_ids,
)
from app.db.models.platform import Organization

router = APIRouter(prefix="/orgs", tags=["Organizations"])

ORG_TYPES = {"VENDOR", "DISTRIBUTOR", "DEALER", "INDEPENDENT"}
ORG_TYPE_LEVEL = {
    "VENDOR": 0,
    "DISTRIBUTOR": 1,
    "DEALER": 2,
    "INDEPENDENT": 3,
}


class OrgResponse(BaseModel):
    id: UUID
    name: str
    org_type: str
    org_level: int
    parent_org_id: UUID | None
    country: str
    timezone: str

    model_config = {"from_attributes": True}


class OrgCreateRequest(BaseModel):
    name: str
    org_type: str = "DEALER"
    country: str
    timezone: str = "UTC"
    parent_org_id: UUID | None = None


class OrgUpdateRequest(BaseModel):
    name: str | None = None
    country: str | None = None
    timezone: str | None = None


class OrgFarmResponse(BaseModel):
    id: UUID
    name: str
    farm_code: str
    country: str
    org_id: UUID
    active: bool


def _require_org_admin(user) -> None:
    if effective_system_role(user) not in ORG_LEVEL_ROLES:
        raise HTTPException(status_code=403, detail="org_admin_required")


async def _get_org_or_404(org_id: UUID, db: AsyncSession) -> Organization:
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="org_not_found")
    return org


async def _get_accessible_org_ids(user, db: AsyncSession) -> set[UUID]:
    return await permission_accessible_org_ids(user, db)


def _validate_child_org(role: str, parent: Organization, child_type: str) -> None:
    if role == "DEALER_ADMIN":
        raise HTTPException(status_code=403, detail="dealer_admin_cannot_create_org")

    allowed_by_parent = {
        "VENDOR": {"DISTRIBUTOR", "DEALER"},
        "DISTRIBUTOR": {"DEALER"},
    }.get(parent.org_type, set())
    if child_type not in allowed_by_parent:
        raise HTTPException(status_code=400, detail="invalid_child_org_type")

    if role == "DISTRIBUTOR_ADMIN" and child_type != "DEALER":
        raise HTTPException(status_code=403, detail="distributor_admin_can_create_dealer_only")


@router.get("", response_model=list[OrgResponse])
async def list_orgs(current_user: CurrentUser, db: DbDep):
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if not ids:
        return []
    result = await db.execute(select(Organization).where(Organization.id.in_(ids)))
    return result.scalars().all()


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: Annotated[UUID, Path()],
    current_user: CurrentUser,
    db: DbDep,
):
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if org_id not in ids:
        raise HTTPException(status_code=403, detail="forbidden")
    return await _get_org_or_404(org_id, db)


@router.post("", response_model=OrgResponse, status_code=201)
async def create_org(body: OrgCreateRequest, current_user: CurrentUser, db: DbDep):
    _require_org_admin(current_user)
    if body.org_type not in ORG_TYPES:
        raise HTTPException(status_code=400, detail="invalid_org_type")

    role = effective_system_role(current_user)
    parent_org_id = body.parent_org_id

    if parent_org_id is None and role != "SUPER_ADMIN":
        parent_org_id = current_user.org_id

    if parent_org_id is None:
        if role != "SUPER_ADMIN":
            raise HTTPException(status_code=400, detail="parent_org_required")
        if body.org_type not in {"VENDOR", "INDEPENDENT"}:
            raise HTTPException(status_code=400, detail="root_org_must_be_vendor_or_independent")
        org = Organization(
            id=uuid4(),
            name=body.name,
            org_type=body.org_type,
            org_level=ORG_TYPE_LEVEL[body.org_type],
            parent_org_id=None,
            country=body.country,
            timezone=body.timezone,
        )
    else:
        accessible_ids = await _get_accessible_org_ids(current_user, db)
        if parent_org_id not in accessible_ids:
            raise HTTPException(status_code=403, detail="forbidden_parent_org")

        parent = await _get_org_or_404(parent_org_id, db)
        _validate_child_org(role, parent, body.org_type)

        org = Organization(
            id=uuid4(),
            name=body.name,
            org_type=body.org_type,
            org_level=ORG_TYPE_LEVEL[body.org_type],
            parent_org_id=parent.id,
            country=body.country,
            timezone=body.timezone,
        )

    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@router.patch("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: Annotated[UUID, Path()],
    body: OrgUpdateRequest,
    current_user: CurrentUser,
    db: DbDep,
):
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if org_id not in ids:
        raise HTTPException(status_code=403, detail="forbidden")

    org = await _get_org_or_404(org_id, db)
    if body.name is not None:
        org.name = body.name
    if body.country is not None:
        org.country = body.country
    if body.timezone is not None:
        org.timezone = body.timezone
    await db.commit()
    await db.refresh(org)
    return org


@router.get("/{org_id}/farms", response_model=list[OrgFarmResponse])
async def get_org_farms(
    org_id: Annotated[UUID, Path()],
    current_user: CurrentUser,
    db: DbDep,
):
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if org_id not in ids:
        raise HTTPException(status_code=403, detail="forbidden")

    result = await db.execute(
        text(f"""
            {ORG_TREE_CTE}
            SELECT f.id, f.name, f.farm_code, f.country, f.org_id, f.active
            FROM farms f
            INNER JOIN org_tree t ON f.org_id = t.id
            WHERE f.active = TRUE
            ORDER BY f.name
        """),
        {"root_org_id": org_id, "max_depth": MAX_ORG_TREE_DEPTH},
    )
    return [
        OrgFarmResponse(
            id=row[0],
            name=row[1],
            farm_code=row[2],
            country=row[3],
            org_id=row[4],
            active=row[5],
        )
        for row in result.fetchall()
    ]


@router.get("/{org_id}/tree", response_model=list[OrgResponse])
async def get_org_subtree(
    org_id: Annotated[UUID, Path()],
    current_user: CurrentUser,
    db: DbDep,
):
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if org_id not in ids:
        raise HTTPException(status_code=403, detail="forbidden")

    result = await db.execute(
        text(f"""
            {ORG_TREE_CTE}
            SELECT id FROM org_tree
        """),
        {"root_org_id": org_id, "max_depth": MAX_ORG_TREE_DEPTH},
    )
    child_ids = {row[0] for row in result.fetchall()}
    if not child_ids:
        return []

    orgs = await db.execute(select(Organization).where(Organization.id.in_(child_ids)))
    return orgs.scalars().all()
