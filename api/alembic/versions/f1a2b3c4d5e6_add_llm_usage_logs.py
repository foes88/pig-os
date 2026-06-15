"""add llm_usage_logs table (Addon #1 AI Insight quota)

Revision ID: f1a2b3c4d5e6
Revises: d2a8c5e7f1b3
Create Date: 2026-06-10
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "d2a8c5e7f1b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id"), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("intent", sa.String(length=50)),
        sa.Column("tokens", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_llm_usage_farm_month", "llm_usage_logs", ["farm_id", "year", "month"])


def downgrade() -> None:
    op.drop_index("idx_llm_usage_farm_month", table_name="llm_usage_logs")
    op.drop_table("llm_usage_logs")
