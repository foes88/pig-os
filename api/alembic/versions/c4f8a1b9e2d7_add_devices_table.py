"""add devices table (G2 push token registration)

Revision ID: c4f8a1b9e2d7
Revises: b7e1c9d3a4f2
Create Date: 2026-06-16
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c4f8a1b9e2d7"
down_revision: str | None = "b7e1c9d3a4f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", sa.String(10), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("app_version", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_device_token", "devices", ["token"])
    op.create_index(
        "idx_device_user_active", "devices", ["user_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_device_user_active", table_name="devices")
    op.drop_constraint("uq_device_token", "devices", type_="unique")
    op.drop_table("devices")
