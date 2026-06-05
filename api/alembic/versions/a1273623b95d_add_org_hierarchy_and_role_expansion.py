"""add_org_hierarchy_and_role_expansion

Revision ID: a1273623b95d
Revises: 6cbf1c758818
Create Date: 2026-06-05 11:48:03.894871

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = 'a1273623b95d'
down_revision: Union[str, None] = '6cbf1c758818'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. organizations: parent_org_id (self-referencing) + org_level
    op.add_column('organizations',
        sa.Column('parent_org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True)
    )
    op.add_column('organizations',
        sa.Column('org_level', sa.SmallInteger(), nullable=False, server_default='0')
    )
    op.create_index('idx_org_parent', 'organizations', ['parent_org_id'],
                    postgresql_where=sa.text('parent_org_id IS NOT NULL'))

    # 2. users: system_role for org-level access (separate from farm role)
    op.add_column('users',
        sa.Column('system_role', sa.String(30), nullable=False, server_default='FARM_OWNER')
    )
    # Migrate existing role values to system_role without silently changing
    # farm-level permissions. Legacy ADMIN becomes the new global admin role.
    op.execute("""
        UPDATE users
        SET system_role = CASE
            WHEN role = 'ADMIN' THEN 'SUPER_ADMIN'
            WHEN role = 'COMPANY' THEN 'VENDOR_ADMIN'
            WHEN role IN (
                'SUPER_ADMIN',
                'VENDOR_ADMIN',
                'DISTRIBUTOR_ADMIN',
                'DEALER_ADMIN',
                'FARM_OWNER',
                'FARM_MANAGER',
                'FARM_WORKER',
                'VET',
                'VIEWER',
                'API_CLIENT'
            ) THEN role
            ELSE 'FARM_OWNER'
        END
    """)

    op.create_index('idx_users_system_role', 'users', ['system_role'])


def downgrade() -> None:
    # Preserve system_role values back into the legacy role column before dropping.
    # SUPER_ADMIN → ADMIN, VENDOR_ADMIN → COMPANY, all others kept as-is.
    op.execute("""
        UPDATE users
        SET role = CASE
            WHEN system_role = 'SUPER_ADMIN' THEN 'ADMIN'
            WHEN system_role = 'VENDOR_ADMIN' THEN 'COMPANY'
            ELSE system_role
        END
    """)
    op.drop_index('idx_users_system_role', table_name='users')
    op.drop_column('users', 'system_role')
    op.drop_index('idx_org_parent', table_name='organizations')
    op.drop_column('organizations', 'org_level')
    op.drop_column('organizations', 'parent_org_id')
