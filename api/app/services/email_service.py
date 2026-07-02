"""이메일 발송 서비스 — SMTP(표준 라이브러리). 비밀번호 재설정 등 트랜잭션 메일용.

설계:
- settings.smtp_configured(host+user+password) 아니면 발송 skip → False 반환(호출부가 로그 폴백).
- 비밀값은 env로만(config). 코드/로그에 자격증명·토큰 평문 노출 금지.
- stdlib smtplib를 asyncio.to_thread로 감싸 비동기 경로 블로킹 방지(새 의존성 없음).
"""
from __future__ import annotations

import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_ses_sync(to: str, subject: str, text_body: str, html_body: str | None) -> str:
    """AWS SES 발송(boto3). 자격증명은 표준 체인(env AWS_ACCESS_KEY_ID/SECRET 또는 IAM 롤).
    boto3는 발송 시점 지연 import(미설치 환경에서 앱 import가 깨지지 않게). pigsignal-collector 패턴."""
    import boto3
    ses = boto3.client(
        "ses",
        region_name=settings.aws_region,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    body: dict = {"Text": {"Data": text_body, "Charset": "UTF-8"}}
    if html_body:
        body["Html"] = {"Data": html_body, "Charset": "UTF-8"}
    resp = ses.send_email(
        Source=settings.ses_from_email,
        Destination={"ToAddresses": [to]},
        Message={"Subject": {"Data": subject, "Charset": "UTF-8"}, "Body": body},
    )
    return resp.get("MessageId", "")


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
    """메일 발송. SES(설정 시) 우선 → SMTP 폴백 → 미설정이면 False.
    성공 True / 미설정·실패 False(예외를 호출부로 던지지 않음 — 트랜잭션 흐름·열거방지 204 보호)."""
    if settings.ses_configured:
        try:
            mid = await asyncio.to_thread(_send_ses_sync, to, subject, text_body, html_body)
            logger.info("[EMAIL][SES] sent to %s (id=%s)", to, mid)
            return True
        except Exception:  # noqa: BLE001 — SES 실패 시 SMTP 폴백 시도(둘 다 실패면 False)
            logger.exception("[EMAIL][SES] send failed to %s", to)
    if settings.smtp_configured:
        try:
            await asyncio.to_thread(_send_sync, to, subject, text_body, html_body)
            return True
        except Exception:  # noqa: BLE001 — 발송 실패가 요청 처리를 깨지 않도록(열거방지·204 유지)
            logger.exception("[EMAIL][SMTP] send failed to %s (subject=%s)", to, subject)
    return False
