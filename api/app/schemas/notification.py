"""Notification 스키마 — 인앱 알림 목록/읽음 (P12-6 + 모바일 공용)."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import UUIDMixin


class NotificationResponse(UUIDMixin):
    farm_id: UUID | None
    title: str
    body: str
    alert_type: str | None
    severity: str | None
    related_entity_type: str | None
    related_entity_id: UUID | None
    read_at: datetime | None
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
    total: int


class MarkReadResult(BaseModel):
    updated: int
    unread_count: int


class GenerateResult(BaseModel):
    created: int
