"""seed KR PigPlan thresholds for expanded rule metrics (region scope)

Phase A — PigPlan(KR) 실측 임계를 default_metric_values(region/KR)에 주입.
출처: handoff/pigplan-rules 본문 전수 추출(위조 0). 기존 KR 행(PSY/NPD/분만율/WSI/RTS/
실산/이유두수/포유폐사, 한돈팜스2023·PigPlan)은 보존 — 여기선 KR 행이 없던 지표만 추가.

제외(코드 기본값 유지): MUMMIFIED_RATE·ADG·FINISH_MORTALITY·WEANING_AGE_HIGH(KR 소스 없음),
BIRTH_WEIGHT(개체 LBW 컷오프≠복평균, 의미 불일치), TOTAL_BORN(직접 총산 밴드 없음, 저신뢰).
critical 미정 행은 NULL → 엔진 resolve()가 코드 기본 critical로 폴백.

Revision ID: f7b9d1c3e5a8
Revises: e5a7c9b1d3f6
"""
from alembic import op

revision = "f7b9d1c3e5a8"
down_revision = "e5a7c9b1d3f6"
branch_labels = None
depends_on = None

# (code, direction, warn, crit, target, avg, top25, unit, source, confidence)
ROWS = [
    ("STILLBORN_RATE",    "above", 8.0,  12.0, 5.0,  None, None, "%",     "PigPlan:PIGLET_DEATH_KPI_V1", "high"),
    ("ABORTION_RATE",     "above", 10.0, 15.0, None, 9.0,  None, "%",     "PigPlan:ACCIDENT_BENCHMARK",  "high"),
    ("FCR",               "above", 3.0,  3.2,  2.5,  2.7,  None, "ratio", "PigPlan:FCR_FINISHING",       "high"),
    ("CULLING_RATE",      "above", 50.0, None, 40.0, 38.0, None, "%",     "PigPlan:CULLING_BENCHMARK",   "high"),
    ("SOW_MORTALITY",     "above", 10.0, None, None, 9.0,  None, "%",     "PigPlan:CULLING_BENCHMARK",   "medium"),
    ("HIGH_PARITY_RATIO", "above", 15.0, 20.0, 10.0, None, None, "%",     "PigPlan:PARITY_STRUCTURE",    "high"),
    ("WEANING_WEIGHT",    "below", 6.5,  5.0,  6.5,  None, None, "kg",    "PigPlan:CAUSAL_CHAIN_MAP",    "medium"),
    ("WEANING_AGE_LOW",   "below", 21.0, None, 21.0, None, None, "days",  "PigPlan:REPRODUCTION",        "high"),
]

_CODES = "', '".join(r[0] for r in ROWS)


def _v(x):
    return "NULL" if x is None else (f"'{x}'" if isinstance(x, str) else str(x))


def upgrade() -> None:
    for (code, direction, warn, crit, target, avg, top25, unit, source, conf) in ROWS:
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, benchmark_avg, benchmark_top25,
                 target_value, warning_threshold, critical_threshold, alert_direction,
                 unit_code, confidence, is_proxy, source_ref)
            VALUES
                ('region', 'KR', '{code}', {_v(avg)}, {_v(top25)},
                 {_v(target)}, {_v(warn)}, {_v(crit)}, '{direction}', '{unit}',
                 '{conf}', FALSE, '{source}')
            ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE SET
                benchmark_avg = EXCLUDED.benchmark_avg,
                benchmark_top25 = EXCLUDED.benchmark_top25,
                target_value = EXCLUDED.target_value,
                warning_threshold = EXCLUDED.warning_threshold,
                critical_threshold = EXCLUDED.critical_threshold,
                alert_direction = EXCLUDED.alert_direction,
                unit_code = EXCLUDED.unit_code,
                confidence = EXCLUDED.confidence,
                is_proxy = EXCLUDED.is_proxy,
                source_ref = EXCLUDED.source_ref
            """
        )


def downgrade() -> None:
    op.execute(
        f"DELETE FROM default_metric_values WHERE scope_type='region' "
        f"AND scope_code='KR' AND metric_code IN ('{_CODES}')"
    )
