"""add threshold metadata to default_metric_values (provenance/confidence)

GPT 리서치 권고 반영: 임계값에 출처/신뢰도/프록시 메타를 함께 저장.
- confidence      : high|medium|low|unknown
- is_proxy        : 프록시(타국/글로벌/표본) 사용 여부
- proxy_type      : top10|best_decile|cooperative|sample|global
- threshold_basis : country_avg|poor_decile|pic_intervention|...
- source_ref      : 기관/연도 (없으면 시드 금지 원칙)

엔진은 기존 effective_metric_values()로 warning/critical/direction을 읽으므로 함수 변경 불필요.
이 컬럼들은 저장·감사·UI 배지(글로벌 기준 등)용.

Revision ID: d5e9c1a3b7f4
Revises: c4f8a1b9e2d7
Create Date: 2026-06-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "d5e9c1a3b7f4"
down_revision: str | None = "c4f8a1b9e2d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE default_metric_values
            ADD COLUMN IF NOT EXISTS confidence      VARCHAR(10),
            ADD COLUMN IF NOT EXISTS is_proxy        BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS proxy_type      VARCHAR(20),
            ADD COLUMN IF NOT EXISTS threshold_basis VARCHAR(40),
            ADD COLUMN IF NOT EXISTS source_ref      VARCHAR(200)
        """
    )


def downgrade() -> None:
    for col in ("confidence", "is_proxy", "proxy_type", "threshold_basis", "source_ref"):
        op.execute(f"ALTER TABLE default_metric_values DROP COLUMN IF EXISTS {col}")
