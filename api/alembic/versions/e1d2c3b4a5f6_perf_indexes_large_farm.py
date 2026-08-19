"""perf indexes for large farms (weanings/re/sows farm+date) + merge 4 heads

대형농장(수만 이벤트)에서 대시보드·PSY·알림 쿼리가 seq scan → 45~90s 타임아웃.
farm_id+날짜 인덱스 추가로 index scan 전환. 동시에 갈라진 4개 alembic head 병합.

Revision ID: e1d2c3b4a5f6
Revises: c1e3f5a7b9d2, c3e5f7a9b1d4, f2b4d6e8a0c1, f7a1c3e5b9d0
Create Date: 2026-07-10
"""
from alembic import op

revision = "e1d2c3b4a5f6"
# DAG 정정: 원래 4개 리프(c1e3·c3e5·f2b4·f7a1)를 직접 물었으나, 같은 리프들이
# 8b817ad8587a(c1e3+f2b4)와 1e6172486c75(c3e5+f7a1)에서 이미 병합돼 있었다.
# 같은 부모를 두 머지가 이중으로 물면 alembic 이 heads 집합에서 두 번 제거를 시도해
# base→head 주행이 KeyError 로 죽는다. 이미 병합된 노드 2개만 문다(적용 순서·집합 동일).
down_revision = ("8b817ad8587a", "1e6172486c75")
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
