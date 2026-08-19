"""country_kpi_presentation — 국가별 KPI 표현 정책 (Presentation Policy).

경계(ADR):
  CKP decides whether/how a KPI may be used.
  Presentation decides how that KPI is named and ordered for a market.

  country_kpi_policy       = 써도 되는가 / 어느 군인가   (거버넌스)
  country_kpi_presentation = 뭐라 부르고 몇 번째인가      (표현)   ← 이 파일
  effective_metric_values  = 값이 얼마인가               (임계·벤치마크)

local_label 은 i18n 번역이 아니다. UI 언어가 영어여도 브라질 농장에는 현지 용어가
표시돼야 하므로 locale 축과 country terminology 축은 분리한다.

상속: GLOBAL → COUNTRY → FARM_TYPE → TENANT
  display_order : display_order_override=true 인 최하위 스코프 값 채택
                  (override=false 인 행은 그 스코프를 건너뜀 → 상위값 유지)
                  override=true + NULL = "명시적으로 마지막"
  local_label   : NULL 이면 상위값 유지(당분간 clear semantics 없음)
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

PRESENTATION_DECISION_STATUSES = ("PROPOSED", "APPROVED")


class CountryKpiPresentation(Base):
    __tablename__ = "country_kpi_presentation"
    __table_args__ = (
        # ★ scope 정합은 country_kpi_policy(ck_ckp_scope_keys) 원문을 그대로 복제한다.
        #   새로 작성하면 farm_type/tenant_id 혼입 같은 케이스를 놓친다.
        CheckConstraint(
            "(scope_level = 'GLOBAL'    AND country_code IS NULL AND farm_type IS NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'COUNTRY'   AND country_code IS NOT NULL AND farm_type IS NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'FARM_TYPE' AND country_code IS NOT NULL AND farm_type IS NOT NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'TENANT'    AND tenant_id IS NOT NULL)",
            name="ck_ckpres_scope_keys",
        ),
        CheckConstraint(
            "scope_level IN ('GLOBAL', 'COUNTRY', 'FARM_TYPE', 'TENANT')", name="ck_ckpres_scope"
        ),
        CheckConstraint("display_order IS NULL OR display_order >= 0", name="ck_ckpres_order"),
        CheckConstraint(
            "decision_status IN ('PROPOSED', 'APPROVED')", name="ck_ckpres_status"
        ),
        Index("ix_ckpres_lookup", "country_code", "kpi_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 스코프 — CKP 와 동일한 컬럼 구성/명칭(scope_level)을 쓴다.
    scope_level: Mapped[str] = mapped_column(String(16), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    farm_type: Mapped[str | None] = mapped_column(String(24))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    kpi_code: Mapped[str] = mapped_column(String(64), nullable=False)

    # 표현 벡터
    display_order: Mapped[int | None] = mapped_column(Integer)
    display_order_override: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    local_label: Mapped[str | None] = mapped_column(String(128))

    # 메타
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    decision_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PROPOSED")
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
