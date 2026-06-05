"""add_rule_thresholds_and_global_markets

Add warning_threshold, critical_threshold, alert_direction to default_metric_values.
Extend effective_metric_values() to return them.
Seed per-country thresholds for 5 markets (KR/US/BR/CN/VN) + FARROWING_RATE baseline.

Revision ID: e3f9a2b4c8d1
Revises: b6f6e3a9c2d1
Create Date: 2026-06-05 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "e3f9a2b4c8d1"
down_revision: Union[str, None] = "c7d4e2a1f9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Add columns ───────────────────────────────────────────────────────
    op.execute("""
        ALTER TABLE default_metric_values
        ADD COLUMN IF NOT EXISTS warning_threshold  DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS critical_threshold DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS alert_direction    VARCHAR(10) NOT NULL DEFAULT 'below'
    """)

    # ── 2. Recreate effective_metric_values() returning new columns ──────────
    op.execute("DROP FUNCTION IF EXISTS effective_metric_values(VARCHAR, VARCHAR, VARCHAR)")
    op.execute("""
        CREATE OR REPLACE FUNCTION effective_metric_values(
            p_farm_code   VARCHAR,
            p_region_code VARCHAR,
            p_market_code VARCHAR
        )
        RETURNS TABLE (
            metric_code         VARCHAR,
            default_value       DECIMAL,
            benchmark_avg       DECIMAL,
            benchmark_top25     DECIMAL,
            target_value        DECIMAL,
            warning_threshold   DECIMAL,
            critical_threshold  DECIMAL,
            alert_direction     VARCHAR,
            unit_code           VARCHAR,
            scope_type          VARCHAR
        ) AS $$
            SELECT DISTINCT ON (dmv.metric_code)
                dmv.metric_code,
                dmv.default_value,
                dmv.benchmark_avg,
                dmv.benchmark_top25,
                dmv.target_value,
                dmv.warning_threshold,
                dmv.critical_threshold,
                dmv.alert_direction,
                dmv.unit_code,
                dmv.scope_type
            FROM default_metric_values dmv
            WHERE (dmv.scope_type = 'farm'   AND dmv.scope_code = p_farm_code)
               OR (dmv.scope_type = 'region' AND dmv.scope_code = p_region_code)
               OR (dmv.scope_type = 'market' AND dmv.scope_code = p_market_code)
               OR (dmv.scope_type = 'system' AND dmv.scope_code = 'SYSTEM')
            ORDER BY
                dmv.metric_code,
                CASE dmv.scope_type
                    WHEN 'farm'   THEN 1
                    WHEN 'region' THEN 2
                    WHEN 'market' THEN 3
                    WHEN 'system' THEN 4
                    ELSE 5
                END
        $$ LANGUAGE SQL STABLE
    """)

    # ── 3. Seed thresholds ───────────────────────────────────────────────────
    # Columns: scope_type, scope_code, metric_code,
    #          default_value, benchmark_avg, benchmark_top25, target_value, unit_code,
    #          warning_threshold, critical_threshold, alert_direction
    op.execute("""
        INSERT INTO default_metric_values
            (scope_type, scope_code, metric_code,
             default_value, benchmark_avg, benchmark_top25, target_value, unit_code,
             warning_threshold, critical_threshold, alert_direction)
        VALUES
        -- ── SYSTEM fallback (global conservative baseline) ───────────────
        ('system','SYSTEM','FARROWING_RATE', 80.0, 81.0, 88.0, 90.0, '%',
         80.0, 70.0, 'below'),

        -- ── KR ──────────────────────────────────────────────────────────
        ('region','KR','FARROWING_RATE', 83.0, 85.0, 90.0, 92.0, '%',
         85.0, 75.0, 'below'),

        -- ── US ──────────────────────────────────────────────────────────
        ('region','US','PSY',            22.0, 22.0, 26.0, 28.0, 'piglets/sow/year',
         23.0, 19.0, 'below'),
        ('region','US','NPD',            38.0, 44.0, 30.0, 25.0, 'days',
         38.0, 53.0, 'above'),
        ('region','US','FARROWING_RATE', 80.0, 81.0, 87.0, 90.0, '%',
         83.0, 73.0, 'below'),

        -- ── BR ──────────────────────────────────────────────────────────
        ('region','BR','PSY',            19.0, 20.5, 24.0, 26.0, 'piglets/sow/year',
         21.0, 17.0, 'below'),
        ('region','BR','NPD',            42.0, 48.0, 33.0, 27.0, 'days',
         42.0, 58.0, 'above'),
        ('region','BR','FARROWING_RATE', 78.0, 79.0, 85.0, 88.0, '%',
         80.0, 70.0, 'below'),

        -- ── CN ──────────────────────────────────────────────────────────
        ('region','CN','PSY',            17.0, 18.5, 22.0, 24.0, 'piglets/sow/year',
         19.0, 16.0, 'below'),
        ('region','CN','NPD',            45.0, 52.0, 36.0, 30.0, 'days',
         45.0, 62.0, 'above'),
        ('region','CN','FARROWING_RATE', 75.0, 76.0, 83.0, 86.0, '%',
         78.0, 68.0, 'below'),

        -- ── VN (Southeast Asia representative) ──────────────────────────
        ('region','VN','PSY',            16.0, 17.5, 21.0, 23.0, 'piglets/sow/year',
         18.0, 15.0, 'below'),
        ('region','VN','NPD',            45.0, 54.0, 37.0, 31.0, 'days',
         45.0, 62.0, 'above'),
        ('region','VN','FARROWING_RATE', 74.0, 75.0, 82.0, 85.0, '%',
         78.0, 68.0, 'below')

        ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE
        SET warning_threshold  = EXCLUDED.warning_threshold,
            critical_threshold = EXCLUDED.critical_threshold,
            alert_direction    = EXCLUDED.alert_direction,
            benchmark_avg      = EXCLUDED.benchmark_avg,
            benchmark_top25    = EXCLUDED.benchmark_top25,
            target_value       = EXCLUDED.target_value,
            updated_at         = NOW()
    """)

    # Back-fill existing KR and SYSTEM PSY/NPD rows with thresholds
    op.execute("""
        UPDATE default_metric_values
        SET warning_threshold  = CASE metric_code
                WHEN 'PSY' THEN 24.0
                WHEN 'NPD' THEN 35.0
            END,
            critical_threshold = CASE metric_code
                WHEN 'PSY' THEN 20.0
                WHEN 'NPD' THEN 50.0
            END,
            alert_direction    = CASE metric_code
                WHEN 'PSY' THEN 'below'
                WHEN 'NPD' THEN 'above'
            END
        WHERE scope_type = 'region' AND scope_code = 'KR'
          AND metric_code IN ('PSY', 'NPD')
    """)
    op.execute("""
        UPDATE default_metric_values
        SET warning_threshold  = CASE metric_code
                WHEN 'PSY' THEN 22.0
                WHEN 'NPD' THEN 40.0
            END,
            critical_threshold = CASE metric_code
                WHEN 'PSY' THEN 18.0
                WHEN 'NPD' THEN 55.0
            END,
            alert_direction    = CASE metric_code
                WHEN 'PSY' THEN 'below'
                WHEN 'NPD' THEN 'above'
            END
        WHERE scope_type = 'system' AND scope_code = 'SYSTEM'
          AND metric_code IN ('PSY', 'NPD')
    """)


def downgrade() -> None:
    # Restore old function signature (without warning/critical/direction columns)
    op.execute("DROP FUNCTION IF EXISTS effective_metric_values(VARCHAR, VARCHAR, VARCHAR)")
    op.execute("""
        CREATE OR REPLACE FUNCTION effective_metric_values(
            p_farm_code   VARCHAR,
            p_region_code VARCHAR,
            p_market_code VARCHAR
        )
        RETURNS TABLE (
            metric_code VARCHAR,
            default_value DECIMAL,
            benchmark_avg DECIMAL,
            benchmark_top25 DECIMAL,
            target_value DECIMAL,
            unit_code VARCHAR,
            scope_type VARCHAR
        ) AS $$
            SELECT DISTINCT ON (dmv.metric_code)
                dmv.metric_code, dmv.default_value, dmv.benchmark_avg,
                dmv.benchmark_top25, dmv.target_value, dmv.unit_code, dmv.scope_type
            FROM default_metric_values dmv
            WHERE (dmv.scope_type = 'farm'   AND dmv.scope_code = p_farm_code)
               OR (dmv.scope_type = 'region' AND dmv.scope_code = p_region_code)
               OR (dmv.scope_type = 'market' AND dmv.scope_code = p_market_code)
               OR (dmv.scope_type = 'system' AND dmv.scope_code = 'SYSTEM')
            ORDER BY dmv.metric_code,
                CASE dmv.scope_type WHEN 'farm' THEN 1 WHEN 'region' THEN 2
                    WHEN 'market' THEN 3 WHEN 'system' THEN 4 ELSE 5 END
        $$ LANGUAGE SQL STABLE
    """)

    # Remove added rows and columns
    op.execute("""
        DELETE FROM default_metric_values
        WHERE (scope_type, scope_code, metric_code) IN (
            ('system','SYSTEM','FARROWING_RATE'),
            ('region','KR','FARROWING_RATE'),
            ('region','US','PSY'), ('region','US','NPD'), ('region','US','FARROWING_RATE'),
            ('region','BR','PSY'), ('region','BR','NPD'), ('region','BR','FARROWING_RATE'),
            ('region','CN','PSY'), ('region','CN','NPD'), ('region','CN','FARROWING_RATE'),
            ('region','VN','PSY'), ('region','VN','NPD'), ('region','VN','FARROWING_RATE')
        )
    """)
    op.execute("ALTER TABLE default_metric_values DROP COLUMN IF EXISTS warning_threshold")
    op.execute("ALTER TABLE default_metric_values DROP COLUMN IF EXISTS critical_threshold")
    op.execute("ALTER TABLE default_metric_values DROP COLUMN IF EXISTS alert_direction")
