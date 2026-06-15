"""add tasks table (Phase 2 auto-assign)

Revision ID: b7e1c9d3a4f2
Revises: f1a2b3c4d5e6
Create Date: 2026-06-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b7e1c9d3a4f2"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id"), nullable=False),
        sa.Column("sow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sows.id"), nullable=True),
        sa.Column("task_type", sa.String(40), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("action", sa.String(200), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="OPEN"),
        sa.Column("priority", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("overdue_days", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_tasks_farm_status", "tasks", ["farm_id", "status"])
    op.create_index(
        "idx_tasks_assigned", "tasks", ["assigned_to", "status"],
        postgresql_where=sa.text("status = 'OPEN'"),
    )
    # 멱등 생성용: 같은 농장·모돈·유형의 OPEN task는 1개만
    op.create_unique_constraint(
        "uq_task_open_per_sow_type", "tasks", ["farm_id", "sow_id", "task_type", "status"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_task_open_per_sow_type", "tasks", type_="unique")
    op.drop_index("idx_tasks_assigned", table_name="tasks")
    op.drop_index("idx_tasks_farm_status", table_name="tasks")
    op.drop_table("tasks")
