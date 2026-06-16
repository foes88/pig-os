"""seed country KPI thresholds (US/BR/CN/VN/KR) — 3-source reconciled + PigPlan KR

해외(US/BR/CN/VN): GPT+Claude+deep-research 3자 대조값(그 시장 최선의 출처).
KR: PigPlan 확정값(재발율 5/12·분만율 target85·임신115) + 한돈팜스 공개값. 나머지 글로벌 폴백.
규칙: warning=평균보다 나쁜 쪽, critical=손실/하위분위. 신뢰도/출처/proxy 메타 포함.
근거: docs/specs/2026-06-16_threshold-research-comparison.md, docs/reference/pigplan-rules-extract.md

scope_type='region', scope_code=국가코드 → 해당국 농장은 글로벌(system) 대신 이 값 사용.

Revision ID: f3a7c2e9b5d1
Revises: e1b3d6f8a2c5
Create Date: 2026-06-16
"""
from collections.abc import Sequence

from alembic import op

revision: str = "f3a7c2e9b5d1"
down_revision: str | None = "e1b3d6f8a2c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (country, metric, dir, avg, top25, target, warn, crit, unit, conf, is_proxy, source)
ROWS = [
    # ── US (PigCHAMP/MetaFarms-NPB 2023-24, 대체로 high) ──────────────────────
    ("US", "STILLBORN_RATE", "above", 8.0, 5.7, 6.0, 8.0, 12.0, "%", "medium", False, "PigCHAMP2023"),
    ("US", "BORN_ALIVE", "below", 13.94, 15.2, 15.0, 13.0, 12.0, "두/복", "high", False, "PorkCheckoff2024"),
    ("US", "PRE_WEANING_MORTALITY", "above", 14.6, 9.85, 10.0, 14.0, 18.0, "%", "high", False, "PorkCheckoff2024"),
    ("US", "WEANED_COUNT", "below", 11.61, 13.0, 14.0, 11.0, 10.0, "두/복", "high", False, "PorkCheckoff2024"),
    ("US", "WSI", "above", 6.7, 6.1, 5.5, 7.0, 9.0, "일", "high", False, "PorkCheckoff2024"),
    ("US", "RTS_RATE", "above", 6.0, 1.0, 5.0, 10.0, 15.0, "%", "medium", False, "PigCHAMP2023"),
    ("US", "FARROWING_RATE", "below", 83.8, 90.0, 85.0, 82.0, 78.0, "%", "high", False, "PorkCheckoff2024"),
    ("US", "PSY", "below", 27.1, 31.0, 28.0, 26.0, 23.0, "두/모돈/년", "high", False, "PigCHAMP2024"),
    ("US", "SOW_MORTALITY", "above", 12.2, 7.5, 8.0, 12.0, 15.0, "%", "high", False, "PorkCheckoff2024"),
    # ── KR (PigPlan 확정값 + 한돈팜스 2023) ───────────────────────────────────
    ("KR", "RTS_RATE", "above", None, None, 5.0, 5.0, 12.0, "%", "high", False, "PigPlan-TAB_THRESHOLDS"),
    ("KR", "FARROWING_RATE", "below", None, None, 85.0, 83.0, 78.0, "%", "high", False, "PigPlan-TAB_THRESHOLDS"),
    ("KR", "PSY", "below", 22.1, 28.0, 24.0, 22.0, 18.0, "두/모돈/년", "high", False, "한돈팜스2023"),
    ("KR", "WEANED_COUNT", "below", 10.37, 11.6, 11.0, 10.0, 9.0, "두/복", "high", False, "한돈팜스2023"),
    ("KR", "BORN_ALIVE", "below", 11.35, None, 12.0, 10.5, 9.5, "두/복", "medium", False, "한돈팜스2023"),
    ("KR", "PRE_WEANING_MORTALITY", "above", 10.0, None, 8.0, 10.0, 14.0, "%", "medium", False, "한돈팜스2023"),
    ("KR", "WSI", "above", 6.9, None, 7.0, 7.0, 10.0, "일", "high", False, "PigPlan-140008"),
    # ── BR (Agriness 2024) ────────────────────────────────────────────────────
    ("BR", "BORN_ALIVE", "below", 13.87, 15.56, 15.0, 13.0, 12.0, "두/복", "high", False, "Agriness2024"),
    ("BR", "PRE_WEANING_MORTALITY", "above", 9.0, 4.73, 10.0, 12.0, 16.0, "%", "medium", False, "Agriness2024"),
    ("BR", "WEANED_COUNT", "below", 12.57, 14.85, 14.0, 12.0, 10.0, "두/복", "medium", False, "Agriness2024"),
    ("BR", "WSI", "above", 6.3, 4.85, 5.5, 7.0, 10.0, "일", "medium", False, "Agriness2024"),
    ("BR", "PSY", "below", 29.5, 37.2, 30.0, 28.0, 25.0, "두/모돈/년", "high", False, "Agriness2024"),
    ("BR", "STILLBORN_RATE", "above", 8.19, 7.41, 6.0, 8.2, 12.0, "%", "medium", False, "Agriness2024"),
    # ── CN (WEPIG 2025, medium-low) ───────────────────────────────────────────
    ("CN", "PSY", "below", 24.34, 31.5, 26.0, 24.0, 20.0, "두/모돈/년", "medium", False, "WEPIG2025"),
    ("CN", "WEANED_COUNT", "below", 11.25, 13.5, 12.0, 10.5, 9.0, "두/복", "medium", False, "WEPIG2025"),
    ("CN", "PRE_WEANING_MORTALITY", "above", 8.89, 4.13, 8.0, 10.0, 14.0, "%", "medium", False, "WEPIG2025"),
    ("CN", "BORN_ALIVE", "below", 12.19, 15.1, 14.0, 11.0, 10.0, "두/복", "low", True, "WEPIG2025-proxy"),
    ("CN", "FARROWING_RATE", "below", 83.26, 94.0, 85.0, 82.0, 78.0, "%", "medium", False, "WEPIG2025"),
    # ── VN (Agriness VIE 표본 29농장, low — sample) ──────────────────────────
    ("VN", "PSY", "below", 25.41, 33.5, 24.0, 22.0, 18.0, "두/모돈/년", "low", True, "AgrinessVIE-sample"),
    ("VN", "BORN_ALIVE", "below", 11.75, 14.6, 12.0, 11.0, 10.0, "두/복", "low", True, "AgrinessVIE-sample"),
    ("VN", "WEANED_COUNT", "below", 11.13, 13.5, 11.0, 10.0, 9.0, "두/복", "low", True, "AgrinessVIE-sample"),
    ("VN", "PRE_WEANING_MORTALITY", "above", 6.1, None, 10.0, 13.6, 19.0, "%", "low", True, "ThaiStudy2018-proxy"),
    ("VN", "WSI", "above", 7.99, 5.59, 5.5, 7.0, 10.0, "일", "low", True, "AgrinessVIE-sample"),
]


def _sql_val(v):
    return "NULL" if v is None else (f"'{v}'" if isinstance(v, str) else str(v))


def upgrade() -> None:
    for (country, code, direction, avg, top25, target, warn, crit, unit, conf, is_proxy, src) in ROWS:
        op.execute(
            f"""
            INSERT INTO default_metric_values
                (scope_type, scope_code, metric_code, benchmark_avg, benchmark_top25,
                 target_value, warning_threshold, critical_threshold, alert_direction,
                 unit_code, confidence, is_proxy, source_ref)
            VALUES
                ('region', '{country}', '{code}', {_sql_val(avg)}, {_sql_val(top25)},
                 {target}, {warn}, {crit}, '{direction}', '{unit}',
                 '{conf}', {str(is_proxy).upper()}, '{src}')
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
    # 신규 이벤트 메트릭만 삭제 (PSY/FARROWING_RATE/SOW_MORTALITY는 이전 마이그 시드라 보존)
    countries = "', '".join({r[0] for r in ROWS})
    op.execute(
        f"DELETE FROM default_metric_values WHERE scope_type='region' "
        f"AND scope_code IN ('{countries}') "
        f"AND metric_code IN ('STILLBORN_RATE','BORN_ALIVE','PRE_WEANING_MORTALITY',"
        f"'WEANED_COUNT','WSI','RTS_RATE')"
    )
