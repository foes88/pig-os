"""
Platform module: multi-tenancy, auth, audit.
Tables: organizations, farms, users, user_farms, audit_log, sync_queue,
        refresh_tokens, addon_subscriptions
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    """
    계층 구조: VENDOR → DISTRIBUTOR → DEALER → INDEPENDENT(농가 직접 가입)
    parent_org_id: NULL = 최상위(업체). 하위 조직은 parent_org_id 설정.
    org_level: 0=VENDOR, 1=DISTRIBUTOR, 2=DEALER, 3=INDEPENDENT
    """
    __tablename__ = "organizations"
    __table_args__ = (
        Index("idx_org_parent", "parent_org_id", postgresql_where=text("parent_org_id IS NOT NULL")),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    org_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="INDEPENDENT"
    )  # VENDOR | DISTRIBUTOR | DEALER | INDEPENDENT
    org_level: Mapped[int] = mapped_column(SmallInteger(), nullable=False, default=0)
    parent_org_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    parent: Mapped["Organization | None"] = relationship(
        "Organization", remote_side="Organization.id", back_populates="children"
    )
    children: Mapped[list["Organization"]] = relationship("Organization", back_populates="parent")
    farms: Mapped[list["Farm"]] = relationship(back_populates="organization")
    users: Mapped[list["User"]] = relationship(back_populates="organization")


class Farm(Base):
    __tablename__ = "farms"
    __table_args__ = (
        Index("idx_farms_org", "org_id"),
        Index("idx_farms_country", "country"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    farm_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))
    gps_lat: Mapped[float | None] = mapped_column()
    gps_lng: Mapped[float | None] = mapped_column()
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    unit_system: Mapped[str] = mapped_column(String(10), nullable=False, default="METRIC")
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    date_format: Mapped[str] = mapped_column(String(15), nullable=False, default="yyyy-MM-dd")
    notification_channel: Mapped[str] = mapped_column(String(20), default="EMAIL")
    farm_scale: Mapped[str] = mapped_column(String(15), default="COMMERCIAL")
    internet_reliability: Mapped[str] = mapped_column(String(10), default="HIGH")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organization: Mapped["Organization"] = relationship(back_populates="farms")
    user_farms: Mapped[list["UserFarm"]] = relationship(back_populates="farm")
    addon_subscriptions: Mapped[list["AddonSubscription"]] = relationship(back_populates="farm")


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id"))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(30), nullable=False, default="FARM_WORKER"
    )  # ADMIN / COMPANY / FARM_OWNER / FARM_MANAGER / FARM_WORKER / VIEWER / API_CLIENT
    system_role: Mapped[str] = mapped_column(
        String(30), nullable=False, default="FARM_OWNER"
    )  # SUPER_ADMIN | VENDOR_ADMIN | DISTRIBUTOR_ADMIN | DEALER_ADMIN | FARM_* | VET | VIEWER | API_CLIENT
    language: Mapped[str] = mapped_column(String(5), default="en")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    organization: Mapped["Organization | None"] = relationship(back_populates="users")
    user_farms: Mapped[list["UserFarm"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class UserFarm(Base):
    __tablename__ = "user_farms"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), primary_key=True)
    role_override: Mapped[str | None] = mapped_column(String(30))

    user: Mapped["User"] = relationship(back_populates="user_farms")
    farm: Mapped["Farm"] = relationship(back_populates="user_farms")


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_farm", "farm_id", "created_at"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    farm_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    # CREATE / UPDATE / DELETE / LOGIN / EXPORT / MONTH_CLOSE
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    old_value: Mapped[dict | None] = mapped_column(JSONB)
    new_value: Mapped[dict | None] = mapped_column(JSONB)
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncQueue(Base):
    __tablename__ = "sync_queue"
    __table_args__ = (
        Index("idx_sync_farm_pending", "farm_id", postgresql_where="synced_at IS NULL"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)  # INSERT / UPDATE / DELETE
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    offline_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    conflict_resolution: Mapped[str | None] = mapped_column(String(20))  # LWW / MANUAL / MERGED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RefreshToken(Base):
    """Stored refresh tokens — enables revocation on logout."""
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("idx_refresh_user", "user_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # store SHA256 hash, never the raw token
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class AddonSubscription(Base):
    """
    Domain gate: which Addons a farm has active.
    Checked by require_addon() dependency — HTTP 402 if missing.
    """
    __tablename__ = "addon_subscriptions"
    __table_args__ = (
        UniqueConstraint("farm_id", "addon_code", name="uq_farm_addon"),
        Index("idx_addon_sub_farm", "farm_id", "is_active"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    farm_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    addon_code: Mapped[str] = mapped_column(String(50), nullable=False)
    # ADDON_FCR / ADDON_HEALTH / ADDON_MARKET / ADDON_BREEDING / ADDON_BIOSECURITY
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    plan_price_usd: Mapped[float | None] = mapped_column()  # 실제 계약 금액
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm: Mapped["Farm"] = relationship(back_populates="addon_subscriptions")
