"""perf indexes for large farms (weanings/re/sows farm+date) + merge 4 heads

대형농장(수만 이벤트)에서 대시보드·PSY·알림 쿼리가 seq scan → 45~90s 타임아웃.
farm_id+날짜 인덱스 추가로 index scan 전환. 동시에 갈라진 4개 alembic head 병합.

Revision ID: e1d2c3b4a5f6
Revises: c1e3f5a7b9d2, c3e5f7a9b1d4, f2b4d6e8a0c1, f7a1c3e5b9d0
Create Date: 2026-07-10
"""
from alembic import op

revision = "e1d2c3b4a5f6"
down_revision = ("c1e3f5a7b9d2", "c3e5f7a9b1d4", "f2b4d6e8a0c1", "f7a1c3e5b9d0")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IF NOT EXISTS: 재실행/부분적용 안전(모델 metadata create_all로 이미 있을 수 있음).
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_weanings_farm_date "
        "ON weanings (farm_id, weaning_date) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_re_farm_date "
        "ON reproductive_events (farm_id, event_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sows_farm_entry "
        "ON sows (farm_id, entry_date)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_sows_farm_entry")
    op.execute("DROP INDEX IF EXISTS idx_re_farm_date")
    op.execute("DROP INDEX IF EXISTS idx_weanings_farm_date")
