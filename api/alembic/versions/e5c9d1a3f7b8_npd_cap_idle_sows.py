"""v_sow_npd: 60일 넘게 미재교배한 유휴 모돈을 NPD 60일 cap으로 포함 (#3)

기존 뷰는 이유 후 60일 내 재교배가 있을 때만 wei_days=간격을 내고, 없으면 NULL →
AVG에서 제외됐음. 그 결과 '가장 비생산적인(오래 놀린) 모돈'이 통째로 빠져 NPD가
과소평가되고 NPD 경고가 사실상 발화하지 않았음(감사 F3). 스펙 §3 엣지표대로
"60일 초과 미재교배 → NPD 60 cap(extended)"를 반영: 이유 후 60일 지났는데 재교배가
없으면 60으로 포함. 아직 60일 미경과(정상 WEI 창)인 이유는 NULL 유지(과대계상 방지).

Revision ID: e5c9d1a3f7b8
Revises: d3b7e1f9a2c4
"""
from alembic import op

revision = "e5c9d1a3f7b8"
down_revision = "d3b7e1f9a2c4"
branch_labels = None
depends_on = None

_NEW = """
CREATE OR REPLACE VIEW v_sow_npd AS
SELECT s.id AS sow_id, s.farm_id, w.id AS weaning_id, w.weaning_date,
       m_next.mating_date AS next_mating_date,
       CASE
           WHEN m_next.mating_date IS NOT NULL THEN LEAST(60, m_next.mating_date - w.weaning_date)
           WHEN w.weaning_date <= CURRENT_DATE - 60 THEN 60
           ELSE NULL
       END AS wei_days
FROM sows s
JOIN weanings w ON w.sow_id = s.id AND w.deleted_at IS NULL
LEFT JOIN LATERAL (
    SELECT m.mating_date FROM matings m
    WHERE m.sow_id = s.id AND m.mating_date > w.weaning_date
      AND m.mating_date <= (w.weaning_date + INTERVAL '60 days') AND m.deleted_at IS NULL
    ORDER BY m.mating_date LIMIT 1
) m_next ON TRUE
WHERE s.deleted_at IS NULL
"""

_OLD = """
CREATE OR REPLACE VIEW v_sow_npd AS
SELECT s.id AS sow_id, s.farm_id, w.id AS weaning_id, w.weaning_date,
       m_next.mating_date AS next_mating_date,
       m_next.mating_date - w.weaning_date AS wei_days
FROM sows s
JOIN weanings w ON w.sow_id = s.id AND w.deleted_at IS NULL
LEFT JOIN LATERAL (
    SELECT m.mating_date FROM matings m
    WHERE m.sow_id = s.id AND m.mating_date > w.weaning_date
      AND m.mating_date <= (w.weaning_date + INTERVAL '60 days') AND m.deleted_at IS NULL
    ORDER BY m.mating_date LIMIT 1
) m_next ON TRUE
WHERE s.deleted_at IS NULL
"""


def upgrade() -> None:
    op.execute(_NEW)


def downgrade() -> None:
    op.execute(_OLD)
