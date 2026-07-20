"""QBridge CRM 아웃바운드 — 문의(SupportTicket)를 QBridge /inbound 로 발신(계약 A).

설계 (email_service.py·push_service.py 관례 준수):
- settings.qbridge_outbound_configured 아니면 조용히 skip(no-op).
- 비밀값은 env로만(config). 코드/로그에 토큰 평문 노출 금지.
- httpx 지연 import(미설치 환경에서 앱 import 안 깨지게). 실패해도 raise 안 함 — 문의 저장은 유지.
- 커밋 후 BackgroundTasks 로 호출되므로, ORM 객체가 아닌 원시값을 받아 detached-세션 이슈를 피한다.
"""
from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def push_ticket_to_qbridge(
    *,
    ticket_id: str,
    subject: str,
    message: str,
    name: str,
    email: str | None,
    lang: str | None,
    phone: str | None = None,
) -> None:
    """SupportTicket 생성 직후 QBridge 로 인입. 계약 A(POST /api/v1/inbound)."""
    if not settings.qbridge_outbound_configured:
        return  # 미구성 — no-op

    import httpx

    payload = {
        "channel": "web",
        "product_slug": "pigos",
        "source_system": "pigos",
        "name": name,
        "email": email,
        "phone": phone,
        "message": message,
        "subject": subject,
        "lang": lang or "en",
        "external_id": ticket_id,  # 원 SupportTicket.id — 답변 콜백(B)의 external_ref
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{settings.qbridge_url.rstrip('/')}/api/v1/inbound",
                json=payload,
                headers={"Authorization": f"Bearer {settings.qbridge_inbound_token}"},
            )
            r.raise_for_status()
    except Exception as exc:  # noqa: BLE001 — 연동 실패는 문의 저장을 막지 않는다
        logger.warning("QBridge 인입 실패(ticket=%s): %s", ticket_id, exc)
