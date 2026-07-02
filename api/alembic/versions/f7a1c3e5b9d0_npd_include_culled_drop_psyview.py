"""v_sow_npd: 도태(소프트삭제) 모돈의 과거 이유 이력도 NPD에 포함 + 죽은 v_farm_psy 드롭

C2: 기존 v_sow_npd는 WHERE s.deleted_at IS NULL로 소프트삭제된 모돈을 통째 제외했음. 도폐사는
cull_sow가 소프트삭제(deleted_at)하므로, 도태 모돈이 도태 전 남긴 이유→재교배 이력(윈도우 내)이
NPD에서 빠져 표본이 급감(라이브: 대상 농장 249두 중 211두 소프트삭제 → NPD가 1/41 표본).
완료된 이유는 사실이므로 sow deleted_at 필터를 제거(weaning/mating의 deleted_at 필터는 유지).
C6: 더 이상 사용하지 않는 v_farm_psy(분모 오류가 있던 옛 뷰) 드롭 — BI/수기 쿼리 오염 방지.

Revision ID: f7a1c3e5b9d0
Revises: e5c9d1a3f7b8
"""
from alembic import op

revision = "f7a1c3e5b9d0"
down_revision = "e5c9d1a3f7b8"
branch_labels = None
depends_on = None

_NPD_NEW = """
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
"""

_NPD_OLD = """
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


def upgrade() -> None:
    op.execute(_NPD_NEW)
    op.execute("DROP VIEW IF EXISTS v_farm_psy")


def downgrade() -> None:
    op.execute(_NPD_OLD)
    # v_farm_psy 재생성은 생략(앱 미사용, 복원 불필요)
