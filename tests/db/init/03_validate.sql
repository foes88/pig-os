-- ============================================================================
-- PigOS 스키마 검증 쿼리
-- 각 \echo 출력 결과를 눈으로 확인
-- ============================================================================

\echo ''
\echo '══════════════════════════════════════════════'
\echo ' PigOS Schema Validation'
\echo '══════════════════════════════════════════════'

-- ── 1. 테이블 수 확인 ─────────────────────────────────────────────────────
\echo ''
\echo '[1] 테이블 수 (v1 49 + v2 신규 4 = 53개 예상)'
SELECT COUNT(*) AS table_count
FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';


-- ── 2. 상태 전이 트리거 검증 ───────────────────────────────────────────────
\echo ''
\echo '[2] 상태 전이 트리거 — A-001 사이클 상태 확인'
SELECT
    ear_tag,
    status,
    parity,
    exit_date
FROM sows
WHERE ear_tag = 'A-001';
-- 기대: status = 'WEANED', parity = 1, exit_date = NULL

\echo '    A-002 (재발정 후 재교배) 상태 확인'
SELECT ear_tag, status, parity FROM sows WHERE ear_tag = 'A-002';
-- 기대: status = 'GESTATING' (재교배 후)


-- ── 3. 자돈 두수 정합성 검증 ───────────────────────────────────────────────
\echo ''
\echo '[3] fn_verify_piglet_count() — A-001 첫 분만 (기대: is_balanced = true)'
SELECT * FROM fn_verify_piglet_count('FA000001-0000-0000-0000-000000000001');
-- 기대: born_alive=13, deaths=3, expected_weaned=10, actual_weaned=10, is_balanced=true


-- ── 4. effective_metric_values() 우선순위 확인 ────────────────────────────
\echo ''
\echo '[4] effective_metric_values() — KR 농장 PSY 기준값 (farm→region→market→system 순)'
SELECT metric_code, default_value, benchmark_avg, benchmark_top25, target_value, scope_type
FROM effective_metric_values(
    '00000000-0000-0000-0000-000000000010',  -- farm_code
    'KR',                                     -- region_code
    'NEA'                                     -- market_code
)
WHERE metric_code IN ('PSY', 'MSY', 'NPD')
ORDER BY metric_code;
-- 기대: PSY scope_type = 'region' (KR 기준값 우선)


-- ── 5. v_farm_psy 뷰 검증 (deleted_at 필터 포함) ─────────────────────────
\echo ''
\echo '[5] v_farm_psy 뷰 — 테스트 농장 PSY'
SELECT * FROM v_farm_psy
WHERE farm_id = '00000000-0000-0000-0000-000000000010';
-- 기대: total_weaned = 10, avg_sow_count = 1 이상, psy 계산값 반환


-- ── 6. v_sow_npd 뷰 검증 (LATERAL JOIN) ─────────────────────────────────
\echo ''
\echo '[6] v_sow_npd 뷰 — A-001 이유 후 WEI (다음 교배까지 대기일)'
SELECT s.ear_tag, n.*
FROM v_sow_npd n
JOIN sows s ON s.id = n.sow_id
WHERE s.ear_tag = 'A-001';
-- 기대: next_mating_date IS NULL (아직 재교배 없음), wei_days = NULL


-- ── 7. breeding_cycles 활성 사이클 UNIQUE 제약 검증 ──────────────────────
\echo ''
\echo '[7] 활성 사이클 제약 — 모돈당 1개만 허용'
SELECT
    s.ear_tag,
    COUNT(*) FILTER (WHERE bc.cycle_status NOT IN ('WEANED','FAILED')) AS active_cycles
FROM breeding_cycles bc
JOIN sows s ON s.id = bc.sow_id
GROUP BY s.ear_tag
ORDER BY s.ear_tag;
-- 기대: 모든 모돈의 active_cycles <= 1


-- ── 8. CHECK 제약 위반 시도 (에러 발생해야 정상) ─────────────────────────
\echo ''
\echo '[8] CHECK 제약 위반 테스트 (아래 각 항목은 에러 발생해야 정상)'

\echo '    8-1. 잘못된 sow status → ERROR 기대'
DO $$
BEGIN
    UPDATE sows SET status = 'PREGNANT' WHERE ear_tag = 'A-005';
    RAISE NOTICE 'FAIL: CHECK constraint not working for sow status';
EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'PASS: chk_sow_status 제약 정상 동작';
END $$;

\echo '    8-2. total_born ≠ born_alive+stillborn+mummified → ERROR 기대'
DO $$
BEGIN
    INSERT INTO farrowings
        (id, farm_id, sow_id, mating_id, farrowing_date,
         total_born, born_alive, stillborn, mummified)
    SELECT
        gen_random_uuid(),
        '00000000-0000-0000-0000-000000000010',
        '11000000-0000-0000-0000-000000000005',
        NULL,
        '2026-03-01',
        15, 12, 1, 0;  -- total_born(15) ≠ 12+1+0=13
    RAISE NOTICE 'FAIL: CHECK constraint not working for total_born integrity';
EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'PASS: chk_total_born_integrity 제약 정상 동작';
END $$;

\echo '    8-3. 교배 없이 분만 시도 → ERROR 기대 (validate_farrowing_sequence)'
DO $$
BEGIN
    INSERT INTO farrowings
        (id, farm_id, sow_id, mating_id, farrowing_date,
         total_born, born_alive, stillborn, mummified)
    VALUES
        (gen_random_uuid(),
         '00000000-0000-0000-0000-000000000010',
         '11000000-0000-0000-0000-000000000005',
         (SELECT id FROM matings WHERE sow_id = '11000000-0000-0000-0000-000000000001' LIMIT 1),
         -- A-005는 교배 기록 없음
         '2026-05-01', 12, 12, 0, 0);
    RAISE NOTICE 'FAIL: Sequence validation not working';
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'PASS: validate_farrowing_sequence 트리거 정상 동작 (%)' , SQLERRM;
END $$;

\echo '    8-4. 음수 weaned_count → ERROR 기대'
DO $$
BEGIN
    -- A-003은 분만/이유 없으므로 직접 제약 위반 테스트
    INSERT INTO weanings
        (id, farm_id, sow_id, farrowing_id, weaning_date, weaned_count)
    VALUES
        (gen_random_uuid(),
         '00000000-0000-0000-0000-000000000010',
         '11000000-0000-0000-0000-000000000001',
         'FA000001-0000-0000-0000-000000000001',
         '2026-06-01', -1);
    RAISE NOTICE 'FAIL: Range check not working for weaned_count';
EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'PASS: chk_weaned_count 제약 정상 동작';
END $$;


-- ── 9. compliance_profiles 5개 시장 커버 확인 ────────────────────────────
\echo ''
\echo '[9] compliance_profiles — 5개 시장 커버 확인'
SELECT profile_code, profile_name,
       requires_antibiotic_tracking, min_wean_period
FROM compliance_profiles
ORDER BY profile_code;


-- ── 10. scope_kpi_recommendations 시드 확인 ──────────────────────────────
\echo ''
\echo '[10] scope_kpi_recommendations — KR/NA/EU 시드 확인'
SELECT scope_code, kpi_code, is_base, is_addon, addon_code, display_priority
FROM scope_kpi_recommendations
ORDER BY scope_code, display_priority;


\echo ''
\echo '══════════════════════════════════════════════'
\echo ' Validation Complete'
\echo '══════════════════════════════════════════════'
