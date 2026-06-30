"""
Health module: health_events, feed_records, removals.
"""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HealthEvent(Base):
    __tablename__ = "health_events"
    __table_args__ = (
        Index("idx_health_farm_date", "farm_id", "event_date"),
        # XOR: sow_id IS NOT NULL OR group_id IS NOT NULL (enforced in DB)
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"))
    group_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))  # finisher group
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # DISEASE / INJURY / OBSERVATION / DEATH / CULLING
    disease_code: Mapped[str | None] = mapped_column(String(50))
    severity: Mapped[str | None] = mapped_column(String(20))  # MILD / MODERATE / SEVERE / FATAL
    treatment: Mapped[str | None] = mapped_column(String(200))
    drug_code: Mapped[str | None] = mapped_column(String(50))
    dose_ml: Mapped[float | None] = mapped_column(Numeric(8, 2))
    # QA #5 (MIGRATION-PENDING a1c3e5b7d9f2): sync가 notes에 보존하던 백신/약물 정식 컬럼화.
    # dose_mg는 질량(mg)으로 dose_ml(부피)과 단위 불호환 → 별도 컬럼.
    vaccine_code: Mapped[str | None] = mapped_column(String(50))
    active_substance: Mapped[str | None] = mapped_column(String(100))
    dose_mg: Mapped[float | None] = mapped_column(Numeric(8, 2))
    withdrawal_days: Mapped[int | None] = mapped_column(Integer)
    head_count: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FeedRecord(Base):
    __tablename__ = "feed_records"
    __table_args__ = (Index("idx_feed_farm_date", "farm_id", "record_date"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"))
    group_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    building_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("buildings.id"))
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    feed_type: Mapped[str | None] = mapped_column(String(50))
    quantity_kg: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(10, 4))
    currency: Mapped[str | None] = mapped_column(String(3))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Removal(Base):
    __tablename__ = "removals"
    __table_args__ = (Index("idx_removals_farm_date", "farm_id", "removal_date"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    removal_date: Mapped[date] = mapped_column(Date, nullable=False)
    removal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # CULL / DEAD / SOLD / TRANSFER
    reason_category: Mapped[str | None] = mapped_column(String(30))
    # REPRODUCTIVE / LAMENESS / DISEASE / AGE / PERFORMANCE / INJURY / BEHAVIOR / UNKNOWN / OTHER
    reason_detail: Mapped[str | None] = mapped_column(Text)
    body_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    sale_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    sale_currency: Mapped[str | None] = mapped_column(String(3))
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
