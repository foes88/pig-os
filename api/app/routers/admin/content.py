"""운영자 어드민 — 공지/문의 백오피스 (Phase 2, PigOS 네이티브).

공지 작성/수정/삭제/노출토글 + 문의 접수목록·답변. require_super_admin. 변경은 AuditLog.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import NotFoundError, ValidationError
from app.db.models.content import Announcement, SupportReply, SupportTicket
from app.db.models.platform import AuditLog
from app.schemas.common import PagedResponse, PageMeta
from app.schemas.content import (
    ANNOUNCEMENT_CATEGORIES,
    TICKET_STATUSES,
    AnnouncementCreate,
    AnnouncementOut,
    AnnouncementUpdate,
    SupportReplyCreate,
    SupportReplyOut,
    SupportTicketDetail,
    SupportTicketOut,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin · Content"],
    dependencies=[Depends(require_super_admin)],
)


def _ann_out(a: Announcement) -> AnnouncementOut:
    return AnnouncementOut(
        id=str(a.id), title=a.title, body=a.body, category=a.category, pinned=a.pinned,
        published=a.published, publish_from=a.publish_from, publish_until=a.publish_until,
        lang=a.lang, created_at=a.created_at,
    )


# ─── 공지 ─────────────────────────────────────────────────────────────────────
@router.get("/announcements", response_model=list[AnnouncementOut])
async def admin_list_announcements(db: DbDep, _admin: SuperAdmin) -> list[AnnouncementOut]:
    """전체 공지(게시여부 무관) — 최신·고정 우선."""
    rows = (
        await db.execute(select(Announcement).order_by(Announcement.pinned.desc(), Announcement.created_at.desc()))
    ).scalars().all()
    return [_ann_out(a) for a in rows]


@router.post("/announcements", response_model=AnnouncementOut, status_code=201)
async def admin_create_announcement(body: AnnouncementCreate, db: DbDep, admin: SuperAdmin) -> AnnouncementOut:
    if body.category not in ANNOUNCEMENT_CATEGORIES:
        raise ValidationError(f"Invalid category. Allowed: {', '.join(sorted(ANNOUNCEMENT_CATEGORIES))}")
    a = Announcement(
        title=body.title, body=body.body, category=body.category, pinned=body.pinned,
        published=body.published, publish_from=body.publish_from, publish_until=body.publish_until,
        lang=body.lang, created_by=admin.id,
    )
    db.add(a)
    await db.flush()
    db.add(AuditLog(user_id=admin.id, action="CREATE", entity_type="announcement", entity_id=a.id,
                    new_value={"title": a.title}))
    await db.commit()
    await db.refresh(a)
    return _ann_out(a)


@router.put("/announcements/{ann_id}", response_model=AnnouncementOut)
async def admin_update_announcement(ann_id: UUID, body: AnnouncementUpdate, db: DbDep, admin: SuperAdmin) -> AnnouncementOut:
    a = await db.get(Announcement, ann_id)
    if not a:
        raise NotFoundError("Announcement not found")
    data = body.model_dump(exclude_unset=True)
    if "category" in data and data["category"] not in ANNOUNCEMENT_CATEGORIES:
        raise ValidationError(f"Invalid category. Allowed: {', '.join(sorted(ANNOUNCEMENT_CATEGORIES))}")
    before = {k: getattr(a, k) for k in data}
    for k, v in data.items():
        setattr(a, k, v)
    db.add(AuditLog(user_id=admin.id, action="UPDATE", entity_type="announcement", entity_id=a.id,
                    old_value={k: str(v) for k, v in before.items()},
                    new_value={k: str(v) for k, v in data.items()}))
    await db.commit()
    await db.refresh(a)
    return _ann_out(a)


@router.delete("/announcements/{ann_id}", status_code=204)
async def admin_delete_announcement(ann_id: UUID, db: DbDep, admin: SuperAdmin) -> None:
    a = await db.get(Announcement, ann_id)
    if not a:
        raise NotFoundError("Announcement not found")
    db.add(AuditLog(user_id=admin.id, action="DELETE", entity_type="announcement", entity_id=a.id,
                    old_value={"title": a.title}))
    await db.delete(a)
    await db.commit()


# ─── 문의 ─────────────────────────────────────────────────────────────────────
def _ticket_out(t: SupportTicket) -> SupportTicketOut:
    return SupportTicketOut(
        id=str(t.id), user_id=str(t.user_id), farm_id=str(t.farm_id) if t.farm_id else None,
        subject=t.subject, body=t.body, status=t.status, created_at=t.created_at,
    )


@router.get("/support", response_model=PagedResponse[SupportTicketOut])
async def admin_list_tickets(
    db: DbDep,
    _admin: SuperAdmin,
    status: Annotated[str | None, Query(description="OPEN/ANSWERED/CLOSED")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PagedResponse[SupportTicketOut]:
    conds = []
    if status:
        st = status.upper()
        if st not in TICKET_STATUSES:
            raise ValidationError(f"Invalid status. Allowed: {', '.join(sorted(TICKET_STATUSES))}")
        conds.append(SupportTicket.status == st)
    total = await db.scalar(select(func.count()).select_from(SupportTicket).where(*conds)) or 0
    pages = max(1, (total + per_page - 1) // per_page)
    rows = (
        await db.execute(
            select(SupportTicket).where(*conds)
            .order_by(SupportTicket.created_at.desc())
            .limit(per_page).offset((page - 1) * per_page)
        )
    ).scalars().all()
    return PagedResponse(items=[_ticket_out(t) for t in rows], meta=PageMeta(total=total, page=page, per_page=per_page, pages=pages))


@router.get("/support/{ticket_id}", response_model=SupportTicketDetail)
async def admin_get_ticket(ticket_id: UUID, db: DbDep, _admin: SuperAdmin) -> SupportTicketDetail:
    t = (
        await db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id).options(selectinload(SupportTicket.replies))
        )
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Ticket not found")
    base = _ticket_out(t)
    replies = [
        SupportReplyOut(id=str(r.id), author_id=str(r.author_id) if r.author_id else None,
                        is_staff=r.is_staff, body=r.body, created_at=r.created_at)
        for r in t.replies
    ]
    return SupportTicketDetail(**base.model_dump(), replies=replies)


@router.post("/support/{ticket_id}/reply", response_model=SupportTicketDetail)
async def admin_reply_ticket(ticket_id: UUID, body: SupportReplyCreate, db: DbDep, admin: SuperAdmin) -> SupportTicketDetail:
    t = await db.get(SupportTicket, ticket_id)
    if not t:
        raise NotFoundError("Ticket not found")
    db.add(SupportReply(ticket_id=t.id, author_id=admin.id, is_staff=True, body=body.body))
    t.status = "ANSWERED"
    db.add(AuditLog(user_id=admin.id, action="UPDATE", entity_type="support_ticket", entity_id=t.id,
                    new_value={"status": "ANSWERED"}))
    await db.commit()
    return await admin_get_ticket(ticket_id, db, admin)
