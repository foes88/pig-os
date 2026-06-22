"""운영자 어드민 콘솔 — Phase 0 (기반) + Phase 1 (회원 운영) 진입점.

SUPER_ADMIN 전용. 전사(cross-tenant) 조회/운영. 모든 라우트는 require_super_admin 가드.
프리픽스: /api/v1/admin
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.db.models.platform import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin Console"],
    # 라우터 전체를 SUPER_ADMIN 으로 보호 (경로별 누락 방지)
    dependencies=[Depends(require_super_admin)],
)


class AdminOverview(BaseModel):
    organizations: int
    farms: int
    users: int
    sows: int


@router.get("/overview", response_model=AdminOverview)
async def get_overview(db: DbDep, _admin: SuperAdmin) -> AdminOverview:
    """플랫폼 전사 개요 카운트 — 어드민 대시보드 상단 카드."""
    orgs = await db.scalar(text("SELECT count(*) FROM organizations"))
    farms = await db.scalar(text("SELECT count(*) FROM farms WHERE active = true"))
    users = await db.scalar(text("SELECT count(*) FROM users"))
    sows = await db.scalar(text("SELECT count(*) FROM sows WHERE deleted_at IS NULL"))
    return AdminOverview(
        organizations=orgs or 0,
        farms=farms or 0,
        users=users or 0,
        sows=sows or 0,
    )


class AdminWhoAmI(BaseModel):
    id: str
    email: str
    name: str
    role: str


@router.get("/me", response_model=AdminWhoAmI)
async def admin_me(admin: Annotated[User, Depends(require_super_admin)]) -> AdminWhoAmI:
    """현재 운영자 정보 — 어드민 셸 헤더용 + 게이트 동작 확인."""
    return AdminWhoAmI(id=str(admin.id), email=admin.email, name=admin.name, role=admin.role)
