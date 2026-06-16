"""seed MARKET_PRICE_HEAD (출하 두당가격) for loss calc — country reference

PigPlan LOSS_CALC 연동: 손실액 = 손실두수 × 출하 두당가격.
가격은 변동성이 커 confidence=medium, source에 as-of 명시. 농장이 override 권장.
- default_value = 출하 1두당 가격, unit_code = 통화코드
없으면(미시드 국가) 손실 금액 표시 안 함(slot 숨김) — QA #8 원칙.

Revision ID: a8d2f4c6e1b9
Revises: f3a7c2e9b5d1
Create Date: 2026-06-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "a8d2f4c6e1b9"
down_revision: str | None = "f3a7c2e9b5d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (country, price_per_head, currency, confidence, source)
ROWS = [
    ("KR", 450000, "KRW", "medium", "축산물품질평가원 경락가 2025(약 5천원/kg·도체88kg)"),
    ("US", 210,    "USD", "medium", "USDA lean hog 2024(약 $0.75/lb·280lb)"),
    ("BR", 700,    "BRL", "low",    "ABCS/시세 추정 2024"),
    ("CN", 1500,   "CNY", "low",    "중국 시세 추정 2025"),
    ("VN", 5000000,"VND", "low",    "베트남 시세 추정 2024"),
]


def upgrade() -> None:
    for (country, price, cur, conf, src) in ROWS:
        is_proxy = "TRUE" if conf == "low" else "FALSE"
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, default_value, alert_direction,
                 unit_code, confidence, is_proxy, threshold_basis, source_ref)
            VALUES
                ('region', '{country}', 'MARKET_PRICE_HEAD', {price}, 'below',
                 '{cur}', '{conf}', {is_proxy}, 'market_reference', '{src}')
            ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE SET
                default_value = EXCLUDED.default_value,
                unit_code = EXCLUDED.unit_code,
                confidence = EXCLUDED.confidence,
                is_proxy = EXCLUDED.is_proxy,
                source_ref = EXCLUDED.source_ref
            """
        )


def downgrade() -> None:
    op.execute(
        "DELETE FROM default_metric_values "
        "WHERE scope_type='region' AND metric_code='MARKET_PRICE_HEAD'"
    )
