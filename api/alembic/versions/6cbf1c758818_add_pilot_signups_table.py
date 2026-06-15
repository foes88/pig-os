"""add_pilot_signups_table

Revision ID: 6cbf1c758818
Revises: 1cbe4adb7e13
Create Date: 2026-06-05 08:31:21.880292

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = '6cbf1c758818'
down_revision: str | None = '1cbe4adb7e13'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'pilot_signups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(320), nullable=False),
        sa.Column('farm_size', sa.String(20), nullable=False),
        sa.Column('country', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('lang', sa.String(5), nullable=False, server_default='en'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("farm_size IN ('under_100','100_500','500_1000','1000_plus')", name='ck_pilot_signups_farm_size'),
        sa.CheckConstraint("role IN ('owner','manager','vet','partner')", name='ck_pilot_signups_role'),
        sa.CheckConstraint("status IN ('pending','contacted','onboarded','rejected')", name='ck_pilot_signups_status'),
    )
    op.create_index('idx_pilot_signups_email', 'pilot_signups', [sa.text('lower(email)')], unique=True)


def downgrade() -> None:
    op.drop_index('idx_pilot_signups_email', table_name='pilot_signups')
    op.drop_table('pilot_signups')
