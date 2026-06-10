"""sow status v2 — SCREEN_MENU_SPEC alignment

ACTIVE/GESTATING/WEANED/DRY → GILT/OPEN/PREGNANT/ACCIDENT 데이터 매핑.
docs/SCREEN_MENU_SPEC.md "Sow Status Definitions" 기준:
  GILT / OPEN / PREGNANT / LACTATING / ACCIDENT / CULLED (+DEAD/SOLD/TRANSFER)

매핑 규칙:
  ACTIVE    → 교배 이력 없고 parity=0 이면 GILT, 아니면 OPEN
  GESTATING → PREGNANT
  WEANED    → OPEN
  DRY       → ACCIDENT (EMPTY/INFERTILE 진단 후 재교배 대기)
  LACTATING / CULLED / DEAD / SOLD / TRANSFER* → 유지

Revision ID: d2a8c5e7f1b3
Revises: e3f9a2b4c8d1
Create Date: 2026-06-10
"""
from typing import Sequence, Union

from alembic import op

revision: str = "d2a8c5e7f1b3"
down_revision: Union[str, None] = "e3f9a2b4c8d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ACTIVE → GILT (미교배 미경산) / OPEN (그 외)
    op.execute("""
        UPDATE sows SET status = 'GILT'
        WHERE status = 'ACTIVE'
          AND parity = 0
          AND NOT EXISTS (SELECT 1 FROM matings m WHERE m.sow_id = sows.id)
    """)
    op.execute("UPDATE sows SET status = 'OPEN' WHERE status = 'ACTIVE'")
    op.execute("UPDATE sows SET status = 'PREGNANT' WHERE status = 'GESTATING'")
    op.execute("UPDATE sows SET status = 'OPEN' WHERE status = 'WEANED'")
    op.execute("UPDATE sows SET status = 'ACCIDENT' WHERE status = 'DRY'")
    # 컬럼 default 변경 (ACTIVE → GILT)
    op.execute("ALTER TABLE sows ALTER COLUMN status SET DEFAULT 'GILT'")


def downgrade() -> None:
    op.execute("ALTER TABLE sows ALTER COLUMN status SET DEFAULT 'ACTIVE'")
    op.execute("UPDATE sows SET status = 'DRY' WHERE status = 'ACCIDENT'")
    op.execute("UPDATE sows SET status = 'GESTATING' WHERE status = 'PREGNANT'")
    # OPEN/GILT → ACTIVE (WEANED 구분은 비가역 — ACTIVE로 통합)
    op.execute("UPDATE sows SET status = 'ACTIVE' WHERE status IN ('OPEN', 'GILT')")
