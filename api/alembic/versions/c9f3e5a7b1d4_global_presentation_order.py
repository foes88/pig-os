"""GLOBAL 표현 순서 시드 — Presentation Policy 전환 시 카드 순서 보존

GLOBAL CKP seed 14행은 display_order 가 전부 NULL 이라 정렬이 kpi_code ASC 로 떨어진다.
그대로 배포하면 비-BR 농장의 카드 순서가 알파벳순으로 바뀐다(리허설에서 검출).
현행 순서를 데이터로 기록해 동작을 보존한다 — 신규 정책이 아니다.

시드 값 SSOT: app/db/global_presentation_seed.py

Revision ID: c9f3e5a7b1d4
Revises: b8e2d4f6a0c3
"""
import uuid

import sqlalchemy as sa

from alembic import op
from app.db.global_presentation_seed import GLOBAL_DISPLAY_ORDER, presentation_rows

revision = "c9f3e5a7b1d4"
down_revision = "b8e2d4f6a0c3"
branch_labels = None
depends_on = None

_CKPRES = sa.table(
    "country_kpi_presentation",
    sa.column("id"), sa.column("scope_level"), sa.column("country_code"), sa.column("kpi_code"),
    sa.column("display_order"), sa.column("display_order_override"), sa.column("local_label"),
    sa.column("decision_status"), sa.column("note"),
)


def upgrade() -> None:
    op.bulk_insert(_CKPRES, [dict(id=uuid.uuid4(), **r) for r in presentation_rows()])


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM country_kpi_presentation WHERE scope_level = 'GLOBAL' "
                "AND kpi_code = ANY(:codes)")
        .bindparams(sa.bindparam("codes", value=[c for c, _ in GLOBAL_DISPLAY_ORDER],
                                 type_=sa.ARRAY(sa.String)))
    )
