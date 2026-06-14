"""
Operations module: period_locks, kpi_snapshots, finisher_groups,
                   api_keys, notifications, sync_logs.
"""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric,
    SmallInteger, String, Text, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PeriodLock(Base):
    __tablename__ = "period_locks"
    __table_args__ = (
        UniqueConstraint("farm_id", "period_year", "period_month"),
        Index("idx_period_locks_farm", "farm_id", "period_year", "period_month"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    period_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    locked_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    unlocked_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)


class KpiSnapshot(Base):
    """
    Pre-computed KPI values written by ARQ background jobs.
    Dashboard reads here instead of running full aggregations.
    is_stale=True → ARQ recalculate_snapshot_on_event_change will recompute.
    """
    __tablename__ = "kpi_snapshots"
    __table_args__ = (
        UniqueConstraint("farm_id", "period_type", "period_start"),
        Index("idx_kpi_snap_farm_period", "farm_id", "period_type", "period_start"),
        Index("idx_kpi_snap_stale", "is_stale", postgresql_where="is_stale = TRUE"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False)  # DAILY/WEEKLY/MONTHLY/ANNUAL
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Base KPIs
    psy: Mapped[float | None] = mapped_column(Numeric(6, 2))
    msy: Mapped[float | None] = mapped_column(Numeric(6, 2))
    npd: Mapped[float | None] = mapped_column(Numeric(6, 2))
    mortality_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))

    # Addon #1 KPIs (only populated when ADDON_FCR subscribed)
    fcr: Mapped[float | None] = mapped_column(Numeric(5, 3))
    avg_daily_gain: Mapped[float | None] = mapped_column(Numeric(6, 2))

    # Headcounts
    active_sow_count: Mapped[int | None] = mapped_column(Integer)
    gestating_count: Mapped[int | None] = mapped_column(Integer)
    lactating_count: Mapped[int | None] = mapped_column(Integer)

    is_stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FinisherGroup(Base):
    """
    Grow-finish pig batch. FCR is calculated at group level, not individual sow.
    feed_records.group_id and health_events.group_id reference this table.
    """
    __tablename__ = "finisher_groups"
    __table_args__ = (
        UniqueConstraint("farm_id", "group_code"),
        Index("idx_fg_farm_active", "farm_id", "start_date", postgresql_where="deleted_at IS NULL"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    building_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("buildings.id"))
    group_code: Mapped[str] = mapped_column(String(30), nullable=False)
    batch_name: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    head_count_in: Mapped[int] = mapped_column(Integer, nullable=False)
    head_count_out: Mapped[int | None] = mapped_column(Integer)
    avg_entry_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    avg_exit_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ApiKey(Base):
    """
    B2B API key auth — separate from JWT.
    Used by PigSignal B2B API clients (feed companies, insurers, slaughterhouses).
    Store SHA256(full_key); never store raw key after issuance.
    """
    __tablename__ = "api_keys"
    __table_args__ = (Index("idx_api_keys_org", "org_id", postgresql_where="is_active = TRUE"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)   # display: "pk_live_"
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    # ['pig_supply_forecast', 'pig_cost_index', 'pig_risk_signal']
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Notification(Base):
    """
    Rule Engine alert delivery tracking.
    One row per delivery attempt per channel.
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notif_user_unread", "user_id", "created_at",
              postgresql_where="read_at IS NULL"),
        Index("idx_notif_farm", "farm_id", "created_at",
              postgresql_where="farm_id IS NOT NULL"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"))
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # PUSH/EMAIL/SMS/IN_APP
    channel: Mapped[str | None] = mapped_column(String(30))        # FCM/APNS/KAKAOTALK…
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    alert_type: Mapped[str | None] = mapped_column(String(50))
    # NPD_OVERDUE / FARROWING_DUE / WEANING_DUE / KPI_CRITICAL / SYSTEM
    severity: Mapped[str | None] = mapped_column(String(10))       # INFO/WARNING/CRITICAL
    related_entity_type: Mapped[str | None] = mapped_column(String(50))
    related_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncConflictQueue(Base):
    """
    Unresolvable sync conflicts requiring user intervention.
    Only DUPLICATE_EVENT (different date) and CYCLE_CONFLICT (different batch) land here.
    Auto-resolved conflicts (LWW merge) are never stored here.
    """
    __tablename__ = "sync_conflict_queue"
    __table_args__ = (
        Index("idx_conflict_queue_farm_unresolved", "farm_id", "created_at",
              postgresql_where="resolved_at IS NULL"),
        Index("idx_conflict_queue_farm_all", "farm_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    client_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    conflict_type: Mapped[str] = mapped_column(String(30), nullable=False)
    client_record: Mapped[dict] = mapped_column(JSONB, nullable=False)
    server_record: Mapped[dict] = mapped_column(JSONB, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution: Mapped[str | None] = mapped_column(String(20))  # CLIENT_WINS / SERVER_WINS / DISCARDED
    resolved_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncLog(Base):
    """
    Offline sync session history.
    sync_queue = pending items, sync_logs = completed sessions.
    """
    __tablename__ = "sync_logs"
    __table_args__ = (
        Index("idx_sync_logs_farm", "farm_id", "started_at"),
        Index("idx_sync_logs_device", "device_id", "started_at"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    sync_direction: Mapped[str] = mapped_column(String(15), nullable=False)
    # PUSH / PULL / BIDIRECTIONAL
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_pushed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_pulled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflicts_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conflicts_resolved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_detail: Mapped[dict | None] = mapped_column(JSONB)
    duration_ms: Mapped[int | None] = mapped_column(Integer)


class LlmUsageLog(Base):
    """
    Addon #1 (AI Insight) LLM call log — per farm per month, for quota enforcement.
    chat_service counts current-month rows to decide template fallback.
    """
    __tablename__ = "llm_usage_logs"
    __table_args__ = (Index("idx_llm_usage_farm_month", "farm_id", "year", "month"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50))
    tokens: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
