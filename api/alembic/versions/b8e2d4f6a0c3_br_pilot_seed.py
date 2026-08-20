"""BR Pilot v1 시드 — COUNTRY 정책(visible 3 / hidden 11) + 표현(순서·현지명)

정본: docs/product/COUNTRY_PRODUCT_SPEC_BR.md v0.3
시드 값은 app/db/br_pilot_seed.py 가 SSOT (마이그레이션·게이트 테스트 공용).

OPTION A: BR 이 표시할 KPI 는 explicit visible, 나머지는 explicit HIDDEN.
GLOBAL 을 암묵 상속해 화면 KPI 가 늘어나지 않게 한다.

Revision ID: b8e2d4f6a0c3
Revises: a7d9c3e5f1b8
"""
import uuid

import sqlalchemy as sa

from alembic import op
from app.db.br_pilot_seed import COUNTRY, policy_rows, presentation_rows

revision = "b8e2d4f6a0c3"
down_revision = "a7d9c3e5f1b8"
branch_labels = None
depends_on = None

_CKP = sa.table(
    "country_kpi_policy",
    sa.column("id"), sa.column("scope_level"), sa.column("country_code"), sa.column("kpi_code"),
    sa.column("compute_enabled"), sa.column("display_role"), sa.column("priority_class"),
    sa.column("decision_status"), sa.column("decided_by"), sa.column("note"),
)
_CKPRES = sa.table(
    "country_kpi_presentation",
    sa.column("id"), sa.column("scope_level"), sa.column("country_code"), sa.column("kpi_code"),
    sa.column("display_order"), sa.column("display_order_override"), sa.column("local_label"),
    sa.column("decision_status"), sa.column("note"),
)


def upgrade() -> None:
    op.bulk_insert(_CKP, [dict(id=uuid.uuid4(), **r) for r in policy_rows()])
    op.bulk_insert(_CKPRES, [dict(id=uuid.uuid4(), **r) for r in presentation_rows()])


def downgrade() -> None:
    for table in ("country_kpi_presentation", "country_kpi_policy"):
        op.execute(
            sa.text(f"DELETE FROM {table} WHERE scope_level = 'COUNTRY' AND country_code = :c")
            .bindparams(c=COUNTRY)
        )
