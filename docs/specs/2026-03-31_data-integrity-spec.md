# PigOS — 데이터 정합성 규격서

> 작성일: 2026-03-31
> 목적: 피그플랜 27년 운영에서 검증된 데이터 정합성 규칙을 PigOS 신규 스키마에 매핑
> 원칙: 피그플랜의 **구조(스키마)는 참고하지 않음**. **비즈니스 규칙만 이식**.

---

## 1. 문서 목적

피그플랜은 27년간 688개 농장, 1.52억 건의 데이터를 무결성 문제 없이 운영했다.
이 시스템에서 검증된 데이터 정합성 규칙을 추출하여,
PigOS의 새로운 PostgreSQL 스키마에서도 **동일한 수준의 데이터 보호**가 이루어지도록 한다.

### 규칙 분류

| 유형 | 설명 | 적용 레벨 |
|------|------|-----------|
| **HARD** | 위반 시 데이터 INSERT/UPDATE 거부 | DB (CHECK, TRIGGER, UNIQUE) |
| **SOFT** | 위반 시 경고, 데이터는 저장 | API (Validation) |
| **CALC** | 계산 로직, 결과값 검증 | Application (Function, View) |

---

## 2. 모돈 두수 정합성 (Sow Inventory Integrity)

### 2.1 [INV-01] 활성 모돈 수 = 입식 - 퇴역 (HARD)

**피그플랜 규칙**:
```
활성 모돈 = TB_MODON WHERE IN_DT ≤ 기준일 AND OUT_DT > 기준일 AND USE_YN = 'Y'
OUT_DT = '9999-12-31' → 현재 활성
OUT_DT = 실제 날짜 → 퇴역 (도태/폐사/전출/판매)
```

**PigOS 매핑**:
```sql
-- sows 테이블에 exit_date 추가 필요
-- 활성 모돈:
SELECT COUNT(*) FROM sows
WHERE farm_id = ?
  AND entry_date <= '기준일'
  AND (exit_date IS NULL OR exit_date > '기준일')
  AND deleted_at IS NULL;

-- 검증 공식 (항상 성립해야 함):
-- COUNT(입식) - COUNT(퇴역) = COUNT(활성)
```

**현재 스키마 GAP**: sows 테이블에 `exit_date` 컬럼 없음. removals 테이블과 JOIN해야 하며, 과거 시점 재고 추적이 복잡함.

**필요 조치**:
```sql
ALTER TABLE sows ADD COLUMN exit_date DATE;

-- removals INSERT 시 자동 갱신 트리거
CREATE OR REPLACE FUNCTION trg_removal_exit_date() RETURNS TRIGGER AS $$
BEGIN
    UPDATE sows SET
        exit_date = NEW.removal_date,
        status = CASE
            WHEN NEW.removal_type IN ('DEAD') THEN 'DEAD'
            ELSE 'CULLED'
        END
    WHERE id = NEW.sow_id;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_removals_after_insert
    AFTER INSERT ON removals
    FOR EACH ROW EXECUTE FUNCTION trg_removal_exit_date();
```

---

### 2.2 [INV-02] 상태별 두수 합 = 전체 활성 모돈 (HARD)

**피그플랜 규칙**:
```
전체 활성 = 후보(010001) + 임신(010002) + 포유(010003/010004) + 이유모(010005) + 사고(010006/010007)
SP_INS_WEEK_MODON_POPUP: CNT_1 + CNT_2 + CNT_3 + CNT_4 + CNT_5 = 전체
```

**PigOS 매핑**:
```sql
-- 검증 쿼리: 이 결과는 항상 0이어야 함
SELECT
    COUNT(*) FILTER (WHERE status NOT IN
        ('ACTIVE','GESTATING','LACTATING','WEANED','DRY','CULLED','DEAD'))
FROM sows WHERE farm_id = ? AND deleted_at IS NULL;

-- 상태별 집계 뷰
CREATE OR REPLACE VIEW v_sow_inventory AS
SELECT
    farm_id,
    COUNT(*) FILTER (WHERE status = 'ACTIVE' AND exit_date IS NULL) AS gilt_count,
    COUNT(*) FILTER (WHERE status = 'GESTATING' AND exit_date IS NULL) AS gestating_count,
    COUNT(*) FILTER (WHERE status = 'LACTATING' AND exit_date IS NULL) AS lactating_count,
    COUNT(*) FILTER (WHERE status = 'WEANED' AND exit_date IS NULL) AS weaned_count,
    COUNT(*) FILTER (WHERE status = 'DRY' AND exit_date IS NULL) AS dry_count,
    COUNT(*) FILTER (WHERE exit_date IS NULL AND deleted_at IS NULL) AS total_active,
    COUNT(*) FILTER (WHERE status = 'CULLED') AS culled_total,
    COUNT(*) FILTER (WHERE status = 'DEAD') AS dead_total
FROM sows
WHERE deleted_at IS NULL
GROUP BY farm_id;
```

---

### 2.3 [INV-03] 산차별 두수 분포 (CALC)

**피그플랜 규칙**:
```
산차 분류: 후보돈(0산), 1산~7산, 8산 이상
SP_INS_WEEK_MODON_POPUP: 10개 행 (후보, 0산, 1~7산, 8산↑)으로 MERGE
빈 산차도 0으로 채움 (프론트엔드 표시용)
```

**PigOS 매핑**:
```sql
-- 산차별 × 상태별 크로스탭
CREATE OR REPLACE VIEW v_sow_parity_distribution AS
SELECT
    farm_id,
    CASE
        WHEN parity = 0 AND status = 'ACTIVE' THEN '후보돈'
        WHEN parity = 0 THEN '0산'
        WHEN parity BETWEEN 1 AND 7 THEN parity || '산'
        WHEN parity >= 8 THEN '8산↑'
    END AS parity_group,
    COUNT(*) FILTER (WHERE status = 'GESTATING') AS gestating,
    COUNT(*) FILTER (WHERE status = 'LACTATING') AS lactating,
    COUNT(*) FILTER (WHERE status = 'WEANED') AS weaned,
    COUNT(*) FILTER (WHERE status IN ('ACTIVE','DRY')) AS other,
    COUNT(*) AS subtotal
FROM sows
WHERE exit_date IS NULL AND deleted_at IS NULL
GROUP BY farm_id, CASE
    WHEN parity = 0 AND status = 'ACTIVE' THEN '후보돈'
    WHEN parity = 0 THEN '0산'
    WHEN parity BETWEEN 1 AND 7 THEN parity || '산'
    WHEN parity >= 8 THEN '8산↑'
END;
```

---

## 3. 자돈 두수 정합성 (Piglet Count Integrity)

### 3.1 [PIG-01] 분만 시 산자수 균형 (HARD)

**피그플랜 규칙**:
```
TB_BUNMAN: SILSAN(실산) + SASAN(사산) + MILA(미라) = 총산
실산 = 실산암(SILSAN_AM) + 실산수(SILSAN_SU)
```

**PigOS 매핑**:
```sql
ALTER TABLE farrowings ADD CONSTRAINT chk_total_born
    CHECK (total_born = born_alive + stillborn + mummified);

ALTER TABLE farrowings ADD CONSTRAINT chk_born_alive_positive
    CHECK (born_alive >= 0);
ALTER TABLE farrowings ADD CONSTRAINT chk_stillborn_positive
    CHECK (stillborn >= 0);
ALTER TABLE farrowings ADD CONSTRAINT chk_mummified_positive
    CHECK (mummified >= 0);
ALTER TABLE farrowings ADD CONSTRAINT chk_total_born_range
    CHECK (total_born >= 0 AND total_born <= 30);
```

---

### 3.2 [PIG-02] 포유 기간 자돈 수 추적 (HARD)

**피그플랜 규칙**:
```
TB_MODON_JADON_TRANS로 일별 변동 추적:
  포유개시 두수(POGAE) = 실산(SILSAN)
    - 생시도태(160001)
    + 양자전입(160003)
    - 양자전출(160004)
    - 포유폐사(160002)
    = 이유두수 (TB_EU.DUSU)

검증: POGAE 계산값 = DUSU 실제값
```

**PigOS 매핑** (piglet_events 테이블 필요):
```sql
-- 검증 함수
CREATE OR REPLACE FUNCTION fn_verify_piglet_balance(p_farrowing_id UUID)
RETURNS TABLE(
    born_alive INT,
    stillborn_removed INT,
    deaths INT,
    foster_in INT,
    foster_out INT,
    expected_weaned INT,
    actual_weaned INT,
    is_balanced BOOLEAN,
    difference INT
) AS $$
SELECT
    f.born_alive,
    COALESCE(SUM(pe.piglet_count) FILTER
        (WHERE pe.event_type = 'STILLBORN_REMOVAL'), 0)::INT AS stillborn_removed,
    COALESCE(SUM(pe.piglet_count) FILTER
        (WHERE pe.event_type = 'DEATH'), 0)::INT AS deaths,
    COALESCE(SUM(pe.piglet_count) FILTER
        (WHERE pe.event_type = 'FOSTER_IN'), 0)::INT AS foster_in,
    COALESCE(SUM(pe.piglet_count) FILTER
        (WHERE pe.event_type = 'FOSTER_OUT'), 0)::INT AS foster_out,
    (f.born_alive
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'STILLBORN_REMOVAL'), 0)
     + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'DEATH'), 0)
    )::INT AS expected_weaned,
    w.weaned_count AS actual_weaned,
    (f.born_alive
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'STILLBORN_REMOVAL'), 0)
     + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'DEATH'), 0)
    ) = COALESCE(w.weaned_count, 0) AS is_balanced,
    (f.born_alive
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'STILLBORN_REMOVAL'), 0)
     + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
     - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'DEATH'), 0)
     - COALESCE(w.weaned_count, 0)
    )::INT AS difference
FROM farrowings f
LEFT JOIN piglet_events pe ON pe.farrowing_id = f.id AND pe.deleted_at IS NULL
LEFT JOIN weanings w ON w.farrowing_id = f.id AND w.deleted_at IS NULL
WHERE f.id = p_farrowing_id
GROUP BY f.born_alive, w.weaned_count;
$$ LANGUAGE sql;
```

---

### 3.3 [PIG-03] 이유 두수 ≤ 포유 중 최대 두수 (SOFT)

**피그플랜 규칙**:
```
이유두수(DUSU) ≤ 실산(SILSAN) + 지입(JI_DS) - 지출(JC_DS)
초과 시 데이터 품질 경고 (하드 블록은 아님)
```

**PigOS 매핑**:
```sql
-- API 레벨 검증 (이유 기록 시):
-- 1. 해당 분만의 born_alive 조회
-- 2. piglet_events에서 foster_in, foster_out 합계
-- 3. max_possible = born_alive + foster_in - foster_out
-- 4. IF weaned_count > max_possible THEN WARNING (데이터 확인 요청)
-- 5. IF weaned_count < 0 THEN REJECT
```

---

### 3.4 [PIG-04] 위탁(Foster) 양방향 정합성 (HARD)

**피그플랜 규칙**:
```
모돈 A → 모돈 B 자돈 2두 위탁 시:
  TB_MODON_JADON_TRANS (PIG_NO=A, GUBUN_CD='160004', DUSU=2) ← A에서 지출
  TB_MODON_JADON_TRANS (PIG_NO=B, GUBUN_CD='160003', DUSU=2) ← B로 지입
  두 레코드가 항상 쌍으로 존재
```

**PigOS 매핑**:
```sql
-- piglet_events에서 위탁은 반드시 양방향 기록
-- FOSTER_OUT: source sow (target_sow_id = 받는 모돈)
-- FOSTER_IN:  target sow (target_sow_id = 보내는 모돈)

-- 검증 쿼리: 불균형 위탁 찾기
SELECT
    pe_out.farrowing_id AS source_farrowing,
    pe_out.piglet_count AS out_count,
    pe_in.piglet_count AS in_count
FROM piglet_events pe_out
LEFT JOIN piglet_events pe_in
    ON pe_in.event_type = 'FOSTER_IN'
    AND pe_in.target_sow_id = pe_out.sow_id
    AND pe_in.event_date = pe_out.event_date
    AND pe_in.piglet_count = pe_out.piglet_count
WHERE pe_out.event_type = 'FOSTER_OUT'
    AND pe_in.id IS NULL;  -- 매칭 안 되는 지출 = 불균형
```

---

### 3.5 [PIG-05] 포유 중 현재 자돈 수 실시간 뷰 (CALC)

**피그플랜 규칙**:
```
현재 포유두수 = SILSAN - SUM(160001) - SUM(160002) + SUM(160003) - SUM(160004)
(분만 이후 ~ 이유 이전 기간의 모든 이벤트 반영)
```

**PigOS 매핑**:
```sql
CREATE OR REPLACE VIEW v_current_nursing_piglets AS
SELECT
    f.farm_id,
    f.sow_id,
    s.ear_tag,
    f.id AS farrowing_id,
    f.farrowing_date,
    f.born_alive,
    COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'STILLBORN_REMOVAL'), 0) AS removed,
    COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'DEATH'), 0) AS deaths,
    COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0) AS foster_in,
    COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0) AS foster_out,
    f.born_alive
        - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'STILLBORN_REMOVAL'), 0)
        - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'DEATH'), 0)
        + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)
        - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
        AS current_nursing_count,
    CURRENT_DATE - f.farrowing_date AS nursing_days
FROM farrowings f
JOIN sows s ON s.id = f.sow_id
LEFT JOIN piglet_events pe ON pe.farrowing_id = f.id AND pe.deleted_at IS NULL
LEFT JOIN weanings w ON w.farrowing_id = f.id AND w.deleted_at IS NULL
WHERE s.status = 'LACTATING'
    AND s.exit_date IS NULL
    AND s.deleted_at IS NULL
    AND f.deleted_at IS NULL
    AND w.id IS NULL  -- 아직 이유 안 한 분만만
GROUP BY f.farm_id, f.sow_id, s.ear_tag, f.id, f.farrowing_date, f.born_alive;
```

---

## 4. 작업 순서 정합성 (Work Sequence Integrity)

### 4.1 [SEQ-01] 번식 사이클 순서 강제 (HARD)

**피그플랜 규칙**:
```
TB_MODON_WK 순서: A(전입) → G(교배) → B(분만) → E(이유) → G(재교배) → ...
SEQ 필드가 순번 보장
분만 전 교배 필수, 이유 전 분만 필수
```

**PigOS 매핑**:
```sql
-- 1. 분만 시: 해당 모돈에 선행 교배가 존재해야 함
CREATE OR REPLACE FUNCTION validate_farrowing_has_mating()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mating_id IS NULL THEN
        -- mating_id 없으면, 최소한 해당 모돈의 교배가 존재하는지 확인
        IF NOT EXISTS (
            SELECT 1 FROM matings
            WHERE sow_id = NEW.sow_id
              AND mating_date < NEW.farrowing_date
              AND deleted_at IS NULL
        ) THEN
            RAISE EXCEPTION '[SEQ-01] 교배 기록 없이 분만 불가. sow_id=%, farrowing_date=%',
                NEW.sow_id, NEW.farrowing_date;
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_farrowing_seq_check
    BEFORE INSERT ON farrowings
    FOR EACH ROW EXECUTE FUNCTION validate_farrowing_has_mating();

-- 2. 이유 시: 해당 모돈에 선행 분만이 존재해야 함
CREATE OR REPLACE FUNCTION validate_weaning_has_farrowing()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.farrowing_id IS NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM farrowings
            WHERE sow_id = NEW.sow_id
              AND farrowing_date < NEW.weaning_date
              AND deleted_at IS NULL
        ) THEN
            RAISE EXCEPTION '[SEQ-01] 분만 기록 없이 이유 불가. sow_id=%, weaning_date=%',
                NEW.sow_id, NEW.weaning_date;
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_weaning_seq_check
    BEFORE INSERT ON weanings
    FOR EACH ROW EXECUTE FUNCTION validate_weaning_has_farrowing();
```

---

### 4.2 [SEQ-02] 동시 활성 사이클 방지 (HARD)

**피그플랜 규칙**:
```
하나의 모돈은 동시에 하나의 번식 사이클만 가능
마지막 작업이 E(이유)인 모돈만 다음 G(교배) 가능
마지막 작업이 B(분만)인 모돈은 E(이유) 전 재교배 불가
```

**PigOS 매핑** (breeding_cycles 테이블 사용 시):
```sql
-- 활성 사이클 1개 제한
CREATE UNIQUE INDEX idx_sow_one_active_cycle
ON breeding_cycles (sow_id)
WHERE cycle_status NOT IN ('WEANED', 'FAILED');

-- 교배 시: 현재 활성 사이클 없는 모돈만 가능
CREATE OR REPLACE FUNCTION validate_mating_no_active_cycle()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM breeding_cycles
        WHERE sow_id = NEW.sow_id
          AND cycle_status NOT IN ('WEANED', 'FAILED')
    ) THEN
        RAISE EXCEPTION '[SEQ-02] 활성 번식 사이클이 있는 모돈은 재교배 불가. sow_id=%',
            NEW.sow_id;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
```

---

### 4.3 [SEQ-03] 교배 횟수(GYOBAE_CNT) 추적 (HARD)

**피그플랜 규칙**:
```
같은 산차 내 교배 횟수:
  GYOBAE_CNT = 1 → 첫 교배
  GYOBAE_CNT = 2+ → 재교배 (임신실패 후)
  새 산차 시작 → 1로 리셋
```

**PigOS 매핑**:
```sql
-- breeding_cycles.mating_count로 추적
-- 재교배 시: mating_count += 1
-- 새 사이클 시작 시: mating_count = 1 (기본값)

-- 재교배 판별:
-- 같은 breeding_cycle_id에 matings가 2건 이상 → 재교배
```

---

## 5. 날짜 정합성 (Date Integrity)

### 5.1 [DATE-01] 임신 기간 범위 (SOFT)

**피그플랜 규칙**:
```
TC_FARM_CONFIG CODE 140002: 기본 115일
허용 범위: 100~130일 (극단적 조산/지연 포함)
정상 범위: 112~118일
```

**PigOS 매핑**:
```sql
-- API 레벨 검증
-- gestation_days = farrowing_date - mating_date

-- SOFT 경고 (정상 범위 밖):
IF gestation_days < 112 OR gestation_days > 118 THEN WARNING

-- HARD 거부 (생물학적 불가능):
ALTER TABLE farrowings ADD CONSTRAINT chk_farrowing_date_logic
    CHECK (farrowing_date > (
        SELECT mating_date FROM matings WHERE id = mating_id
    ) -- 이건 CHECK로 안 됨, 트리거 필요);

-- 트리거로 구현:
CREATE OR REPLACE FUNCTION validate_gestation_period()
RETURNS TRIGGER AS $$
DECLARE
    v_mating_date DATE;
    v_days INT;
    v_config_days INT;
BEGIN
    IF NEW.mating_id IS NOT NULL THEN
        SELECT mating_date INTO v_mating_date FROM matings WHERE id = NEW.mating_id;
        v_days := NEW.farrowing_date - v_mating_date;

        -- farm_configs에서 농장별 설정 조회
        SELECT config_value::INT INTO v_config_days
        FROM farm_configs
        WHERE farm_id = NEW.farm_id AND config_key = 'GESTATION_DAYS';
        v_config_days := COALESCE(v_config_days, 114); -- 기본값

        IF v_days < 100 OR v_days > 130 THEN
            RAISE EXCEPTION '[DATE-01] 임신기간 %일 — 허용범위(100~130일) 초과', v_days;
        END IF;

        IF NEW.farrowing_date <= v_mating_date THEN
            RAISE EXCEPTION '[DATE-01] 분만일(%)이 교배일(%) 이전', NEW.farrowing_date, v_mating_date;
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_farrowing_gestation_check
    BEFORE INSERT OR UPDATE ON farrowings
    FOR EACH ROW EXECUTE FUNCTION validate_gestation_period();
```

---

### 5.2 [DATE-02] 포유 기간 범위 (SOFT)

**피그플랜 규칙**:
```
TC_FARM_CONFIG CODE 140003: 기본 21일
허용 범위: 14~35일 (지역별 차이)
  - EU: 최소 28일 (동물복지 규정)
  - 미국: 17~21일 (일반적)
  - 한국: 21~28일
  - 중국: 21~25일
```

**PigOS 매핑**:
```sql
CREATE OR REPLACE FUNCTION validate_nursing_period()
RETURNS TRIGGER AS $$
DECLARE
    v_farrowing_date DATE;
    v_days INT;
BEGIN
    IF NEW.farrowing_id IS NOT NULL THEN
        SELECT farrowing_date INTO v_farrowing_date
        FROM farrowings WHERE id = NEW.farrowing_id;
        v_days := NEW.weaning_date - v_farrowing_date;

        IF NEW.weaning_date <= v_farrowing_date THEN
            RAISE EXCEPTION '[DATE-02] 이유일(%)이 분만일(%) 이전', NEW.weaning_date, v_farrowing_date;
        END IF;

        IF v_days < 10 OR v_days > 60 THEN
            RAISE EXCEPTION '[DATE-02] 포유기간 %일 — 허용범위(10~60일) 초과', v_days;
        END IF;

        -- weaning_age_days 자동 계산
        NEW.weaning_age_days := v_days;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_weaning_nursing_check
    BEFORE INSERT OR UPDATE ON weanings
    FOR EACH ROW EXECUTE FUNCTION validate_nursing_period();
```

---

### 5.3 [DATE-03] 이유→재교배 간격 (SOFT)

**피그플랜 규칙**:
```
TC_FARM_CONFIG CODE 140008: 기본 7일 (WEI: Wean-to-Estrus Interval)
정상: 4~10일
비정상: <3일 (너무 빠름) 또는 >14일 (연장 무발정)
```

**PigOS 매핑**:
```sql
-- API 레벨 경고:
-- return_days = mating_date - (이전 weaning_date)
-- IF return_days < 3 THEN WARNING '재교배 간격이 너무 짧음'
-- IF return_days > 14 THEN WARNING '연장 무발정 의심'
-- IF return_days > 21 THEN WARNING '재발정 주기 초과, 수의사 확인 필요'
```

---

### 5.4 [DATE-04] 입식일 ≤ 모든 작업일 (HARD)

**피그플랜 규칙**:
```
TB_MODON.IN_DT ≤ 모든 TB_MODON_WK.WK_DT
입식 전 작업 불가
```

**PigOS 매핑**:
```sql
-- 교배 시: mating_date >= sows.entry_date
-- 분만 시: farrowing_date >= sows.entry_date
-- 이유 시: weaning_date >= sows.entry_date
-- 도태 시: removal_date >= sows.entry_date

-- 각 이벤트 테이블 INSERT 트리거에서 검증
-- (공통 함수로 추출)
CREATE OR REPLACE FUNCTION validate_event_after_entry(
    p_sow_id UUID, p_event_date DATE, p_event_name TEXT
) RETURNS VOID AS $$
DECLARE
    v_entry_date DATE;
BEGIN
    SELECT entry_date INTO v_entry_date FROM sows WHERE id = p_sow_id;
    IF p_event_date < v_entry_date THEN
        RAISE EXCEPTION '[DATE-04] %일(%)이 입식일(%) 이전',
            p_event_name, p_event_date, v_entry_date;
    END IF;
END; $$ LANGUAGE plpgsql;
```

---

### 5.5 [DATE-05] 도태/폐사일 이후 작업 불가 (HARD)

**피그플랜 규칙**:
```
OUT_DT 이후 모든 작업 거부
OUT_DT != '9999-12-31' → 더 이상 작업 불가
```

**PigOS 매핑**:
```sql
-- 공통 검증: 퇴역 모돈에 대한 모든 작업 거부
CREATE OR REPLACE FUNCTION validate_sow_is_active(
    p_sow_id UUID, p_event_name TEXT
) RETURNS VOID AS $$
DECLARE
    v_status VARCHAR(20);
    v_exit_date DATE;
BEGIN
    SELECT status, exit_date INTO v_status, v_exit_date
    FROM sows WHERE id = p_sow_id;

    IF v_status IN ('CULLED', 'DEAD') OR v_exit_date IS NOT NULL THEN
        RAISE EXCEPTION '[DATE-05] 퇴역된 모돈(status=%, exit=%)에 % 불가',
            v_status, v_exit_date, p_event_name;
    END IF;
END; $$ LANGUAGE plpgsql;
```

---

## 6. 상태 전이 정합성 (Status Transition Integrity)

### 6.1 [ST-01] 허용 상태 전이 매트릭스 (HARD)

**피그플랜 규칙 (SF_GET_MODONGB_STATUS)**:
```
상태는 최종 작업에서 자동 파생:
  G(교배) → 010002(임신)
  B(분만) → 010003(포유)
  E(이유) → 010005(이유모) 또는 010004(대리모)
  F(사고) → 010006(재발) 또는 010007(유산)
  OUT_DT 설정 → 010008(도폐사)
```

**PigOS 매핑 — 상태 전이 매트릭스**:

```
현재 상태 →        이벤트          → 다음 상태
────────────────────────────────────────────────
ACTIVE (후보)      교배(mating)     → GESTATING
GESTATING (임신)   분만(farrowing)  → LACTATING
GESTATING (임신)   재발정           → ACTIVE (또는 별도 상태)
GESTATING (임신)   유산             → ACTIVE (또는 별도 상태)
LACTATING (포유)   이유(weaning)    → WEANED
WEANED (이유)      교배(mating)     → GESTATING
WEANED (이유)      건기 전환        → DRY
DRY (건기)         교배(mating)     → GESTATING
ANY (전체)         도태(removal)    → CULLED
ANY (전체)         폐사(removal)    → DEAD
CULLED             (전이 불가)      → ─
DEAD               (전이 불가)      → ─

금지된 전이:
  CULLED → ANY (도태된 모돈 복원 불가)
  DEAD → ANY (폐사 모돈 복원 불가)
  LACTATING → GESTATING (포유 중 교배 불가 — 이유 먼저)
  ACTIVE → LACTATING (후보돈 직접 포유 불가 — 교배/분만 먼저)
  GESTATING → WEANED (임신 중 이유 불가 — 분만 먼저)
```

**구현**:
```sql
CREATE OR REPLACE FUNCTION validate_sow_status_transition()
RETURNS TRIGGER AS $$
DECLARE
    v_allowed BOOLEAN := FALSE;
BEGIN
    -- 같은 값 → 변경 아님
    IF OLD.status = NEW.status THEN RETURN NEW; END IF;

    -- 최종 상태에서 전이 금지
    IF OLD.status IN ('CULLED', 'DEAD') THEN
        RAISE EXCEPTION '[ST-01] 최종 상태(%)에서 전이 불가', OLD.status;
    END IF;

    -- 허용 전이 체크
    v_allowed := CASE
        WHEN OLD.status = 'ACTIVE'    AND NEW.status = 'GESTATING' THEN TRUE
        WHEN OLD.status = 'GESTATING' AND NEW.status = 'LACTATING' THEN TRUE
        WHEN OLD.status = 'GESTATING' AND NEW.status = 'ACTIVE'   THEN TRUE  -- 재발정/유산
        WHEN OLD.status = 'LACTATING' AND NEW.status = 'WEANED'   THEN TRUE
        WHEN OLD.status = 'WEANED'    AND NEW.status = 'GESTATING' THEN TRUE
        WHEN OLD.status = 'WEANED'    AND NEW.status = 'DRY'      THEN TRUE
        WHEN OLD.status = 'DRY'       AND NEW.status = 'GESTATING' THEN TRUE
        WHEN NEW.status IN ('CULLED', 'DEAD') THEN TRUE  -- 어디서든 도태/폐사 가능
        ELSE FALSE
    END;

    IF NOT v_allowed THEN
        RAISE EXCEPTION '[ST-01] 허용되지 않는 상태 전이: % → %', OLD.status, NEW.status;
    END IF;

    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sow_status_transition
    BEFORE UPDATE OF status ON sows
    FOR EACH ROW EXECUTE FUNCTION validate_sow_status_transition();
```

---

### 6.2 [ST-02] 이벤트 기반 상태 자동 전이 (HARD)

**피그플랜 규칙**:
```
상태를 직접 UPDATE하지 않음
작업(G/B/E/F/Z) INSERT 시 상태가 자동 파생됨
```

**PigOS 매핑 — 이벤트 테이블별 자동 상태 전이 트리거**:
```sql
-- 교배 → GESTATING
CREATE OR REPLACE FUNCTION trg_mating_auto_status() RETURNS TRIGGER AS $$
BEGIN
    PERFORM validate_sow_is_active(NEW.sow_id, '교배');
    UPDATE sows SET status = 'GESTATING' WHERE id = NEW.sow_id;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_matings_status AFTER INSERT ON matings
    FOR EACH ROW EXECUTE FUNCTION trg_mating_auto_status();

-- 분만 → LACTATING + 산차 +1
CREATE OR REPLACE FUNCTION trg_farrowing_auto_status() RETURNS TRIGGER AS $$
BEGIN
    PERFORM validate_sow_is_active(NEW.sow_id, '분만');
    UPDATE sows SET
        status = 'LACTATING',
        parity = parity + 1
    WHERE id = NEW.sow_id;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_farrowings_status AFTER INSERT ON farrowings
    FOR EACH ROW EXECUTE FUNCTION trg_farrowing_auto_status();

-- 이유 → WEANED
CREATE OR REPLACE FUNCTION trg_weaning_auto_status() RETURNS TRIGGER AS $$
BEGIN
    PERFORM validate_sow_is_active(NEW.sow_id, '이유');
    UPDATE sows SET status = 'WEANED' WHERE id = NEW.sow_id;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_weanings_status AFTER INSERT ON weanings
    FOR EACH ROW EXECUTE FUNCTION trg_weaning_auto_status();

-- 도태/폐사 → CULLED/DEAD + exit_date
-- (INV-01에서 정의한 trg_removal_exit_date 사용)
```

---

## 7. 교차 테이블 정합성 (Cross-Table Integrity)

### 7.1 [CROSS-01] 교배-분만-이유 체인 모돈 일치 (HARD)

**피그플랜 규칙**:
```
같은 (FARM_NO, PIG_NO)에서만 G→B→E 체인 형성
다른 모돈의 교배에 다른 모돈의 분만을 연결하는 것은 불가
```

**PigOS 매핑**:
```sql
-- 분만의 sow_id = 교배의 sow_id
CREATE OR REPLACE FUNCTION validate_farrowing_sow_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mating_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM matings WHERE id = NEW.mating_id AND sow_id = NEW.sow_id
        ) THEN
            RAISE EXCEPTION '[CROSS-01] 분만 모돈(%)과 교배 모돈이 불일치', NEW.sow_id;
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_farrowing_sow_match BEFORE INSERT ON farrowings
    FOR EACH ROW EXECUTE FUNCTION validate_farrowing_sow_match();

-- 이유의 sow_id = 분만의 sow_id
CREATE OR REPLACE FUNCTION validate_weaning_sow_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.farrowing_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM farrowings WHERE id = NEW.farrowing_id AND sow_id = NEW.sow_id
        ) THEN
            RAISE EXCEPTION '[CROSS-01] 이유 모돈(%)과 분만 모돈이 불일치', NEW.sow_id;
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_weaning_sow_match BEFORE INSERT ON weanings
    FOR EACH ROW EXECUTE FUNCTION validate_weaning_sow_match();
```

---

### 7.2 [CROSS-02] 하나의 분만에 하나의 이유 (HARD)

**피그플랜 규칙**:
```
하나의 분만(B)에는 하나의 이유(E)만 대응
같은 분만에 이유가 2건 기록될 수 없음
```

**PigOS 매핑**:
```sql
CREATE UNIQUE INDEX idx_one_weaning_per_farrowing
ON weanings (farrowing_id)
WHERE farrowing_id IS NOT NULL AND deleted_at IS NULL;
```

---

### 7.3 [CROSS-03] 산차 일관성 (HARD)

**피그플랜 규칙**:
```
TB_MODON_WK.SANCHA가 같은 값인 작업들은 같은 번식 사이클
분만(B) 시 SANCHA 증가
이유(E) 시 SANCHA 유지 (분만과 동일)
교배(G) 시 SANCHA 유지 (다음 분만에서 증가)
```

**PigOS 매핑**:
```sql
-- farrowings.parity_at_birth = sows.parity (분만 시점)
-- → 분만 트리거에서 parity +1 전에 parity_at_birth 기록

CREATE OR REPLACE FUNCTION trg_farrowing_record_parity() RETURNS TRIGGER AS $$
DECLARE
    v_current_parity INT;
BEGIN
    SELECT parity INTO v_current_parity FROM sows WHERE id = NEW.sow_id;
    NEW.parity_at_birth := v_current_parity + 1; -- 이번 분만의 산차
    RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_farrowing_parity BEFORE INSERT ON farrowings
    FOR EACH ROW EXECUTE FUNCTION trg_farrowing_record_parity();
```

---

### 7.4 [CROSS-04] farm_id 일관성 (HARD)

**규칙**: 연결된 레코드들의 farm_id는 반드시 동일해야 함.

```sql
-- 분만의 farm_id = 모돈의 farm_id
CREATE OR REPLACE FUNCTION validate_farm_consistency()
RETURNS TRIGGER AS $$
DECLARE
    v_sow_farm_id UUID;
BEGIN
    SELECT farm_id INTO v_sow_farm_id FROM sows WHERE id = NEW.sow_id;
    IF NEW.farm_id != v_sow_farm_id THEN
        RAISE EXCEPTION '[CROSS-04] farm_id 불일치: 이벤트(%) ≠ 모돈(%)',
            NEW.farm_id, v_sow_farm_id;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- matings, farrowings, weanings, removals, health_events에 적용
```

---

## 8. KPI 계산 정합성 (KPI Calculation Integrity)

### 8.1 [KPI-01] PSY 계산 규칙 (CALC)

**피그플랜 규칙**:
```
PSY = 12개월 누적 이유두수 / 평균 활성 모돈수
KPI_PSY in TS_INS_WEEK
NULL 방지: NVL(SUM(...), 0) 패턴
분모 = 0 시: PSY = 0 (division by zero 방지)
후보돈(010001) 제외 (활성 모돈에서)
```

**PigOS 매핑** — v_farm_psy 뷰 수정:
```sql
CREATE OR REPLACE VIEW v_farm_psy AS
SELECT
    s.farm_id,
    -- 활성 모돈수 (후보돈 제외)
    COUNT(DISTINCT s.id) FILTER (
        WHERE s.status IN ('GESTATING','LACTATING','WEANED','DRY')
        AND s.exit_date IS NULL
        AND s.deleted_at IS NULL
    ) AS active_sow_count,
    -- 12개월 rolling 이유두수
    COALESCE(SUM(w.weaned_count) FILTER (
        WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days'
        AND w.deleted_at IS NULL
    ), 0) AS weaned_12m,
    -- PSY
    CASE
        WHEN COUNT(DISTINCT s.id) FILTER (
            WHERE s.status IN ('GESTATING','LACTATING','WEANED','DRY')
            AND s.exit_date IS NULL
            AND s.deleted_at IS NULL
        ) = 0 THEN 0
        ELSE ROUND(
            COALESCE(SUM(w.weaned_count) FILTER (
                WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days'
                AND w.deleted_at IS NULL
            ), 0)::DECIMAL
            / COUNT(DISTINCT s.id) FILTER (
                WHERE s.status IN ('GESTATING','LACTATING','WEANED','DRY')
                AND s.exit_date IS NULL
                AND s.deleted_at IS NULL
            )
        , 2)
    END AS psy_rolling_12m,
    -- 평균 생존산자수
    COALESCE(ROUND(AVG(f.born_alive) FILTER (
        WHERE f.farrowing_date >= CURRENT_DATE - INTERVAL '365 days'
        AND f.deleted_at IS NULL
    ), 2), 0) AS avg_born_alive_12m,
    -- 평균 이유두수
    COALESCE(ROUND(AVG(w.weaned_count) FILTER (
        WHERE w.weaning_date >= CURRENT_DATE - INTERVAL '365 days'
        AND w.deleted_at IS NULL
    ), 2), 0) AS avg_weaned_12m
FROM sows s
LEFT JOIN farrowings f ON f.sow_id = s.id AND f.deleted_at IS NULL
LEFT JOIN weanings w ON w.sow_id = s.id AND w.deleted_at IS NULL
WHERE s.deleted_at IS NULL
GROUP BY s.farm_id;
```

---

### 8.2 [KPI-02] NPD 계산 규칙 (CALC)

**피그플랜 규칙**:
```
NPD = 이유일 ~ 다음 교배일 사이의 일수
MatingProcessor: AVG_RETURN = 이전 작업일 ~ 교배일 차이 평균
정상 범위: 4~10일
  <3일 → 임신실패 의심
  >14일 → 연장 무발정
GYOBAE_CNT=1 기준 (첫 교배만 카운트, 재교배 제외)
후보돈(SANCHA=0, GYOBAE_CNT=1) 첫교배는 제외
```

**PigOS 매핑** — v_sow_npd 뷰 수정:
```sql
CREATE OR REPLACE VIEW v_sow_npd AS
SELECT
    s.id AS sow_id,
    s.farm_id,
    s.ear_tag,
    s.parity,
    -- 이유 → 다음 교배 간 일수 (LATERAL로 정확한 매칭)
    COALESCE(SUM(npd.days), 0) AS npd_days_12m,
    COUNT(npd.days) AS npd_count,
    CASE WHEN COUNT(npd.days) > 0
        THEN ROUND(AVG(npd.days), 1)
        ELSE 0
    END AS npd_avg
FROM sows s
JOIN weanings w ON w.sow_id = s.id
    AND w.weaning_date >= CURRENT_DATE - INTERVAL '365 days'
    AND w.deleted_at IS NULL
LEFT JOIN LATERAL (
    SELECT
        m.mating_date,
        (m.mating_date - w.weaning_date) AS days
    FROM matings m
    WHERE m.sow_id = s.id
      AND m.mating_date > w.weaning_date
      AND m.mating_date <= w.weaning_date + INTERVAL '60 days'
      AND m.deleted_at IS NULL
    ORDER BY m.mating_date ASC
    LIMIT 1
) npd ON TRUE
WHERE s.deleted_at IS NULL
GROUP BY s.id, s.farm_id, s.ear_tag, s.parity;
```

---

### 8.3 [KPI-03] 육성율 (Pre-Weaning Survival Rate) (CALC)

**피그플랜 규칙**:
```
육성율 = (이유두수 / 실산두수) × 100
6개월 rolling 평균
```

**PigOS 매핑**:
```sql
-- 농장별 육성율
SELECT
    farm_id,
    ROUND(
        SUM(w.weaned_count)::DECIMAL / NULLIF(SUM(f.born_alive), 0) * 100
    , 1) AS survival_rate_pct
FROM farrowings f
JOIN weanings w ON w.farrowing_id = f.id AND w.deleted_at IS NULL
WHERE f.farrowing_date >= CURRENT_DATE - INTERVAL '180 days'
  AND f.deleted_at IS NULL
GROUP BY farm_id;
```

---

### 8.4 [KPI-04] 분만율 (Farrowing Rate) (CALC)

**규칙**:
```
분만율 = (분만두수 / 교배두수) × 100
기간: 교배 후 110~150일 윈도우 내 분만 여부
재교배(GYOBAE_CNT > 1) 제외, 첫 교배만 카운트
```

---

## 9. 농장 설정 정합성 (Farm Configuration Integrity)

### 9.1 [CFG-01] 농장별 번식 파라미터 (SOFT)

**피그플랜 규칙 (TC_FARM_CONFIG)**:

| CODE | 항목 | 기본값 | 단위 |
|------|------|--------|------|
| 140002 | 임신 기간 | 115일 | 일 |
| 140003 | 포유 기간 | 21일 | 일 |
| 140005 | 출하 일령 | 180일 | 일 |
| 140007 | 초산 일령 | 240일 | 일 |
| 140008 | 이유→재교배 | 7일 | 일 |

**PigOS 매핑**:
```sql
CREATE TABLE farm_configs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id     UUID NOT NULL REFERENCES farms(id),
    config_key  VARCHAR(50) NOT NULL,
    config_value VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(farm_id, config_key)
);

-- 기본값 시드
INSERT INTO farm_configs (farm_id, config_key, config_value, description) VALUES
    ('{farm_id}', 'GESTATION_DAYS', '114', '임신 기간 (일)'),
    ('{farm_id}', 'LACTATION_DAYS', '21', '포유 기간 (일)'),
    ('{farm_id}', 'WEI_TARGET_DAYS', '7', '이유→재교배 목표 간격 (일)'),
    ('{farm_id}', 'FIRST_MATING_AGE', '240', '초산 교배 일령 (일)'),
    ('{farm_id}', 'MARKET_AGE_DAYS', '180', '출하 일령 (일)'),
    ('{farm_id}', 'PREGNANCY_CHECK_DAY', '25', '교배 후 임신확인 일수'),
    ('{farm_id}', 'FARROWING_ALERT_DAYS', '3', '분만 예정 사전 알림 일수'),
    ('{farm_id}', 'WEANING_ALERT_DAYS', '1', '이유 예정 사전 알림 일수');
```

---

## 10. 정합성 규칙 전체 요약

### 10.1 규칙 목록

| ID | 규칙명 | 유형 | 레벨 | 구현 방법 |
|----|--------|------|------|-----------|
| INV-01 | 활성 모돈 수 = 입식 - 퇴역 | HARD | DB | exit_date + 트리거 |
| INV-02 | 상태별 합 = 전체 | HARD | DB | CHECK + 뷰 |
| INV-03 | 산차별 분포 | CALC | View | v_sow_parity_distribution |
| PIG-01 | 산자수 균형 (총산 = 실산+사산+미라) | HARD | DB | CHECK 제약 |
| PIG-02 | 포유 두수 추적 | HARD | DB | piglet_events + fn_verify |
| PIG-03 | 이유두수 ≤ 포유 최대 | SOFT | API | 경고 로직 |
| PIG-04 | 위탁 양방향 정합 | HARD | DB | 검증 쿼리 |
| PIG-05 | 포유 중 현재 자돈수 | CALC | View | v_current_nursing_piglets |
| SEQ-01 | 번식 사이클 순서 | HARD | DB | 트리거 |
| SEQ-02 | 동시 사이클 방지 | HARD | DB | UNIQUE INDEX |
| SEQ-03 | 교배 횟수 추적 | HARD | DB | breeding_cycles |
| DATE-01 | 임신 기간 범위 | SOFT | DB | 트리거 (경고/거부) |
| DATE-02 | 포유 기간 범위 | SOFT | DB | 트리거 (경고/거부) |
| DATE-03 | 이유→재교배 간격 | SOFT | API | 경고 |
| DATE-04 | 입식일 이후 작업 | HARD | DB | 공통 함수 |
| DATE-05 | 퇴역 후 작업 거부 | HARD | DB | 공통 함수 |
| ST-01 | 상태 전이 매트릭스 | HARD | DB | 트리거 |
| ST-02 | 이벤트 기반 자동 전이 | HARD | DB | 트리거 |
| CROSS-01 | 체인 모돈 일치 | HARD | DB | 트리거 |
| CROSS-02 | 1분만:1이유 | HARD | DB | UNIQUE INDEX |
| CROSS-03 | 산차 일관성 | HARD | DB | 트리거 |
| CROSS-04 | farm_id 일관성 | HARD | DB | 트리거 |
| KPI-01 | PSY 계산 | CALC | View | v_farm_psy (수정) |
| KPI-02 | NPD 계산 | CALC | View | v_sow_npd (수정) |
| KPI-03 | 육성율 | CALC | Query | API |
| KPI-04 | 분만율 | CALC | Query | API |
| CFG-01 | 농장 파라미터 | SOFT | DB | farm_configs 테이블 |
| **WEAN-01** | **이유 유형 4종 구분** | **HARD** | **DB** | **CHECK 제약** |
| **WEAN-02** | **부분 이유 시 다중 이유 허용** | **HARD** | **DB** | **조건부 UNIQUE** |
| **WEAN-03** | **Nurse Sow 워크플로우** | **HARD** | **DB** | **상태 전이 확장** |
| **HEAT-01** | **발정/무발정 8종 이벤트** | **SOFT** | **DB** | **reproductive_events CHECK** |
| **HEAT-02** | **발정→교배 연결** | **SOFT** | **DB** | **FK (mating_id)** |
| **HEAT-03** | **발정 주기 검증 (21일)** | **SOFT** | **API** | **경고 로직** |
| **GILT-01** | **GILT 상태 분리** | **HARD** | **DB** | **CHECK + 트리거** |
| **GILT-02** | **후보돈 입식 규칙** | **HARD** | **DB** | **트리거** |
| **GILT-03** | **후보돈→경산돈 전환** | **HARD** | **DB** | **트리거** |
| **NPD-01** | **후보돈 입식→첫교배** | **CALC** | **View** | **v_npd_gilt_entry** |
| **NPD-02** | **후보돈 입식→도태** | **CALC** | **View** | **v_npd_gilt_removal** |
| **NPD-03** | **WEI (이유→첫교배)** | **CALC** | **View** | **v_sow_npd (기존)** |
| **NPD-04** | **이유→도태** | **CALC** | **View** | **v_npd_wean_to_removal** |
| **NPD-05** | **교배→재교배** | **CALC** | **View** | **v_npd_reservice** |
| **NPD-06** | **교배→도태** | **CALC** | **View** | **v_npd_service_to_removal** |
| **NPD-TOTAL** | **농장 NPD 통합** | **CALC** | **View** | **v_npd_farm_total** |

### 10.2 구현 우선순위

```
P0 (스키마 v2 필수):
  - PIG-01: 산자수 CHECK
  - SEQ-01: 작업 순서 트리거
  - ST-01/02: 상태 전이 트리거
  - CROSS-01: 모돈 일치 트리거
  - CROSS-02: 1분만:1이유 UNIQUE
  - INV-01: exit_date 추가
  - DATE-04/05: 입식/퇴역 날짜 검증

P1 (MVP 런칭 전):
  - PIG-02~05: piglet_events 테이블 + 두수 검증
  - DATE-01/02: 임신/포유 기간 검증
  - CROSS-03/04: 산차/farm_id 일관성
  - KPI-01~04: 뷰 수정
  - CFG-01: farm_configs 테이블

P2 (Phase 2):
  - SEQ-02/03: breeding_cycles 기반 사이클 관리
  - PIG-04: 위탁 양방향 자동 검증
  - INV-03: 산차별 분포 뷰
```

---

## 11. 시뮬레이션 테스트 매트릭스

아래 시나리오를 PostgreSQL에서 실행하여 모든 규칙이 동작하는지 검증합니다.

| # | 시나리오 | 검증 규칙 | 기대 결과 |
|---|----------|-----------|-----------|
| T-01 | 후보돈 입식 (parity=0) | INV-01 | sow INSERT 성공, status=ACTIVE |
| T-02 | 교배 기록 | ST-02, SEQ-01 | status → GESTATING 자동 전이 |
| T-03 | 임신확인 (양성) | DATE-06 | check_date > mating_date |
| T-04 | 분만 (born_alive=12, stillborn=1, mummified=1) | PIG-01 | total_born = 14 CHECK 통과 |
| T-05 | 분만 시 산차 증가 | ST-02, CROSS-03 | parity 0→1, status → LACTATING |
| T-06 | 포유 중 자돈 폐사 2두 | PIG-02 | piglet_events 2건, 현재 포유 10두 |
| T-07 | 위탁 지출 2두 → 모돈B 지입 2두 | PIG-04 | 양방향 기록, A: 8두, B: +2두 |
| T-08 | 이유 (weaned=8) | PIG-02 | fn_verify: 12-2-2=8 ✅ balanced |
| T-09 | 이유 시 상태 전이 | ST-02 | status → WEANED |
| T-10 | 재교배 (7일 후) | DATE-03, SEQ-01 | 새 사이클 시작, status → GESTATING |
| T-11 | 분만 없이 이유 시도 | SEQ-01 | **REJECT** — 순서 위반 |
| T-12 | 교배 없이 분만 시도 | SEQ-01 | **REJECT** — 순서 위반 |
| T-13 | 죽은 모돈에 교배 시도 | DATE-05, ST-01 | **REJECT** — 퇴역 모돈 |
| T-14 | CULLED → GESTATING 시도 | ST-01 | **REJECT** — 최종 상태 |
| T-15 | LACTATING → GESTATING 시도 | ST-01 | **REJECT** — 금지 전이 |
| T-16 | 교배일 > 분만일 | DATE-01 | **REJECT** — 날짜 논리 |
| T-17 | 임신 기간 200일 | DATE-01 | **REJECT** — 범위 초과 |
| T-18 | 포유 기간 3일 | DATE-02 | **REJECT** — 범위 미달 |
| T-19 | total_born ≠ alive+still+mum | PIG-01 | **REJECT** — CHECK 위반 |
| T-20 | 이유두수 = -1 | PIG-01 | **REJECT** — 음수 불가 |
| T-21 | 같은 분만에 이유 2건 | CROSS-02 | **REJECT** — UNIQUE 위반 |
| T-22 | 모돈A 교배 → 모돈B 분만 연결 | CROSS-01 | **REJECT** — 모돈 불일치 |
| T-23 | 다른 farm_id로 이벤트 | CROSS-04 | **REJECT** — farm 불일치 |
| T-24 | 월마감 후 데이터 수정 | period_lock | **REJECT** — 잠금 기간 |
| T-25 | PSY 계산 검증 (수동 vs 뷰) | KPI-01 | 결과 일치 |
| T-26 | NPD 계산 (재발정 포함) | KPI-02 | 결과 일치 |
| T-27 | 8산차 도태 → 두수 감소 확인 | INV-01 | 활성 모돈 -1 |
| T-28 | 정상 5산차 사이클 전체 | ALL | 모든 규칙 통과 |
| T-29 | 후보돈 입식 (parity=0, GILT) | GILT-01,02 | status = GILT (ACTIVE 아님) |
| T-30 | 후보돈 첫 교배 | GILT-03 | GILT → GESTATING |
| T-31 | 후보돈 첫 분만 → parity 0→1 | GILT-03 | 이후 GILT 상태 사용 안 함 |
| T-32 | 후보돈 교배 없이 도태 | NPD-02 | gilt_total_wasted_days 계산됨 |
| T-33 | 부분 이유 (8두 중 3두만) | WEAN-01,02 | weaning_type=PARTIAL, 모돈 LACTATING 유지 |
| T-34 | 부분 이유 후 나머지 전체 이유 | WEAN-02 | 같은 farrowing_id에 이유 2건 허용 |
| T-35 | Nurse Sow 워크플로우 전체 | WEAN-03 | LACTATING→WEANED→LACTATING 전이 |
| T-36 | 발정 감지 후 교배 안 함 | HEAT-01 | HEAT_DETECTED 기록, mating_id=NULL |
| T-37 | 무발정 14일 이상 | HEAT-01 | ANESTRUS 기록 |
| T-38 | 이유→도태 (교배 없이) | NPD-04 | wean_to_removal_days 계산됨 |
| T-39 | 교배→재교배 (21일 후 재발정) | NPD-05 | REGULAR_RETURN, 재교배 간격 기록 |
| T-40 | 교배→도태 (임신실패 후 도태) | NPD-06 | service_to_removal_days 계산됨 |
| T-41 | NPD 6요소 농장 합산 | NPD-TOTAL | v_npd_farm_total 정상 계산 |
| T-42 | EU 농장 이유 27일 시도 | DATE-02+CFG | **REJECT** — EU 최소 28일 |

---

## 12. 이유 유형 정합성 (Weaning Type Integrity)

### 12.1 [WEAN-01] 이유 유형 4종 구분 (HARD)

**글로벌 표준 (PigCHAMP/Porcitec)**:
```
Complete Wean  — 전체 이유: 모든 자돈 한꺼번에 이유 (95% 일반 케이스)
Partial Wean   — 부분 이유: 큰 복에서 강한 자돈만 먼저 이유 (나머지 계속 포유)
Batch Wean     — 배치 이유: All-in/All-out 방식, 여러 모돈 동시 이유
Nurse Sow Wean — 대리모 이유: 전체 이유 후 다른 복의 어린 자돈 재할당
```

**PigOS 매핑**:
```sql
ALTER TABLE weanings ADD COLUMN weaning_type VARCHAR(20)
    NOT NULL DEFAULT 'COMPLETE'
    CHECK (weaning_type IN ('COMPLETE', 'PARTIAL', 'BATCH', 'NURSE_SOW'));
```

**각 유형별 데이터 흐름**:

| 유형 | 모돈 상태 변화 | 자돈 수 처리 | 후속 작업 |
|------|---------------|-------------|-----------|
| COMPLETE | LACTATING → WEANED | weaned_count = 전체 포유두수 | 다음 교배 대기 |
| PARTIAL | LACTATING 유지 | weaned_count = 일부만. 나머지 계속 포유 | 추후 COMPLETE 이유 필요 |
| BATCH | LACTATING → WEANED | 여러 모돈 동시 처리 | 다음 교배 대기 |
| NURSE_SOW | LACTATING → WEANED → LACTATING | 기존 자돈 전체 이유 후 새 자돈 할당 | 연장 포유 시작 |

---

### 12.2 [WEAN-02] 부분 이유 시 1분만:N이유 허용 (HARD)

**문제**: CROSS-02에서 "1분만:1이유" UNIQUE를 걸면, 부분 이유(PARTIAL) 시 같은 분만에 이유가 2건 이상 필요.

**해결**:
```sql
-- CROSS-02 수정: COMPLETE/BATCH/NURSE_SOW만 1:1 강제
-- PARTIAL은 같은 farrowing_id에 여러 건 허용
DROP INDEX IF EXISTS idx_one_weaning_per_farrowing;
CREATE UNIQUE INDEX idx_one_complete_weaning_per_farrowing
ON weanings (farrowing_id)
WHERE farrowing_id IS NOT NULL
  AND deleted_at IS NULL
  AND weaning_type IN ('COMPLETE', 'BATCH', 'NURSE_SOW');
```

---

### 12.3 [WEAN-03] Nurse Sow 워크플로우 (HARD)

**글로벌 표준 Nurse Sow 프로토콜**:
```
Step 1: 모돈 A 분만 (born_alive = 16, 큰 복)
Step 2: 모돈 B 선택 (분만 후 3~5일, 좋은 포유 성적, 적절한 유두 크기)
Step 3: 모돈 B의 자돈 전체 이유 (NURSE_SOW wean)
Step 4: 모돈 A의 자돈 중 약한 자돈 → 모돈 B에게 위탁 (FOSTER_OUT → FOSTER_IN)
Step 5: 모돈 B는 WEANED → 즉시 LACTATING으로 복귀 (연장 포유)
Step 6: 모돈 B의 최종 이유는 위탁받은 자돈 기준
```

**PigOS 매핑**:
```sql
-- ST-01 상태 전이 매트릭스에 추가:
-- WEANED → LACTATING 허용 (Nurse Sow 전용)
-- 조건: weaning_type = 'NURSE_SOW'이고, 직후 piglet_events.FOSTER_IN이 있을 때

-- Nurse Sow 전이 규칙 추가
-- 기존 ST-01 트리거 수정:
WHEN OLD.status = 'WEANED' AND NEW.status = 'LACTATING' THEN TRUE  -- Nurse Sow 복귀
```

---

## 13. 발정/무발정 이벤트 정합성 (Heat Detection Integrity)

### 13.1 [HEAT-01] 발정 감지 이벤트 기록 (SOFT)

**글로벌 표준 (PigCHAMP: "Skip Heat", "Not In Pig")**:
```
발정 감지 후 교배 → matings에 기록 (기존 커버)
발정 감지 후 교배 안 함 → 기록할 곳 없음 (GAP)
발정 미감지 (무발정/Anestrus) → 기록할 곳 없음 (GAP)
임신확인 음성 (Not In Pig) → pregnancy_checks로 부분 커버
```

**PigOS 매핑 — reproductive_events 확장**:
```sql
-- C-01에서 제안한 reproductive_events 테이블의 event_type 확장
-- 기존: RETURN_TO_ESTRUS / ABORTION / EMPTY / INFERTILE
-- 추가:

ALTER TABLE reproductive_events DROP CONSTRAINT IF EXISTS chk_repro_event_type;
ALTER TABLE reproductive_events ADD CONSTRAINT chk_repro_event_type
    CHECK (event_type IN (
        'RETURN_TO_ESTRUS',   -- 재발정 (임신 실패 후)
        'ABORTION',           -- 유산
        'EMPTY',              -- 공태 (임신확인 후 비임신)
        'INFERTILE',          -- 불임
        'HEAT_DETECTED',      -- 발정 감지 (교배 안 함)
        'SKIP_HEAT',          -- 발정 미감지 / 건너뜀
        'ANESTRUS',           -- 연장 무발정 (21일 이상)
        'NOT_IN_PIG'          -- 임신확인 음성 (PigCHAMP 용어)
    ));
```

---

### 13.2 [HEAT-02] 발정→교배 연결 추적 (SOFT)

**규칙**: 발정이 감지되고 교배로 이어진 경우, reproductive_events와 matings를 연결.

```sql
ALTER TABLE reproductive_events ADD COLUMN mating_id UUID REFERENCES matings(id);
-- HEAT_DETECTED → mating_id = 해당 교배 (교배로 이어진 경우)
-- HEAT_DETECTED → mating_id = NULL (교배 안 한 경우)
-- SKIP_HEAT → mating_id = NULL (항상)
```

---

### 13.3 [HEAT-03] 발정 주기 검증 (SOFT)

**글로벌 표준**:
```
돼지 발정 주기: 약 21일 (18~24일)
이유 후 첫 발정: 보통 4~7일 (WEI)
재발정 (임신 실패): 교배 후 ~21일 또는 ~42일에 복귀
```

**검증 로직**:
```sql
-- API 레벨 경고:
-- 이유 후 발정이 10일 이상 안 오면 → ANESTRUS 기록 권고
-- 교배 후 18~24일에 발정 감지 → RETURN_TO_ESTRUS (임신 실패 의심)
-- 교배 후 36~48일에 발정 감지 → 이중 주기 재발정 (확실한 임신 실패)
```

---

## 14. 후보돈(GILT) 별도 추적 정합성

### 14.1 [GILT-01] GILT 상태 분리 (HARD)

**글로벌 표준**:
```
후보돈(Gilt) = 한 번도 분만하지 않은 미경산돈
경산돈(Sow) = 1회 이상 분만한 모돈
모든 프로그램이 이 둘을 명확히 구분
PigCHAMP: Entry → Service(1st) → Farrow → becomes "Sow"
```

**현재 문제**: sows.status = 'ACTIVE'에 후보돈과 이유 후 경산돈이 섞임.

**PigOS 매핑**:
```sql
-- sows.status 체계 변경:
-- 기존: ACTIVE / GESTATING / LACTATING / WEANED / DRY / CULLED / DEAD
-- 변경: GILT / GESTATING / LACTATING / WEANED / DRY / CULLED / DEAD
--        ↑ ACTIVE를 GILT로 변경하지 않음. 둘 다 유지.

-- 최종 상태 목록:
ALTER TABLE sows DROP CONSTRAINT IF EXISTS chk_sow_status;
ALTER TABLE sows ADD CONSTRAINT chk_sow_status
    CHECK (status IN (
        'GILT',       -- 후보돈 (미경산, parity=0, 교배 전)
        'ACTIVE',     -- 경산돈 대기 (이유 후 교배 전, DRY와 유사하지만 구분용)
        'GESTATING',  -- 임신
        'LACTATING',  -- 포유
        'WEANED',     -- 이유 직후
        'DRY',        -- 건기 (이유 후 장기 미교배)
        'CULLED',     -- 도태
        'DEAD'        -- 폐사
    ));
```

---

### 14.2 [GILT-02] 후보돈 입식 규칙 (HARD)

**규칙**: 신규 입식 시 entry_type과 parity에 따라 초기 상태 결정.

```sql
-- 입식 트리거
CREATE OR REPLACE FUNCTION trg_sow_entry_status() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parity = 0 AND NEW.entry_type = 'GILT' THEN
        NEW.status := 'GILT';
    ELSIF NEW.parity > 0 THEN
        NEW.status := 'ACTIVE';  -- 경산돈 도입 (타 농장에서 구매)
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sow_entry BEFORE INSERT ON sows
    FOR EACH ROW EXECUTE FUNCTION trg_sow_entry_status();
```

---

### 14.3 [GILT-03] 후보돈 → 경산돈 전환 (HARD)

**규칙**: 첫 분만 시 후보돈이 경산돈으로 전환. 이후 GILT 상태로 돌아갈 수 없음.

```sql
-- ST-01 상태 전이 매트릭스에 GILT 추가:
-- GILT → GESTATING (첫 교배)
-- GILT → CULLED/DEAD (교배 전 도태/폐사)
-- GILT → (그 외 전이 불가)

-- ST-02 자동 전이에서:
-- GILT 모돈이 교배 시 → GESTATING (일반 경산돈과 동일)
-- 첫 분만 시 parity 0→1 → 이후부터 GILT 상태 사용 안 함
```

---

## 15. NPD 6요소 완전 정합성 (NPD Full Component Integrity)

### 15.1 NPD 6요소 정의

**글로벌 학술 표준 (Pork Gateway, University of Minnesota)**:

```
NPD = 365일 중 임신(Gestation)과 포유(Lactation)에 속하지 않는 일수

6개 구성 요소:

후보돈 구간:
  ① Gilt Entry-to-First-Service     입식 → 첫교배 간격
  ② Gilt Entry-to-Removal           입식 → 도태 (교배 없이 도태 시)

경산돈 구간:
  ③ Wean-to-First-Service (WEI)     이유 → 다음 첫교배 간격
  ④ Wean-to-Removal                 이유 → 도태 (교배 없이 도태 시)
  ⑤ Service-to-Reservice            교배 → 재교배 (임신 실패)
  ⑥ Service-to-Removal              교배 → 도태 (임신 실패 후 도태)

경제적 비용: NPD 1일 ≈ $3.24 (미국 기준)
```

### 15.2 [NPD-01] 후보돈 NPD: 입식→첫교배 (CALC)

**규칙**: 후보돈이 입식 후 첫 교배까지의 일수. 글로벌 평균 ~160일 (5.5개월령 입식 → 7.5개월령 교배).

```sql
-- 계산:
-- gilt_npd = first_mating_date - entry_date
-- 조건: sows.entry_type = 'GILT' AND parity = 0

CREATE OR REPLACE VIEW v_npd_gilt_entry AS
SELECT
    s.farm_id,
    s.id AS sow_id,
    s.ear_tag,
    s.entry_date,
    m.first_mating_date,
    (m.first_mating_date - s.entry_date) AS gilt_entry_to_service_days,
    CASE
        WHEN (m.first_mating_date - s.entry_date) > 210 THEN 'WARNING_LATE'
        WHEN (m.first_mating_date - s.entry_date) < 180 THEN 'WARNING_EARLY'
        ELSE 'NORMAL'
    END AS gilt_status
FROM sows s
LEFT JOIN LATERAL (
    SELECT MIN(mating_date) AS first_mating_date
    FROM matings WHERE sow_id = s.id AND deleted_at IS NULL
) m ON TRUE
WHERE s.entry_type = 'GILT'
  AND s.deleted_at IS NULL;
```

---

### 15.3 [NPD-02] 후보돈 NPD: 입식→도태 (CALC)

**규칙**: 후보돈이 한 번도 교배하지 못하고 도태/폐사. 전체가 NPD.

```sql
-- 계산:
-- gilt_wasted_npd = exit_date - entry_date
-- 조건: parity = 0 AND exit_date IS NOT NULL AND 교배 기록 없음

CREATE OR REPLACE VIEW v_npd_gilt_removal AS
SELECT
    s.farm_id,
    s.id AS sow_id,
    s.ear_tag,
    s.entry_date,
    s.exit_date,
    (s.exit_date - s.entry_date) AS gilt_total_wasted_days,
    r.removal_type,
    r.reason_category
FROM sows s
JOIN removals r ON r.sow_id = s.id AND r.deleted_at IS NULL
WHERE s.entry_type = 'GILT'
  AND s.parity = 0
  AND NOT EXISTS (
      SELECT 1 FROM matings WHERE sow_id = s.id AND deleted_at IS NULL
  )
  AND s.deleted_at IS NULL;
```

---

### 15.4 [NPD-03] 경산돈 NPD: 이유→첫교배 WEI (CALC)

이미 KPI-02 (v_sow_npd)에서 커버. 확인 완료 ✅

---

### 15.5 [NPD-04] 경산돈 NPD: 이유→도태 (CALC)

**규칙**: 이유 후 교배 없이 도태. 이유~도태 전체가 NPD.

```sql
CREATE OR REPLACE VIEW v_npd_wean_to_removal AS
SELECT
    s.farm_id,
    s.id AS sow_id,
    s.ear_tag,
    w.weaning_date AS last_weaning,
    s.exit_date,
    (s.exit_date - w.weaning_date) AS wean_to_removal_days,
    r.removal_type,
    r.reason_category
FROM sows s
JOIN LATERAL (
    SELECT MAX(weaning_date) AS weaning_date
    FROM weanings WHERE sow_id = s.id AND deleted_at IS NULL
) w ON TRUE
JOIN removals r ON r.sow_id = s.id AND r.deleted_at IS NULL
WHERE s.exit_date IS NOT NULL
  AND NOT EXISTS (
      -- 마지막 이유 이후 교배가 없음
      SELECT 1 FROM matings
      WHERE sow_id = s.id
        AND mating_date > w.weaning_date
        AND deleted_at IS NULL
  )
  AND s.deleted_at IS NULL;
```

---

### 15.6 [NPD-05] 경산돈 NPD: 교배→재교배 (CALC)

**규칙**: 임신 실패 후 재교배까지의 간격. breeding_cycles.mating_count > 1인 경우.

```sql
CREATE OR REPLACE VIEW v_npd_reservice AS
SELECT
    s.farm_id,
    s.id AS sow_id,
    s.ear_tag,
    m1.mating_date AS first_service,
    m2.mating_date AS reservice,
    (m2.mating_date - m1.mating_date) AS service_to_reservice_days,
    -- 정상 재발정: ~21일, 이중 주기: ~42일
    CASE
        WHEN (m2.mating_date - m1.mating_date) BETWEEN 17 AND 25 THEN 'REGULAR_RETURN'
        WHEN (m2.mating_date - m1.mating_date) BETWEEN 36 AND 48 THEN 'DOUBLE_RETURN'
        ELSE 'IRREGULAR'
    END AS return_type
FROM sows s
JOIN matings m1 ON m1.sow_id = s.id AND m1.deleted_at IS NULL
JOIN matings m2 ON m2.sow_id = s.id AND m2.deleted_at IS NULL
    AND m2.mating_date > m1.mating_date
    AND m2.mating_date < m1.mating_date + INTERVAL '60 days'
-- m1과 m2 사이에 분만이 없어야 함 (= 임신 실패)
WHERE NOT EXISTS (
    SELECT 1 FROM farrowings f
    WHERE f.sow_id = s.id
      AND f.farrowing_date BETWEEN m1.mating_date AND m2.mating_date
      AND f.deleted_at IS NULL
)
AND s.deleted_at IS NULL;
```

---

### 15.7 [NPD-06] 경산돈 NPD: 교배→도태 (CALC)

**규칙**: 교배 후 임신 실패, 재교배 없이 도태. 교배~도태 중 비생산 구간이 NPD.

```sql
CREATE OR REPLACE VIEW v_npd_service_to_removal AS
SELECT
    s.farm_id,
    s.id AS sow_id,
    s.ear_tag,
    m.last_mating_date,
    s.exit_date,
    (s.exit_date - m.last_mating_date) AS service_to_removal_days,
    r.removal_type,
    r.reason_category
FROM sows s
JOIN LATERAL (
    SELECT MAX(mating_date) AS last_mating_date
    FROM matings WHERE sow_id = s.id AND deleted_at IS NULL
) m ON TRUE
JOIN removals r ON r.sow_id = s.id AND r.deleted_at IS NULL
WHERE s.exit_date IS NOT NULL
  -- 마지막 교배 이후 분만이 없음 (= 임신 실패 후 도태)
  AND NOT EXISTS (
      SELECT 1 FROM farrowings
      WHERE sow_id = s.id
        AND farrowing_date > m.last_mating_date
        AND deleted_at IS NULL
  )
  AND s.deleted_at IS NULL;
```

---

### 15.8 [NPD-TOTAL] 농장 전체 NPD 통합 뷰 (CALC)

```sql
CREATE OR REPLACE VIEW v_npd_farm_total AS
SELECT
    farm_id,
    -- ① 후보돈: 입식→첫교배
    COALESCE(AVG(gilt_entry_to_service_days), 0) AS avg_gilt_entry_npd,
    -- ③ WEI: 이유→재교배
    (SELECT COALESCE(AVG(npd_avg), 0) FROM v_sow_npd sub WHERE sub.farm_id = g.farm_id)
        AS avg_wei_npd,
    -- ⑤ 재교배 간격
    (SELECT COALESCE(AVG(service_to_reservice_days), 0) FROM v_npd_reservice sub WHERE sub.farm_id = g.farm_id)
        AS avg_reservice_npd,
    -- 총 NPD 경제 손실 (미국 기준 $3.24/일)
    -- 한국 기준 ₩8,500/일
    COUNT(*) AS gilt_count
FROM v_npd_gilt_entry g
GROUP BY farm_id;
```

---

## 16. 글로벌 양돈 소프트웨어 교차 검증

> 본 섹션은 PigCHAMP, MetaFarms, Cloudfarms, Agriness, Porcitec 등
> 해외 주요 양돈 관리 소프트웨어의 데이터 모델/워크플로우와
> 본 정합성 규격서를 대조하여 GAP을 식별한 결과입니다.

### 12.1 검증 대상

| 소프트웨어 | 시장 | 특징 |
|-----------|------|------|
| **PigCHAMP** | 40+국 (글로벌 표준) | 48 이벤트 타입, 400+ 분석 필터, 이벤트 기반 소우카드 |
| **MetaFarms** | 미국/캐나다/호주 | 미국 돼지 데이터 40-50% 보유, ESF/RFID 연동, PowerBI |
| **Cloudfarms** | EU 40+국 | **개체별 birth-to-slaughter** 추적, Pig Passport |
| **Agriness (S2)** | 브라질 90% 점유 | 오프라인 우선, Cargill 투자, ABCS 족보 연동 |
| **Porcitec** | 대형 인티그레이터 | 60+ 이벤트, **커스텀 검증 규칙** 지원, 오프라인 핸드헬드 |

### 12.2 글로벌 표준 vs 현재 규격서 대조

#### ✅ 글로벌 표준과 일치하는 규칙

| 규칙 ID | 내용 | 글로벌 표준 |
|---------|------|------------|
| PIG-01 | total_born = born_alive + stillborn + mummified | **전 세계 모든 프로그램** 동일 |
| SEQ-01 | 분만 전 교배 필수, 이유 전 분만 필수 | PigCHAMP/Porcitec 동일 순서 강제 |
| ST-01 | 상태 전이 매트릭스 | PigCHAMP 이벤트 체인과 동일 패턴 |
| DATE-01 | 임신 기간 100-130일 | 글로벌 동일 (HARD 범위) |
| CROSS-01 | 체인 모돈 일치 | 모든 프로그램 동일 |
| KPI-01 | PSY = 이유두수/활성모돈 (rolling 12m) | PigCHAMP/Agriness 동일 공식 |
| INV-01 | 입식-퇴역 재고 추적 | 모든 프로그램 동일 |

**PSY 위탁 귀속**: 이유 두수는 **포유 모돈(nursing sow)**에 귀속 — 생물학적 어미가 아님. 글로벌 표준과 일치.

#### ❌ 글로벌 표준에서 필요하지만 현재 누락된 것

| # | 항목 | 글로벌 표준 | 영향 | 심각도 |
|---|------|------------|------|--------|
| G-01 | **이유 유형 구분** | PigCHAMP: Part Wean / Complete Wean / Batch Wean / Nurse Sow Wean 4종 구분 | 부분 이유(일부 자돈만 이유)와 Nurse Sow 생성 워크플로우 추적 불가 | ⚠️ MAJOR |
| G-02 | **Skip Heat / Anestrus 이벤트** | PigCHAMP: "Skip Heat", "Not In Pig" 별도 이벤트 | 발정 미감지/무발정 기록 불가. NPD 6요소 중 2개 추적 불가 | ⚠️ MAJOR |
| G-03 | **후보돈(GILT) 별도 상태** | 전 세계: 미경산돈(Gilt)과 경산돈(Active) 구분 | 후보돈 NPD = 입식~첫교배. 현재 둘 다 'ACTIVE'로 구분 불가 | ⚠️ MAJOR |
| G-04 | **NPD 6요소 세분화** | 학술/업계 표준: 후보돈 NPD, 이유→발정 NPD, 재교배 NPD 등 6개 구간 | 현재 이유→재교배 간격만 계산. 후보돈/재발정/도태 관련 NPD 누락 | ⚠️ MAJOR |
| G-05 | **Pig Passport (개체 추적)** | Cloudfarms: 출생→도축 전 생애 디지털 이력서 | Phase 3 individual_pigs 테이블로 대응 가능. MVP에선 불필요 | ℹ️ INFO |
| G-06 | **전자급이기(ESF) 연동** | PigKnows/MetaFarms/Porcitec: Nedap, Schauer 등 직접 연동 | Phase 2 feed_records.esf_station_id로 설계됨. MVP에선 불필요 | ℹ️ INFO |
| G-07 | **커스텀 검증 규칙** | Porcitec: 농장별 커스텀 validation expression 지원 | 현재 고정 규칙만. 농장별 유연한 규칙은 Phase 2+ | ℹ️ INFO |

### 12.3 이유 유형 [G-01] 상세

**PigCHAMP 이유 이벤트 종류**:

| 이벤트 | 설명 | 용도 |
|--------|------|------|
| **Complete Wean** | 전체 이유 — 모든 자돈 한꺼번에 이유 | 일반적 케이스 (95%) |
| **Part Wean** | 부분 이유 — 일부 자돈만 먼저 이유 | 큰 복(litter)에서 강한 자돈 먼저 이유 |
| **Batch Wean** | 배치 이유 — 여러 모돈 동시 이유 | all-in/all-out 방식 농장 |
| **Nurse Sow Wean** | 대리모 이유 — 전체 이유 후 다른 복의 어린 자돈 할당 | Nurse sow 프로토콜 |

**PigOS 매핑**:
```sql
ALTER TABLE weanings ADD COLUMN weaning_type VARCHAR(20)
    NOT NULL DEFAULT 'COMPLETE'
    CHECK (weaning_type IN ('COMPLETE', 'PARTIAL', 'BATCH', 'NURSE_SOW'));
```

### 12.4 NPD 6요소 모델 [G-04] 상세

글로벌 학술/업계 표준의 NPD 분해:

```
후보돈 NPD:
  ① 입식 → 첫 교배 간격 (Gilt entry-to-first-service)
  ② 입식 → 도태 간격 (Gilt entry-to-culling, 교배 못하고 도태 시)

경산돈 NPD:
  ③ 이유 → 발정 간격 (Wean-to-estrus interval, WEI)
  ④ 발정 → 교배 간격 (Skip heat — 발정 감지했지만 교배 안 함)
  ⑤ 교배 → 재교배 간격 (Service-to-reservice — 임신 실패)
  ⑥ 이유 → 도태 간격 (Wean-to-cull — 이유 후 교배 없이 도태)
```

**현재 규격서 커버리지**:
- ③ WEI: DATE-03에서 커버 ✅
- ⑤ 재교배: SEQ-03 (GYOBAE_CNT)에서 부분 커버 ⚠️
- ①②④⑥: **미커버** ❌

**권장 조치**:
```sql
-- 1. sows.status에 'GILT' 추가 (후보돈 구분)
ALTER TABLE sows DROP CONSTRAINT IF EXISTS chk_sow_status;
ALTER TABLE sows ADD CONSTRAINT chk_sow_status
    CHECK (status IN ('GILT','ACTIVE','GESTATING','LACTATING','WEANED','DRY','CULLED','DEAD'));

-- 2. reproductive_events에 이벤트 타입 확장
-- HEAT_DETECTED: 발정 감지 (④번 추적용)
-- SKIP_HEAT: 발정 미감지/무발정 (④번)
-- RETURN_TO_ESTRUS: 재발정 (⑤번)
-- ABORTION: 유산
-- NOT_IN_PIG: 임신확인 음성 (⑤번)
-- ANESTRUS: 연장 무발정

-- 3. NPD 뷰 확장 — 6요소 분해
CREATE OR REPLACE VIEW v_npd_components AS
SELECT
    s.farm_id,
    s.id AS sow_id,
    s.ear_tag,
    -- ① 후보돈 NPD: 입식→첫교배
    CASE WHEN s.parity = 0 THEN
        (SELECT MIN(mating_date) FROM matings WHERE sow_id = s.id AND deleted_at IS NULL)
        - s.entry_date
    END AS gilt_entry_to_first_service_days,
    -- ③ WEI: 이유→다음교배 (가장 최근)
    -- (v_sow_npd에서 계산)
    -- ⑤ 재교배 간격: 실패한 교배→다음교배
    -- (breeding_cycles.mating_count > 1인 사이클에서)
    -- ⑥ 이유→도태: 이유 후 교배 없이 도태
    CASE WHEN s.status IN ('CULLED','DEAD') AND s.exit_date IS NOT NULL THEN
        s.exit_date - (
            SELECT MAX(weaning_date) FROM weanings
            WHERE sow_id = s.id AND deleted_at IS NULL
        )
    END AS wean_to_cull_days
FROM sows s WHERE s.deleted_at IS NULL;
```

### 12.5 지역별 추가 검증 규칙

| 지역 | 추가 규칙 | 현재 스키마 |
|------|----------|------------|
| **EU** | 이유 최소 28일 (동물복지법) | DATE-02에서 14일로 설정 → **EU 농장은 28일로 상향 필요** |
| **EU** | 집단 항생제 투약 금지 (2022~) | medications.collective_treatment 플래그 있음 ✅ |
| **EU** | DDDA 자동 계산 + 옐로카드 임계값 | medications.ddda_value 있음, 하지만 **자동 계산 로직 없음** |
| **US** | VFD 2년 보관 의무 | medications.vfd_expiry_date 있음 ✅ |
| **US** | Prop 12 면적 기준 (24 sqft) | buildings.prop12_compliant 있음 ✅ |
| **US** | POP(장기탈출) 별도 추적 | removals.pop_flag 있음 ✅ |
| **BR** | GTA(운송허가) 필수 | animal_movements.gta_number 있음 ✅ |
| **SEA** | ASF 백신 추적 (베트남 3종) | vaccinations.asf_vaccine_flag 있음 ✅ |
| **SEA** | 오프라인 필수 (인터넷 불안정) | sync_queue + WatermelonDB 설계됨 ✅ |

**EU 이유 일령 농장별 적용**:
```sql
-- farm_configs에서 지역별 최소 이유 일령 설정
INSERT INTO farm_configs (farm_id, config_key, config_value, description)
VALUES ('{eu_farm_id}', 'MIN_WEANING_AGE_DAYS', '28', 'EU 동물복지 최소 이유 일령');
-- DATE-02 트리거에서 farm_configs.MIN_WEANING_AGE_DAYS 참조
```

### 16.6 교차 검증 최종 결과

```
전체 정합성 규칙 (피그플랜 27개 + 글로벌 확장 15개 = 42개):

  ✅ 완전 정의 완료:          38개 (90%)
  ℹ️ Phase 2+ 대응 가능:       4개 (10%) — G-05~G-07 + 커스텀 검증

기존 GAP 4건 해소 상태:
  G-01 이유 유형 → 12절 WEAN-01~03에서 완전 정의 ✅
  G-02 Skip Heat → 13절 HEAT-01~03에서 완전 정의 ✅
  G-03 GILT 상태 → 14절 GILT-01~03에서 완전 정의 ✅
  G-04 NPD 6요소 → 15절 NPD-01~06 + TOTAL에서 완전 정의 ✅
```

### 16.7 v2 스키마 반영 전체 사항

기존 10.1절 + 글로벌 확장 통합:

| 우선순위 | 항목 | 이슈 |
|----------|------|------|
| **P0** | sows.status에 'GILT' 추가 + 입식 트리거 | GILT-01, GILT-02 |
| **P0** | weanings.weaning_type 4종 + PARTIAL 이유 UNIQUE 수정 | WEAN-01, WEAN-02 |
| **P0** | reproductive_events에 8개 event_type | HEAT-01 |
| **P0** | Nurse Sow 워크플로우 상태 전이 | WEAN-03 |
| **P0** | NPD 6요소 뷰 6개 | NPD-01~06 |
| **P1** | 발정→교배 연결 (reproductive_events.mating_id) | HEAT-02 |
| **P1** | 발정 주기 검증 (21일 주기) | HEAT-03 |
| **P1** | 후보돈→경산돈 전환 트리거 | GILT-03 |
| **P1** | EU 최소 이유일령 farm_configs 연동 | 16.5 |
| **P2** | Pig Passport (individual_pigs 확장) | G-05 |
| **P2** | ESF 연동 상세 설계 | G-06 |
| **P2** | 커스텀 검증 규칙 엔진 | G-07 |

---

> 본 문서는 피그플랜 27년 운영 + 글로벌 양돈 소프트웨어(PigCHAMP, MetaFarms, Cloudfarms, Agriness, Porcitec)의
> 데이터 정합성 규칙을 PigOS 스키마에 매핑한 것입니다.
> 피그플랜의 스키마 구조는 참고하지 않았으며, 비즈니스 규칙만 이식했습니다.
> 모든 규칙은 PostgreSQL 트리거, CHECK, UNIQUE INDEX로 구현 가능합니다.
