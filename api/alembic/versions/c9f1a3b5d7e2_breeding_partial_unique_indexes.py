"""번식 무결성 — 모돈 1두당 활성 사이클 1건 partial unique index 추가

모델(sow.py) 주석에 DDL만 적혀있고 실제 마이그레이션이 누락되어 있던
부분 유니크 인덱스를 생성한다. 동시요청(모바일 더블탭/재시도) 시 발생하는
이중 활성 사이클(breeding_cycle)을 DB 레벨에서 차단.

- idx_one_active_cycle : 모돈 1두당 활성 사이클 1건

(주의: '분만 1건당 이유 1건' 인덱스는 두지 않는다 — 부분이유가 한 분만에 대해
 이유 이벤트 다건을 허용하므로. events.py 모델 주석 참고.)

Revision ID: c9f1a3b5d7e2
Revises: b8e2c4f60a91
"""
from alembic import op

revision = "c9f1a3b5d7e2"
down_revision = "b8e2c4f60a91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_cycle "
        "ON breeding_cycles (sow_id) "
        "WHERE cycle_status NOT IN ('WEANED', 'FAILED')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_one_active_cycle")
