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
import sqlalchemy as sa

from alembic import op

revision = "e2b5d7c9a1f3"
down_revision = "d1a4c6e8b2f5"
branch_labels = None
depends_on = None


_NAME = "idx_farrowings_sow_date"
_WANT = "(sow_id, farrowing_date)"


def upgrade() -> None:
    # IF NOT EXISTS: 장애 대응 중 프로덕션에 CONCURRENTLY 로 먼저 만들어 둔 상태에서도
    # 안전하게 통과해야 한다(재실행·부분적용 안전).
    #
    # ★ 다만 IF NOT EXISTS 는 **이름만** 본다. 같은 이름으로 다른 컬럼 조합의 인덱스가
    #   있으면 조용히 통과해 성능 문제가 그대로 남는다(독립검증 2026-08-25).
    #   그래서 이미 있으면 정의까지 확인한다.
    bind = op.get_bind()
    existing = bind.execute(sa.text(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = current_schema() "
        "AND indexname = :n"), {"n": _NAME}).scalar()
    if existing:
        normalized = existing.replace(" ", "").lower()
        if _WANT.replace(" ", "").lower() not in normalized:
            raise RuntimeError(
                f"{_NAME} 이 이미 있는데 정의가 다릅니다: {existing}. "
                f"기대: ... ON farrowings {_WANT}. "
                "이름만 같고 컬럼이 다르면 NPD LATERAL 이 여전히 느립니다. "
                "기존 인덱스를 확인한 뒤 수동으로 정리하십시오.")
        return

    op.execute(f"CREATE INDEX {_NAME} ON farrowings {_WANT}")


def downgrade() -> None:
    # ★ 이 마이그레이션이 만든 경우에만 지운다. 운영에 손으로 먼저 만들어져 있었다면
    #   upgrade 가 건너뛰었으므로 downgrade 가 지우면 **남의 객체를 파괴**한다.
    #   구분할 방법이 없으므로 안전한 쪽(보존)을 택하고 로그로 알린다.
    # ★ ASCII 로만 쓴다. 콘솔 인코딩(cp949 등)에 따라 print 가 UnicodeEncodeError 로
    #   죽으면 **마이그레이션 자체가 실패**한다(2026-08-25 실측).
    print(f"[downgrade] keeping {_NAME}: cannot tell whether this migration created it. "
          "Drop it manually if you really need to.")
