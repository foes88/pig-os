"""
operational_defaults — Threshold Resolver의 글로벌 임계 레지스트리 (A-하이브리드).

룰 코드 인라인 임계를 '값 그대로' 이전(origin='code_default'). threshold 전용 — benchmark/평균 아님.
조회 순서: rule_configs(운영자) → operational_defaults(글로벌). direction은 발화 시 kpi_definitions 우선.
옛 default_metric_values와 무관(§14.6).
"""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Numeric, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OperationalDefault(Base):
    __tablename__ = "operational_defaults"
    __table_args__ = (
        UniqueConstraint("scope", "country_code", "rule_id", name="uq_opdef_scope_rule"),
        CheckConstraint("direction IN ('higher_better','lower_better','range_target')", name="ck_opdef_direction"),
        CheckConstraint("value_scale IN ('percent_0_100','ratio_0_1','n/a')", name="ck_opdef_valuescale"),
        CheckConstraint("origin IN ('code_default','operator','imported')", name="ck_opdef_origin"),
        Index("idx_opdef_lookup", "country_code", "rule_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(Text, nullable=False, server_default="global")
    country_code: Mapped[str | None] = mapped_column(Text)   # global → NULL
    rule_id: Mapped[str] = mapped_column(Text, nullable=False)
    kpi_code: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(Text, nullable=False)
    value_scale: Mapped[str] = mapped_column(Text, nullable=False)
    warning_min: Mapped[float | None] = mapped_column(Numeric)
    warning_max: Mapped[float | None] = mapped_column(Numeric)
    critical_min: Mapped[float | None] = mapped_column(Numeric)
    critical_max: Mapped[float | None] = mapped_column(Numeric)
    # 감사 메타 (②)
    origin: Mapped[str] = mapped_column(Text, nullable=False, server_default="code_default")
    source_rule: Mapped[str | None] = mapped_column(Text)        # 원래 룰 키
    source_loc: Mapped[str | None] = mapped_column(Text)         # 원본 코드 위치
    original_warning: Mapped[float | None] = mapped_column(Numeric)  # 원본 경고값(보존 증명용)
    original_critical: Mapped[float | None] = mapped_column(Numeric)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
