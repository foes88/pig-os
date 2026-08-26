"""스키마 드리프트 해소 — 운영의 수동 보정을 마이그레이션으로 정본화

독립검증(2026-08-25)에서 `alembic check` 가 실패했다. head 까지 적용한 DB 가 모델과
일치하지 않는다는 뜻이고, 실제 원인은 **운영에 손으로 만든 객체가 마이그레이션에
없다**는 것이었다.

★ 왜 위험한가: 재해복구·새 환경 구축은 마이그레이션만 돌린다. 운영에만 손으로 있는
  것은 그때 재현되지 않는다. 즉 "복구했는데 인덱스가 없어서 대시보드가 느리다"거나
  "컬럼이 없어서 앱이 죽는다"가 된다. 통합 테스트는 Base.metadata.create_all() 을
  쓰기 때문에 이 결함을 **숨기고 있었다** — 테스트는 모델대로 만들어 통과한다.

프로덕션 실측(2026-08-25):

| 객체 | 모델 | 운영 | 마이그레이션 |
|---|---|---|---|
| farms.data_origin / data_classification | 있음 | **손으로 있음** | 없음 |
| idx_farrowings_mating / matings·weanings·removals _sow_date | 있음 | **손으로 있음** | 없음 |
| idx_farms_classification | 있음 | **없음** | 없음 |
| devices·tasks·llm_usage_logs·password_reset_tokens·operational_defaults .created_at NOT NULL | NOT NULL | **nullable** | 없음 |

전부 IF NOT EXISTS / 조건부로 쓴다 — 운영에는 이미 있는 것이 대부분이라 재실행 안전성이
필수다(운영은 이 마이그레이션으로 사실상 idx_farms_classification 과 NOT NULL 만 바뀐다).

Revision ID: f3c6a8d0b2e4
Revises: e2b5d7c9a1f3
Create Date: 2026-08-25
"""
from alembic import op

revision = "f3c6a8d0b2e4"
down_revision = "e2b5d7c9a1f3"
branch_labels = None
depends_on = None

# 운영에 손으로 만들어져 있던 인덱스들 — 정의는 운영 실물과 모델 선언이 일치함을 확인했다.
_INDEXES = (
    ("idx_farms_classification", "farms (data_classification, data_origin)"),
    ("idx_farrowings_mating", "farrowings (mating_id)"),
    ("idx_matings_sow_date", "matings (sow_id, mating_date)"),
    ("idx_weanings_sow_date", "weanings (sow_id, weaning_date)"),
    ("idx_removals_sow_date", "removals (sow_id, removal_date)"),
)

# 모델은 NOT NULL 인데 DB 는 nullable 인 (테이블, 컬럼, 채울 값).
# ★ 값을 먼저 채우고 제약을 건다 — 순서를 바꾸면 기존 NULL 행 때문에 실패한다.
#   server_default 가 있어 실제 NULL 은 없어야 하지만, default 없이 들어간 과거 행을
#   가정하고 방어한다(마이그레이션은 재실행·복구 환경에서도 돌아야 한다).
_NOT_NULL: tuple[tuple[str, str, str], ...] = (
    ("devices", "created_at", "now()"),
    ("tasks", "created_at", "now()"),
    ("llm_usage_logs", "created_at", "now()"),
    ("password_reset_tokens", "created_at", "now()"),
    ("operational_defaults", "created_at", "now()"),
    ("country_kpi_presentation", "created_at", "now()"),
    ("country_kpi_presentation", "updated_at", "now()"),
    ("benchmarks", "created_at", "now()"),
    ("benchmarks", "production_system", "'ALL'"),
    ("benchmarks", "farm_size_band", "'ALL'"),
    ("benchmarks", "benchmark_status", "'DRAFT'"),
    ("benchmarks", "is_provisional", "false"),
    ("source_observations", "is_provisional", "false"),
)


def upgrade() -> None:
    # ── farms 분류 컬럼 ──────────────────────────────────────────────────────
    # 하베스트 산물과 실고객을 구분하는 값이다. 운영에는 손으로 들어가 있다.
    op.execute(
        "ALTER TABLE farms ADD COLUMN IF NOT EXISTS "
        "data_origin VARCHAR(20) NOT NULL DEFAULT 'native_signup'"
    )
    op.execute(
        "ALTER TABLE farms ADD COLUMN IF NOT EXISTS "
        "data_classification VARCHAR(20) NOT NULL DEFAULT 'live_customer'"
    )

    for name, target in _INDEXES:
        op.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {target}")

    # ── 모델이 NOT NULL 로 선언한 컬럼들 ────────────────────────────────────
    for table, col, fill in _NOT_NULL:
        op.execute(f"UPDATE {table} SET {col} = {fill} WHERE {col} IS NULL")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL")


def downgrade() -> None:
    for table, col, _fill in _NOT_NULL:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL")
    # ★ 인덱스·컬럼은 되돌리지 않는다. 운영에 **이 마이그레이션 이전부터 손으로**
    #   존재하던 것들이라, downgrade 가 지우면 이 마이그레이션이 만들지 않은 객체를
    #   파괴한다. 되돌릴 일이 있으면 해당 객체만 명시적으로 지운다.
