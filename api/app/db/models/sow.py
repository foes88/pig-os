"""
Sow management module: buildings, boars, sows, breeding_cycles, piglet_groups.
"""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = (Index("idx_buildings_farm", "farm_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    building_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # GESTATION / FARROWING / NURSERY / FINISHER / GILT_DEVELOPMENT / ISOLATION / QUARANTINE / STORAGE
    floor_number: Mapped[int] = mapped_column(Integer, default=1)
    capacity: Mapped[int | None] = mapped_column(Integer)
    housing_type: Mapped[str] = mapped_column(String(20), default="GROUP")
    area_per_pig_m2: Mapped[float | None] = mapped_column(Numeric(5, 2))
    area_per_pig_sqft: Mapped[float | None] = mapped_column(Numeric(5, 2))
    prop12_compliant: Mapped[bool | None] = mapped_column(Boolean)
    welfare_enrichment: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Boar(Base):
    __tablename__ = "boars"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    ear_tag: Mapped[str] = mapped_column(String(30), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(50))
    breed_company: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    # ACTIVE / CULLED / DEAD / TRANSFERRED
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_type: Mapped[str | None] = mapped_column(String(20))
    semen_quality: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("farm_id", "ear_tag"),)


class Sow(Base):
    __tablename__ = "sows"
    __table_args__ = (
        Index("idx_sows_farm_status", "farm_id", "status"),
        Index("idx_sows_parity", "farm_id", "parity"),
        Index("idx_sow_exit", "exit_date", postgresql_where="exit_date IS NOT NULL"),
        UniqueConstraint("farm_id", "ear_tag"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    building_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("buildings.id"))
    ear_tag: Mapped[str] = mapped_column(String(30), nullable=False)
    rfid_tag: Mapped[str | None] = mapped_column(String(50))
    parity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    breed: Mapped[str | None] = mapped_column(String(50))
    breed_company: Mapped[str | None] = mapped_column(String(30))
    genetics_id: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="GILT")
    # 번식 상태 머신 — docs/SCREEN_MENU_SPEC.md "Sow Status Definitions" 준수
    # (모바일 sync 프로토콜과 공유 — 값 변경 시 모바일 스펙 협의 필수):
    #   GILT      후보돈(입식, 미교배)                → 교배 가능
    #   OPEN      공태(이유 후 / 경산돈 전입)         → 교배 가능
    #   PREGNANT  임신(교배 기록 시 전이)
    #   LACTATING 포유(분만 기록 시 전이)
    #   ACCIDENT  번식사고(재발/공태판정/유산/불임)   → 교배 가능
    #   CULLED / DEAD / SOLD / TRANSFER  제거(removals 이력 + soft-delete)
    entry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # GILT / PURCHASE / TRANSFER / BORN
    source_farm_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    exit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stall_to_group_converted: Mapped[bool | None] = mapped_column(Boolean)
    nurse_sow_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    ractopamine_free: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    breeding_cycles: Mapped[list["BreedingCycle"]] = relationship(back_populates="sow")


class BreedingCycle(Base):
    """
    Per-parity cycle tracker. Connects matings → farrowings → weanings.
    Active cycle = cycle_status NOT IN ('WEANED', 'FAILED').
    Max 1 active cycle per sow enforced by partial unique index.
    """
    __tablename__ = "breeding_cycles"
    __table_args__ = (
        Index("idx_bc_farm_sow", "farm_id", "sow_id"),
        Index("idx_bc_sow_parity", "sow_id", "parity"),
        # Partial unique index (DDL only — defined in migration):
        # CREATE UNIQUE INDEX idx_one_active_cycle ON breeding_cycles (sow_id)
        # WHERE cycle_status NOT IN ('WEANED', 'FAILED');
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    parity: Mapped[int] = mapped_column(Integer, nullable=False)
    cycle_status: Mapped[str] = mapped_column(String(20), nullable=False, default="MATED")
    # MATED / CONFIRMED / FARROWED / WEANED / FAILED
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    mating_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sow: Mapped["Sow"] = relationship(back_populates="breeding_cycles")


class PigletGroup(Base):
    """
    이유 후 자돈 그룹 (피그플랜 자돈관리 P03).
    개별 개체 추적 없이 그룹 단위로 관리.
    weaning_date → transfer_date 기간이 자돈 사육 기간.
    """
    __tablename__ = "piglet_groups"
    __table_args__ = (
        UniqueConstraint("farm_id", "group_code"),
        Index("idx_pg_farm_active", "farm_id", "weaning_date", postgresql_where="deleted_at IS NULL"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    building_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("buildings.id"))
    group_code: Mapped[str] = mapped_column(String(30), nullable=False)
    batch_name: Mapped[str | None] = mapped_column(String(100))
    weaning_date: Mapped[date] = mapped_column(Date, nullable=False)
    head_count_in: Mapped[int] = mapped_column(Integer, nullable=False)
    head_count_dead: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    head_count_out: Mapped[int | None] = mapped_column(Integer)  # 전출/판매 두수
    avg_entry_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    avg_exit_weight_kg: Mapped[float | None] = mapped_column(Numeric(6, 2))
    transfer_date: Mapped[date | None] = mapped_column(Date)  # 비육사 전출 또는 판매일
    transfer_type: Mapped[str | None] = mapped_column(String(20))
    # FINISHER_TRANSFER / SOLD / CULLED
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PigletTransfer(Base):
    """
    양자/대리모 이벤트 — 모돈 간 자돈 이동.
    분만 기록과 분리: 분만 = 출생(생물학적), 양자 = 포유 중 이동(관리적).
    PSY는 생물학적 산자 기준, 이유두수는 포유 중인 수(양자 반영) 기준으로 각각 계산.
    """
    __tablename__ = "piglet_transfers"
    __table_args__ = (
        Index("idx_pt_farm_date", "farm_id", "transfer_date"),
        Index("idx_pt_source_sow", "source_sow_id"),
        Index("idx_pt_dest_sow", "dest_sow_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    source_sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    dest_sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    source_farrowing_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farrowings.id"))
    dest_farrowing_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farrowings.id"))
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    piglet_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
