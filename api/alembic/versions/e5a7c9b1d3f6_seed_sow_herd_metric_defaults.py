"""seed system-scope defaults for sow-herd structure metrics

모돈군 구조 규칙(culling/sow_mortality/parity/total_born)의 system 스코프 기본 임계.
국가별 위조 아님: confidence='low', is_proxy=TRUE, source='global_clinical_default'.
국가(region) 행 있으면 우선(예: SOW_MORTALITY는 US region 시드 존재).

Revision ID: e5a7c9b1d3f6
Revises: d4f6a8c0e2b5
"""
from alembic import op

revision = "e5a7c9b1d3f6"
down_revision = "d4f6a8c0e2b5"
branch_labels = None
depends_on = None

# (metric_code, direction, target, warn, crit, unit)
ROWS = [
    ("CULLING_RATE",      "above", 40.0, 45.0, 55.0, "%"),
    ("SOW_MORTALITY",     "above", 6.0,  8.0,  12.0, "%"),
    ("HIGH_PARITY_RATIO", "above", 15.0, 20.0, 30.0, "%"),
    ("TOTAL_BORN",        "below", 13.0, 12.0, 11.0, "두/복"),
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
