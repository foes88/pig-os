"""QBridge CRM 인바운드 — 상담사 답변 수신(계약 B).

QBridge 가 호출하는 쪽. 사람 세션이 아니라 서비스-투-서비스이므로 base/admin 가드 대신
전용 서비스토큰(Bearer)만 상수시간 비교로 검사한다. 미설정이면 503.
external_ref = 원 SupportTicket.id(UUID 문자열).
"""
from __future__ import annotations

import hmac
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import DbDep
from app.db.models.content import SupportReply, SupportTicket
from app.db.models.ops import Notification

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/qbridge", tags=["integration"])


class QBridgeReply(BaseModel):
    external_ref: str = Field(..., description="원 SupportTicket.id (UUID 문자열)")
    body: str = Field(..., description="상담사 답변 — 이미 고객 언어로 번역됨")
    lang: str | None = None
    ticket_number: str | None = None
    sender_name: str | None = None


async def require_service_token(authorization: str | None = Header(default=None)) -> None:
    """서비스토큰 상수시간 검사. 미설정 시 503(인바운드 미구성)."""
    if not settings.qbridge_service_token:
        raise HTTPException(503, "integration not configured")
    expected = f"Bearer {settings.qbridge_service_token}"
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(401, "invalid service token")


@router.post("/reply", dependencies=[Depends(require_service_token)])
async def receive_reply(body: QBridgeReply, db: DbDep) -> dict:
    try:
        ticket_id = UUID(body.external_ref)
    except (ValueError, AttributeError):
        raise HTTPException(422, "external_ref must be a valid ticket id") from None

    ticket = await db.get(SupportTicket, ticket_id)
    if ticket is None:
        raise HTTPException(404, "ticket not found")

    db.add(SupportReply(ticket_id=ticket.id, author_id=None, is_staff=True, body=body.body))
    ticket.status = "ANSWERED"
    db.add(Notification(
        user_id=ticket.user_id, farm_id=ticket.farm_id, type="IN_APP",
        title="문의 답변이 등록되었습니다", body=body.body[:200],
        related_entity_type="support_ticket", related_entity_id=ticket.id,
    ))
    await db.commit()
    logger.info("QBridge 답변 수신 반영(ticket=%s, qb=%s)", ticket.id, body.ticket_number)
    return {"ok": True}
