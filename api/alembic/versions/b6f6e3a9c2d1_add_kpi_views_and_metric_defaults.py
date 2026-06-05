"""add_kpi_views_and_metric_defaults

Revision ID: b6f6e3a9c2d1
Revises: a1273623b95d
Create Date: 2026-06-05 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "b6f6e3a9c2d1"
down_revision: Union[str, None] = "a1273623b95d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO default_metric_values
            (scope_type, scope_code, metric_code, default_value, benchmark_avg,
             benchmark_top25, target_value, unit_code)
        VALUES
            ('system', 'SYSTEM', 'PSY',       22.00, 24.30, 27.00, 28.00, 'piglets/sow/year'),
            ('system', 'SYSTEM', 'MSY',       20.00, 22.00, 25.00, 26.00, 'piglets/sow/year'),
            ('system', 'SYSTEM', 'NPD',       35.00, 30.00, 22.00, 20.00, 'days'),
            ('system', 'SYSTEM', 'FCR',        2.80,  2.60,  2.40,  2.30, 'ratio'),
            ('system', 'SYSTEM', 'MORTALITY',  5.00,  4.00,  2.50,  2.00, '%'),
            ('region', 'KR',     'PSY',       22.00, 24.30, 27.00, 28.00, 'piglets/sow/year'),
            ('region', 'KR',     'MSY',       20.00, 22.10, 25.00, 26.00, 'piglets/sow/year'),
            ('region', 'KR',     'NPD',       35.00, 31.00, 22.00, 20.00, 'days')
        ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE
        SET default_value = EXCLUDED.default_value,
            benchmark_avg = EXCLUDED.benchmark_avg,
            benchmark_top25 = EXCLUDED.benchmark_top25,
            target_value = EXCLUDED.target_value,
            unit_code = EXCLUDED.unit_code,
            updated_at = NOW()
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION effective_metric_values(
            p_farm_code VARCHAR,
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
                dmv.metric_code,
                dmv.default_value,
                dmv.benchmark_avg,
                dmv.benchmark_top25,
                dmv.target_value,
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
                    WHEN 'farm' THEN 1
                    WHEN 'region' THEN 2
                    WHEN 'market' THEN 3
                    WHEN 'system' THEN 4
                    ELSE 5
                END
        $$ LANGUAGE SQL STABLE
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_farm_psy AS
        SELECT
            s.farm_id,
            DATE_TRUNC('year', w.weaning_date)::DATE AS year_start,
            COUNT(DISTINCT s.id) AS avg_sow_count,
            COALESCE(SUM(w.weaned_count), 0) AS total_weaned,
            ROUND(
                COALESCE(SUM(w.weaned_count), 0)::NUMERIC
                / NULLIF(COUNT(DISTINCT s.id), 0),
                2
            ) AS psy
        FROM sows s
        LEFT JOIN weanings w
            ON w.sow_id = s.id
           AND w.deleted_at IS NULL
        WHERE s.deleted_at IS NULL
        GROUP BY s.farm_id, DATE_TRUNC('year', w.weaning_date)::DATE
    """)

    op.execute("""
        CREATE OR REPLACE VIEW v_sow_npd AS
        SELECT
            s.id AS sow_id,
            s.farm_id,
            w.id AS weaning_id,
            w.weaning_date,
            m_next.mating_date AS next_mating_date,
            (m_next.mating_date - w.weaning_date) AS wei_days
        FROM sows s
        JOIN weanings w
            ON w.sow_id = s.id
           AND w.deleted_at IS NULL
        LEFT JOIN LATERAL (
            SELECT m.mating_date
            FROM matings m
            WHERE m.sow_id = s.id
              AND m.mating_date > w.weaning_date
              AND m.mating_date <= w.weaning_date + INTERVAL '60 days'
              AND m.deleted_at IS NULL
            ORDER BY m.mating_date ASC
            LIMIT 1
        ) m_next ON TRUE
        WHERE s.deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_sow_npd")
    op.execute("DROP VIEW IF EXISTS v_farm_psy")
    op.execute("DROP FUNCTION IF EXISTS effective_metric_values(VARCHAR, VARCHAR, VARCHAR)")
    op.execute("""
        DELETE FROM default_metric_values
        WHERE (scope_type, scope_code, metric_code) IN (
            ('system', 'SYSTEM', 'PSY'),
            ('system', 'SYSTEM', 'MSY'),
            ('system', 'SYSTEM', 'NPD'),
            ('system', 'SYSTEM', 'FCR'),
            ('system', 'SYSTEM', 'MORTALITY'),
            ('region', 'KR', 'PSY'),
            ('region', 'KR', 'MSY'),
            ('region', 'KR', 'NPD')
        )
    """)
