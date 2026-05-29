"""
Configuration layer: market/region defaults, KPI benchmarks, compliance, farm_configs.
These are mostly seed data + farm-level overrides.
"""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketDefault(Base):
    __tablename__ = "market_defaults"

    market_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    market_name: Mapped[str] = mapped_column(String(50), nullable=False)
    weight_unit: Mapped[str] = mapped_column(String(5), nullable=False)   # kg / lb
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    pricing_unit: Mapped[str | None] = mapped_column(String(20))
    compliance_profile_code: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RegionDefault(Base):
    __tablename__ = "region_defaults"

    region_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    region_name: Mapped[str] = mapped_column(String(50), nullable=False)
    market_code: Mapped[str] = mapped_column(String(10), ForeignKey("market_defaults.market_code"), nullable=False)
    weight_unit: Mapped[str | None] = mapped_column(String(5))
    currency_code: Mapped[str | None] = mapped_column(String(3))
    pricing_unit: Mapped[str | None] = mapped_column(String(20))
    compliance_profile_code: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DefaultMetricValue(Base):
    """
    KPI benchmarks: system → market → region → farm priority chain.
    Query with effective_metric_values() DB function for resolved value.
    """
    __tablename__ = "default_metric_values"
    __table_args__ = (
        UniqueConstraint("scope_type", "scope_code", "metric_code"),
        Index("idx_dmv_lookup", "metric_code", "scope_type", "scope_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # system / market / region / farm
    scope_code: Mapped[str] = mapped_column(String(20), nullable=False)
    metric_code: Mapped[str] = mapped_column(String(50), nullable=False)
    # PSY / MSY / NPD / FCR / MORTALITY
    default_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    benchmark_avg: Mapped[float | None] = mapped_column(Numeric(10, 2))
    benchmark_top25: Mapped[float | None] = mapped_column(Numeric(10, 2))
    target_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    unit_code: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScopeKpiRecommendation(Base):
    """
    Controls KPI visibility and domain gating per market/region.
    is_base=True → free, is_addon=True → requires addon_code subscription.
    """
    __tablename__ = "scope_kpi_recommendations"
    __table_args__ = (
        Index("idx_skr_lookup", "scope_type", "scope_code", "display_priority"),
        UniqueConstraint("scope_type", "scope_code", "kpi_code", "farm_type", "min_sow_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)  # system / market / region
    scope_code: Mapped[str] = mapped_column(String(20), nullable=False)
    kpi_code: Mapped[str] = mapped_column(String(50), nullable=False)
    display_priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_base: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_addon: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    addon_code: Mapped[str | None] = mapped_column(String(50))
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    farm_type: Mapped[str | None] = mapped_column(String(20))
    min_sow_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ComplianceProfile(Base):
    __tablename__ = "compliance_profiles"

    profile_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    profile_name: Mapped[str] = mapped_column(String(100), nullable=False)
    requires_traceability: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_welfare_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_antibiotic_tracking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_env_reporting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_wean_period: Mapped[int | None] = mapped_column(Integer)
    max_antibiotic_treatments: Mapped[float | None] = mapped_column(Numeric(5, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MarketPriceReference(Base):
    __tablename__ = "market_price_reference"
    __table_args__ = (
        Index("idx_mpr_region_date", "region_code", "price_date"),
        Index("idx_mpr_market_date", "market_code", "price_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    region_code: Mapped[str | None] = mapped_column(String(10), ForeignKey("region_defaults.region_code"))
    market_code: Mapped[str | None] = mapped_column(String(10), ForeignKey("market_defaults.market_code"))
    price_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # LIVE_HOG / PORK_CUTOUT / LEAN_HOG_FUTURES
    price_value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    weight_unit: Mapped[str] = mapped_column(String(5), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FarmConfig(Base):
    """
    Per-farm reproductive parameters: gestation days, lactation days, alert thresholds.
    Overrides market/region defaults.
    """
    __tablename__ = "farm_configs"
    __table_args__ = (UniqueConstraint("farm_id", "config_key"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    config_key: Mapped[str] = mapped_column(String(50), nullable=False)
    # GESTATION_DAYS / LACTATION_DAYS / WEI_TARGET_DAYS / PREGNANCY_CHECK_DAY
    # FARROWING_ALERT_DAYS / WEANING_ALERT_DAYS / NPD_ALERT_THRESHOLD / SOW_CULL_PARITY_THRESHOLD
    config_value: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
