"""AI 규칙 운영 설정 — 운영자가 배포 없이 임계값·활성여부 조정 (운영자 콘솔 Phase 3).

엔진 규칙(engine/rules/*)은 RuleRegistry에 코드로 등록되고, 임계값/활성은 이 테이블로 오버라이드.
행이 없으면 코드 기본값(하드코딩) + enabled=True 로 동작(비파괴적 폴백).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RuleConfig(Base):
    __tablename__ = "rule_configs"

    rule_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    # null = 코드 기본값 사용
    warning: Mapped[float | None] = mapped_column(Float)
    critical: Mapped[float | None] = mapped_column(Float)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
