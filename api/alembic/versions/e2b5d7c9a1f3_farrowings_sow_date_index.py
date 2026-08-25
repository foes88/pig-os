"""farrowings(sow_id, farrowing_date) 인덱스 — NPD lact_open LATERAL 대형농장 지연

증상: 1만두 농장 대시보드 5.67s. 그중 calculate_npd 가 5.27s, 다시 그중 _NPD_SQL 이 5.34s.
실행계획상 lact_open 의 LATERAL

    SELECT MAX(f.farrowing_date) FROM farrowings f
     WHERE f.sow_id = s.id AND f.deleted_at IS NULL AND f.farrowing_date <= ref

이 모돈마다 돌면서 idx_farrowings_farm_sow(farm_id 선행)를 못 써 3,691ms 를 썼다.
matings 는 idx_matings_sow_date, weanings 는 idx_weanings_sow_date 로 같은 패턴을
이미 처리하고 있었는데(2026-07, e1d2c3b4a5f6 계열) farrowings 만 누락돼 있었다.

실측(프로덕션 데이터 141,359두 / 66농장, 2026-08-25):
    NPD  10,251두 농장   5.447s → 0.269s
    NPD   1,508두 농장   2.634s → 0.056s
    get_dashboard 전체   5.673s → 0.570s

인덱스 추가만 하며 쿼리·정의는 바꾸지 않는다(NPD 값 불변).

Revision ID: e2b5d7c9a1f3
Revises: d1a4c6e8b2f5
Create Date: 2026-08-25
"""
from alembic import op

revision = "e2b5d7c9a1f3"
down_revision = "d1a4c6e8b2f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # IF NOT EXISTS: 장애 대응 중 프로덕션에 CONCURRENTLY 로 먼저 만들어 둔 상태에서도
    # 안전하게 통과해야 한다(재실행·부분적용 안전).
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_farrowings_sow_date "
        "ON farrowings (sow_id, farrowing_date)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_farrowings_sow_date")
