"""1:1 문의 — 고객(로그인 사용자) 등록/조회. 답변은 운영자(admin/content)."""
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUser, DbDep
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.models.content import SupportReply, SupportTicket
from app.schemas.content import (
    SupportReplyCreate,
    SupportReplyOut,
    SupportTicketCreate,
    SupportTicketDetail,
    SupportTicketOut,
)

router = APIRouter(prefix="/support", tags=["Support"])


def _ticket_out(t: SupportTicket) -> SupportTicketOut:
    return SupportTicketOut(
        id=str(t.id), user_id=str(t.user_id), farm_id=str(t.farm_id) if t.farm_id else None,
        subject=t.subject, body=t.body, status=t.status, created_at=t.created_at,
    )


@router.post("/tickets", response_model=SupportTicketOut, status_code=201)
async def create_ticket(body: SupportTicketCreate, db: DbDep, user: CurrentUser) -> SupportTicketOut:
    t = SupportTicket(
        user_id=user.id,
        farm_id=UUID(body.farm_id) if body.farm_id else None,
        subject=body.subject, body=body.body, status="OPEN",
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return _ticket_out(t)


@router.get("/tickets", response_model=list[SupportTicketOut])
async def my_tickets(db: DbDep, user: CurrentUser) -> list[SupportTicketOut]:
    rows = (
        await db.execute(
            select(SupportTicket).where(SupportTicket.user_id == user.id)
            .order_by(SupportTicket.created_at.desc())
        )
    ).scalars().all()
    return [_ticket_out(t) for t in rows]


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetail)
async def my_ticket_detail(ticket_id: UUID, db: DbDep, user: CurrentUser) -> SupportTicketDetail:
    t = (
        await db.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id).options(selectinload(SupportTicket.replies))
        )
    ).scalar_one_or_none()
    if not t:
        raise NotFoundError("Ticket not found")
    if t.user_id != user.id:
        raise ForbiddenError("Not your ticket")
    base = _ticket_out(t)
    replies = [
        SupportReplyOut(id=str(r.id), author_id=str(r.author_id) if r.author_id else None,
                        is_staff=r.is_staff, body=r.body, created_at=r.created_at)
        for r in t.replies
    ]
    return SupportTicketDetail(**base.model_dump(), replies=replies)


@router.post("/tickets/{ticket_id}/reply", response_model=SupportTicketDetail)
async def my_ticket_followup(ticket_id: UUID, body: SupportReplyCreate, db: DbDep, user: CurrentUser) -> SupportTicketDetail:
    t = await db.get(SupportTicket, ticket_id)
    if not t:
        raise NotFoundError("Ticket not found")
    if t.user_id != user.id:
        raise ForbiddenError("Not your ticket")
    db.add(SupportReply(ticket_id=t.id, author_id=user.id, is_staff=False, body=body.body))
    t.status = "OPEN"  # 추가 문의 → 재오픈
    await db.commit()
    return await my_ticket_detail(ticket_id, db, user)
