"""
Core reproductive events: matings, farrowings, weanings,
reproductive_events (returns/abortions), piglet_events (foster/death).
"""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Mating(Base):
    __tablename__ = "matings"
    __table_args__ = (
        Index("idx_matings_farm_sow", "farm_id", "sow_id"),
        Index("idx_matings_farm_created", "farm_id", "created_at"),  # admin data-monitor
        Index("idx_matings_date", "farm_id", "mating_date"),
        # NPD(v_sow_npd LATERAL)가 sow_id로 다음 교배를 조회 → by-sow 인덱스 없으면 대형농장
        # 스캔(대시보드 타임아웃 근인, 2026-07). farm 스코프 인덱스는 sow_id 단독 조회에 안 걸림.
        Index("idx_matings_sow_date", "sow_id", "mating_date"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    boar_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("boars.id"))
    breeding_cycle_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("breeding_cycles.id"))
    mating_date: Mapped[date] = mapped_column(Date, nullable=False)
    mating_type: Mapped[str] = mapped_column(String(10), nullable=False)  # AI / NATURAL
    mating_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1~5
    semen_batch: Mapped[str | None] = mapped_column(String(50))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # #7: 서버측 수정분 pull 감지
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PregnancyCheck(Base):
    __tablename__ = "pregnancy_checks"
    __table_args__ = (Index("idx_pc_farm", "farm_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    mating_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("matings.id"))
    check_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_after_mating: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # POSITIVE / NEGATIVE / UNCERTAIN
    method: Mapped[str | None] = mapped_column(String(30))  # ULTRASOUND / VISUAL / BLOOD_TEST
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # #7: 서버측 수정분 pull 감지
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Farrowing(Base):
    __tablename__ = "farrowings"
    __table_args__ = (
        Index("idx_farrowings_farm_sow", "farm_id", "sow_id"),
        Index("idx_farrowings_farm_created", "farm_id", "created_at"),  # admin data-monitor
        Index("idx_farrowings_date", "farm_id", "farrowing_date"),
        # 분만율 코호트(mating LEFT JOIN farrowing ON mating_id)가 mating_id로 조회 →
        # 인덱스 없으면 대형농장 스캔(대시보드 지연, 2026-07).
        Index("idx_farrowings_mating", "mating_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    mating_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("matings.id"), nullable=False)
    breeding_cycle_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("breeding_cycles.id"))
    farrowing_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_born: Mapped[int] = mapped_column(Integer, nullable=False)
    born_alive: Mapped[int] = mapped_column(Integer, nullable=False)
    stillborn: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mummified: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Constraint: total_born = born_alive + stillborn + mummified (enforced in DB trigger)
    # 포유개시두수 — 초기값 = born_alive, 양자 이동(piglet_event) 시 집계로 갱신 (P0-BE-4)
    nursing_head: Mapped[int | None] = mapped_column(Integer)
    avg_birth_weight_kg: Mapped[float | None] = mapped_column()  # 평균 출생체중(kg), 검증 ≤3.0 (P0-BE-6)
    farrowing_ease: Mapped[str | None] = mapped_column(String(20))  # EASY / ASSISTED / DIFFICULT
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # #7: 서버측 수정분 pull 감지
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    piglet_events: Mapped[list["PigletEvent"]] = relationship(
        back_populates="farrowing",
        foreign_keys="[PigletEvent.farrowing_id]",
    )
    weaning: Mapped["Weaning | None"] = relationship(back_populates="farrowing")


class Weaning(Base):
    __tablename__ = "weanings"
    __table_args__ = (
        Index("idx_weanings_farm_sow", "farm_id", "sow_id"),
        Index("idx_weanings_farm_created", "farm_id", "created_at"),  # admin data-monitor
        # PSY/NPD/리포트/대시보드가 farm_id+weaning_date로 집계 → 대형농장(수만건) seq scan 방지.
        Index("idx_weanings_farm_date", "farm_id", "weaning_date", postgresql_where="deleted_at IS NULL"),
        # WSI 상관 서브쿼리(build_herd_kpis)가 sow_id로 직전 이유일을 조회 → by-sow 인덱스 필수
        # (대형농장 대시보드 40s→<1s, 2026-07). farm 스코프 인덱스는 sow_id 단독 조회에 안 걸림.
        Index("idx_weanings_sow_date", "sow_id", "weaning_date"),
        # NOTE: 분만당 이유 1건 unique 인덱스는 두지 않는다. 부분이유(partial weaning)는
        # 한 분만에 대해 이유 이벤트가 여러 건 생기는 것을 허용하므로(일부 먼저, 나머지 나중)
        # farrowing_id 단일 unique 는 기능과 모순된다. 과다이유(sum>litter) 방어는
        # record_weaning 의 remaining 검사(앱 레벨)로 처리. (구 주석의 stale 불변식 폐기)
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    farrowing_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farrowings.id"), nullable=False)
    breeding_cycle_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("breeding_cycles.id"))
    weaning_date: Mapped[date] = mapped_column(Date, nullable=False)
    weaned_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weaning_age_days: Mapped[int | None] = mapped_column(Integer)  # auto-computed by DB trigger
    avg_weaning_weight_kg: Mapped[float | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # #7: 서버측 수정분 pull 감지
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    farrowing: Mapped["Farrowing"] = relationship(back_populates="weaning")


class ReproductiveEvent(Base):
    """
    Non-productive events: return to estrus, abortion, empty, culled, dead.
    Used for NPD calculation accuracy. Mirrors PigPlan TB_SAGO.
    """
    __tablename__ = "reproductive_events"
    __table_args__ = (
        Index("idx_re_farm_sow", "farm_id", "sow_id"),
        Index("idx_re_mating", "mating_id", postgresql_where="mating_id IS NOT NULL"),
        # 알림(RTS/HEAT)·NPD가 farm_id+event_date로 집계 → 대형농장 seq scan 방지.
        Index("idx_re_farm_date", "farm_id", "event_date"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    mating_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("matings.id"))
    breeding_cycle_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("breeding_cycles.id"))
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # RETURN_TO_ESTRUS / ABORTION / EMPTY / INFERTILE / CULLED / DEAD / TRANSFER_OUT / SOLD / HEAT_DETECTED
    detected_method: Mapped[str | None] = mapped_column(String(20))
    # ULTRASOUND / VISUAL / BEHAVIOR / BLOOD_TEST
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # #7: 서버측 수정분 pull 감지
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PigletEvent(Base):
    """
    In-lactation piglet movements: foster in/out, deaths.
    Used for weaned count integrity: born_alive + foster_in - foster_out - deaths = weaned.
    """
    __tablename__ = "piglet_events"
    __table_args__ = (
        Index("idx_pe_farrowing", "farrowing_id"),
        Index("idx_piglet_farm_created", "farm_id", "created_at"),  # admin data-monitor
        Index("idx_pe_farm_date", "farm_id", "event_date"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    farrowing_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farrowings.id"), nullable=False)
    sow_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # STILLBORN_REMOVAL / DEATH / FOSTER_IN / FOSTER_OUT
    piglet_count: Mapped[int] = mapped_column(Integer, nullable=False)
    age_days: Mapped[int | None] = mapped_column(Integer)  # 자돈 일령 = event_date - farrowing_date (P0-BE-5)
    reason: Mapped[str | None] = mapped_column(String(50))
    # CRUSHING / SCOURS / STARVATION / CONGENITAL / HYPOTHERMIA / OTHER
    target_sow_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sows.id"))
    target_farrowing_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farrowings.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # #7: 서버측 수정분 pull 감지
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    farrowing: Mapped["Farrowing"] = relationship(
        back_populates="piglet_events",
        foreign_keys=[farrowing_id],
    )
