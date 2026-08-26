"""운영자 콘솔 콘텐츠 — 공지/1:1 문의 (PigOS 네이티브).

레거시 board/qna 스키마 복제 아님. SaaS 운영에 필요한 최소 필드로 설계.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (
    # 마이그레이션이 만든 인덱스를 모델에도 선언한다 — 선언이 없으면 alembic check 가
    # "모델이 원하지 않는 인덱스"로 보고 drop 을 제안한다(독립검증 2026-08-25 드리프트).
        Index("idx_announcements_published", "published", "pinned"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # 분류(태그 색상 매핑용): GENERAL / UPDATE / MAINTENANCE
    category: Mapped[str] = mapped_column(String(20), nullable=False, default="GENERAL")
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # 게시 기간(둘 다 nullable = 무기한)
    publish_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    publish_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 특정 언어 타깃(null=전체 언어 노출)
    lang: Mapped[str | None] = mapped_column(String(5))
    created_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = (
    # 마이그레이션이 만든 인덱스를 모델에도 선언한다 — 선언이 없으면 alembic check 가
    # "모델이 원하지 않는 인덱스"로 보고 drop 을 제안한다(독립검증 2026-08-25 드리프트).
        Index("idx_support_tickets_status", "status", "created_at"),
        Index("idx_support_tickets_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    farm_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # OPEN(접수) / ANSWERED(답변완료) / CLOSED(종료)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    replies: Mapped[list["SupportReply"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="SupportReply.created_at"
    )


class SupportReply(Base):
    __tablename__ = "support_replies"
    __table_args__ = (
    # 마이그레이션이 만든 인덱스를 모델에도 선언한다 — 선언이 없으면 alembic check 가
    # "모델이 원하지 않는 인덱스"로 보고 drop 을 제안한다(독립검증 2026-08-25 드리프트).
        Index("idx_support_replies_ticket", "ticket_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    # 운영자(스태프) 답변 여부 — true=운영자, false=가입자 추가 문의
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ticket: Mapped["SupportTicket"] = relationship(back_populates="replies")
