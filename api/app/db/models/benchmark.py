"""
KPI Governance v3.1 — 3-테이블 (kpi_definitions / source_observations / benchmarks).

설계 기준: handoff/KPI_GOVERNANCE_v3.1.md §3.1~§3.3, §3.5.
핵심 원칙: KPI 단위 verified. 원문(source_observations)과 PigOS 변환값(benchmarks) 분리.
transform_formula 없으면 normalized_verified 금지. value_scale 없으면 Rule Engine 비교 금지.

기존 default_metric_values(단일테이블 임계)는 유지 — 본 3-테이블은 그 위에 얹는 거버넌스 계층.
Rule Engine 연결은 작업 B 이후 별도 단계.
"""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# ── 허용 enum (문서 §2~§3.5) ──────────────────────────────────────────────────
DENOMINATOR_TYPES = ("avg_inventory_sow", "mated_female", "farrowed_female", "litter", "piglet", "total_born", "weight")
PERIOD_BASES = ("rolling_365", "annual", "quarterly", "period")
DIRECTIONS = ("higher_better", "lower_better", "range_target")
VALUE_SCALES = ("percent_0_100", "ratio_0_1", "n/a")          # kpi_definitions 허용 (n/a 포함)
# benchmarks도 n/a 허용 — count KPI(PSY/NPD 등 value_scale='n/a')가 NULL이면 can_fire가 막혀 발화 불가해지므로.
# kpi_definitions.value_scale와 동일 집합을 써 ★⑫-4(value_scale 일치)를 깔끔히 성립시킴.
BENCH_VALUE_SCALES = ("percent_0_100", "ratio_0_1", "n/a")
MAPPING_STATUSES = ("exact", "normalized", "incompatible", "unknown")
COMPARISON_STATUSES = ("exact", "compatible", "normalized", "incompatible", "unknown")
BENCHMARK_STATUSES = ("verified", "normalized_verified", "provisional", "missing", "global_fallback")
FIREABLE_COMPARISON = ("exact", "compatible", "normalized")   # Rule Engine 발화 허용 (★③)


class KpiDefinition(Base):
    """KPI 본질 정의 (국가 무관). definition_id의 정본 레지스트리. §3.1"""
    __tablename__ = "kpi_definitions"
    __table_args__ = (
        PrimaryKeyConstraint("kpi_code", "definition_id"),
        CheckConstraint(f"direction IN {DIRECTIONS}", name="ck_kpidef_direction"),
        CheckConstraint(f"denominator_type IN {DENOMINATOR_TYPES}", name="ck_kpidef_denomtype"),
        CheckConstraint(f"period_basis IN {PERIOD_BASES}", name="ck_kpidef_period"),
        # value_scale NULL 금지 + enum 강제 (§4.3)
        CheckConstraint(f"value_scale IN {VALUE_SCALES}", name="ck_kpidef_valuescale"),
    )

    kpi_code: Mapped[str] = mapped_column(Text, nullable=False)
    definition_id: Mapped[str] = mapped_column(Text, nullable=False)   # 예: PIGOS_PSY_V1
    name_ko: Mapped[str | None] = mapped_column(Text)
    numerator_def: Mapped[str] = mapped_column(Text, nullable=False)
    denominator_def: Mapped[str] = mapped_column(Text, nullable=False)
    denominator_type: Mapped[str] = mapped_column(Text, nullable=False)
    period_basis: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(Text, nullable=False)
    value_scale: Mapped[str] = mapped_column(Text, nullable=False)     # 문서 §4.3: NULL 금지
    notes: Mapped[str | None] = mapped_column(Text)


class SourceObservation(Base):
    """외부 원문 (변환 전, 가공 금지). §3.2"""
    __tablename__ = "source_observations"
    __table_args__ = (
        Index("idx_srcobs_group", "obs_group_id"),
        Index("idx_srcobs_country_kpi", "country_code", "source_kpi_code"),
    )

    obs_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obs_group_id: Mapped[str | None] = mapped_column(Text)            # ★⑤ 변환근거 묶음
    source_id: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(Text)
    source_year: Mapped[int | None] = mapped_column(Integer)
    source_url: Mapped[str | None] = mapped_column(Text)
    period_start: Mapped[date | None] = mapped_column(Date)           # ★⑨
    period_end: Mapped[date | None] = mapped_column(Date)
    publication_date: Mapped[date | None] = mapped_column(Date)
    country_code: Mapped[str | None] = mapped_column(Text)
    source_kpi_code: Mapped[str | None] = mapped_column(Text)
    source_kpi_label: Mapped[str | None] = mapped_column(Text)
    source_value: Mapped[float | None] = mapped_column(Numeric)
    source_numerator: Mapped[str | None] = mapped_column(Text)
    source_denominator: Mapped[str | None] = mapped_column(Text)
    source_denominator_raw: Mapped[str | None] = mapped_column(Text)  # present_sow 등 모호표기 보존
    population_scope: Mapped[str | None] = mapped_column(Text)        # national_avg|coop_avg|pro_user|top10|top1
    period_basis: Mapped[str | None] = mapped_column(Text)
    source_value_scale: Mapped[str | None] = mapped_column(Text)
    is_provisional: Mapped[bool] = mapped_column(Boolean, server_default="false")
    confidence_level: Mapped[str | None] = mapped_column(Text)        # A|B|C
    raw_fields_json: Mapped[dict | None] = mapped_column(JSONB)       # ★⑩ 분리항목 보존
    notes: Mapped[str | None] = mapped_column(Text)


class Benchmark(Base):
    """PigOS 변환값만. §3.3 + §3.5 제약."""
    __tablename__ = "benchmarks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["kpi_code", "definition_id"],
            ["kpi_definitions.kpi_code", "kpi_definitions.definition_id"],
            name="fk_bench_kpidef",
        ),  # ★④
        CheckConstraint(f"mapping_status IN {MAPPING_STATUSES}", name="ck_bench_mapping"),
        CheckConstraint(f"comparison_status IN {COMPARISON_STATUSES}", name="ck_bench_comparison"),
        CheckConstraint(f"benchmark_status IN {BENCHMARK_STATUSES}", name="ck_bench_status"),
        CheckConstraint(f"value_scale IS NULL OR value_scale IN {BENCH_VALUE_SCALES}", name="ck_bench_valuescale"),
        # ★⑦ verified/normalized_verified → is_provisional=false + transformed_value NOT NULL
        CheckConstraint(
            "benchmark_status NOT IN ('verified','normalized_verified') "
            "OR (is_provisional = false AND transformed_value IS NOT NULL)",
            name="ck_bench_verified_notprovisional",
        ),
        # ★⑧ normalized_verified 6조건
        CheckConstraint(
            "benchmark_status <> 'normalized_verified' OR ("
            "transform_formula IS NOT NULL AND mapping_status = 'normalized' "
            "AND comparison_status = 'normalized' AND transformed_value IS NOT NULL "
            "AND value_scale IS NOT NULL AND (source_obs_id IS NOT NULL OR obs_group_id IS NOT NULL))",
            name="ck_bench_normverified_6cond",
        ),
        # ★⑫-1 verified → comparison_status ∈ {exact, compatible}
        CheckConstraint(
            "benchmark_status <> 'verified' OR comparison_status IN ('exact','compatible')",
            name="ck_bench_verified_comparison",
        ),
        # ★⑫-3 verified → transform_formula IS NULL (재정규화 필요하면 normalized_verified여야)
        CheckConstraint(
            "benchmark_status <> 'verified' OR transform_formula IS NULL",
            name="ck_bench_verified_noformula",
        ),
        # ★⑫-5 missing → transformed_value IS NULL
        CheckConstraint(
            "benchmark_status <> 'missing' OR transformed_value IS NULL",
            name="ck_bench_missing_novalue",
        ),
        # ★⑫-6 incompatible/unknown → 발화값(threshold/transformed_value) 전부 NULL
        CheckConstraint(
            "comparison_status NOT IN ('incompatible','unknown') OR ("
            "transformed_value IS NULL AND warning_min IS NULL AND warning_max IS NULL "
            "AND critical_min IS NULL AND critical_max IS NULL)",
            name="ck_bench_incompatible_silent",
        ),
        Index("idx_bench_lookup", "country_code", "kpi_code", "definition_id"),
        # active verified 중복 방지: 동일 (country,system,size,kpi,def) verified류 1개만 (§4.5)
        Index(
            "uq_bench_active_verified",
            "country_code", "production_system", "farm_size_band", "kpi_code", "definition_id",
            unique=True,
            postgresql_where="benchmark_status IN ('verified','normalized_verified') AND is_active",
        ),
    )

    bench_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(Text, nullable=False)
    production_system: Mapped[str] = mapped_column(Text, server_default="all")
    farm_size_band: Mapped[str] = mapped_column(Text, server_default="all")
    kpi_code: Mapped[str] = mapped_column(Text, nullable=False)
    definition_id: Mapped[str] = mapped_column(Text, nullable=False)
    transformed_value: Mapped[float | None] = mapped_column(Numeric)
    transform_formula: Mapped[str | None] = mapped_column(Text)
    value_scale: Mapped[str | None] = mapped_column(Text)
    source_obs_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("source_observations.obs_id"))
    obs_group_id: Mapped[str | None] = mapped_column(Text)
    warning_min: Mapped[float | None] = mapped_column(Numeric)
    warning_max: Mapped[float | None] = mapped_column(Numeric)
    critical_min: Mapped[float | None] = mapped_column(Numeric)
    critical_max: Mapped[float | None] = mapped_column(Numeric)
    target: Mapped[float | None] = mapped_column(Numeric)
    mapping_status: Mapped[str | None] = mapped_column(Text)
    comparison_status: Mapped[str | None] = mapped_column(Text)
    benchmark_status: Mapped[str] = mapped_column(Text, server_default="missing")
    is_provisional: Mapped[bool] = mapped_column(Boolean, server_default="false")
    # 이력/버전 (§4.5 — 과거 verified 보관, active 중복 방지용)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
