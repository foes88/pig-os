"""seed KR sow residual-value table for loss.sow_culling (region scope)

D-lite — PigPlan(KR) 조기도태 손실 계산용 산차별 잔여가치 + 잔존가(salvage).
출처: handoff S2_SOW_RETIREMENT / S2_SOW_CULL (TC_CODE_JOHAP PCODE 031). 위조 0.
country 하드코딩 회피 — region/KR seed로 주입, 타국은 행 없으면 loss.sow_culling 미발화.

값(원): 잔여가치 0산 8.4M·1산 7.1M·2산 5.8M·3산 4.5M·4산 3.3M·5산 1.95M·6산 0.8M·7산+ 0
       salvage 도태 0.3M·폐사 0

Revision ID: a1c3e5079b2d
Revises: f7b9d1c3e5a8
"""
from alembic import op

revision = "a1c3e5079b2d"
down_revision = "f7b9d1c3e5a8"
branch_labels = None
depends_on = None

# metric_code → 원(KRW) 금액 (target_value에 저장; warning/critical 미사용)
VALUES = {
    "SOW_RESIDUAL_P0": 8400000,
    "SOW_RESIDUAL_P1": 7100000,
    "SOW_RESIDUAL_P2": 5800000,
    "SOW_RESIDUAL_P3": 4500000,
    "SOW_RESIDUAL_P4": 3300000,
    "SOW_RESIDUAL_P5": 1950000,
    "SOW_RESIDUAL_P6": 800000,
    "SOW_SALVAGE_CULL": 300000,
    "SOW_SALVAGE_DEATH": 0,
}
_CODES = "', '".join(VALUES)


def upgrade() -> None:
    for code, won in VALUES.items():
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, target_value, alert_direction,
                 unit_code, confidence, is_proxy, source_ref)
            VALUES
                ('region', 'KR', '{code}', {won}, 'above',
                 'KRW', 'high', FALSE, 'PigPlan:S2_SOW_RETIREMENT')
            ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE SET
                target_value = EXCLUDED.target_value,
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
