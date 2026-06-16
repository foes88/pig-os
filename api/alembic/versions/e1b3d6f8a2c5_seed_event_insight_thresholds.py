"""seed event-insight thresholds (system/global defaults, 3-source reconciled)

3자 리서치(Claude/GPT/deep-research) 대조 후 글로벌(system) 기본 임계값 시드.
규칙: warning=평균보다 나쁜 쪽, critical=손실 발생 구간. 출처/신뢰도 메타 포함.
국가별(US/KR 등) 미세조정은 추후 region 행으로 override (없으면 이 system 값 폴백).
근거: docs/specs/2026-06-16_threshold-research-comparison.md

Revision ID: e1b3d6f8a2c5
Revises: d5e9c1a3b7f4
Create Date: 2026-06-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "e1b3d6f8a2c5"
down_revision: str | None = "d5e9c1a3b7f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (metric_code, dir, avg, target, warning, critical, unit, confidence, basis, source)
ROWS = [
    ("STILLBORN_RATE", "above", 8.0, 6.0, 8.0, 12.0, "%", "medium",
     "investigate_gt7_normal_5_10", "PigCHAMP2023/NADIS/Le2022"),
    ("BORN_ALIVE", "below", 13.9, 15.0, 13.0, 11.5, "두/복", "medium",
     "us_avg_pic_intervention", "PorkCheckoff2024/PIC2021"),
    ("PRE_WEANING_MORTALITY", "above", 14.4, 10.0, 13.0, 18.0, "%", "high",
     "us_median_pic_gt12_eu", "PorkCheckoff2024/PIC2021/EU"),
    ("WEANED_COUNT", "below", 11.6, 14.0, 11.0, 9.5, "두/복", "medium",
     "us_avg_pic_intervention", "PorkCheckoff2024/PIC2021"),
    ("WSI", "above", 6.0, 5.5, 7.0, 10.0, "일", "high",
     "normal_3_6_pic_gt7", "PIC2021/Koketsu2017"),
    ("WEANING_AGE_LOW", "below", 21.0, 21.0, 18.0, 14.0, "일", "medium",
     "early_wean_risk", "industry/EU2008"),
    ("WEANING_AGE_HIGH", "above", 21.0, 24.0, 28.0, 32.0, "일", "medium",
     "turnover_loss_eu28_legal", "EU2008/PIC2021"),
]


def upgrade() -> None:
    for (code, direction, avg, target, warn, crit, unit, conf, basis, src) in ROWS:
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, benchmark_avg, target_value,
                 warning_threshold, critical_threshold, alert_direction, unit_code,
                 confidence, is_proxy, threshold_basis, source_ref)
            VALUES
                ('system', 'SYSTEM', '{code}', {avg}, {target},
                 {warn}, {crit}, '{direction}', '{unit}',
                 '{conf}', FALSE, '{basis}', '{src}')
            ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE SET
                benchmark_avg = EXCLUDED.benchmark_avg,
                target_value = EXCLUDED.target_value,
                warning_threshold = EXCLUDED.warning_threshold,
                critical_threshold = EXCLUDED.critical_threshold,
                alert_direction = EXCLUDED.alert_direction,
                unit_code = EXCLUDED.unit_code,
                confidence = EXCLUDED.confidence,
                threshold_basis = EXCLUDED.threshold_basis,
                source_ref = EXCLUDED.source_ref
            """
        )


def downgrade() -> None:
    codes = "', '".join(r[0] for r in ROWS)
    op.execute(
        f"DELETE FROM default_metric_values WHERE scope_type='system' AND metric_code IN ('{codes}')"
    )
