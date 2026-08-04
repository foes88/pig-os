"""이벤트 테이블 (farm_id, created_at) 인덱스 — admin data-monitor 성능

문제: /admin/data-monitor 의 _EVENT_UNION 이 7개 이벤트테이블을 WHERE 없이 풀스캔 +
created_at 무인덱스 → 프로드 164만행에서 8.8초(타임아웃·무데이터). 농장별 max/기간 count가
(farm_id, created_at) 인덱스로 전환되도록 인덱스 추가.

⚠️ 프로드 alembic divergent — 로컬/CI 전용. 프로드는 아래를 무중단으로 별도 적용:
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_matings_farm_created   ON matings(farm_id, created_at);
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_farrowings_farm_created ON farrowings(farm_id, created_at);
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_weanings_farm_created  ON weanings(farm_id, created_at);
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_farm_created    ON health_events(farm_id, created_at);
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_removals_farm_created  ON removals(farm_id, created_at);
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_piglet_farm_created    ON piglet_events(farm_id, created_at);
  CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_feed_farm_created      ON feed_records(farm_id, created_at);

Revision ID: e3f5a7c9b1d2
Revises: c7d9e1f3a5b8
"""
from collections.abc import Sequence

from alembic import op

revision: str = "e3f5a7c9b1d2"
down_revision: str | Sequence[str] | None = "c7d9e1f3a5b8"
branch_labels = None
depends_on = None

_IDX = [
    ("idx_matings_farm_created", "matings"),
    ("idx_farrowings_farm_created", "farrowings"),
    ("idx_weanings_farm_created", "weanings"),
    ("idx_health_farm_created", "health_events"),
    ("idx_removals_farm_created", "removals"),
    ("idx_piglet_farm_created", "piglet_events"),
    ("idx_feed_farm_created", "feed_records"),
]


def upgrade() -> None:
    for name, table in _IDX:
        op.create_index(name, table, ["farm_id", "created_at"], if_not_exists=True)


def downgrade() -> None:
    for name, table in _IDX:
        op.drop_index(name, table_name=table, if_exists=True)
