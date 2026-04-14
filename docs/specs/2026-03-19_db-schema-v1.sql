-- ============================================================================
-- PigOS — Global DB Schema v1.0
-- ============================================================================
-- 설계 원칙:
--   1. 모듈형 구조: 각 도메인 독립 배포 가능 (마이크로서비스 대응)
--   2. 지역 중립: 6개 권역(KR/EU/US/BR/SEA/CN) 단일 스키마로 커버
--   3. Schema-per-tenant: 농장별 스키마 분리 (Phase 1~2)
--   4. 감사 추적: 모든 CUD 이벤트 audit_log 기록
--   5. 오프라인 동기화: offline_created_at + synced_at + conflict 지원
--   6. 단위계 자동 전환: METRIC/IMPERIAL 농장 설정 기반
--   7. 다국어: i18n 코드 테이블 분리
--
-- 기준 문서:
--   - PigOS_GlobalStrategy.html (심층분석 16개 섹션)
--   - 01_글로벌_양돈_관리포인트_지역별분석.md
--   - 04_글로벌_양돈_관리포인트_개발반영사항.md
--   - 03_MVP_개발계획.md
--
-- 작성: 2026.03.19
-- ============================================================================


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 0: PLATFORM — 멀티테넌시 / 인증 / 감사                          │
-- │  Phase 1 필수                                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 0-1. 조직 (회사/계열화 그룹)
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    org_type        VARCHAR(20) NOT NULL DEFAULT 'INDEPENDENT',
        -- INDEPENDENT / INTEGRATOR / COOPERATIVE / GOVERNMENT
    country         CHAR(2) NOT NULL,           -- ISO 3166-1 alpha-2
    timezone        VARCHAR(50) NOT NULL DEFAULT 'UTC',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 0-2. 농장
CREATE TABLE farms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    farm_code       VARCHAR(30) UNIQUE NOT NULL, -- FARM-VN-001
    name            VARCHAR(200) NOT NULL,
    country         CHAR(2) NOT NULL,
    region          VARCHAR(100),                -- 주/도/성
    gps_lat         DECIMAL(10,7),               -- 역학/물류/보험 리스크
    gps_lng         DECIMAL(10,7),
    timezone        VARCHAR(50) NOT NULL,
    unit_system     VARCHAR(10) NOT NULL DEFAULT 'METRIC',
        -- METRIC / IMPERIAL
    language        VARCHAR(5) NOT NULL DEFAULT 'en',
        -- en / ko / vi / th / pt / zh / da / nl / de / es
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
        -- USD / KRW / VND / EUR / BRL / CNY
    date_format     VARCHAR(15) NOT NULL DEFAULT 'yyyy-MM-dd',
        -- yyyy-MM-dd / dd/MM/yyyy / MM/dd/yyyy
    notification_channel VARCHAR(20) DEFAULT 'EMAIL',
        -- EMAIL / SMS / KAKAOTALK / ZALO / WECHAT / WHATSAPP
    farm_scale      VARCHAR(15) DEFAULT 'COMMERCIAL',
        -- COMMERCIAL / SMALL / BACKYARD (SEA 구분)
    internet_reliability VARCHAR(10) DEFAULT 'HIGH',
        -- HIGH / LOW / NONE (오프라인 동기화 전략 결정)
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_farms_org ON farms(org_id);
CREATE INDEX idx_farms_country ON farms(country);

-- 0-3. 사용자 (7단계 권한)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id),
    email           VARCHAR(255) UNIQUE,
    phone           VARCHAR(30),
    name            VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(30) NOT NULL DEFAULT 'FARM_WORKER',
        -- ADMIN / COMPANY / FARM_OWNER / FARM_MANAGER
        -- FARM_WORKER / VIEWER / API_CLIENT
    language        VARCHAR(5) DEFAULT 'en',
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 0-4. 사용자-농장 매핑 (다대다: 한 사용자가 여러 농장 접근 가능)
CREATE TABLE user_farms (
    user_id         UUID NOT NULL REFERENCES users(id),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    role_override   VARCHAR(30),    -- 농장별 역할 오버라이드 (nullable)
    PRIMARY KEY (user_id, farm_id)
);

-- 0-5. 감사 로그
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,
    farm_id         UUID,
    action          VARCHAR(20) NOT NULL,   -- CREATE / UPDATE / DELETE / LOGIN / EXPORT / MONTH_CLOSE
    entity_type     VARCHAR(50) NOT NULL,   -- sows / matings / farrowings ...
    entity_id       UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_farm ON audit_log(farm_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);

-- 0-6. 오프라인 동기화 큐
CREATE TABLE sync_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    device_id       VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(50) NOT NULL,
    entity_id       UUID NOT NULL,
    operation       VARCHAR(10) NOT NULL,   -- INSERT / UPDATE / DELETE
    payload         JSONB NOT NULL,
    offline_created_at TIMESTAMPTZ NOT NULL, -- 오프라인 기기에서 입력 시각
    synced_at       TIMESTAMPTZ,             -- 서버 동기화 시각
    conflict        BOOLEAN DEFAULT FALSE,
    conflict_resolution VARCHAR(20),         -- LWW / MANUAL / MERGED
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sync_farm_pending ON sync_queue(farm_id) WHERE synced_at IS NULL;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 1: SOW MANAGEMENT — 모돈 번식 관리 (Core)                        │
-- │  Phase 1 필수 — MVP 핵심                                                │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 1-1. 돈방/건물
CREATE TABLE buildings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    name            VARCHAR(100) NOT NULL,
    building_type   VARCHAR(30) NOT NULL,
        -- GESTATION / FARROWING / NURSERY / FINISHER / BOAR / QUARANTINE / GDU
    floor_number    INT DEFAULT 1,          -- 중국 다층 양돈 빌딩 대응
    capacity        INT,
    housing_type    VARCHAR(20) DEFAULT 'GROUP',
        -- STALL / GROUP / FREE_RANGE / OUTDOOR
    area_per_pig_m2 DECIMAL(5,2),           -- 두당 면적 (m2)
    area_per_pig_sqft DECIMAL(5,2),         -- 미국용 sqft 자동 환산
    prop12_compliant BOOLEAN,               -- 미국 CA Prop 12 준수
    welfare_enrichment VARCHAR(100),         -- EU: 짚/건초/장난감 등
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_buildings_farm ON buildings(farm_id);

-- 1-2. 씨수퇘지 (Boar)
CREATE TABLE boars (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    ear_tag         VARCHAR(30) NOT NULL,
    breed           VARCHAR(50),
    breed_company   VARCHAR(30),    -- PIC / TOPIGS / DANBRED / HYPOR / DOMESTIC_KR
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
        -- ACTIVE / CULLED / DEAD / TRANSFERRED
    entry_date      DATE NOT NULL,
    entry_type      VARCHAR(20),    -- PURCHASE / BORN / TRANSFER
    semen_quality   VARCHAR(20),    -- EXCELLENT / GOOD / FAIR / POOR
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(farm_id, ear_tag)
);

-- 1-3. 모돈 (Sow) — PigOS 핵심 개체
CREATE TABLE sows (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    building_id     UUID REFERENCES buildings(id),
    ear_tag         VARCHAR(30) NOT NULL,
    rfid_tag        VARCHAR(50),            -- UHF RFID (LeeO 방식 개체추적)
    parity          INT NOT NULL DEFAULT 0, -- 산차
    breed           VARCHAR(50),
    breed_company   VARCHAR(30),
    genetics_id     VARCHAR(50),            -- 유전사 개체 ID (PIC/Topigs/DanBred)
    status          VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
        -- ACTIVE / GESTATING / LACTATING / WEANED / DRY / CULLED / DEAD
    entry_date      DATE NOT NULL,
    entry_type      VARCHAR(20) NOT NULL,
        -- GILT / PURCHASE / TRANSFER / BORN
    source_farm_id  UUID,                   -- 도입 원농장 (이동 추적)
    stall_to_group_converted BOOLEAN,       -- 한국: 군사 전환 완료 여부
    nurse_sow_flag  BOOLEAN DEFAULT FALSE,  -- EU: 위탁 모돈
    ractopamine_free BOOLEAN DEFAULT TRUE,  -- 미국: 무락토파민 여부
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(farm_id, ear_tag)
);
CREATE INDEX idx_sows_farm_status ON sows(farm_id, status);
CREATE INDEX idx_sows_parity ON sows(farm_id, parity);

-- 1-4. 교배 (Mating)
CREATE TABLE matings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    boar_id         UUID REFERENCES boars(id),
    mating_date     DATE NOT NULL,
    mating_type     VARCHAR(10) NOT NULL,   -- AI / NATURAL
    semen_source    VARCHAR(50),            -- 정액 공급처
    semen_batch     VARCHAR(50),            -- 정액 배치번호 (이력추적)
    technician_id   UUID REFERENCES users(id),
    estrus_detected_at TIMESTAMPTZ,         -- 발정 감지 시각
    mating_number   INT DEFAULT 1,          -- 복수 교배 시 순번 (1st/2nd/3rd)
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    offline_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_matings_sow ON matings(sow_id, mating_date DESC);

-- 1-5. 임신 확인 (Pregnancy Check)
CREATE TABLE pregnancy_checks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    mating_id       UUID REFERENCES matings(id),
    check_date      DATE NOT NULL,
    check_method    VARCHAR(20) NOT NULL,   -- ULTRASOUND / BACKFAT / VISUAL / NONE
    result          VARCHAR(10) NOT NULL,   -- POSITIVE / NEGATIVE / UNCERTAIN
    checked_by      UUID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 1-6. 분만 (Farrowing)
CREATE TABLE farrowings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    mating_id       UUID REFERENCES matings(id),
    building_id     UUID REFERENCES buildings(id),
    farrowing_date  DATE NOT NULL,
    parity_at_birth INT NOT NULL,
    -- 산자수 상세
    total_born      INT NOT NULL DEFAULT 0,
    born_alive      INT NOT NULL DEFAULT 0,
    stillborn       INT NOT NULL DEFAULT 0,
    mummified       INT NOT NULL DEFAULT 0,
    -- 체중
    avg_birth_weight_kg DECIMAL(5,2),       -- 평균 출생 체중
    litter_weight_kg    DECIMAL(6,2),       -- 복당 총 체중
    -- 분만 상세
    farrowing_duration_min INT,             -- 분만 소요 시간(분)
    assisted        BOOLEAN DEFAULT FALSE,  -- 보조 분만 여부
    induction       BOOLEAN DEFAULT FALSE,  -- 유도 분만 여부
    -- 위탁
    cross_fostered_in  INT DEFAULT 0,       -- 타 모돈에서 위탁 받음
    cross_fostered_out INT DEFAULT 0,       -- 타 모돈으로 위탁 보냄
    nurse_sow_id    UUID REFERENCES sows(id), -- 위탁 모돈 ID
    --
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    offline_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_farrowings_sow ON farrowings(sow_id, farrowing_date DESC);
CREATE INDEX idx_farrowings_farm_date ON farrowings(farm_id, farrowing_date DESC);

-- 1-7. 이유 (Weaning)
CREATE TABLE weanings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    farrowing_id    UUID REFERENCES farrowings(id),
    weaning_date    DATE NOT NULL,
    weaned_count    INT NOT NULL DEFAULT 0,
    weaning_age_days INT,                   -- 이유 일령
    avg_weaning_weight_kg DECIMAL(5,2),     -- 평균 이유 체중
    litter_weaning_weight_kg DECIMAL(6,2),  -- 복당 이유 체중
    destination     VARCHAR(30),            -- NURSERY / FINISHER / SALE / TRANSFER
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    offline_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_weanings_sow ON weanings(sow_id, weaning_date DESC);

-- 1-8. 폐사/도태 (Removal)
CREATE TABLE removals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    removal_date    DATE NOT NULL,
    removal_type    VARCHAR(10) NOT NULL,   -- CULL / DEAD / SOLD / TRANSFER
    reason_category VARCHAR(30) NOT NULL,
        -- REPRODUCTIVE / LAMENESS / DISEASE / AGE / LOW_PRODUCTION
        -- PROLAPSE / INJURY / BODY_CONDITION / OTHER
    reason_detail   VARCHAR(100),
    parity_at_removal INT,
    body_weight_kg  DECIMAL(6,2),
    destination     VARCHAR(100),           -- 도축장명 / 이동 농장
    pop_flag        BOOLEAN DEFAULT FALSE,  -- 미국: POP (골반장기탈출) 여부
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 2: GROWING / FATTENING — 비육돈 관리                             │
-- │  Phase 2 확장                                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 2-1. 동물 그룹 (배치 관리)
CREATE TABLE animal_groups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    building_id     UUID REFERENCES buildings(id),
    group_code      VARCHAR(30) NOT NULL,
    group_type      VARCHAR(20) NOT NULL,   -- NURSERY / GROWER / FINISHER / WEAN_TO_FINISH
    entry_date      DATE NOT NULL,
    entry_count     INT NOT NULL,
    entry_avg_weight_kg DECIMAL(6,2),
    current_count   INT,
    status          VARCHAR(15) DEFAULT 'ACTIVE', -- ACTIVE / CLOSED / SHIPPED
    source_farrowing_ids UUID[],            -- 원래 분만 ID 배열
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2-2. 비육 기록 (주기적 체중/폐사 기록)
CREATE TABLE grow_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id        UUID NOT NULL REFERENCES animal_groups(id),
    record_date     DATE NOT NULL,
    head_count      INT,
    avg_weight_kg   DECIMAL(6,2),
    mortality_count INT DEFAULT 0,
    mortality_reason VARCHAR(50),
    adg_g           DECIMAL(6,1),           -- 일당 증체 (g/day)
    fcr             DECIMAL(4,2),           -- 사료전환율
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2-3. 출하 (Shipment)
CREATE TABLE shipments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    group_id        UUID REFERENCES animal_groups(id),
    shipment_date   DATE NOT NULL,
    head_count      INT NOT NULL,
    avg_live_weight_kg DECIMAL(6,2),
    destination     VARCHAR(200),           -- 도축장명
    destination_type VARCHAR(20),           -- SLAUGHTERHOUSE / WET_MARKET / TRANSFER
    market_type     VARCHAR(20),            -- WET / MODERN / EXPORT (SEA wet market 구분)
    trader_id       UUID,                   -- SEA: 중개인
    ractopamine_free BOOLEAN DEFAULT TRUE,  -- 미국: 수출 적격
    transport_vehicle VARCHAR(50),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2-4. 도체 성적 (Carcass / Slaughter Grade)
CREATE TABLE carcass_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id     UUID REFERENCES shipments(id),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    slaughter_date  DATE NOT NULL,
    head_count      INT,
    -- 공통
    avg_carcass_weight_kg DECIMAL(6,2),
    avg_backfat_mm  DECIMAL(5,1),
    avg_loin_depth_mm DECIMAL(5,1),
    dressing_pct    DECIMAL(5,2),           -- 도체율
    -- 한국 등급
    grade_kr        VARCHAR(5),             -- 1+ / 1 / 2 / 등외
    grade_kr_1plus_ratio DECIMAL(5,2),      -- 1+등급 비율
    price_per_kg_kr DECIMAL(10,2),          -- 한국: kg당 가격
    -- EU SEUROP 등급
    seurop_grade    CHAR(1),                -- S / E / U / R / O / P
    lmp_pct         DECIMAL(5,2),           -- Lean Meat Percentage (정육률)
    autofom_data    JSONB,                  -- AutoFOM 측정값
    -- 미국
    carcass_merit_score DECIMAL(5,2),       -- 미국: carcass merit 기반 가치
    price_per_cwt_us DECIMAL(10,2),         -- 미국: cwt당 가격
    -- 브라질
    sif_inspection_id VARCHAR(30),          -- 브라질: SIF 검사 번호
    --
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 3: FEED — 사료 관리                                              │
-- │  Phase 2 확장 (미국/EU 우선)                                             │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 3-1. 사료빈 (Feed Bin)
CREATE TABLE feed_bins (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    building_id     UUID REFERENCES buildings(id),
    bin_code        VARCHAR(30) NOT NULL,
    capacity_kg     DECIMAL(10,2),
    current_level_kg DECIMAL(10,2),
    feed_type       VARCHAR(50),            -- STARTER / GROWER / FINISHER / SOW_GESTATION / SOW_LACTATION
    last_filled_at  TIMESTAMPTZ,
    low_level_alert_kg DECIMAL(10,2),       -- 재고 부족 알림 기준
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3-2. 사료 배합 (Feed Formula)
CREATE TABLE feed_formulas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    name            VARCHAR(100) NOT NULL,
    feed_stage      VARCHAR(30) NOT NULL,   -- 갓돈/젖돈/자돈/육성/비육/모돈임신/모돈포유
    -- 주요 성분 (% 기반)
    corn_pct        DECIMAL(5,2),
    soybean_meal_pct DECIMAL(5,2),
    ddgs_pct        DECIMAL(5,2),           -- 미국: 건조주정박
    barley_pct      DECIMAL(5,2),           -- EU 북유럽: 보리
    wheat_pct       DECIMAL(5,2),           -- EU 북유럽: 밀
    -- 규제 관련
    nitrogen_content_pct DECIMAL(5,3),      -- EU 질소 배출 계산용
    phosphorus_content_pct DECIMAL(5,3),    -- EU
    ractopamine_included BOOLEAN DEFAULT FALSE, -- 미국: 락토파민 포함 여부
    -- 원가
    cost_per_kg     DECIMAL(8,2),
    cost_currency   VARCHAR(3),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3-3. 사료 입고 (Feed Delivery / Feed Mill 연동)
CREATE TABLE feed_deliveries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    feed_bin_id     UUID REFERENCES feed_bins(id),
    formula_id      UUID REFERENCES feed_formulas(id),
    feed_mill_name  VARCHAR(100),
    feed_mill_id    UUID,                   -- 외부 Feed Mill 시스템 연동용
    delivery_date   DATE NOT NULL,
    quantity_kg     DECIMAL(10,2) NOT NULL,
    quantity_lbs    DECIMAL(10,2),           -- 미국: 파운드 자동 환산
    cost_per_unit   DECIMAL(8,2),
    cost_unit       VARCHAR(10),            -- KG / CWT / TON
    total_cost      DECIMAL(12,2),
    invoice_no      VARCHAR(50),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3-4. 급이 기록 (Daily Feed Record)
CREATE TABLE feed_records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    building_id     UUID REFERENCES buildings(id),
    group_id        UUID REFERENCES animal_groups(id),
    sow_id          UUID REFERENCES sows(id),          -- 개체별 급이 시
    record_date     DATE NOT NULL,
    formula_id      UUID REFERENCES feed_formulas(id),
    quantity_kg     DECIMAL(8,2) NOT NULL,
    head_count      INT,
    feed_per_head_kg DECIMAL(6,3),          -- 두당 급이량 자동 계산
    esf_station_id  VARCHAR(30),            -- ESF 급이기 연동 시
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 4: HEALTH — 건강/방역/백신/항생제                                 │
-- │  Phase 1 (SEA ASF 경보) + Phase 2 (EU 항생제 보고)                       │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 4-1. 건강 이벤트 (Health Event)
CREATE TABLE health_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID REFERENCES sows(id),
    group_id        UUID REFERENCES animal_groups(id),
    building_id     UUID REFERENCES buildings(id),
    event_date      DATE NOT NULL,
    event_type      VARCHAR(20) NOT NULL,
        -- DISEASE / INJURY / OBSERVATION / DEATH / CULLING
    disease_code    VARCHAR(20),
        -- ASF / PRRS / PED / FMD / MH / APP / PMWS / ILEITIS / ERYSIPELAS / OTHER
    severity        VARCHAR(10),            -- MILD / MODERATE / SEVERE / FATAL
    affected_count  INT DEFAULT 1,
    mortality_count INT DEFAULT 0,
    -- ASF 특화 (SEA/KR/CN)
    asf_zone_level  INT,                    -- 1/2/3 위험 구역 등급
    quarantine_start DATE,
    quarantine_end  DATE,
    -- PRRS 특화 (US)
    prrs_status     VARCHAR(20),            -- POSITIVE / NEGATIVE / STABLE / VACCINATED
    prrs_strain     VARCHAR(50),            -- PRRSV-1 / PRRSV-2 / 1-4-4C / 1C.5
    -- Morrison MSHMP
    mshmp_reported  BOOLEAN DEFAULT FALSE,  -- 미국: MSHMP 보고 여부
    --
    vet_name        VARCHAR(100),
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    offline_created_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_health_farm_date ON health_events(farm_id, event_date DESC);
CREATE INDEX idx_health_disease ON health_events(disease_code, event_date DESC);

-- 4-2. 백신 접종 (Vaccination)
CREATE TABLE vaccinations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID REFERENCES sows(id),
    group_id        UUID REFERENCES animal_groups(id),
    vaccine_name    VARCHAR(100) NOT NULL,
    vaccine_type    VARCHAR(30),            -- LIVE / KILLED / SUBUNIT / MRNA
    manufacturer    VARCHAR(100),           -- Zoetis / BI / MSD / Ceva / NAVET 등
    batch_no        VARCHAR(50),
    -- ASF 백신 특화 (베트남)
    asf_vaccine_flag BOOLEAN DEFAULT FALSE,
    asf_vaccine_name VARCHAR(100),          -- NAVET-ASFVAC / AVAC ASF LIVE / DACOVAC-ASF2
    --
    dose_count      INT NOT NULL DEFAULT 1,
    vaccination_date DATE NOT NULL,
    next_due_date   DATE,
    administered_by UUID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4-3. 투약/항생제 (Medication)
CREATE TABLE medications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID REFERENCES sows(id),
    group_id        UUID REFERENCES animal_groups(id),
    medication_date DATE NOT NULL,
    drug_name       VARCHAR(100) NOT NULL,
    active_substance VARCHAR(100),
    -- 항생제 규제 필드
    antibiotic_flag BOOLEAN NOT NULL DEFAULT FALSE,
    antibiotic_class VARCHAR(50),           -- TETRACYCLINE / PENICILLIN / MACROLIDE / COLISTIN 등
    dose_mg         DECIMAL(10,2),
    dose_per_kg_bw  DECIMAL(8,4),           -- mg/kg 체중
    treatment_days  INT,
    animal_count    INT DEFAULT 1,
    -- EU 항생제 보고 자동 계산
    ddda_value      DECIMAL(10,4),          -- Defined Daily Dose Animal
    mg_pcu          DECIMAL(10,4),          -- mg/PCU (ESVAC 보고)
    mg_animal_biomass DECIMAL(10,4),        -- 한국: WOAH mg/Animal Biomass (2029~)
    collective_treatment BOOLEAN DEFAULT FALSE, -- EU: 집단 투약 (2022년~ 금지)
    -- 미국 VFD
    vfd_number      VARCHAR(50),            -- 미국: VFD 처방 번호
    vfd_vet_license VARCHAR(30),
    vfd_issued_date DATE,
    vfd_expiry_date DATE,                   -- VFD 2년 보관 의무
    -- 출하 제한
    withdrawal_days INT,                    -- 출하 제한일 수
    withdrawal_end_date DATE,               -- 출하 가능일 자동 계산
    --
    prescribed_by   VARCHAR(100),
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_med_farm_date ON medications(farm_id, medication_date DESC);
CREATE INDEX idx_med_antibiotic ON medications(farm_id, antibiotic_flag) WHERE antibiotic_flag = TRUE;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 5: GENETICS — 유전/종돈                                          │
-- │  Phase 2~3 확장                                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 5-1. 유전 데이터
CREATE TABLE genetics (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sow_id          UUID REFERENCES sows(id),
    boar_id         UUID REFERENCES boars(id),
    breed_company   VARCHAR(30) NOT NULL,
        -- PIC / TOPIGS / DANBRED / HYPOR / HENDRIX / DOMESTIC_KR / OTHER
    external_id     VARCHAR(50),            -- 유전사 외부 ID
    -- EBV (Estimated Breeding Value)
    ebv_total_born  DECIMAL(6,2),
    ebv_born_alive  DECIMAL(6,2),
    ebv_growth_rate DECIMAL(6,2),
    ebv_backfat     DECIMAL(6,2),
    ebv_feed_conversion DECIMAL(6,2),
    ebv_litter_weight DECIMAL(6,2),
    -- 근교 계수
    inbreeding_coefficient DECIMAL(6,4),
    -- 유전형
    genotype_data   JSONB,                  -- 유전자형 raw 데이터
    pedigree_sire_id UUID,                  -- 아비 ID
    pedigree_dam_id  UUID,                  -- 어미 ID
    --
    evaluation_date DATE,
    source          VARCHAR(100),           -- 유전사/검정소
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 6: COMPLIANCE — 규정 준수 / 이력 추적                             │
-- │  Phase 2 (EU/KR 우선)                                                   │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 6-1. 국가별 규정 보고
CREATE TABLE compliance_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    country         CHAR(2) NOT NULL,
    report_type     VARCHAR(30) NOT NULL,
        -- ESVAC / HIT / TAM / CHR / MTRACE / GTA / VFD_LOG / PQA_PLUS / MARA
    report_period   VARCHAR(10),            -- 2026-Q1 등
    status          VARCHAR(15) DEFAULT 'DRAFT',
        -- DRAFT / SUBMITTED / ACCEPTED / REJECTED
    report_data     JSONB NOT NULL,         -- 보고서 데이터 (국가별 형식)
    submitted_at    TIMESTAMPTZ,
    submitted_by    UUID REFERENCES users(id),
    external_ref    VARCHAR(100),           -- 외부 시스템 접수 번호
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6-2. 동물 이동 증명 (GTA/TRACES/mtrace)
CREATE TABLE animal_movements (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    movement_type   VARCHAR(10) NOT NULL,   -- INBOUND / OUTBOUND
    movement_date   DATE NOT NULL,
    origin_farm     VARCHAR(100),
    destination_farm VARCHAR(100),
    animal_type     VARCHAR(20),            -- SOW / BOAR / PIGLET / FINISHER
    head_count      INT NOT NULL,
    -- 국가별 증명
    gta_number      VARCHAR(30),            -- 브라질: GTA 번호
    traces_number   VARCHAR(30),            -- EU: TRACES 번호
    mtrace_id       VARCHAR(30),            -- 한국: mtrace 이력번호
    -- 생물보안
    vehicle_disinfected BOOLEAN,
    quarantine_required BOOLEAN DEFAULT FALSE,
    ractopamine_free_cert BOOLEAN,          -- 브라질: 수출용
    --
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6-3. 동물복지 인증 (EU)
CREATE TABLE welfare_certifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    cert_type       VARCHAR(30) NOT NULL,
        -- BETER_LEVEN / BEDRE_DYREVELFAERD / TIERHALTUNG / RSPCA / GLOBAL_GAP
    cert_level      INT,                    -- 1/2/3 (별 또는 하트)
    issued_date     DATE,
    expiry_date     DATE,
    auditor         VARCHAR(100),
    status          VARCHAR(15) DEFAULT 'ACTIVE',
    checklist_data  JSONB,                  -- 인증 요건 체크리스트
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6-4. 옐로카드 추적 (덴마크)
CREATE TABLE yellow_card_tracking (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    period          VARCHAR(10) NOT NULL,   -- 2026-H1
    antibiotic_usage_ddda DECIMAL(10,4),
    national_threshold_ddda DECIMAL(10,4),
    status          VARCHAR(15),            -- NORMAL / WARNING / YELLOW_CARD
    action_plan     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 7: ENVIRONMENT / ESG — 환경/탄소/ESG                             │
-- │  Phase 3 확장                                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 7-1. 환경 센서 데이터 (TimescaleDB 권장)
CREATE TABLE environment_readings (
    farm_id         UUID NOT NULL REFERENCES farms(id),
    building_id     UUID NOT NULL REFERENCES buildings(id),
    reading_time    TIMESTAMPTZ NOT NULL,
    temperature_c   DECIMAL(5,1),
    humidity_pct    DECIMAL(5,1),
    ammonia_ppm     DECIMAL(6,2),
    co2_ppm         DECIMAL(7,1),
    h2s_ppm         DECIMAL(6,3),
    air_velocity_ms DECIMAL(5,2),
    PRIMARY KEY (farm_id, building_id, reading_time)
);
-- TimescaleDB 하이퍼테이블 전환
-- SELECT create_hypertable('environment_readings', 'reading_time');

-- 7-2. 탄소 배출 산출 (FAO GLEAM 기반)
CREATE TABLE carbon_footprint (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    period          VARCHAR(10) NOT NULL,   -- 2026-Q1
    -- FAO GLEAM Scope 1+2+3
    feed_co2e_kg    DECIMAL(12,2),          -- 사료 (68.8%)
    manure_co2e_kg  DECIMAL(12,2),          -- 분뇨 (22.9%)
    energy_co2e_kg  DECIMAL(12,2),          -- 에너지 (7.5%)
    other_co2e_kg   DECIMAL(12,2),          -- 기타
    total_co2e_kg   DECIMAL(12,2),
    co2e_per_kg_cwt DECIMAL(8,4),           -- kg CO2e / kg 도체중
    -- 분뇨 관리
    nitrogen_output_kg DECIMAL(10,2),       -- EU 질산염 지침 대응
    phosphorus_output_kg DECIMAL(10,2),
    manure_treatment VARCHAR(30),           -- LAGOON / SEPARATOR / BIOGAS / COMPOSTING
    --
    methodology     VARCHAR(20) DEFAULT 'GLEAM',
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7-3. AMR (항균제 내성) 모니터링
CREATE TABLE amr_monitoring (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sample_date     DATE NOT NULL,
    sample_type     VARCHAR(20),            -- FECAL / NASAL / ENVIRONMENTAL
    pathogen        VARCHAR(50),            -- E_COLI / SALMONELLA / MRSA / ENTEROCOCCUS
    antibiotic_tested VARCHAR(50),
    resistance      BOOLEAN,
    mic_value       DECIMAL(8,2),           -- Minimum Inhibitory Concentration
    lab_name        VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 8: KPI ENGINE — 지표 계산 / 벤치마킹                              │
-- │  Phase 1 (기본 PSY/NPD) → Phase 2 (전체 KPI + 벤치마킹)                  │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 8-1. KPI 스냅샷 (월별/분기별 자동 집계)
CREATE TABLE kpi_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    period          VARCHAR(10) NOT NULL,   -- 2026-03
    period_type     VARCHAR(10) NOT NULL,   -- MONTHLY / QUARTERLY / YEARLY
    -- 번식 KPI
    active_sow_count INT,
    psy             DECIMAL(5,2),           -- 모돈당 연간 이유 자돈수
    msy             DECIMAL(5,2),           -- 모돈당 연간 출하 두수
    npd_days        DECIMAL(5,1),           -- 비생산일수
    farrowing_rate  DECIMAL(5,1),           -- 분만율 (%)
    conception_rate DECIMAL(5,1),           -- 수태율 (%)
    avg_born_alive  DECIMAL(5,2),           -- 평균 생존산자수
    avg_weaned      DECIMAL(5,2),           -- 평균 이유두수
    avg_weaning_age DECIMAL(5,1),           -- 평균 이유일령
    pre_weaning_mortality DECIMAL(5,2),     -- 포유 중 폐사율 (%)
    sow_mortality   DECIMAL(5,2),           -- 모돈 폐사율 (%)
    replacement_rate DECIMAL(5,2),          -- 갱신율 (%)
    -- 비육 KPI
    avg_adg_g       DECIMAL(6,1),           -- 일당 증체
    avg_fcr         DECIMAL(4,2),           -- 사료전환율
    avg_days_to_market INT,                 -- 출하일령
    avg_market_weight_kg DECIMAL(6,2),      -- 출하 체중
    post_weaning_mortality DECIMAL(5,2),    -- 이유 후 폐사율
    -- 경제 KPI
    feed_cost_per_pig DECIMAL(10,2),        -- 두당 사료비
    total_cost_per_pig DECIMAL(10,2),       -- 두당 총 생산비
    revenue_per_pig DECIMAL(10,2),          -- 두당 수익
    cost_currency   VARCHAR(3),
    -- ROI 환산 (Blue Ocean 기능)
    fcr_savings_per_head DECIMAL(10,2),     -- "FCR 0.1↓ = X원 절감"
    psy_additional_revenue DECIMAL(12,2),   -- "PSY +1두 = X원 추가수익"
    --
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(farm_id, period, period_type)
);
CREATE INDEX idx_kpi_farm_period ON kpi_snapshots(farm_id, period DESC);

-- 8-2. 벤치마크 기준값 (국가/지역별)
CREATE TABLE benchmarks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country         CHAR(2) NOT NULL,
    region          VARCHAR(50),            -- 세부 지역 (주/도)
    period          VARCHAR(10) NOT NULL,
    farm_scale      VARCHAR(15),            -- COMMERCIAL / SMALL / TOP_10PCT
    -- 벤치마크 값
    psy_avg         DECIMAL(5,2),
    psy_top10       DECIMAL(5,2),
    psy_bottom10    DECIMAL(5,2),
    fcr_avg         DECIMAL(4,2),
    fcr_top10       DECIMAL(4,2),
    npd_avg         DECIMAL(5,1),
    farrowing_rate_avg DECIMAL(5,1),
    sow_mortality_avg DECIMAL(5,2),
    -- 원가 벤치마크
    production_cost_per_kg DECIMAL(8,2),    -- kg당 생산비
    cost_currency   VARCHAR(3),
    --
    source          VARCHAR(100),           -- PigCHAMP / DanBred / 한돈팜스 / USDA 등
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 9: MARKET DATA — 시세/선물 연동                                   │
-- │  Phase 3 확장                                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 9-1. 시세 데이터
CREATE TABLE market_prices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country         CHAR(2) NOT NULL,
    price_date      DATE NOT NULL,
    -- 돈가
    live_pig_price  DECIMAL(10,2),
    carcass_price   DECIMAL(10,2),
    price_unit      VARCHAR(20),            -- KRW_KG / USD_CWT / EUR_KG / CNY_KG / BRL_KG
    -- 사료 원료
    corn_price      DECIMAL(10,2),
    soybean_meal_price DECIMAL(10,2),
    -- 비율
    pig_feed_ratio  DECIMAL(6,2),           -- 돈곡비 (중국 DCE 기반)
    --
    source          VARCHAR(50),            -- USDA / DCE / EU_COMMISSION / CEPEA
    UNIQUE(country, price_date)
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  MODULE 10: DATA ANONYMIZATION — 데이터 익명화/수익화 파이프라인            │
-- │  Phase 3 (Pigsignal 연계)                                                │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 10-1. 데이터 수출 동의
CREATE TABLE data_consent (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    consent_type    VARCHAR(20) NOT NULL,   -- ANONYMIZED_SHARING / BENCHMARKING / FULL_OPT_OUT
    consented       BOOLEAN NOT NULL,
    consented_at    TIMESTAMPTZ,
    consented_by    UUID REFERENCES users(id),
    revoked_at      TIMESTAMPTZ,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10-2. 익명화 데이터셋 (Pigsignal 전달용)
CREATE TABLE anonymized_datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_type    VARCHAR(30) NOT NULL,
        -- BREEDING_KPI / FEED_FCR / DISEASE_PATTERN / GENETICS / ENVIRONMENTAL
    country         CHAR(2),
    region          VARCHAR(50),
    period          VARCHAR(10) NOT NULL,
    farm_count      INT,                    -- 포함 농장 수
    record_count    INT,                    -- 포함 레코드 수
    data_payload    JSONB NOT NULL,         -- 익명화된 집계 데이터
    -- 수요처
    target_buyer_type VARCHAR(30),
        -- FEED / PHARMA / GENETICS / INSURANCE / INTL_ORG / MARKET_RESEARCH
    exported_at     TIMESTAMPTZ,
    export_status   VARCHAR(15) DEFAULT 'PENDING',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  VIEWS — KPI 자동 계산                                                   │
-- └──────────────────────────────────────────────────────────────────────────┘

-- PSY 실시간 계산 뷰
CREATE OR REPLACE VIEW v_farm_psy AS
SELECT
    s.farm_id,
    COUNT(DISTINCT s.id) FILTER (WHERE s.status IN ('ACTIVE','GESTATING','LACTATING','WEANED','DRY'))
        AS active_sow_count,
    COALESCE(
        ROUND(
            SUM(w.weaned_count)
                FILTER (WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days')::DECIMAL
            / NULLIF(COUNT(DISTINCT s.id)
                FILTER (WHERE s.status IN ('ACTIVE','GESTATING','LACTATING','WEANED','DRY')), 0)
        , 2)
    , 0) AS psy_rolling_12m,
    COALESCE(
        ROUND(
            AVG(f.born_alive)
                FILTER (WHERE f.farrowing_date >= CURRENT_DATE - INTERVAL '365 days')
        , 2)
    , 0) AS avg_born_alive_12m,
    COALESCE(
        ROUND(
            AVG(w.weaned_count)
                FILTER (WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days')
        , 2)
    , 0) AS avg_weaned_12m
FROM sows s
LEFT JOIN farrowings f ON f.sow_id = s.id
LEFT JOIN weanings w ON w.sow_id = s.id
GROUP BY s.farm_id;

-- NPD (비생산일수) 계산 뷰
CREATE OR REPLACE VIEW v_sow_npd AS
SELECT
    s.id AS sow_id,
    s.farm_id,
    s.ear_tag,
    s.parity,
    -- NPD = (365 - 임신일수 - 포유일수) / 연간 분만 회수
    -- 간단 계산: 이유~다음 교배 사이 일수 합계
    COALESCE(
        SUM(
            CASE WHEN m.mating_date IS NOT NULL AND w.weaning_date IS NOT NULL
                THEN EXTRACT(DAY FROM (m.mating_date::timestamp - w.weaning_date::timestamp))
                ELSE 0
            END
        ) FILTER (WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days')
    , 0) AS npd_days_12m
FROM sows s
LEFT JOIN weanings w ON w.sow_id = s.id
LEFT JOIN matings m ON m.sow_id = s.id
    AND m.mating_date > w.weaning_date
    AND m.mating_date <= w.weaning_date + INTERVAL '60 days'
GROUP BY s.id, s.farm_id, s.ear_tag, s.parity;


-- ============================================================================
-- INDEXES SUMMARY
-- ============================================================================
-- 주요 인덱스는 각 테이블 정의 직후 생성됨
-- 추가 복합 인덱스는 쿼리 패턴 확인 후 Phase 2에서 튜닝

-- ============================================================================
-- SCHEMA SUMMARY
-- ============================================================================
-- Module 0: Platform      — 6 tables  (organizations, farms, users, user_farms, audit_log, sync_queue)
-- Module 1: Sow           — 8 tables  (buildings, boars, sows, matings, pregnancy_checks, farrowings, weanings, removals)
-- Module 2: Growing       — 4 tables  (animal_groups, grow_records, shipments, carcass_records)
-- Module 3: Feed          — 4 tables  (feed_bins, feed_formulas, feed_deliveries, feed_records)
-- Module 4: Health        — 3 tables  (health_events, vaccinations, medications)
-- Module 5: Genetics      — 1 table   (genetics)
-- Module 6: Compliance    — 4 tables  (compliance_reports, animal_movements, welfare_certifications, yellow_card_tracking)
-- Module 7: Environment   — 3 tables  (environment_readings, carbon_footprint, amr_monitoring)
-- Module 8: KPI           — 2 tables  (kpi_snapshots, benchmarks)
-- Module 9: Market        — 1 table   (market_prices)
-- Module 10: Data         — 2 tables  (data_consent, anonymized_datasets)
-- Views                   — 2 views   (v_farm_psy, v_sow_npd)
-- ============================================================================
-- TOTAL: 38 tables + 2 views across 11 modules
-- ============================================================================


-- ############################################################################
-- SUPPLEMENT v1.1 — 보완 사항
-- ############################################################################


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-1. SOFT DELETE 패턴 — 모든 핵심 테이블에 deleted_at 추가               │
-- └──────────────────────────────────────────────────────────────────────────┘

ALTER TABLE sows ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE boars ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE matings ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE farrowings ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE weanings ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE removals ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE animal_groups ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE health_events ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE vaccinations ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE medications ADD COLUMN deleted_at TIMESTAMPTZ;
ALTER TABLE feed_records ADD COLUMN deleted_at TIMESTAMPTZ;

-- 조회 시 WHERE deleted_at IS NULL 조건 사용
-- 또는 각 테이블에 partial index 생성:
CREATE INDEX idx_sows_active ON sows(farm_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_matings_active ON matings(sow_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_farrowings_active ON farrowings(sow_id) WHERE deleted_at IS NULL;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-2. 월마감 잠금 (Period Lock)                                          │
-- │  확정된 기간 데이터 수정 차단 — CLAUDE.md 요구사항                         │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE period_locks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    period          VARCHAR(10) NOT NULL,   -- 2026-03
    locked          BOOLEAN NOT NULL DEFAULT FALSE,
    locked_at       TIMESTAMPTZ,
    locked_by       UUID REFERENCES users(id),
    unlock_reason   TEXT,                   -- 잠금 해제 시 사유 필수
    unlocked_at     TIMESTAMPTZ,
    unlocked_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(farm_id, period)
);
-- API 레이어에서: INSERT/UPDATE/DELETE 시 해당 기간 lock 여부 확인
-- locked = TRUE 면 수정 거부 (HTTP 423 Locked)


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-3. 코드 마스터 & 다국어 번역                                           │
-- │  VARCHAR 하드코딩 값 → 코드 테이블 분리, i18n 지원                        │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 코드 그룹
CREATE TABLE code_groups (
    group_code      VARCHAR(30) PRIMARY KEY,    -- SOW_STATUS, REMOVAL_REASON, DISEASE_CODE, MATING_TYPE ...
    description     VARCHAR(200) NOT NULL,
    editable        BOOLEAN DEFAULT FALSE       -- 사용자 커스텀 추가 가능 여부
);

-- 코드 값
CREATE TABLE code_values (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_code      VARCHAR(30) NOT NULL REFERENCES code_groups(group_code),
    code            VARCHAR(50) NOT NULL,       -- ACTIVE, CULLED, REPRODUCTIVE, ASF ...
    sort_order      INT DEFAULT 0,
    active          BOOLEAN DEFAULT TRUE,
    -- 기본값 (fallback)
    label_default   VARCHAR(100) NOT NULL,      -- 영어 기본 라벨
    UNIQUE(group_code, code)
);

-- 다국어 번역
CREATE TABLE code_translations (
    code_value_id   UUID NOT NULL REFERENCES code_values(id),
    language        VARCHAR(5) NOT NULL,        -- ko, vi, th, da, de, es, pt, zh
    label           VARCHAR(200) NOT NULL,
    PRIMARY KEY (code_value_id, language)
);

-- 초기 데이터 예시:
INSERT INTO code_groups VALUES ('SOW_STATUS', '모돈 상태', FALSE);
INSERT INTO code_groups VALUES ('REMOVAL_REASON', '도태/폐사 사유', TRUE);
INSERT INTO code_groups VALUES ('DISEASE_CODE', '질병 코드', TRUE);
INSERT INTO code_groups VALUES ('MATING_TYPE', '교배 유형', FALSE);
INSERT INTO code_groups VALUES ('BUILDING_TYPE', '건물 유형', FALSE);
INSERT INTO code_groups VALUES ('VACCINE_TYPE', '백신 유형', TRUE);
INSERT INTO code_groups VALUES ('ANTIBIOTIC_CLASS', '항생제 계열', FALSE);
INSERT INTO code_groups VALUES ('GRADE_KR', '한국 도체 등급', FALSE);
INSERT INTO code_groups VALUES ('SEUROP_GRADE', 'EU SEUROP 등급', FALSE);

-- SOW_STATUS 예시
INSERT INTO code_values (group_code, code, sort_order, label_default) VALUES
    ('SOW_STATUS', 'ACTIVE', 1, 'Active'),
    ('SOW_STATUS', 'GESTATING', 2, 'Gestating'),
    ('SOW_STATUS', 'LACTATING', 3, 'Lactating'),
    ('SOW_STATUS', 'WEANED', 4, 'Weaned'),
    ('SOW_STATUS', 'DRY', 5, 'Dry'),
    ('SOW_STATUS', 'CULLED', 6, 'Culled'),
    ('SOW_STATUS', 'DEAD', 7, 'Dead');

-- 한국어 번역 예시 (code_value_id는 실제 UUID로 대체)
-- INSERT INTO code_translations VALUES ('{uuid}', 'ko', '활성');
-- INSERT INTO code_translations VALUES ('{uuid}', 'vi', 'Hoạt động');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-4. 알림 / 경보 시스템                                                 │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 알림 규칙 (농장별 설정)
CREATE TABLE alert_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    alert_type      VARCHAR(30) NOT NULL,
        -- MATING_DUE / FARROWING_DUE / WEANING_DUE / PREGNANCY_CHECK_DUE
        -- FEED_BIN_LOW / ASF_OUTBREAK / MORTALITY_SPIKE / ANTIBIOTIC_THRESHOLD
        -- PERIOD_LOCK_REMINDER / KPI_DEVIATION
    enabled         BOOLEAN DEFAULT TRUE,
    threshold_value DECIMAL(10,2),          -- 임계값 (예: 사료빈 잔량 kg, 폐사율 %)
    lead_days       INT,                    -- 사전 알림일 (예: 분만 예정 3일 전)
    notify_roles    VARCHAR(100),           -- FARM_OWNER,FARM_MANAGER (쉼표 구분)
    channel         VARCHAR(20),            -- PUSH / SMS / EMAIL / KAKAOTALK / ZALO / WECHAT
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 알림 발송 이력
CREATE TABLE alert_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    rule_id         UUID REFERENCES alert_rules(id),
    alert_type      VARCHAR(30) NOT NULL,
    title           VARCHAR(200) NOT NULL,
    message         TEXT,
    severity        VARCHAR(10) DEFAULT 'INFO',
        -- INFO / WARNING / CRITICAL / EMERGENCY
    target_user_id  UUID REFERENCES users(id),
    channel         VARCHAR(20),
    sent_at         TIMESTAMPTZ,
    read_at         TIMESTAMPTZ,
    entity_type     VARCHAR(50),            -- sows / feed_bins / health_events
    entity_id       UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_alerts_user_unread ON alert_history(target_user_id) WHERE read_at IS NULL;
CREATE INDEX idx_alerts_farm ON alert_history(farm_id, created_at DESC);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-5. 파일 첨부 (모든 이벤트에 사진/문서 첨부 가능)                        │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE attachments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    entity_type     VARCHAR(50) NOT NULL,   -- sows / farrowings / health_events / ...
    entity_id       UUID NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_type       VARCHAR(50),            -- image/jpeg, application/pdf, ...
    file_size_bytes BIGINT,
    storage_path    VARCHAR(500) NOT NULL,  -- S3 key: farms/{farm_id}/attachments/{uuid}.jpg
    thumbnail_path  VARCHAR(500),           -- 축소 이미지 (모바일용)
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_attach_entity ON attachments(entity_type, entity_id);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-6. 개체 돼지 추적 (Individual Pig — LeeO Birth-to-Slaughter 대응)      │
-- │  Phase 3 선택 확장                                                       │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE individual_pigs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    ear_tag         VARCHAR(30),
    rfid_tag        VARCHAR(50),            -- UHF RFID 이어태그
    -- 출생 정보
    dam_id          UUID REFERENCES sows(id),       -- 어미 모돈
    sire_id         UUID REFERENCES boars(id),      -- 아비
    farrowing_id    UUID REFERENCES farrowings(id),
    birth_date      DATE,
    birth_weight_kg DECIMAL(5,2),
    sex             CHAR(1),                -- M / F / C (거세)
    -- 현재 상태
    status          VARCHAR(15) DEFAULT 'ALIVE',
        -- ALIVE / DEAD / SOLD / SLAUGHTERED / TRANSFERRED
    current_group_id UUID REFERENCES animal_groups(id),
    current_building_id UUID REFERENCES buildings(id),
    -- 출하/도축
    slaughter_date  DATE,
    slaughter_weight_kg DECIMAL(6,2),
    carcass_record_id UUID REFERENCES carcass_records(id),
    -- Pig Passport (Cloudfarms C2C 대응)
    passport_data   JSONB,                  -- Farm-to-Fork 디지털 이력서
    --
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
CREATE INDEX idx_pigs_farm ON individual_pigs(farm_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_pigs_rfid ON individual_pigs(rfid_tag) WHERE rfid_tag IS NOT NULL;
CREATE INDEX idx_pigs_dam ON individual_pigs(dam_id);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-7. 국가별 설정 (Country Pack)                                         │
-- │  규정/단위/보고 양식을 국가별로 모듈화                                     │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE country_configs (
    country         CHAR(2) PRIMARY KEY,
    country_name    VARCHAR(100) NOT NULL,
    weight_unit     VARCHAR(5) NOT NULL DEFAULT 'kg',   -- kg / lb
    temperature_unit CHAR(1) NOT NULL DEFAULT 'C',      -- C / F
    currency        VARCHAR(3) NOT NULL,
    date_format     VARCHAR(15) NOT NULL,
    notification_default VARCHAR(20),       -- EMAIL / SMS / KAKAOTALK / ZALO / WECHAT / WHATSAPP
    -- 규정 모듈 플래그
    has_antibiotic_report BOOLEAN DEFAULT FALSE,     -- EU, KR
    has_animal_movement_cert BOOLEAN DEFAULT FALSE,  -- BR(GTA), EU(TRACES), KR(mtrace)
    has_welfare_cert BOOLEAN DEFAULT FALSE,          -- EU
    has_prop12 BOOLEAN DEFAULT FALSE,                -- US (CA)
    has_asf_alert BOOLEAN DEFAULT FALSE,             -- SEA, KR, CN
    has_carbon_report BOOLEAN DEFAULT FALSE,         -- EU
    -- 도체 등급 시스템
    grading_system  VARCHAR(20),            -- KR_GRADE / SEUROP / CARCASS_MERIT / SIF / NONE
    -- KPI 벤치마크 기본 출처
    benchmark_source VARCHAR(50)            -- PIGCHAMP / DANBRED / HANDON / AGRINESS / USDA
);

-- 초기 데이터
INSERT INTO country_configs VALUES
    ('KR', '한국', 'kg', 'C', 'KRW', 'yyyy.MM.dd', 'KAKAOTALK',
     TRUE, TRUE, FALSE, FALSE, TRUE, FALSE, 'KR_GRADE', 'HANDON'),
    ('DK', '덴마크', 'kg', 'C', 'DKK', 'dd/MM/yyyy', 'EMAIL',
     TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, 'SEUROP', 'DANBRED'),
    ('DE', '독일', 'kg', 'C', 'EUR', 'dd.MM.yyyy', 'EMAIL',
     TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, 'SEUROP', 'DANBRED'),
    ('NL', '네덜란드', 'kg', 'C', 'EUR', 'dd-MM-yyyy', 'EMAIL',
     TRUE, TRUE, TRUE, FALSE, FALSE, TRUE, 'SEUROP', 'PIGCHAMP'),
    ('ES', '스페인', 'kg', 'C', 'EUR', 'dd/MM/yyyy', 'EMAIL',
     TRUE, TRUE, TRUE, FALSE, FALSE, FALSE, 'SEUROP', 'PIGCHAMP'),
    ('US', '미국', 'lb', 'F', 'USD', 'MM/dd/yyyy', 'EMAIL',
     FALSE, FALSE, FALSE, TRUE, FALSE, FALSE, 'CARCASS_MERIT', 'PIGCHAMP'),
    ('BR', '브라질', 'kg', 'C', 'BRL', 'dd/MM/yyyy', 'WHATSAPP',
     FALSE, TRUE, FALSE, FALSE, FALSE, FALSE, 'SIF', 'AGRINESS'),
    ('VN', '베트남', 'kg', 'C', 'VND', 'dd/MM/yyyy', 'ZALO',
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, 'NONE', NULL),
    ('TH', '태국', 'kg', 'C', 'THB', 'dd/MM/yyyy', 'SMS',
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, 'NONE', NULL),
    ('PH', '필리핀', 'kg', 'C', 'PHP', 'MM/dd/yyyy', 'SMS',
     FALSE, FALSE, FALSE, FALSE, TRUE, FALSE, 'NONE', NULL),
    ('CN', '중국', 'kg', 'C', 'CNY', 'yyyy-MM-dd', 'WECHAT',
     TRUE, FALSE, FALSE, FALSE, TRUE, FALSE, 'NONE', NULL);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-8. updated_at 자동 갱신 트리거                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- updated_at 컬럼이 있는 테이블에 트리거 적용
CREATE TRIGGER trg_organizations_updated BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_farms_updated BEFORE UPDATE ON farms FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_sows_updated BEFORE UPDATE ON sows FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- 나머지 핵심 테이블에도 updated_at 추가 후 트리거 적용
ALTER TABLE boars ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE buildings ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE animal_groups ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
CREATE TRIGGER trg_boars_updated BEFORE UPDATE ON boars FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_buildings_updated BEFORE UPDATE ON buildings FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_groups_updated BEFORE UPDATE ON animal_groups FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  S-9. 파티셔닝 전략 (대량 테이블)                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

-- 파티셔닝 대상: 시간 기반 대량 데이터 테이블
-- PostgreSQL 12+ 선언적 파티셔닝 사용

-- audit_log — 월별 파티셔닝
-- CREATE TABLE audit_log (...) PARTITION BY RANGE (created_at);
-- CREATE TABLE audit_log_2026_03 PARTITION OF audit_log
--     FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
-- CREATE TABLE audit_log_2026_04 PARTITION OF audit_log
--     FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- environment_readings — 일별 파티셔닝 (TimescaleDB가 자동 관리)
-- SELECT create_hypertable('environment_readings', 'reading_time',
--     chunk_time_interval => INTERVAL '1 day');

-- feed_records — 월별 파티셔닝
-- health_events — 월별 파티셔닝
-- sync_queue — 주별 파티셔닝 (동기화 완료 후 오래된 파티션 DROP)

-- NOTE: 실제 파티셔닝은 테이블 생성 시 적용해야 함 (ALTER 불가)
-- 위 CREATE TABLE 문을 PARTITION BY RANGE (created_at)로 변경 필요
-- Phase 1 MVP에서는 파티셔닝 없이 시작, 100만 행 초과 시 적용


-- ============================================================================
-- UPDATED SCHEMA SUMMARY (v1.1)
-- ============================================================================
-- Module 0: Platform      — 6 tables  (+ period_locks, code_groups, code_values, code_translations)
-- Module 1: Sow           — 8 tables
-- Module 2: Growing       — 4 tables
-- Module 3: Feed          — 4 tables
-- Module 4: Health        — 3 tables
-- Module 5: Genetics      — 1 table
-- Module 6: Compliance    — 4 tables
-- Module 7: Environment   — 3 tables
-- Module 8: KPI           — 2 tables
-- Module 9: Market        — 1 table
-- Module 10: Data         — 2 tables
-- Supplement: S-2 period_locks, S-3 code (3 tables), S-4 alerts (2 tables),
--             S-5 attachments, S-6 individual_pigs, S-7 country_configs
-- Views                   — 2 views
-- ============================================================================
-- TOTAL: 49 tables + 2 views + 3 triggers + 11 country configs
-- ============================================================================
