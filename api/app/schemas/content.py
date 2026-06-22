"""공지/문의 스키마 (운영자 콘솔 Phase 2)."""
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import OrmBase

ANNOUNCEMENT_CATEGORIES = {"GENERAL", "UPDATE", "MAINTENANCE"}
TICKET_STATUSES = {"OPEN", "ANSWERED", "CLOSED"}


# ── 공지 ──────────────────────────────────────────────────────────────────────
class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    category: str = "GENERAL"
    pinned: bool = False
    published: bool = True
    publish_from: datetime | None = None
    publish_until: datetime | None = None
    lang: str | None = None


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None
    category: str | None = None
    pinned: bool | None = None
    published: bool | None = None
    publish_from: datetime | None = None
    publish_until: datetime | None = None
    lang: str | None = None


class AnnouncementOut(OrmBase):
    id: str
    title: str
    body: str
    category: str
    pinned: bool
    published: bool
    publish_from: datetime | None
    publish_until: datetime | None
    lang: str | None
    created_at: datetime | None


# ── 문의 ──────────────────────────────────────────────────────────────────────
class SupportTicketCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    farm_id: str | None = None


class SupportReplyOut(OrmBase):
    id: str
    author_id: str | None
    is_staff: bool
    body: str
    created_at: datetime | None


class SupportTicketOut(OrmBase):
    id: str
    user_id: str
    farm_id: str | None
    subject: str
    body: str
    status: str
    created_at: datetime | None


class SupportTicketDetail(SupportTicketOut):
    replies: list[SupportReplyOut]


class SupportReplyCreate(BaseModel):
    body: str = Field(min_length=1)
