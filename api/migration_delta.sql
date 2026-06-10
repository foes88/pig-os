BEGIN;

-- Running upgrade 6cbf1c758818 -> a1273623b95d

ALTER TABLE organizations ADD COLUMN parent_org_id UUID;

ALTER TABLE organizations ADD FOREIGN KEY(parent_org_id) REFERENCES organizations (id);

ALTER TABLE organizations ADD COLUMN org_level SMALLINT DEFAULT '0' NOT NULL;

CREATE INDEX idx_org_parent ON organizations (parent_org_id) WHERE parent_org_id IS NOT NULL;

ALTER TABLE users ADD COLUMN system_role VARCHAR(30) DEFAULT 'FARM_OWNER' NOT NULL;

UPDATE users
        SET system_role = CASE
            WHEN role = 'ADMIN' THEN 'SUPER_ADMIN'
            WHEN role = 'COMPANY' THEN 'VENDOR_ADMIN'
            WHEN role IN (
                'SUPER_ADMIN',
                'VENDOR_ADMIN',
                'DISTRIBUTOR_ADMIN',
                'DEALER_ADMIN',
                'FARM_OWNER',
                'FARM_MANAGER',
                'FARM_WORKER',
                'VET',
                'VIEWER',
                'API_CLIENT'
            ) THEN role
            ELSE 'FARM_OWNER'
        END;

CREATE INDEX idx_users_system_role ON users (system_role);

UPDATE alembic_version SET version_num='a1273623b95d' WHERE alembic_version.version_num = '6cbf1c758818';

-- Running upgrade a1273623b95d -> b6f6e3a9c2d1

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
            updated_at = NOW();

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
        $$ LANGUAGE SQL STABLE;

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
        GROUP BY s.farm_id, DATE_TRUNC('year', w.weaning_date)::DATE;

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
        WHERE s.deleted_at IS NULL;

UPDATE alembic_version SET version_num='b6f6e3a9c2d1' WHERE alembic_version.version_num = 'a1273623b95d';

-- Running upgrade b6f6e3a9c2d1 -> c7d4e2a1f9b0

ALTER TABLE default_metric_values ALTER COLUMN scope_code TYPE VARCHAR(50);

ALTER TABLE scope_kpi_recommendations ALTER COLUMN scope_code TYPE VARCHAR(50);

UPDATE alembic_version SET version_num='c7d4e2a1f9b0' WHERE alembic_version.version_num = 'b6f6e3a9c2d1';

-- Running upgrade c7d4e2a1f9b0 -> e3f9a2b4c8d1

ALTER TABLE default_metric_values
        ADD COLUMN IF NOT EXISTS warning_threshold  DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS critical_threshold DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS alert_direction    VARCHAR(10) NOT NULL DEFAULT 'below';

DROP FUNCTION IF EXISTS effective_metric_values(VARCHAR, VARCHAR, VARCHAR);

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
        $$ LANGUAGE SQL STABLE;

INSERT INTO default_metric_values
            (scope_type, scope_code, metric_code,
             default_value, benchmark_avg, benchmark_top25, target_value, unit_code,
             warning_threshold, critical_threshold, alert_direction)
        VALUES
        -- ���� SYSTEM fallback (global conservative baseline) ������������������������������
        ('system','SYSTEM','FARROWING_RATE', 80.0, 81.0, 88.0, 90.0, '%',
         80.0, 70.0, 'below'),

        -- ���� KR ��������������������������������������������������������������������������������������������������������������������
        ('region','KR','FARROWING_RATE', 83.0, 85.0, 90.0, 92.0, '%',
         85.0, 75.0, 'below'),

        -- ���� US ��������������������������������������������������������������������������������������������������������������������
        ('region','US','PSY',            22.0, 22.0, 26.0, 28.0, 'piglets/sow/year',
         23.0, 19.0, 'below'),
        ('region','US','NPD',            38.0, 44.0, 30.0, 25.0, 'days',
         38.0, 53.0, 'above'),
        ('region','US','FARROWING_RATE', 80.0, 81.0, 87.0, 90.0, '%',
         83.0, 73.0, 'below'),

        -- ���� BR ��������������������������������������������������������������������������������������������������������������������
        ('region','BR','PSY',            19.0, 20.5, 24.0, 26.0, 'piglets/sow/year',
         21.0, 17.0, 'below'),
        ('region','BR','NPD',            42.0, 48.0, 33.0, 27.0, 'days',
         42.0, 58.0, 'above'),
        ('region','BR','FARROWING_RATE', 78.0, 79.0, 85.0, 88.0, '%',
         80.0, 70.0, 'below'),

        -- ���� CN ��������������������������������������������������������������������������������������������������������������������
        ('region','CN','PSY',            17.0, 18.5, 22.0, 24.0, 'piglets/sow/year',
         19.0, 16.0, 'below'),
        ('region','CN','NPD',            45.0, 52.0, 36.0, 30.0, 'days',
         45.0, 62.0, 'above'),
        ('region','CN','FARROWING_RATE', 75.0, 76.0, 83.0, 86.0, '%',
         78.0, 68.0, 'below'),

        -- ���� VN (Southeast Asia representative) ����������������������������������������������������
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
            updated_at         = NOW();

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
          AND metric_code IN ('PSY', 'NPD');

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
          AND metric_code IN ('PSY', 'NPD');

UPDATE alembic_version SET version_num='e3f9a2b4c8d1' WHERE alembic_version.version_num = 'c7d4e2a1f9b0';

COMMIT;

