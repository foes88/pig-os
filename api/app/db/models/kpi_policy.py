"""country_kpi_policy — 국가별 KPI 정책 벡터 (COUNTRY_KPI_RULE_SPEC v0.3.1 §4.2 + v0.4 패치).

어떤 KPI를 (국가×farm_type×production_stage×tenant)별로 계산·표시·경보·벤치마크·예측·수출할지 결정.
상속: GLOBAL → COUNTRY → FARM_TYPE → TENANT (하위가 NULL 아닌 축만 override).
**리졸버·프론트·API는 이 원본을 직접 조회 금지 — resolve_kpi_policy()가 상속 해석한 결과만 사용.**
decision_status='APPROVED' 행만 resolved에 반영(fail-closed). 위조0: 미승인/미검증 seed 금지.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SCOPE_LEVELS = ("GLOBAL", "COUNTRY", "FARM_TYPE", "TENANT")
DISPLAY_ROLES = ("PRIMARY", "SECONDARY", "HIDDEN")
BENCHMARK_EXPOSURES = ("FULL", "CONTEXT_ONLY", "NONE")
API_EXPORT_POLICIES = ("PUBLIC", "TENANT_ONLY", "INTERNAL_ONLY", "NONE")
DECISION_STATUSES = ("PROPOSED", "REVIEWED", "APPROVED", "REJECTED")
# v0.4 신설
PRIORITY_CLASSES = ("NORTH_STAR", "DRIVER", "GUARDRAIL", "FINANCIAL", "QUALITY", "CONTEXT")
PRODUCTION_STAGES = ("BREEDING", "NURSERY", "GROW_FINISH", "FARROW_TO_FINISH")
EVIDENCE_STATUSES = (
    "VERIFIED", "OFFICIAL_GUIDANCE", "DRAFT_GUIDANCE",
    "REVIEWED_DIRECTION", "UNVERIFIED_DRAFT", "INSUFFICIENT",
)


def _in(col: str, vals: tuple[str, ...]) -> str:
    return f"{col} IN (" + ", ".join(f"'{v}'" for v in vals) + ")"


class CountryKpiPolicy(Base):
    __tablename__ = "country_kpi_policy"
    __table_args__ = (
        # scope별 키 정합(§4.2 chk_scope_keys)
        CheckConstraint(
            "(scope_level = 'GLOBAL'    AND country_code IS NULL AND farm_type IS NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'COUNTRY'   AND country_code IS NOT NULL AND farm_type IS NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'FARM_TYPE' AND country_code IS NOT NULL AND farm_type IS NOT NULL AND tenant_id IS NULL) OR "
            "(scope_level = 'TENANT'    AND tenant_id IS NOT NULL)",
            name="ck_ckp_scope_keys",
        ),
        # GLOBAL은 정책벡터 6축 전부 NOT NULL(§4.2 chk_global_complete)
        CheckConstraint(
            "scope_level != 'GLOBAL' OR ("
            "compute_enabled IS NOT NULL AND display_role IS NOT NULL AND rule_enabled IS NOT NULL AND "
            "benchmark_exposure IS NOT NULL AND prediction_feature IS NOT NULL AND api_export_policy IS NOT NULL)",
            name="ck_ckp_global_complete",
        ),
        CheckConstraint("decision_status != 'APPROVED' OR decided_by IS NOT NULL", name="ck_ckp_approved_decided"),
        # v0.4: 미검증 승인 금지(임시보수는 note 필수)
        CheckConstraint(
            "decision_status != 'APPROVED' OR evidence_status IS NULL "
            "OR evidence_status NOT IN ('UNVERIFIED_DRAFT','INSUFFICIENT') OR note IS NOT NULL",
            name="ck_ckp_approved_needs_evidence",
        ),
        CheckConstraint(_in("scope_level", SCOPE_LEVELS), name="ck_ckp_scope"),
        CheckConstraint("display_role IS NULL OR " + _in("display_role", DISPLAY_ROLES), name="ck_ckp_display"),
        CheckConstraint("priority_class IS NULL OR " + _in("priority_class", PRIORITY_CLASSES), name="ck_ckp_priority"),
        CheckConstraint("production_stage IS NULL OR " + _in("production_stage", PRODUCTION_STAGES), name="ck_ckp_stage"),
        CheckConstraint("evidence_status IS NULL OR " + _in("evidence_status", EVIDENCE_STATUSES), name="ck_ckp_evidence"),
        CheckConstraint("benchmark_exposure IS NULL OR " + _in("benchmark_exposure", BENCHMARK_EXPOSURES), name="ck_ckp_bench"),
        CheckConstraint("api_export_policy IS NULL OR " + _in("api_export_policy", API_EXPORT_POLICIES), name="ck_ckp_api"),
        CheckConstraint(_in("decision_status", DECISION_STATUSES), name="ck_ckp_decision"),
        Index("idx_ckp_resolve", "kpi_code", "scope_level", "country_code", "farm_type", "production_stage"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope_level: Mapped[str] = mapped_column(String(16), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2))
    farm_type: Mapped[str | None] = mapped_column(String(24))
    production_system: Mapped[str | None] = mapped_column(String(24))
    production_stage: Mapped[str | None] = mapped_column(String(16))  # v0.4
    herd_size_band: Mapped[str | None] = mapped_column(String(24))
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True))

    kpi_code: Mapped[str] = mapped_column(String(64), nullable=False)

    # 정책 벡터 — NULL = 상위 상속
    compute_enabled: Mapped[bool | None] = mapped_column(Boolean)
    display_role: Mapped[str | None] = mapped_column(String(16))
    priority_class: Mapped[str | None] = mapped_column(String(16))  # v0.4
    # ※ display_order 는 country_kpi_presentation 으로 이관됨(a7d9c3e5f1b8).
    #    CKP = 써도 되는가/어느 군인가, CKPRES = 뭐라 부르고 몇 번째인가.
    #    headline 은 여전히 여기 priority_class='NORTH_STAR'(uq_ckp_north_star 가 국가당 1개 강제).
    rule_enabled: Mapped[bool | None] = mapped_column(Boolean)
    benchmark_exposure: Mapped[str | None] = mapped_column(String(16))
    prediction_feature: Mapped[bool | None] = mapped_column(Boolean)
    api_export_policy: Mapped[str | None] = mapped_column(String(24))

    # 상태 축 (v0.4: evidence ⊥ decision)
    evidence_status: Mapped[str | None] = mapped_column(String(24))  # v0.4
    decision_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PROPOSED")
    decided_by: Mapped[str | None] = mapped_column(String(64))

    effective_from: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())
    effective_to: Mapped[date | None] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
