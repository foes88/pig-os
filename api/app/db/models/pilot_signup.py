import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PilotSignup(Base):
    __tablename__ = "pilot_signups"
    __table_args__ = (
        CheckConstraint(
            "farm_size IN ('under_100','100_500','500_1000','1000_plus')",
            name="ck_pilot_signups_farm_size",
        ),
        CheckConstraint(
            "role IN ('owner','manager','vet','partner')",
            name="ck_pilot_signups_role",
        ),
        CheckConstraint(
            "status IN ('pending','contacted','onboarded','rejected')",
            name="ck_pilot_signups_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # ★ unique=True 를 쓰지 않는다. 실제 유일성은 마이그레이션이 만든
    #   `idx_pilot_signups_email` = UNIQUE INDEX ON (lower(email)) 로 강제된다
    #   — **대소문자를 무시하는** 유일성이라 컬럼 unique 제약과 의미가 다르다.
    #   표현식 인덱스는 alembic 이 모델과 대조하지 못해 env.py 의 비교 제외 목록에 있다.
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    farm_size: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    lang: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
