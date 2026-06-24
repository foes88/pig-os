"""seed market_defaults + region_defaults (weight unit + currency per country)

QA #6 — market_defaults/region_defaults가 비어 모든 국가가 kg/USD로 폴백하던 문제.
국가별 **사실 데이터**(US=lb·돈가 통화 ISO코드)이며 추정 KPI 아님.
resolve_config: country → region_defaults → market_defaults → 하드코딩(kg/USD).

Revision ID: b3d5f7091a2c
Revises: a1c3e5079b2d
"""
from alembic import op

revision = "b3d5f7091a2c"
down_revision = "a1c3e5079b2d"
branch_labels = None
depends_on = None

# market_code, name, weight_unit, currency
MARKETS = [
    ("US",     "United States",   "lb", "USD"),
    ("KR",     "South Korea",     "kg", "KRW"),
    ("CN",     "China",           "kg", "CNY"),
    ("SEA",    "Southeast Asia",  "kg", "USD"),
    ("LATAM",  "Latin America",   "kg", "USD"),
    ("GLOBAL", "Global",          "kg", "USD"),
]
# region_code(country), name, market_code, weight_unit, currency
REGIONS = [
    ("US", "United States", "US",    "lb", "USD"),
    ("KR", "South Korea",   "KR",    "kg", "KRW"),
    ("CN", "China",         "CN",    "kg", "CNY"),
    ("VN", "Vietnam",       "SEA",   "kg", "VND"),
    ("TH", "Thailand",      "SEA",   "kg", "THB"),
    ("PH", "Philippines",   "SEA",   "kg", "PHP"),
    ("BR", "Brazil",        "LATAM", "kg", "BRL"),
    ("MX", "Mexico",        "LATAM", "kg", "MXN"),
]
_RCODES = "', '".join(r[0] for r in REGIONS)
_MCODES = "', '".join(m[0] for m in MARKETS)


def upgrade() -> None:
    for code, name, wu, cur in MARKETS:
        op.execute(
            f"INSERT INTO market_defaults (market_code, market_name, weight_unit, currency_code) "
            f"VALUES ('{code}', '{name}', '{wu}', '{cur}') "
            f"ON CONFLICT (market_code) DO UPDATE SET weight_unit=EXCLUDED.weight_unit, "
            f"currency_code=EXCLUDED.currency_code, market_name=EXCLUDED.market_name"
        )
    for code, name, mkt, wu, cur in REGIONS:
        op.execute(
            f"INSERT INTO region_defaults (region_code, region_name, market_code, weight_unit, currency_code) "
            f"VALUES ('{code}', '{name}', '{mkt}', '{wu}', '{cur}') "
            f"ON CONFLICT (region_code) DO UPDATE SET weight_unit=EXCLUDED.weight_unit, "
            f"currency_code=EXCLUDED.currency_code, market_code=EXCLUDED.market_code, region_name=EXCLUDED.region_name"
        )


def downgrade() -> None:
    op.execute(f"DELETE FROM region_defaults WHERE region_code IN ('{_RCODES}')")
    op.execute(f"DELETE FROM market_defaults WHERE market_code IN ('{_MCODES}')")
