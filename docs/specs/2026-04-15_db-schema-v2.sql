-- ============================================================================
-- PigOS — Global DB Schema v2.0 (기획서 v2.3 반영)
-- ============================================================================
-- 변경 요약 (v1.0 → v2.0):
--   1. country_configs → market_defaults + region_defaults 2단계 분리
--   2. kpi_snapshots 컬럼 구조 → default_metric_values 속성 테이블
--      (scope_type, metric_code, default_value/benchmark_avg/top25/target_value)
--   3. JSONB KPI 권장 → scope_kpi_recommendations 테이블
--      (is_base / is_addon / addon_code / display_priority)
--   4. regulation_notes TEXT → compliance_profiles boolean 플래그 테이블
--   5. market_prices → market_price_reference (설정값/시장가격 분리)
--   6. 우선순위: farm → region → market → system (DISTINCT ON 쿼리)
--
-- 기준 문서:
--   - PigOS_PlanUpdate_v2.3.md (2026-04-15)
--   - db-schema-review-v1.md (2026-03-31 검증 리포트)
--
-- 작성: 2026-04-15
-- ============================================================================


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  A. 설정 계층 (Configuration Layer)                                      │
-- │  우선순위: farm_config > region_defaults > market_defaults > system      │
-- └──────────────────────────────────────────────────────────────────────────┘

-- A-1. 권역 메타
CREATE TABLE market_defaults (
    market_code             VARCHAR(10) PRIMARY KEY,    -- NA / EU / SEA / NEA / SA
    market_name             VARCHAR(50) NOT NULL,
    weight_unit             VARCHAR(5) NOT NULL,        -- kg / lb
    currency_code           CHAR(3) NOT NULL,           -- USD / EUR / KRW...
    pricing_unit            VARCHAR(20),                -- USD/lb, KRW/kg (표시용)
    compliance_profile_code VARCHAR(50),                -- → compliance_profiles
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO market_defaults VALUES
    ('NA',  '북미',       'lb', 'USD', 'USD/lb', 'US_STANDARD',  NOW(), NOW()),
    ('EU',  '유럽',       'kg', 'EUR', 'EUR/kg', 'EU_STANDARD',  NOW(), NOW()),
    ('SEA', '동남아',     'kg', 'USD', 'USD/kg', 'SEA_STANDARD', NOW(), NOW()),
    ('NEA', '동북아',     'kg', 'KRW', 'KRW/kg', 'KR_STANDARD',  NOW(), NOW()),
    ('SA',  '남미',       'kg', 'USD', 'USD/kg', 'SEA_STANDARD', NOW(), NOW());


-- A-2. 국가(지역) 메타
CREATE TABLE region_defaults (
    region_code             VARCHAR(10) PRIMARY KEY,    -- KR / US / TH / VN / DE...
    region_name             VARCHAR(50) NOT NULL,
    market_code             VARCHAR(10) NOT NULL REFERENCES market_defaults(market_code),
    weight_unit             VARCHAR(5),                 -- 국가별 override
    currency_code           CHAR(3),
    pricing_unit            VARCHAR(20),
    compliance_profile_code VARCHAR(50),                -- → compliance_profiles
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO region_defaults VALUES
    ('KR', '한국',     'NEA', 'kg', 'KRW', 'KRW/kg', 'KR_STANDARD',  NOW(), NOW()),
    ('US', '미국',     'NA',  'lb', 'USD', 'USD/lb', 'US_STANDARD',  NOW(), NOW()),
    ('TH', '태국',     'SEA', 'kg', 'USD', 'USD/kg', 'SEA_STANDARD', NOW(), NOW()),
    ('VN', '베트남',   'SEA', 'kg', 'USD', 'USD/kg', 'SEA_STANDARD', NOW(), NOW()),
    ('DE', '독일',     'EU',  'kg', 'EUR', 'EUR/kg', 'EU_STANDARD',  NOW(), NOW()),
    ('DK', '덴마크',   'EU',  'kg', 'EUR', 'EUR/kg', 'EU_STANDARD',  NOW(), NOW()),
    ('NL', '네덜란드', 'EU',  'kg', 'EUR', 'EUR/kg', 'EU_STANDARD',  NOW(), NOW()),
    ('ES', '스페인',   'EU',  'kg', 'EUR', 'EUR/kg', 'EU_STANDARD',  NOW(), NOW()),
    ('BR', '브라질',   'SA',  'kg', 'USD', 'USD/kg', 'SEA_STANDARD', NOW(), NOW()),
    ('PH', '필리핀',   'SEA', 'kg', 'USD', 'USD/kg', 'SEA_STANDARD', NOW(), NOW()),
    ('CN', '중국',     'NEA', 'kg', 'USD', 'USD/kg', 'KR_STANDARD',  NOW(), NOW());


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  B. KPI 기본값·벤치마크 (default_metric_values)                          │
-- │  KPI를 컬럼이 아닌 행으로 정규화. 4개 값 분리.                            │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE default_metric_values (
    id               BIGSERIAL PRIMARY KEY,
    scope_type       VARCHAR(20) NOT NULL
        CHECK (scope_type IN ('system','market','region','farm')),
    scope_code       VARCHAR(20) NOT NULL,           -- SYSTEM / NA / KR / FARM_001
    metric_code      VARCHAR(50) NOT NULL,           -- PSY / MSY / NPD / FCR / MORTALITY
    default_value    DECIMAL(10,2),                  -- 신규 농장 자동 입력값
    benchmark_avg    DECIMAL(10,2),                  -- 국가/권역 평균
    benchmark_top25  DECIMAL(10,2),                  -- 상위 25%
    target_value     DECIMAL(10,2),                  -- 제품 권장 목표
    unit_code        VARCHAR(20),                    -- %, days, kg, ratio
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (scope_type, scope_code, metric_code)
);
CREATE INDEX idx_dmv_lookup ON default_metric_values(metric_code, scope_type, scope_code);

-- 시스템 기본값
INSERT INTO default_metric_values
  (scope_type, scope_code, metric_code,
   default_value, benchmark_avg, benchmark_top25, target_value, unit_code) VALUES
  ('system','SYSTEM','PSY',       22.0, 24.3, 27.0, 28.0, 'piglets/sow/year'),
  ('system','SYSTEM','MSY',       20.0, 22.0, 25.0, 26.0, 'piglets/sow/year'),
  ('system','SYSTEM','NPD',       35.0, 30.0, 22.0, 20.0, 'days'),
  ('system','SYSTEM','FCR',        2.8,  2.6,  2.4,  2.3, 'ratio'),
  ('system','SYSTEM','MORTALITY',  5.0,  4.0,  2.5,  2.0, '%');

-- 북미
INSERT INTO default_metric_values
  (scope_type, scope_code, metric_code,
   default_value, benchmark_avg, benchmark_top25, target_value, unit_code) VALUES
  ('market','NA','PSY', 24.0, 26.5, 29.0, 30.0, 'piglets/sow/year'),
  ('market','NA','NPD', 28.0, 24.0, 18.0, 16.0, 'days'),
  ('market','NA','FCR',  2.6,  2.5,  2.3,  2.2, 'ratio');

-- EU (항생제 필수)
INSERT INTO default_metric_values
  (scope_type, scope_code, metric_code,
   default_value, benchmark_avg, benchmark_top25, target_value, unit_code) VALUES
  ('market','EU','PSY',            26.0, 28.5, 31.0, 32.0, 'piglets/sow/year'),
  ('market','EU','ANTIBIOTIC_USE',  0.5,  0.3,  0.1,  0.05,'treatments/year'),
  ('market','EU','WELFARE_SCORE',   3.0,  3.5,  4.2,  4.5, 'score');

-- 한국
INSERT INTO default_metric_values
  (scope_type, scope_code, metric_code,
   default_value, benchmark_avg, benchmark_top25, target_value, unit_code) VALUES
  ('region','KR','PSY', 22.0, 24.3, 27.0, 28.0, 'piglets/sow/year'),
  ('region','KR','MSY', 20.0, 22.1, 25.0, 26.0, 'piglets/sow/year'),
  ('region','KR','NPD', 35.0, 31.0, 22.0, 20.0, 'days');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  C. KPI 노출·추천·과금 (scope_kpi_recommendations)                        │
-- │  무료/유료·표시 순서·Addon 연결을 테이블로 관리 (JSONB 대체)               │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE scope_kpi_recommendations (
    id               BIGSERIAL PRIMARY KEY,
    scope_type       VARCHAR(20) NOT NULL
        CHECK (scope_type IN ('system','market','region')),
    scope_code       VARCHAR(20) NOT NULL,
    kpi_code         VARCHAR(50) NOT NULL,
    display_priority INT NOT NULL DEFAULT 100,       -- 낮을수록 먼저 노출
    is_base          BOOLEAN NOT NULL DEFAULT FALSE, -- 베이직(무료) 포함
    is_addon         BOOLEAN NOT NULL DEFAULT FALSE, -- 유료 Addon
    addon_code       VARCHAR(50),                    -- ADDON_FCR / ADDON_COST 등
    is_visible       BOOLEAN NOT NULL DEFAULT TRUE,  -- 대시보드 기본 노출
    farm_type        VARCHAR(20),                    -- 일관/번식/비육 (NULL=전체)
    min_sow_count    INT,                            -- 최소 모돈 수 조건
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (NOT (is_base = TRUE AND is_addon = TRUE)),
    UNIQUE (scope_type, scope_code, kpi_code, farm_type, min_sow_count)
);
CREATE INDEX idx_skr_lookup ON scope_kpi_recommendations(scope_type, scope_code, display_priority);

-- 한국 KPI 세팅
INSERT INTO scope_kpi_recommendations
  (scope_type, scope_code, kpi_code, display_priority, is_base, is_addon, addon_code,
   is_visible, farm_type, min_sow_count) VALUES
  ('region','KR','PSY',  1, TRUE,  FALSE, NULL,        TRUE,  NULL, NULL),
  ('region','KR','MSY',  2, TRUE,  FALSE, NULL,        TRUE,  NULL, NULL),
  ('region','KR','NPD',  3, TRUE,  FALSE, NULL,        TRUE,  NULL, NULL),
  ('region','KR','FCR',  4, FALSE, TRUE,  'ADDON_FCR', FALSE, NULL, 100);

-- 북미 (FCR이 Base)
INSERT INTO scope_kpi_recommendations
  (scope_type, scope_code, kpi_code, display_priority, is_base, is_addon, addon_code,
   is_visible, farm_type, min_sow_count) VALUES
  ('market','NA','PSY',  1, TRUE,  FALSE, NULL,         TRUE,  NULL, NULL),
  ('market','NA','NPD',  2, TRUE,  FALSE, NULL,         TRUE,  NULL, NULL),
  ('market','NA','FCR',  3, TRUE,  FALSE, NULL,         TRUE,  NULL, NULL),
  ('market','NA','COST', 4, FALSE, TRUE,  'ADDON_COST', FALSE, NULL, 500);

-- EU (항생제 추적 Base)
INSERT INTO scope_kpi_recommendations
  (scope_type, scope_code, kpi_code, display_priority, is_base, is_addon, addon_code,
   is_visible, farm_type, min_sow_count) VALUES
  ('market','EU','PSY',             1, TRUE,  FALSE, NULL,            TRUE,  NULL, NULL),
  ('market','EU','ANTIBIOTIC_USE',  2, TRUE,  FALSE, NULL,            TRUE,  NULL, NULL),
  ('market','EU','WELFARE_SCORE',   3, FALSE, TRUE,  'ADDON_WELFARE', FALSE, NULL, NULL);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  D. 규제·컴플라이언스 (compliance_profiles)                              │
-- │  Boolean 플래그로 기능 조건 분기 (regulation_notes TEXT 대체)             │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE compliance_profiles (
    profile_code                  VARCHAR(50) PRIMARY KEY,
    profile_name                  VARCHAR(100) NOT NULL,
    requires_traceability         BOOLEAN NOT NULL DEFAULT FALSE,
    requires_welfare_metrics      BOOLEAN NOT NULL DEFAULT FALSE,
    requires_antibiotic_tracking  BOOLEAN NOT NULL DEFAULT FALSE,
    requires_env_reporting        BOOLEAN NOT NULL DEFAULT FALSE,
    min_wean_period               INT,                   -- 최소 이유일령 (일)
    max_antibiotic_treatments     DECIMAL(5,2),          -- 연간 처치 상한
    notes                         TEXT,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO compliance_profiles
  (profile_code, profile_name,
   requires_traceability, requires_welfare_metrics,
   requires_antibiotic_tracking, requires_env_reporting,
   min_wean_period, max_antibiotic_treatments, notes) VALUES
  ('KR_STANDARD', '한국 표준',
   FALSE, FALSE, FALSE, FALSE, 21, NULL, '국내 일반 기준'),
  ('EU_STANDARD', 'EU 표준',
   TRUE,  TRUE,  TRUE,  TRUE,  28, 1.0,  'EU 동물복지·항생제 규정'),
  ('US_STANDARD', '미국 표준',
   FALSE, FALSE, FALSE, FALSE, 21, NULL, 'USDA 기본 기준'),
  ('SEA_STANDARD','동남아 표준',
   FALSE, FALSE, FALSE, FALSE, 25, NULL, 'ASF 대응 가이드 포함');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  E. 시장 가격 (market_price_reference)                                   │
-- │  설정값과 분리된 시장 변동 가격 (외부 소스 연동)                           │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE market_price_reference (
    id              BIGSERIAL PRIMARY KEY,
    region_code     VARCHAR(10) REFERENCES region_defaults(region_code),
    market_code     VARCHAR(10) REFERENCES market_defaults(market_code),
    price_type      VARCHAR(30) NOT NULL,       -- LIVE_HOG / PORK_CUTOUT / LEAN_HOG_FUTURES
    price_value     DECIMAL(12,4) NOT NULL,
    currency_code   CHAR(3) NOT NULL,
    weight_unit     VARCHAR(5) NOT NULL,
    price_date      DATE NOT NULL,
    source          VARCHAR(100),               -- USDA / CME / EKAPEPIA / MAFRA
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (region_code IS NOT NULL OR market_code IS NOT NULL)
);
CREATE INDEX idx_mpr_region_date ON market_price_reference(region_code, price_date DESC);
CREATE INDEX idx_mpr_market_date ON market_price_reference(market_code, price_date DESC);

INSERT INTO market_price_reference
  (region_code, market_code, price_type, price_value, currency_code, weight_unit,
   price_date, source) VALUES
  ('KR', 'NEA', 'LIVE_HOG',          5200,   'KRW', 'kg', '2026-04-17', 'MAFRA'),
  ('US', 'NA',  'LEAN_HOG_FUTURES',     0.89,'USD', 'lb', '2026-04-17', 'CME'),
  (NULL, 'EU',  'PORK_CUTOUT',          1.85,'EUR', 'kg', '2026-04-17', 'EC_DASHBOARD');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  F. 우선순위 조회 View — effective KPI 기준값                             │
-- │  farm → region → market → system 순으로 DISTINCT ON                      │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION effective_metric_values(
    p_farm_code   VARCHAR,
    p_region_code VARCHAR,
    p_market_code VARCHAR
)
RETURNS TABLE (
    metric_code      VARCHAR,
    default_value    DECIMAL,
    benchmark_avg    DECIMAL,
    benchmark_top25  DECIMAL,
    target_value     DECIMAL,
    unit_code        VARCHAR,
    scope_type       VARCHAR
) AS $$
    SELECT DISTINCT ON (metric_code)
      metric_code, default_value, benchmark_avg,
      benchmark_top25, target_value, unit_code, scope_type
    FROM default_metric_values
    WHERE (scope_type = 'farm'   AND scope_code = p_farm_code)
       OR (scope_type = 'region' AND scope_code = p_region_code)
       OR (scope_type = 'market' AND scope_code = p_market_code)
       OR (scope_type = 'system' AND scope_code = 'SYSTEM')
    ORDER BY
      metric_code,
      CASE scope_type
        WHEN 'farm'   THEN 1
        WHEN 'region' THEN 2
        WHEN 'market' THEN 3
        WHEN 'system' THEN 4
      END;
$$ LANGUAGE SQL STABLE;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  G. 트리거: updated_at 자동 갱신                                          │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TRIGGER trg_market_defaults_updated
    BEFORE UPDATE ON market_defaults
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_region_defaults_updated
    BEFORE UPDATE ON region_defaults
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_dmv_updated
    BEFORE UPDATE ON default_metric_values
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_compliance_profiles_updated
    BEFORE UPDATE ON compliance_profiles
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- ============================================================================
-- v2.0 SCHEMA SUMMARY (신규/변경 테이블만)
-- ============================================================================
-- A. Config Layer      : market_defaults, region_defaults                 (신규)
-- B. Metric Values     : default_metric_values                            (신규)
-- C. KPI Routing       : scope_kpi_recommendations                        (신규)
-- D. Compliance        : compliance_profiles                              (신규)
-- E. Market Price      : market_price_reference                           (신규, market_prices 대체)
-- F. View              : effective_metric_values()                        (신규)
--
-- 제거/대체:
--   - country_configs      → market_defaults + region_defaults
--   - kpi_snapshots (컬럼) → default_metric_values (행 정규화)
--                            kpi_snapshots 자체는 실측 스냅샷 저장용으로 유지
--   - compliance_reports   → compliance_profiles (+ 기존 JSONB report_data 보존)
--   - market_prices        → market_price_reference
-- ============================================================================


-- ============================================================================
-- CRITICAL & MAJOR FIXES  (db-schema-review-v1.md 기반)
-- C-01 ~ C-07 (CRITICAL) + M-01, M-03, M-06, M-07 (MAJOR P1)
-- v1 스키마 위에 적용 (ALTER + 신규 테이블)
-- ============================================================================


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-03] 산차별 번식 사이클 (breeding_cycles)                             │
-- │  reproductive_events 등이 참조하므로 먼저 생성                           │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE breeding_cycles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    parity          INT NOT NULL CHECK (parity >= 0 AND parity <= 20),
    cycle_status    VARCHAR(20) NOT NULL DEFAULT 'MATED'
        CHECK (cycle_status IN ('MATED','CONFIRMED','FARROWED','WEANED','FAILED')),
    started_at      DATE NOT NULL,
    ended_at        DATE,
    mating_count    INT NOT NULL DEFAULT 1
        CHECK (mating_count >= 1 AND mating_count <= 5),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (sow_id, parity)
);
CREATE INDEX idx_bc_farm_sow ON breeding_cycles(farm_id, sow_id);

-- 활성 사이클은 모돈당 최대 1개 (WEANED/FAILED 제외)
CREATE UNIQUE INDEX idx_one_active_cycle
    ON breeding_cycles (sow_id)
    WHERE cycle_status NOT IN ('WEANED', 'FAILED');

-- breeding_cycle_id FK를 핵심 이벤트 테이블에 추가
ALTER TABLE matings    ADD COLUMN breeding_cycle_id UUID REFERENCES breeding_cycles(id);
ALTER TABLE farrowings ADD COLUMN breeding_cycle_id UUID REFERENCES breeding_cycles(id);
ALTER TABLE weanings   ADD COLUMN breeding_cycle_id UUID REFERENCES breeding_cycles(id);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-01] 재발정/유산/사고 이벤트 (reproductive_events)                    │
-- │  피그플랜 TB_SAGO 대응. NPD 계산 정확도 필수.                            │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE reproductive_events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id           UUID NOT NULL REFERENCES farms(id),
    sow_id            UUID NOT NULL REFERENCES sows(id),
    mating_id         UUID REFERENCES matings(id),
    breeding_cycle_id UUID REFERENCES breeding_cycles(id),
    event_date        DATE NOT NULL,
    event_type        VARCHAR(30) NOT NULL
        CHECK (event_type IN (
            'RETURN_TO_ESTRUS','ABORTION','EMPTY','INFERTILE',
            'CULLED','DEAD','TRANSFER_OUT','SOLD','HEAT_DETECTED'
        )),
    detected_method   VARCHAR(20)
        CHECK (detected_method IN ('ULTRASOUND','VISUAL','BEHAVIOR','BLOOD_TEST')
               OR detected_method IS NULL),
    notes             TEXT,
    created_by        UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);
CREATE INDEX idx_re_farm_sow ON reproductive_events(farm_id, sow_id);
CREATE INDEX idx_re_mating   ON reproductive_events(mating_id)
    WHERE mating_id IS NOT NULL;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-02] 포유중 자돈 이동/폐사 (piglet_events)                            │
-- │  피그플랜 TB_MODON_JADON_TRANS 대응. 두수 정합성 검증 필수.              │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE piglet_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id             UUID NOT NULL REFERENCES farms(id),
    farrowing_id        UUID NOT NULL REFERENCES farrowings(id),
    sow_id              UUID NOT NULL REFERENCES sows(id),
    event_date          DATE NOT NULL,
    event_type          VARCHAR(20) NOT NULL
        CHECK (event_type IN ('STILLBORN_REMOVAL','DEATH','FOSTER_IN','FOSTER_OUT')),
    piglet_count        INT NOT NULL CHECK (piglet_count > 0),
    reason              VARCHAR(50)
        CHECK (reason IN (
            'CRUSHING','SCOURS','STARVATION','CONGENITAL','HYPOTHERMIA','OTHER'
        ) OR reason IS NULL),
    target_sow_id       UUID REFERENCES sows(id),
    target_farrowing_id UUID REFERENCES farrowings(id),
    notes               TEXT,
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);
CREATE INDEX idx_pe_farrowing ON piglet_events(farrowing_id);
CREATE INDEX idx_pe_farm_date  ON piglet_events(farm_id, event_date);

-- 두수 정합성 검증 함수: weaned = born_alive + foster_in - foster_out - deaths
CREATE OR REPLACE FUNCTION fn_verify_piglet_count(p_farrowing_id UUID)
RETURNS TABLE(
    born_alive      INT,
    foster_in       INT,
    foster_out      INT,
    deaths          INT,
    expected_weaned INT,
    actual_weaned   INT,
    is_balanced     BOOLEAN
) AS $$
    SELECT
        f.born_alive,
        COALESCE(SUM(pe.piglet_count)
            FILTER (WHERE pe.event_type = 'FOSTER_IN'),  0)::INT,
        COALESCE(SUM(pe.piglet_count)
            FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)::INT,
        COALESCE(SUM(pe.piglet_count)
            FILTER (WHERE pe.event_type IN ('DEATH','STILLBORN_REMOVAL')), 0)::INT,
        (f.born_alive
         + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'),  0)
         - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
         - COALESCE(SUM(pe.piglet_count)
             FILTER (WHERE pe.event_type IN ('DEATH','STILLBORN_REMOVAL')), 0)
        )::INT,
        w.weaned_count,
        (f.born_alive
         + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'),  0)
         - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
         - COALESCE(SUM(pe.piglet_count)
             FILTER (WHERE pe.event_type IN ('DEATH','STILLBORN_REMOVAL')), 0)
        ) = w.weaned_count
    FROM farrowings f
    LEFT JOIN piglet_events pe
        ON pe.farrowing_id = f.id AND pe.deleted_at IS NULL
    LEFT JOIN weanings w
        ON w.farrowing_id = f.id AND w.deleted_at IS NULL
    WHERE f.id = p_farrowing_id
    GROUP BY f.born_alive, w.weaned_count;
$$ LANGUAGE sql;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-04] 작업 전후관계 강제 + 모돈 일치 검증                               │
-- │  교배→분만→이유 체인 무결성 보장                                          │
-- └──────────────────────────────────────────────────────────────────────────┘

-- FK NOT NULL: 교배 없는 분만, 분만 없는 이유 차단
ALTER TABLE farrowings ALTER COLUMN mating_id    SET NOT NULL;
ALTER TABLE weanings   ALTER COLUMN farrowing_id SET NOT NULL;

-- 이유는 분만당 1건만
CREATE UNIQUE INDEX idx_one_weaning_per_farrowing
    ON weanings (farrowing_id)
    WHERE farrowing_id IS NOT NULL AND deleted_at IS NULL;

-- 분만 전 교배 존재 확인
CREATE OR REPLACE FUNCTION validate_farrowing_sequence()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM matings
        WHERE sow_id = NEW.sow_id
          AND mating_date < NEW.farrowing_date
          AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION
            'Cannot record farrowing without prior mating for sow %', NEW.sow_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_farrowing_sequence
    BEFORE INSERT ON farrowings
    FOR EACH ROW EXECUTE FUNCTION validate_farrowing_sequence();

-- 분만 sow ↔ 교배 sow 일치 검증
CREATE OR REPLACE FUNCTION validate_farrowing_sow_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mating_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM matings
            WHERE id = NEW.mating_id AND sow_id = NEW.sow_id
        ) THEN
            RAISE EXCEPTION
                'Farrowing sow_id must match mating sow_id (mating_id=%)',
                NEW.mating_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_farrowing_sow
    BEFORE INSERT OR UPDATE ON farrowings
    FOR EACH ROW EXECUTE FUNCTION validate_farrowing_sow_match();

-- 이유 sow ↔ 분만 sow 일치 검증
CREATE OR REPLACE FUNCTION validate_weaning_sow_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.farrowing_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM farrowings
            WHERE id = NEW.farrowing_id AND sow_id = NEW.sow_id
        ) THEN
            RAISE EXCEPTION
                'Weaning sow_id must match farrowing sow_id (farrowing_id=%)',
                NEW.farrowing_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_weaning_sow
    BEFORE INSERT OR UPDATE ON weanings
    FOR EACH ROW EXECUTE FUNCTION validate_weaning_sow_match();


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-05] CHECK 제약조건 — 상태/유형 VARCHAR 필드 전수                      │
-- └──────────────────────────────────────────────────────────────────────────┘

ALTER TABLE sows ADD CONSTRAINT chk_sow_status
    CHECK (status IN (
        'ACTIVE','GESTATING','LACTATING','WEANED','DRY','CULLED','DEAD'
    ));
ALTER TABLE sows ADD CONSTRAINT chk_sow_entry_type
    CHECK (entry_type IN ('GILT','PURCHASE','TRANSFER','BORN'));

ALTER TABLE matings ADD CONSTRAINT chk_mating_type
    CHECK (mating_type IN ('AI','NATURAL'));

ALTER TABLE pregnancy_checks ADD CONSTRAINT chk_pregnancy_result
    CHECK (result IN ('POSITIVE','NEGATIVE','UNCERTAIN'));

ALTER TABLE removals ADD CONSTRAINT chk_removal_type
    CHECK (removal_type IN ('CULL','DEAD','SOLD','TRANSFER'));
ALTER TABLE removals ADD CONSTRAINT chk_removal_reason
    CHECK (reason_category IN (
        'REPRODUCTIVE','LAMENESS','DISEASE','AGE','PERFORMANCE',
        'INJURY','BEHAVIOR','UNKNOWN','OTHER'
    ) OR reason_category IS NULL);

ALTER TABLE health_events ADD CONSTRAINT chk_health_event_type
    CHECK (event_type IN (
        'DISEASE','INJURY','OBSERVATION','DEATH','CULLING'
    ));
ALTER TABLE health_events ADD CONSTRAINT chk_health_severity
    CHECK (severity IN ('MILD','MODERATE','SEVERE','FATAL') OR severity IS NULL);

ALTER TABLE buildings ADD CONSTRAINT chk_building_type
    CHECK (building_type IN (
        'GESTATION','FARROWING','NURSERY','FINISHER',
        'GILT_DEVELOPMENT','ISOLATION','QUARANTINE','STORAGE'
    ));

-- XOR: health_events / feed_records 는 sow 또는 group 중 하나 필수
ALTER TABLE health_events ADD CONSTRAINT chk_health_target
    CHECK (sow_id IS NOT NULL OR group_id IS NOT NULL);
ALTER TABLE feed_records  ADD CONSTRAINT chk_feed_target
    CHECK (sow_id IS NOT NULL OR group_id IS NOT NULL);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-06] 숫자 범위 제약 + 두수 정합성                                      │
-- └──────────────────────────────────────────────────────────────────────────┘

ALTER TABLE sows ADD CONSTRAINT chk_sow_parity
    CHECK (parity >= 0 AND parity <= 20);

-- total_born = born_alive + stillborn + mummified
ALTER TABLE farrowings ADD CONSTRAINT chk_total_born_integrity
    CHECK (total_born = born_alive + stillborn + mummified);
ALTER TABLE farrowings ADD CONSTRAINT chk_total_born_range
    CHECK (total_born >= 0 AND total_born <= 30);
ALTER TABLE farrowings ADD CONSTRAINT chk_born_alive_range
    CHECK (born_alive >= 0);
ALTER TABLE farrowings ADD CONSTRAINT chk_stillborn_range
    CHECK (stillborn >= 0);
ALTER TABLE farrowings ADD CONSTRAINT chk_mummified_range
    CHECK (mummified >= 0);

ALTER TABLE weanings ADD CONSTRAINT chk_weaned_count
    CHECK (weaned_count >= 0 AND weaned_count <= 25);
ALTER TABLE weanings ADD CONSTRAINT chk_weaning_age
    CHECK (weaning_age_days >= 10 AND weaning_age_days <= 60);

ALTER TABLE matings ADD CONSTRAINT chk_mating_number
    CHECK (mating_number >= 1 AND mating_number <= 5);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [C-07] pregnancy_checks 에 farm_id 추가                                 │
-- └──────────────────────────────────────────────────────────────────────────┘

ALTER TABLE pregnancy_checks
    ADD COLUMN farm_id UUID NOT NULL REFERENCES farms(id);
CREATE INDEX idx_pc_farm ON pregnancy_checks(farm_id);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [M-01 + H-02] 모돈 상태 전이 트리거 + exit_date                         │
-- │  이벤트 INSERT 시 sows.status 자동 전이 (수동 UPDATE 오류 방지)           │
-- └──────────────────────────────────────────────────────────────────────────┘

-- exit_date 추가: 특정 시점 재고 역추적 가능 (피그플랜 OUT_DT 대응)
ALTER TABLE sows ADD COLUMN exit_date DATE;
CREATE INDEX idx_sow_exit ON sows(exit_date) WHERE exit_date IS NOT NULL;

-- 교배 INSERT → GESTATING
CREATE OR REPLACE FUNCTION trg_fn_mating_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sows SET status = 'GESTATING', updated_at = NOW()
    WHERE id = NEW.sow_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mating_sow_status
    AFTER INSERT ON matings
    FOR EACH ROW EXECUTE FUNCTION trg_fn_mating_status();

-- 분만 INSERT → LACTATING + parity +1
CREATE OR REPLACE FUNCTION trg_fn_farrowing_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sows
    SET status = 'LACTATING', parity = parity + 1, updated_at = NOW()
    WHERE id = NEW.sow_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_farrowing_sow_status
    AFTER INSERT ON farrowings
    FOR EACH ROW EXECUTE FUNCTION trg_fn_farrowing_status();

-- 이유 INSERT → WEANED
CREATE OR REPLACE FUNCTION trg_fn_weaning_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE sows SET status = 'WEANED', updated_at = NOW()
    WHERE id = NEW.sow_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_weaning_sow_status
    AFTER INSERT ON weanings
    FOR EACH ROW EXECUTE FUNCTION trg_fn_weaning_status();

-- 도태/폐사 INSERT → CULLED/DEAD + exit_date
CREATE OR REPLACE FUNCTION trg_fn_removal_status()
RETURNS TRIGGER AS $$
DECLARE
    v_status VARCHAR(10);
BEGIN
    v_status := CASE NEW.removal_type WHEN 'DEAD' THEN 'DEAD' ELSE 'CULLED' END;
    UPDATE sows
    SET status = v_status, exit_date = NEW.removal_date, updated_at = NOW()
    WHERE id = NEW.sow_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_removal_sow_status
    AFTER INSERT ON removals
    FOR EACH ROW EXECUTE FUNCTION trg_fn_removal_status();


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [M-03] 농장별 번식 파라미터 (farm_configs)                               │
-- │  피그플랜 TC_FARM_CONFIG 대응. 임신기간/포유기간 농장별 커스텀.            │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE farm_configs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id      UUID NOT NULL REFERENCES farms(id),
    config_key   VARCHAR(50) NOT NULL
        CHECK (config_key IN (
            'GESTATION_DAYS',        -- 임신 기간 (기본 114)
            'LACTATION_DAYS',        -- 포유 기간 (기본 21)
            'WEI_TARGET_DAYS',       -- 이유→교배 목표 간격 (기본 7)
            'PREGNANCY_CHECK_DAY',   -- 임신확인 시점: 교배 후 N일 (기본 25)
            'FARROWING_ALERT_DAYS',  -- 분만 예정 알림: D-N일
            'WEANING_ALERT_DAYS',    -- 이유 예정 알림: D-N일
            'NPD_ALERT_THRESHOLD',   -- NPD 경보 기준값 (일)
            'SOW_CULL_PARITY_THRESHOLD' -- 도태 권고 산차
        )),
    config_value VARCHAR(100) NOT NULL,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (farm_id, config_key)
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  [M-06 / M-07] 날짜 검증 트리거 + 뷰 수정                                │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 분만 날짜 검증: 분만일 > 교배일, 임신기간 100~130일
CREATE OR REPLACE FUNCTION validate_farrowing_dates()
RETURNS TRIGGER AS $$
DECLARE
    v_mating_date    DATE;
    v_gestation_days INT;
BEGIN
    SELECT mating_date INTO v_mating_date
    FROM matings WHERE id = NEW.mating_id;

    IF v_mating_date IS NOT NULL THEN
        IF NEW.farrowing_date <= v_mating_date THEN
            RAISE EXCEPTION 'Farrowing date must be after mating date';
        END IF;

        v_gestation_days := NEW.farrowing_date - v_mating_date;
        IF v_gestation_days < 100 OR v_gestation_days > 130 THEN
            RAISE EXCEPTION
                'Invalid gestation period: % days (expected 100-130)',
                v_gestation_days;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_farrowing_dates
    BEFORE INSERT OR UPDATE ON farrowings
    FOR EACH ROW EXECUTE FUNCTION validate_farrowing_dates();

-- 이유 날짜 검증: 이유일 > 분만일, 포유기간 10~60일 + weaning_age_days 자동계산
CREATE OR REPLACE FUNCTION validate_weaning_dates()
RETURNS TRIGGER AS $$
DECLARE
    v_farrowing_date DATE;
    v_nursing_days   INT;
BEGIN
    SELECT farrowing_date INTO v_farrowing_date
    FROM farrowings WHERE id = NEW.farrowing_id;

    IF v_farrowing_date IS NOT NULL THEN
        IF NEW.weaning_date <= v_farrowing_date THEN
            RAISE EXCEPTION 'Weaning date must be after farrowing date';
        END IF;

        v_nursing_days := NEW.weaning_date - v_farrowing_date;
        IF v_nursing_days < 10 OR v_nursing_days > 60 THEN
            RAISE EXCEPTION
                'Invalid nursing period: % days (expected 10-60)',
                v_nursing_days;
        END IF;

        NEW.weaning_age_days := v_nursing_days;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_weaning_dates
    BEFORE INSERT OR UPDATE ON weanings
    FOR EACH ROW EXECUTE FUNCTION validate_weaning_dates();

-- [M-07] v_farm_psy: deleted_at IS NULL 필터 추가
CREATE OR REPLACE VIEW v_farm_psy AS
SELECT
    s.farm_id,
    DATE_TRUNC('year', w.weaning_date)::DATE AS year_start,
    COUNT(DISTINCT s.id)                     AS avg_sow_count,
    SUM(w.weaned_count)                      AS total_weaned,
    ROUND(
        SUM(w.weaned_count)::NUMERIC
        / NULLIF(COUNT(DISTINCT s.id), 0),
    2)                                       AS psy
FROM sows s
LEFT JOIN farrowings f ON f.sow_id = s.id AND f.deleted_at IS NULL
LEFT JOIN weanings   w ON w.sow_id = s.id AND w.deleted_at IS NULL
WHERE s.deleted_at IS NULL
GROUP BY s.farm_id, DATE_TRUNC('year', w.weaning_date);

-- [M-06] v_sow_npd: LATERAL + LIMIT 1 (중복 집계 방지)
CREATE OR REPLACE VIEW v_sow_npd AS
SELECT
    s.id         AS sow_id,
    s.farm_id,
    w.id         AS weaning_id,
    w.weaning_date,
    m_next.mating_date AS next_mating_date,
    (m_next.mating_date - w.weaning_date) AS wei_days
FROM sows s
JOIN weanings w ON w.sow_id = s.id AND w.deleted_at IS NULL
LEFT JOIN LATERAL (
    SELECT mating_date
    FROM matings
    WHERE sow_id = s.id
      AND mating_date > w.weaning_date
      AND mating_date <= w.weaning_date + INTERVAL '60 days'
      AND deleted_at IS NULL
    ORDER BY mating_date ASC
    LIMIT 1
) m_next ON TRUE
WHERE s.deleted_at IS NULL;


-- ============================================================================
-- v2.0 FULL SUMMARY (적용 후)
-- ============================================================================
-- Config Layer (신규):
--   market_defaults, region_defaults, default_metric_values,
--   scope_kpi_recommendations, compliance_profiles, market_price_reference
--
-- Core Domain 신규 테이블:
--   breeding_cycles         [C-03] 산차별 사이클
--   reproductive_events     [C-01] 재발정/유산/사고
--   piglet_events           [C-02] 포유중 자돈 이동/폐사
--   farm_configs            [M-03] 농장별 번식 파라미터
--
-- Core Domain 변경:
--   sows               + exit_date             [H-02]
--   sows               + CHECK (status, entry_type, parity)   [C-05, C-06]
--   matings            + breeding_cycle_id      [C-03]
--   matings            + CHECK (mating_type, mating_number)   [C-05, C-06]
--   farrowings         + breeding_cycle_id      [C-03]
--   farrowings         + mating_id NOT NULL     [C-04]
--   farrowings         + CHECK (born counts, total_born integrity) [C-06]
--   weanings           + breeding_cycle_id      [C-03]
--   weanings           + farrowing_id NOT NULL  [C-04]
--   weanings           + CHECK (weaned_count, weaning_age_days)    [C-06]
--   pregnancy_checks   + farm_id NOT NULL       [C-07]
--   removals           + CHECK (removal_type, reason_category)     [C-05]
--   health_events      + CHECK (event_type, severity, XOR target)  [C-05]
--   buildings          + CHECK (building_type)  [C-05]
--   feed_records       + CHECK (XOR target)     [C-05]
--
-- 신규 함수/트리거:
--   fn_verify_piglet_count()        [C-02] 두수 정합성 검증
--   validate_farrowing_sequence()   [C-04] 교배→분만 순서
--   validate_farrowing_sow_match()  [C-04] 분만 sow 일치
--   validate_weaning_sow_match()    [C-04] 이유 sow 일치
--   validate_farrowing_dates()      [M-06] 임신기간 날짜 검증
--   validate_weaning_dates()        [M-06] 포유기간 날짜 검증
--   trg_fn_mating_status()          [M-01] 교배→GESTATING
--   trg_fn_farrowing_status()       [M-01] 분만→LACTATING + parity+1
--   trg_fn_weaning_status()         [M-01] 이유→WEANED
--   trg_fn_removal_status()         [M-01] 도태/폐사→CULLED/DEAD + exit_date
--
-- 신규 인덱스:
--   idx_one_active_cycle, idx_one_weaning_per_farrowing (부분 인덱스)
--   idx_bc_farm_sow, idx_re_farm_sow, idx_re_mating, idx_pe_farrowing
--   idx_pe_farm_date, idx_pc_farm, idx_sow_exit
--
-- 수정된 뷰:
--   v_farm_psy   deleted_at IS NULL 필터  [M-07]
--   v_sow_npd    LATERAL + LIMIT 1        [M-06]
-- ============================================================================
