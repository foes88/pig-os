"""seed KR PigPlan2025 real-data benchmark_avg (region scope) — verified only

R4. KR 전체농가 2025 실데이터(`전체농가_품종별_주요생산성적_2025.xlsx`, n=456)에서 산출한
중앙값(median, 0-inflated 평균 대신)을 region/KR benchmark_avg로 갱신. target/threshold는
기존 PigPlan 확정값 유지(benchmark_avg·source_ref·confidence만 갱신).

검증 출처만(임의 생성 0): 값 산출 근거 `docs/specs/2026-06-17_country-kpi-differences.md`,
원자료 `docs/specs/_pigplan_kr_means.txt`. 출처 미확보(MSY·정의값·모돈도폐사율 등)는 시드하지 않음.

운영 DB 직접 변경 아님 — 마이그레이션 파일만(적용은 사람: `alembic upgrade head`).

Revision ID: b1c2d3e4f5a6
Revises: a8d2f4c6e1b9
Create Date: 2026-06-17
"""
from collections.abc import Sequence

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a8d2f4c6e1b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (metric_code, benchmark_avg [PigPlan2025 median], alert_direction, unit)
# 전부 KR region scope. 기존 행 존재(f3a7c2e9 시드) → benchmark_avg만 갱신.
KR_2025 = [
    ("PSY", 24.73, "below", "두/모돈/년"),
    ("FARROWING_RATE", 83.19, "below", "%"),
    ("BORN_ALIVE", 12.22, "below", "두/복"),
    ("WEANED_COUNT", 10.85, "below", "두/복"),
    ("WSI", 6.30, "above", "일"),
]
SOURCE = "PigPlan2025-xlsx-median-n456"


def upgrade() -> None:
    for metric, avg, direction, unit in KR_2025:
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, benchmark_avg,
                 alert_direction, unit_code, confidence, is_proxy, source_ref)
            VALUES
                ('region', 'KR', '{metric}', {avg},
                 '{direction}', '{unit}', 'high', FALSE, '{SOURCE}')
            ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE SET
                benchmark_avg = EXCLUDED.benchmark_avg,
                confidence    = EXCLUDED.confidence,
                source_ref    = EXCLUDED.source_ref
            """
        )


def downgrade() -> None:
    # benchmark_avg를 NULL로 되돌리진 않음(이전 한돈팜스 값이 손실되므로). source_ref만 표식 제거.
    metrics = "', '".join(m for m, *_ in KR_2025)
    op.execute(
        f"UPDATE default_metric_values SET source_ref = NULL "
        f"WHERE scope_type='region' AND scope_code='KR' "
        f"AND metric_code IN ('{metrics}') AND source_ref='{SOURCE}'"
    )
