"""seed system-scope defaults for expanded rule-engine metrics

확장 Rule Engine(litter/grow-finish/abortion) 신규 metric_code의 **system 스코프** 기본 임계.
- 국가별 위조 아님: confidence='low', is_proxy=TRUE, source='global_clinical_default'.
- 국가(region) 행이 있으면 그 값 우선, 없으면 이 system 기본 → 코드 기본값과 동일.
- /admin/rules + benchmark 화면에서 운영자가 편집 가능(단일 소스).

Revision ID: d4f6a8c0e2b5
Revises: c3d5e7f9a1b3
"""
from alembic import op

revision = "d4f6a8c0e2b5"
down_revision = "c3d5e7f9a1b3"
branch_labels = None
depends_on = None

# (metric_code, direction, target, warn, crit, unit)
ROWS = [
    ("MUMMIFIED_RATE",   "above", 1.5,  2.0,  4.0,  "%"),
    ("ABORTION_RATE",    "above", 2.0,  3.0,  5.0,  "%"),
    ("BIRTH_WEIGHT",     "below", 1.4,  1.3,  1.1,  "kg"),
    ("WEANING_WEIGHT",   "below", 6.0,  5.5,  5.0,  "kg"),
    ("ADG",              "below", 750.0, 650.0, 550.0, "g/day"),
    ("FCR",              "above", 2.7,  3.0,  3.3,  ""),
    ("FINISH_MORTALITY", "above", 3.0,  5.0,  8.0,  "%"),
]

_CODES = "', '".join(r[0] for r in ROWS)


def upgrade() -> None:
    for (code, direction, target, warn, crit, unit) in ROWS:
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, benchmark_avg, benchmark_top25,
                 target_value, warning_threshold, critical_threshold, alert_direction,
                 unit_code, confidence, is_proxy, source_ref)
            VALUES
                ('system', 'SYSTEM', '{code}', NULL, NULL,
                 {target}, {warn}, {crit}, '{direction}', '{unit}',
                 'low', TRUE, 'global_clinical_default')
            ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE SET
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
        f"DELETE FROM default_metric_values WHERE scope_type='system' "
        f"AND scope_code='SYSTEM' AND metric_code IN ('{_CODES}')"
    )
