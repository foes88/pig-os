-- ============================================================================
-- PigOS 검증용 시드 데이터 (v1 스키마 컬럼명 기준)
-- 목표: T-01~T-10 번식 사이클 시나리오 + 트리거/제약 검증
-- ============================================================================

-- ── 기반 데이터 ──────────────────────────────────────────────────────────────

INSERT INTO organizations (id, name, country) VALUES
    ('00000000-0000-0000-0000-000000000001', 'PigOS Test Org', 'KR');

INSERT INTO farms (id, org_id, farm_code, name, country, region, timezone)
VALUES
    ('00000000-0000-0000-0000-000000000010',
     '00000000-0000-0000-0000-000000000001',
     'TEST-KR-001', '테스트농장-한국', 'KR', '경기', 'Asia/Seoul');

INSERT INTO users (id, org_id, email, name, password_hash, role)
VALUES
    ('00000000-0000-0000-0000-000000000020',
     '00000000-0000-0000-0000-000000000001',
     'test@pigos.io', '테스트관리자', '$2b$10$placeholder_hash', 'FARM_MANAGER');

INSERT INTO buildings (id, farm_id, name, building_type, capacity)
VALUES
    ('00000000-0000-0000-0000-000000000030',
     '00000000-0000-0000-0000-000000000010', '1번분만사', 'FARROWING', 20),
    ('00000000-0000-0000-0000-000000000031',
     '00000000-0000-0000-0000-000000000010', '임신사', 'GESTATION', 100);

INSERT INTO boars (id, farm_id, ear_tag, breed, entry_date, status)
VALUES
    ('00000000-0000-0000-0000-000000000040',
     '00000000-0000-0000-0000-000000000010', 'BOAR-001', 'DUROC', '2025-01-01', 'ACTIVE');

-- ── 모돈 5두 (정상 사이클 + 특수 케이스) ───────────────────────────────────

-- A-001: 정상 번식 사이클 (T-01~T-10)
INSERT INTO sows (id, farm_id, ear_tag, breed, parity, status, entry_date, entry_type)
VALUES
    ('11000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010', 'A-001', 'LANDRACE', 0, 'ACTIVE',
     '2025-06-01', 'GILT');

-- A-002: 재발정 경험 모돈 (T-06)
INSERT INTO sows (id, farm_id, ear_tag, breed, parity, status, entry_date, entry_type)
VALUES
    ('11000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000010', 'A-002', 'YORKSHIRE', 0, 'ACTIVE',
     '2025-06-01', 'GILT');

-- A-003: 위탁 모돈 (T-08)
INSERT INTO sows (id, farm_id, ear_tag, breed, parity, status, entry_date, entry_type)
VALUES
    ('11000000-0000-0000-0000-000000000003',
     '00000000-0000-0000-0000-000000000010', 'A-003', 'LANDRACE', 0, 'ACTIVE',
     '2025-06-01', 'GILT');

-- A-004: 8산차 도태 예정 모돈 (T-09)
INSERT INTO sows (id, farm_id, ear_tag, breed, parity, status, entry_date, entry_type)
VALUES
    ('11000000-0000-0000-0000-000000000004',
     '00000000-0000-0000-0000-000000000010', 'A-004', 'DUROC', 0, 'ACTIVE',
     '2024-01-01', 'PURCHASE');

-- A-005: 제약 위반 테스트용 (T-13~T-15)
INSERT INTO sows (id, farm_id, ear_tag, breed, parity, status, entry_date, entry_type)
VALUES
    ('11000000-0000-0000-0000-000000000005',
     '00000000-0000-0000-0000-000000000010', 'A-005', 'YORKSHIRE', 0, 'ACTIVE',
     '2025-06-01', 'GILT');


-- ── farm_configs 초기값 ──────────────────────────────────────────────────────

INSERT INTO farm_configs (farm_id, config_key, config_value) VALUES
    ('00000000-0000-0000-0000-000000000010', 'GESTATION_DAYS',      '114'),
    ('00000000-0000-0000-0000-000000000010', 'LACTATION_DAYS',       '21'),
    ('00000000-0000-0000-0000-000000000010', 'WEI_TARGET_DAYS',       '7'),
    ('00000000-0000-0000-0000-000000000010', 'PREGNANCY_CHECK_DAY',  '25');


-- ── T-01: 후보돈 입식 → 첫 교배 ────────────────────────────────────────────

INSERT INTO breeding_cycles
    (id, farm_id, sow_id, parity, cycle_status, started_at, mating_count)
VALUES
    ('BC000001-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000001',
     1, 'MATED', '2026-01-10', 1);

INSERT INTO matings
    (id, farm_id, sow_id, boar_id, mating_date, mating_type,
     mating_number, breeding_cycle_id)
VALUES
    ('A0000001-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000040',
     '2026-01-10', 'AI', 1,
     'BC000001-0000-0000-0000-000000000001');
-- trg_mating_sow_status → A-001 status = 'GESTATING'


-- ── T-02: 임신확인 (양성) ──────────────────────────────────────────────────

INSERT INTO pregnancy_checks
    (id, farm_id, sow_id, mating_id, check_date, result, check_method)
VALUES
    ('C0000001-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000001',
     'A0000001-0000-0000-0000-000000000001',
     '2026-02-04', 'POSITIVE', 'ULTRASOUND');


-- ── T-03: 분만 (교배 후 114일) ──────────────────────────────────────────────

UPDATE breeding_cycles
SET cycle_status = 'FARROWED'
WHERE id = 'BC000001-0000-0000-0000-000000000001';

INSERT INTO farrowings
    (id, farm_id, sow_id, mating_id, farrowing_date,
     parity_at_birth, total_born, born_alive, stillborn, mummified,
     building_id, breeding_cycle_id)
VALUES
    ('FA000001-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000001',
     'A0000001-0000-0000-0000-000000000001',
     '2026-05-04',
     1, 14, 13, 1, 0,
     '00000000-0000-0000-0000-000000000030',
     'BC000001-0000-0000-0000-000000000001');
-- trg_farrowing_sow_status → A-001 status = 'LACTATING', parity = 1


-- ── T-07: 포유중 자돈 폐사 3두 ─────────────────────────────────────────────

INSERT INTO piglet_events
    (id, farm_id, farrowing_id, sow_id, event_date, event_type, piglet_count, reason)
VALUES
    (gen_random_uuid(),
     '00000000-0000-0000-0000-000000000010',
     'FA000001-0000-0000-0000-000000000001',
     '11000000-0000-0000-0000-000000000001',
     '2026-05-06', 'DEATH', 1, 'CRUSHING'),
    (gen_random_uuid(),
     '00000000-0000-0000-0000-000000000010',
     'FA000001-0000-0000-0000-000000000001',
     '11000000-0000-0000-0000-000000000001',
     '2026-05-10', 'DEATH', 1, 'SCOURS'),
    (gen_random_uuid(),
     '00000000-0000-0000-0000-000000000010',
     'FA000001-0000-0000-0000-000000000001',
     '11000000-0000-0000-0000-000000000001',
     '2026-05-15', 'DEATH', 1, 'STARVATION');


-- ── T-04: 이유 (분만 21일 후, 10두) ────────────────────────────────────────

UPDATE breeding_cycles
SET cycle_status = 'WEANED', ended_at = '2026-05-25'
WHERE id = 'BC000001-0000-0000-0000-000000000001';

INSERT INTO weanings
    (id, farm_id, sow_id, farrowing_id, weaning_date, weaned_count, breeding_cycle_id)
VALUES
    ('E0000001-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000001',
     'FA000001-0000-0000-0000-000000000001',
     '2026-05-25', 10,
     'BC000001-0000-0000-0000-000000000001');
-- trg_weaning_sow_status → A-001 status = 'WEANED'


-- ── T-06: 재발정 모돈 (A-002) ──────────────────────────────────────────────

INSERT INTO breeding_cycles
    (id, farm_id, sow_id, parity, cycle_status, started_at, mating_count)
VALUES
    ('BC000002-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000002',
     1, 'MATED', '2026-01-10', 1);

INSERT INTO matings
    (id, farm_id, sow_id, boar_id, mating_date, mating_type,
     mating_number, breeding_cycle_id)
VALUES
    ('A0000002-0000-0000-0000-000000000001',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000040',
     '2026-01-10', 'AI', 1,
     'BC000002-0000-0000-0000-000000000001');

-- 재발정 기록
INSERT INTO reproductive_events
    (id, farm_id, sow_id, mating_id, breeding_cycle_id,
     event_date, event_type, detected_method)
VALUES
    (gen_random_uuid(),
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000002',
     'A0000002-0000-0000-0000-000000000001',
     'BC000002-0000-0000-0000-000000000001',
     '2026-01-31', 'RETURN_TO_ESTRUS', 'VISUAL');

UPDATE breeding_cycles
SET cycle_status = 'FAILED', ended_at = '2026-01-31'
WHERE id = 'BC000002-0000-0000-0000-000000000001';

-- 재교배
INSERT INTO breeding_cycles
    (id, farm_id, sow_id, parity, cycle_status, started_at, mating_count)
VALUES
    ('BC000002-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000002',
     1, 'MATED', '2026-02-03', 1);

INSERT INTO matings
    (id, farm_id, sow_id, boar_id, mating_date, mating_type,
     mating_number, breeding_cycle_id)
VALUES
    ('A0000002-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000010',
     '11000000-0000-0000-0000-000000000002',
     '00000000-0000-0000-0000-000000000040',
     '2026-02-03', 'AI', 1,
     'BC000002-0000-0000-0000-000000000002');
-- trg_mating_sow_status → A-002 status = 'GESTATING'
