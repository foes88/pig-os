"""QBridge 연동 검증 — 인바운드(계약 B) 반영 + 아웃바운드 graceful-skip."""
import pytest
from sqlalchemy import select

from app.core.config import settings
from app.db.models.content import SupportReply, SupportTicket
from app.db.models.ops import Notification
from app.services.qbridge_service import push_ticket_to_qbridge


async def _make_ticket(db, user) -> SupportTicket:
    t = SupportTicket(user_id=user.id, subject="사료 문의", body="질문입니다", status="OPEN")
    db.add(t)
    await db.flush()
    return t


@pytest.mark.asyncio
async def test_inbound_reply_creates_reply_status_notification(client, db, test_user, monkeypatch):
    monkeypatch.setattr(settings, "qbridge_service_token", "svc-token")
    t = await _make_ticket(db, test_user)

    r = await client.post(
        "/api/v1/integrations/qbridge/reply",
        json={"external_ref": str(t.id), "body": "답변드립니다", "ticket_number": "QB-2026-1", "lang": "ko"},
        headers={"Authorization": "Bearer svc-token"},
    )
    assert r.status_code == 200

    replies = (await db.execute(select(SupportReply).where(SupportReply.ticket_id == t.id))).scalars().all()
    assert len(replies) == 1 and replies[0].is_staff is True and replies[0].body == "답변드립니다"
    await db.refresh(t)
    assert t.status == "ANSWERED"
    notes = (await db.execute(select(Notification).where(Notification.user_id == test_user.id))).scalars().all()
    assert any(n.type == "IN_APP" and n.related_entity_id == t.id for n in notes)


@pytest.mark.asyncio
async def test_inbound_reply_accepts_external_id_alias(client, db, test_user, monkeypatch):
    # QBridge Partner API 가이드는 콜백에 external_id를 보냄 → external_ref alias로 수용돼야 함
    monkeypatch.setattr(settings, "qbridge_service_token", "svc-token")
    t = await _make_ticket(db, test_user)
    r = await client.post(
        "/api/v1/integrations/qbridge/reply",
        json={"external_id": str(t.id), "body": "가이드 필드로 답변", "ticket_number": "QB-2026-2"},
        headers={"Authorization": "Bearer svc-token"},
    )
    assert r.status_code == 200
    replies = (await db.execute(select(SupportReply).where(SupportReply.ticket_id == t.id))).scalars().all()
    assert len(replies) == 1 and replies[0].body == "가이드 필드로 답변"


@pytest.mark.asyncio
async def test_inbound_rejects_bad_token(client, db, test_user, monkeypatch):
    monkeypatch.setattr(settings, "qbridge_service_token", "svc-token")
    t = await _make_ticket(db, test_user)
    r = await client.post(
        "/api/v1/integrations/qbridge/reply",
        json={"external_ref": str(t.id), "body": "x"},
        headers={"Authorization": "Bearer WRONG"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_inbound_503_when_unconfigured(client, test_user, monkeypatch):
    monkeypatch.setattr(settings, "qbridge_service_token", "")
    r = await client.post(
        "/api/v1/integrations/qbridge/reply",
        json={"external_ref": "00000000-0000-0000-0000-000000000000", "body": "x"},
        headers={"Authorization": "Bearer whatever"},
    )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_inbound_404_unknown_ticket(client, monkeypatch):
    monkeypatch.setattr(settings, "qbridge_service_token", "svc-token")
    r = await client.post(
        "/api/v1/integrations/qbridge/reply",
        json={"external_ref": "00000000-0000-0000-0000-000000000000", "body": "x"},
        headers={"Authorization": "Bearer svc-token"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_outbound_noop_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "qbridge_url", "")
    monkeypatch.setattr(settings, "qbridge_inbound_token", "")
    # 미구성이면 httpx 호출 없이 조용히 반환(예외 없음)
    await push_ticket_to_qbridge(
        ticket_id="t1", subject="s", message="m", name="n", email=None, lang="ko",
    )
