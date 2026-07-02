"""이메일 발송 서비스 — SMTP(표준 라이브러리). 비밀번호 재설정 등 트랜잭션 메일용.

설계:
- settings.smtp_configured(host+user+password) 아니면 발송 skip → False 반환(호출부가 로그 폴백).
- 비밀값은 env로만(config). 코드/로그에 자격증명·토큰 평문 노출 금지.
- stdlib smtplib를 asyncio.to_thread로 감싸 비동기 경로 블로킹 방지(새 의존성 없음).
"""
from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_sync(to: str, subject: str, text_body: str, html_body: str | None) -> None:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)


async def send_email(to: str, subject: str, text_body: str, html_body: str | None = None) -> bool:
    """메일 발송. 성공 True / 미설정·실패 False(예외를 호출부로 던지지 않음 — 트랜잭션 흐름 보호)."""
    if not settings.smtp_configured:
        return False
    try:
        await asyncio.to_thread(_send_sync, to, subject, text_body, html_body)
        return True
    except Exception:  # noqa: BLE001 — 발송 실패가 요청 처리를 깨지 않도록(열거방지·204 유지)
        logger.exception("[EMAIL] send failed to %s (subject=%s)", to, subject)
        return False
