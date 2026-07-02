"""이메일 발송 서비스 + 비밀번호 재설정 토큰 전달(자동 메일) 테스트.

- SMTP 미설정: 발송 skip → False(크래시/예외 없음, 요청 흐름 보호).
- SMTP 설정: smtplib로 발송(자격증명 login + 메시지 헤더).
- _deliver_reset_token: 재설정 링크(토큰 포함)로 메일 발송.
"""
import pytest

from app.core.config import settings
from app.services.email_service import send_email

pytestmark = pytest.mark.anyio


async def test_skips_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "", raising=False)
    monkeypatch.setattr(settings, "smtp_user", "", raising=False)
    monkeypatch.setattr(settings, "smtp_password", "", raising=False)
    assert await send_email("to@x.com", "Subj", "body") is False


async def test_sends_via_smtp_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(settings, "smtp_user", "u@test", raising=False)
    monkeypatch.setattr(settings, "smtp_password", "pw", raising=False)
    monkeypatch.setattr(settings, "smtp_from", "noreply@pigos.io", raising=False)
    captured: dict = {}

    class FakeSMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): captured["tls"] = True
        def login(self, u, p): captured["login"] = (u, p)
        def send_message(self, msg): captured["msg"] = msg

    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", FakeSMTP)
    ok = await send_email("to@x.com", "Subj", "body", "<p>body</p>")
    assert ok is True
    assert captured["login"] == ("u@test", "pw")
    assert captured["msg"]["To"] == "to@x.com"
    assert captured["msg"]["From"] == "noreply@pigos.io"
    assert captured["msg"]["Subject"] == "Subj"


async def test_send_failure_returns_false_not_raise(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(settings, "smtp_user", "u", raising=False)
    monkeypatch.setattr(settings, "smtp_password", "pw", raising=False)

    def boom(*a, **k):
        raise OSError("connection refused")

    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", boom)
    assert await send_email("to@x.com", "s", "b") is False  # 예외 삼키고 False


async def test_prefers_ses_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "ses_from_email", "noreply@pigos.io", raising=False)
    captured: dict = {}

    def fake_ses(to, subject, text_body, html_body):
        captured.update(to=to, subject=subject)
        return "msg-123"

    # SES 경로 사용 확인 + SMTP는 호출 안 됨
    monkeypatch.setattr("app.services.email_service._send_ses_sync", fake_ses)
    monkeypatch.setattr("app.services.email_service._send_sync",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("SMTP should not be used")))
    ok = await send_email("to@x.com", "S", "b", "<p>b</p>")
    assert ok is True and captured["to"] == "to@x.com"


async def test_ses_failure_falls_back_to_smtp(monkeypatch):
    monkeypatch.setattr(settings, "ses_from_email", "noreply@pigos.io", raising=False)
    monkeypatch.setattr(settings, "smtp_host", "smtp.test", raising=False)
    monkeypatch.setattr(settings, "smtp_user", "u", raising=False)
    monkeypatch.setattr(settings, "smtp_password", "pw", raising=False)
    monkeypatch.setattr("app.services.email_service._send_ses_sync",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("SES down")))
    used = {}
    monkeypatch.setattr("app.services.email_service._send_sync",
                        lambda *a, **k: used.update(smtp=True))
    ok = await send_email("to@x.com", "S", "b")
    assert ok is True and used.get("smtp") is True  # SES 실패 → SMTP 폴백


async def test_deliver_reset_token_sends_link_with_token(monkeypatch):
    monkeypatch.setattr(settings, "app_base_url", "https://app.pigos.io", raising=False)
    captured: dict = {}

    async def fake_send(to, subject, text_body, html_body=None):
        captured.update(to=to, text=text_body, html=html_body)
        return True

    monkeypatch.setattr("app.services.email_service.send_email", fake_send)
    from app.services.auth_service import _deliver_reset_token
    await _deliver_reset_token("user@x.com", "TOK123")
    assert captured["to"] == "user@x.com"
    assert "https://app.pigos.io/forgot-password?token=TOK123" in captured["text"]
    assert "token=TOK123" in (captured["html"] or "")
