"""country_kpi_policy: display_order 추가 (Presentation Policy STEP B)

같은 표시군 내 카드 정렬 순서. NULL=마지막. 간격 10 규약(10,20,30…)으로
중간 삽입 시 전체 재배열이 불필요하다.

headline은 별도 컬럼을 만들지 않고 priority_class='NORTH_STAR'를 재사용한다
(부분 유니크 uq_ckp_north_star가 이미 국가당 1개를 강제하므로 스키마 무변경).
DISPLAY_ROLES / PRIORITY_CLASSES enum, uq_ckp_north_star 제약은 건드리지 않는다.

Revision ID: f2b4d6a8c1e5
Revises: e3f5a7c9b1d2
"""
import sqlalchemy as sa

from alembic import op

revision = "f2b4d6a8c1e5"
down_revision = "e3f5a7c9b1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("country_kpi_policy", sa.Column("display_order", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("country_kpi_policy", "display_order")
