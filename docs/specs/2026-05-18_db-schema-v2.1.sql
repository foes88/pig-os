-- ============================================================================
-- PigOS — DB Schema v2.1 (2026-05-18)
-- ============================================================================
-- v2.0 위에 적용하는 추가 테이블 6개
--
-- 추가 배경 (CLAUDE.md 설계 원칙):
--   - period_locks   : 월마감 잠금 (4번 원칙)
--   - kpi_snapshots  : 대시보드 스냅샷 전략 (ARQ 백그라운드 잡 대상)
--   - finisher_groups: 비육돈 FCR 계산 (Addon #1 필수)
--   - api_keys       : B2B API 클라이언트 인증 (PigSignal B2B)
--   - notifications  : 알림 전달 추적 (Rule Engine 알림)
--   - sync_logs      : 오프라인 동기화 이력
-- ============================================================================


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  1. 월마감 잠금 (period_locks)                                            │
-- │  확정 월의 데이터 수정 차단. MONTH_CLOSE → audit_log 기록.               │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE period_locks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id      UUID NOT NULL REFERENCES farms(id),
    period_year  SMALLINT NOT NULL CHECK (period_year >= 2020 AND period_year <= 2099),
    period_month SMALLINT NOT NULL CHECK (period_month >= 1 AND period_month <= 12),
    locked_by    UUID NOT NULL REFERENCES users(id),
    locked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unlocked_by  UUID REFERENCES users(id),
    unlocked_at  TIMESTAMPTZ,
    note         TEXT,
    UNIQUE (farm_id, period_year, period_month)
);
CREATE INDEX idx_period_locks_farm ON period_locks(farm_id, period_year, period_month);

-- 잠금 여부 확인 함수: 해당 날짜가 잠긴 기간인지
CREATE OR REPLACE FUNCTION is_period_locked(p_farm_id UUID, p_date DATE)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM period_locks
        WHERE farm_id = p_farm_id
          AND period_year  = EXTRACT(YEAR  FROM p_date)::SMALLINT
          AND period_month = EXTRACT(MONTH FROM p_date)::SMALLINT
          AND unlocked_at IS NULL
    );
$$ LANGUAGE SQL STABLE;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  2. KPI 스냅샷 (kpi_snapshots)                                           │
-- │  ARQ 백그라운드 잡이 계산 결과를 여기 저장.                              │
-- │  대시보드는 실시간 계산 대신 이 테이블 조회.                             │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE kpi_snapshots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    period_type     VARCHAR(10) NOT NULL
        CHECK (period_type IN ('DAILY','WEEKLY','MONTHLY','ANNUAL')),
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,

    -- Base KPIs (항상 계산)
    psy             DECIMAL(6,2),   -- Piglets per Sow per Year
    msy             DECIMAL(6,2),   -- Market pigs per Sow per Year
    npd             DECIMAL(6,2),   -- Non-Productive Days
    mortality_rate  DECIMAL(5,2),   -- %

    -- Addon #1 KPIs (ADDON_FCR 구독 시만 유효)
    fcr             DECIMAL(5,3),   -- Feed Conversion Ratio
    avg_daily_gain  DECIMAL(6,2),   -- g/day

    -- 두수 현황
    active_sow_count    INT,
    gestating_count     INT,
    lactating_count     INT,

    -- 메타
    is_stale        BOOLEAN NOT NULL DEFAULT FALSE,  -- 이벤트 수정 후 재계산 필요
    calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (farm_id, period_type, period_start)
);
CREATE INDEX idx_kpi_snap_farm_period ON kpi_snapshots(farm_id, period_type, period_start DESC);
CREATE INDEX idx_kpi_snap_stale ON kpi_snapshots(is_stale) WHERE is_stale = TRUE;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  3. 비육돈 그룹 (finisher_groups)                                        │
-- │  Addon #1 FCR 계산 단위. 모돈(sow_id)이 아닌 그룹 기반.                 │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE finisher_groups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    building_id     UUID REFERENCES buildings(id),
    group_code      VARCHAR(30) NOT NULL,
    batch_name      VARCHAR(100),           -- 예: "2026-W12 Batch A"
    start_date      DATE NOT NULL,
    end_date        DATE,                   -- NULL = 진행 중
    head_count_in   INT NOT NULL,           -- 입식 두수
    head_count_out  INT,                    -- 출하/폐사 포함 최종 두수
    avg_entry_weight_kg  DECIMAL(6,2),
    avg_exit_weight_kg   DECIMAL(6,2),
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    UNIQUE (farm_id, group_code)
);
CREATE INDEX idx_fg_farm_active ON finisher_groups(farm_id, start_date)
    WHERE deleted_at IS NULL;

-- feed_records·health_events의 group_id가 이 테이블을 참조
-- (기존 group_id UUID 컬럼에 FK 추가)
ALTER TABLE feed_records   ADD CONSTRAINT fk_feed_finisher_group
    FOREIGN KEY (group_id) REFERENCES finisher_groups(id);
ALTER TABLE health_events  ADD CONSTRAINT fk_health_finisher_group
    FOREIGN KEY (group_id) REFERENCES finisher_groups(id);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  4. API 키 (api_keys)                                                    │
-- │  B2B API 클라이언트 인증. JWT와 분리.                                    │
-- │  PigSignal B2B API (#2·#3) 전용.                                         │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(100) NOT NULL,          -- "Samsam Feed API Key"
    key_prefix      VARCHAR(8) NOT NULL,            -- 표시용 앞 8자: "pk_live_"
    key_hash        VARCHAR(255) NOT NULL UNIQUE,   -- SHA256(full_key)
    scopes          TEXT[] NOT NULL DEFAULT '{}',
    -- ['pig_supply_forecast','pig_cost_index','pig_risk_signal']
    rate_limit_per_min  INT NOT NULL DEFAULT 60,
    expires_at      TIMESTAMPTZ,                    -- NULL = 만료 없음
    last_used_at    TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);
CREATE INDEX idx_api_keys_org ON api_keys(org_id) WHERE is_active = TRUE;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  5. 알림 (notifications)                                                 │
-- │  Rule Engine 알림 + 시스템 알림 전달 추적.                               │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID REFERENCES farms(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    type            VARCHAR(20) NOT NULL
        CHECK (type IN ('PUSH','EMAIL','SMS','IN_APP')),
    channel         VARCHAR(30),
    -- EMAIL / FCM / APNS / KAKAOTALK / ZALO / WECHAT / WHATSAPP
    title           VARCHAR(200) NOT NULL,
    body            TEXT NOT NULL,
    alert_type      VARCHAR(50),
    -- NPD_OVERDUE / FARROWING_DUE / WEANING_DUE / KPI_CRITICAL / SYSTEM
    severity        VARCHAR(10)
        CHECK (severity IN ('INFO','WARNING','CRITICAL') OR severity IS NULL),
    related_entity_type VARCHAR(50),    -- sows / farms / farrowings …
    related_entity_id   UUID,
    sent_at         TIMESTAMPTZ,
    read_at         TIMESTAMPTZ,
    failed_at       TIMESTAMPTZ,
    failure_reason  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_notif_user_unread ON notifications(user_id, created_at DESC)
    WHERE read_at IS NULL;
CREATE INDEX idx_notif_farm ON notifications(farm_id, created_at DESC)
    WHERE farm_id IS NOT NULL;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  6. 동기화 이력 (sync_logs)                                              │
-- │  오프라인 sync_queue 처리 결과 기록.                                     │
-- │  sync_queue = 대기열, sync_logs = 완료 이력.                             │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE sync_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    device_id       VARCHAR(100) NOT NULL,
    user_id         UUID REFERENCES users(id),
    sync_direction  VARCHAR(10) NOT NULL
        CHECK (sync_direction IN ('PUSH','PULL','BIDIRECTIONAL')),
    started_at      TIMESTAMPTZ NOT NULL,
    completed_at    TIMESTAMPTZ,
    records_pushed  INT NOT NULL DEFAULT 0,
    records_pulled  INT NOT NULL DEFAULT 0,
    conflicts_found INT NOT NULL DEFAULT 0,
    conflicts_resolved INT NOT NULL DEFAULT 0,
    error_count     INT NOT NULL DEFAULT 0,
    error_detail    JSONB,
    duration_ms     INT
);
CREATE INDEX idx_sync_logs_farm ON sync_logs(farm_id, started_at DESC);
CREATE INDEX idx_sync_logs_device ON sync_logs(device_id, started_at DESC);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  7. 충돌 대기열 (sync_conflict_queue)                                     │
-- │  자동 해소 불가능한 충돌을 보관. 앱에서 사용자가 직접 해소.               │
-- │  DUPLICATE_EVENT(날짜 다름), CYCLE_CONFLICT(다른 배치)만 이 테이블에 기록 │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE sync_conflict_queue (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    client_id       UUID NOT NULL,                     -- 요청 기기 UUID
    entity          VARCHAR(50) NOT NULL,              -- mating / farrowing / …
    conflict_type   VARCHAR(30) NOT NULL,              -- DUPLICATE_EVENT / CYCLE_CONFLICT
    client_record   JSONB NOT NULL,
    server_record   JSONB NOT NULL,
    resolved_at     TIMESTAMPTZ,                       -- NULL = 미해소
    resolution      VARCHAR(20)                        -- CLIENT_WINS / SERVER_WINS / DISCARDED
        CHECK (resolution IN ('CLIENT_WINS','SERVER_WINS','DISCARDED') OR resolution IS NULL),
    resolved_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_conflict_queue_farm_unresolved
    ON sync_conflict_queue(farm_id, created_at DESC)
    WHERE resolved_at IS NULL;
CREATE INDEX idx_conflict_queue_farm_all
    ON sync_conflict_queue(farm_id, created_at DESC);
