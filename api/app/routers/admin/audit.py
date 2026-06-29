"""운영자 어드민 — 활동 로그 뷰어 (Phase 4, 읽기 전용).

AuditLog 조회. 운영자 변경(회원상태·공지·문의·규칙 등)을 추적. require_super_admin.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.db.models.platform import AuditLog, User
from app.schemas.common import PagedResponse, PageMeta

router = APIRouter(
    prefix="/admin",
    tags=["Admin · Audit"],
    dependencies=[Depends(require_super_admin)],
)


class AuditRow(BaseModel):
    id: str
    actor_id: str | None
    actor_name: str | None
    action: str
    entity_type: str
    entity_id: str | None
    old_value: dict | None
    new_value: dict | None
    created_at: str | None


@router.get("/audit-log", response_model=PagedResponse[AuditRow])
async def list_audit(
    db: DbDep,
    _admin: SuperAdmin,
    action: Annotated[str | None, Query(description="CREATE/UPDATE/DELETE 등")] = None,
    entity_type: Annotated[str | None, Query(description="admin_user/announcement/rule_config 등")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 30,
) -> PagedResponse[AuditRow]:
    conds = []
    if action:
        conds.append(AuditLog.action == action.upper())
    if entity_type:
        conds.append(AuditLog.entity_type == entity_type)

    total = await db.scalar(select(func.count()).select_from(AuditLog).where(*conds)) or 0
    pages = max(1, (total + per_page - 1) // per_page)
    rows = (
        await db.execute(
            select(AuditLog, User.name)
            .outerjoin(User, User.id == AuditLog.user_id)
            .where(*conds)
            .order_by(AuditLog.created_at.desc())
            .limit(per_page).offset((page - 1) * per_page)
        )
    ).all()
    items = [
        AuditRow(
            id=str(a.id), actor_id=str(a.user_id) if a.user_id else None, actor_name=name,
            action=a.action, entity_type=a.entity_type,
            entity_id=str(a.entity_id) if a.entity_id else None,
            old_value=a.old_value, new_value=a.new_value,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for (a, name) in rows
    ]
    return PagedResponse(items=items, meta=PageMeta(total=total, page=page, per_page=per_page, pages=pages))
