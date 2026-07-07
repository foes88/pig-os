"""handoff #4·#5: piglet_transfers.deleted_at + health_events 정식 약물/백신 컬럼

Revision ID: a1c3e5b7d9f2
Revises: b8e2c4f60a91
Create Date: 2026-07-01

MIGRATION-PENDING: DB 미적용 상태로 작성. `alembic upgrade head`로 적용 후 모델/코드 활성화.
- #4 PigletTransfer.deleted_at: 삭제경로(delete_sow/farrowing) 캐스케이드 가능케 함(현재 hard 잔존).
- #5 health_events: sync가 notes에 보존하던 vaccine_code/active_substance/dose_mg를 정식 컬럼화.
  (기존 drug_code/dose_ml/treatment와 별개 — dose_mg는 질량(mg), dose_ml는 부피(ml)로 단위 불호환이라 별도 컬럼.)
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1c3e5b7d9f2"
down_revision: str | None = "b8e2c4f60a91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # #4 PigletTransfer soft-delete
    op.add_column("piglet_transfers", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    # #5 health_events 정식 백신/약물 컬럼(sync notes → 컬럼)
    op.add_column("health_events", sa.Column("vaccine_code", sa.String(length=50), nullable=True))
    op.add_column("health_events", sa.Column("active_substance", sa.String(length=100), nullable=True))
    op.add_column("health_events", sa.Column("dose_mg", sa.Numeric(8, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("health_events", "dose_mg")
    op.drop_column("health_events", "active_substance")
    op.drop_column("health_events", "vaccine_code")
    op.drop_column("piglet_transfers", "deleted_at")
