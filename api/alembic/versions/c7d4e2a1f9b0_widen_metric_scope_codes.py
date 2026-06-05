"""widen_metric_scope_codes

Revision ID: c7d4e2a1f9b0
Revises: b6f6e3a9c2d1
Create Date: 2026-06-05 14:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c7d4e2a1f9b0"
down_revision: Union[str, None] = "b6f6e3a9c2d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "default_metric_values",
        "scope_code",
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=False,
    )
    op.alter_column(
        "scope_kpi_recommendations",
        "scope_code",
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute("DELETE FROM default_metric_values WHERE LENGTH(scope_code) > 20")
    op.execute("DELETE FROM scope_kpi_recommendations WHERE LENGTH(scope_code) > 20")
    op.alter_column(
        "scope_kpi_recommendations",
        "scope_code",
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.alter_column(
        "default_metric_values",
        "scope_code",
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
