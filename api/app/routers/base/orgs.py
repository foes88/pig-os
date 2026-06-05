"""
Organization 관리 API

계층: VENDOR → DISTRIBUTOR → DEALER → INDEPENDENT
접근: SUPER_ADMIN = 전체 / VENDOR_ADMIN = 자기 트리 / 나머지 = 자기 org만
"""
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, DbDep
from app.core.permissions import ORG_LEVEL_ROLES, effective_system_role
from app.db.models.platform import Farm, Organization

router = APIRouter(prefix="/orgs", tags=["Organizations"])

# ── Schemas ───────────────────────────────────────────────────────────────────

ORG_TYPES = {"VENDOR", "DISTRIBUTOR", "DEALER", "INDEPENDENT"}


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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_org_admin(user):
    if effective_system_role(user) not in ORG_LEVEL_ROLES:
        raise HTTPException(status_code=403, detail="org_admin_required")


async def _get_org_or_404(org_id: UUID, db: AsyncSession) -> Organization:
    org = await db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="org_not_found")
    return org


async def _get_accessible_org_ids(user, db: AsyncSession) -> set[UUID]:
    """현재 사용자가 볼 수 있는 조직 ID 집합."""
    role = effective_system_role(user)
    if role == "SUPER_ADMIN":
        result = await db.execute(select(Organization.id))
        return {row[0] for row in result.fetchall()}
    # 자기 org 트리만
    result = await db.execute(
        text("""
            WITH RECURSIVE tree AS (
                SELECT id FROM organizations WHERE id = :root
                UNION ALL
                SELECT o.id FROM organizations o
                INNER JOIN tree t ON o.parent_org_id = t.id
            )
            SELECT id FROM tree
        """),
        {"root": user.org_id},
    )
    return {row[0] for row in result.fetchall()}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[OrgResponse])
async def list_orgs(current_user: CurrentUser, db: DbDep):
    """접근 가능한 조직 목록."""
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
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
    """하위 조직 생성. VENDOR_ADMIN은 DISTRIBUTOR/DEALER, DISTRIBUTOR_ADMIN은 DEALER만."""
    _require_org_admin(current_user)
    if body.org_type not in ORG_TYPES:
        raise HTTPException(status_code=400, detail="invalid_org_type")

    parent_org_id = body.parent_org_id or current_user.org_id
    parent = await _get_org_or_404(parent_org_id, db)

    org = Organization(
        id=uuid4(),
        name=body.name,
        org_type=body.org_type,
        org_level=parent.org_level + 1,
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


@router.get("/{org_id}/farms", response_model=list[dict])
async def get_org_farms(
    org_id: Annotated[UUID, Path()],
    current_user: CurrentUser,
    db: DbDep,
):
    """org 하위 모든 농장 목록 (recursive)."""
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if org_id not in ids:
        raise HTTPException(status_code=403, detail="forbidden")

    result = await db.execute(
        text("""
            WITH RECURSIVE tree AS (
                SELECT id FROM organizations WHERE id = :root
                UNION ALL
                SELECT o.id FROM organizations o
                INNER JOIN tree t ON o.parent_org_id = t.id
            )
            SELECT f.id, f.name, f.farm_code, f.country, f.org_id, f.active
            FROM farms f
            INNER JOIN tree t ON f.org_id = t.id
            WHERE f.active = TRUE
            ORDER BY f.name
        """),
        {"root": org_id},
    )
    rows = result.fetchall()
    return [
        {"id": str(r[0]), "name": r[1], "farm_code": r[2], "country": r[3],
         "org_id": str(r[4]), "active": r[5]}
        for r in rows
    ]


@router.get("/{org_id}/tree", response_model=list[OrgResponse])
async def get_org_subtree(
    org_id: Annotated[UUID, Path()],
    current_user: CurrentUser,
    db: DbDep,
):
    """org 하위 조직 트리 전체."""
    _require_org_admin(current_user)
    ids = await _get_accessible_org_ids(current_user, db)
    if org_id not in ids:
        raise HTTPException(status_code=403, detail="forbidden")

    result = await db.execute(
        text("""
            WITH RECURSIVE tree AS (
                SELECT id FROM organizations WHERE id = :root
                UNION ALL
                SELECT o.id FROM organizations o
                INNER JOIN tree t ON o.parent_org_id = t.id
            )
            SELECT id FROM tree
        """),
        {"root": org_id},
    )
    child_ids = {row[0] for row in result.fetchall()}
    orgs = await db.execute(select(Organization).where(Organization.id.in_(child_ids)))
    return orgs.scalars().all()
