# PigPlan Oracle → PigOS PostgreSQL 임포트 가이드

> 목적: 피그플랜 실제 데이터로 KPI 계산 정합성 검증

---

## 1. Oracle에서 추출할 테이블

| Oracle 테이블 | PigOS 테이블 | 설명 |
|--------------|-------------|------|
| TB_MODON | sows | 모돈 마스터 |
| TB_GYOBAE | matings | 교배 이력 |
| TB_BUNMAN | farrowings | 분만 이력 |
| TB_EU | weanings | 이유 이력 |
| TB_SAGO | reproductive_events | 재발정/유산 |
| TB_MODON_JADON_TRANS | piglet_events | 포유중 자돈 이동/폐사 |

---

## 2. Oracle 추출 SQL (샘플)

```sql
-- Oracle에서 실행: 검증용 모돈 10두 + 관련 이력 추출

-- 모돈 (최근 3산차 이상, 정상 이력 있는 것)
SELECT
    MODON_NO          AS ear_tag,
    BREED_CD          AS breed,
    SANCHA            AS parity,
    MODONGB_CD        AS status_code,  -- 01=임신, 02=포유, 03=이유, 09=도태
    IN_DT             AS entry_date,
    OUT_DT            AS exit_date_raw
FROM TB_MODON
WHERE FARM_CD = :farm_code
  AND SANCHA >= 2
  AND IN_DT >= '20240101'
  AND ROWNUM <= 10;

-- 교배 이력
SELECT
    MODON_NO, GYOBAE_DT AS mating_date,
    GYOBAE_GUBUN_CD AS mating_type,  -- 01=AI, 02=자연교배
    GYOBAE_CNT AS mating_number,
    SANCHA AS parity
FROM TB_GYOBAE
WHERE MODON_NO IN (:modon_list);

-- 분만 이력
SELECT
    MODON_NO, BUNMAN_DT AS farrowing_date,
    SANCHA AS parity,
    TOTAL_BORN, BORN_ALIVE, STILLBORN, MUMMIFIED
FROM TB_BUNMAN
WHERE MODON_NO IN (:modon_list);

-- 이유 이력
SELECT
    MODON_NO, EU_DT AS weaning_date,
    WEANED_COUNT, WEANING_AGE
FROM TB_EU
WHERE MODON_NO IN (:modon_list);

-- 재발정/유산
SELECT
    MODON_NO, SAGO_DT AS event_date,
    SAGO_GUBUN_CD AS event_type_code
    -- 050001=재발정, 050002=유산, 050003=공태 ...
FROM TB_SAGO
WHERE MODON_NO IN (:modon_list);
```

---

## 3. CSV → PostgreSQL 임포트

Oracle에서 CSV로 내보낸 후 `tests/db/pigplan_data/` 에 저장:

```
pigplan_data/
├── sows.csv
├── matings.csv
├── farrowings.csv
├── weanings.csv
└── reproductive_events.csv
```

임포트 SQL (`pigplan_data/import.sql`):

```sql
-- 테스트 농장 생성 (피그플랜 데이터용)
INSERT INTO organizations (id, name, country_code)
VALUES ('AAAAAAAA-0000-0000-0000-000000000001', '피그플랜테스트', 'KR')
ON CONFLICT DO NOTHING;

INSERT INTO farms (id, organization_id, farm_name, country_code, region_code, farm_type, sow_count)
VALUES ('AAAAAAAA-0000-0000-0000-000000000010',
        'AAAAAAAA-0000-0000-0000-000000000001',
        '피그플랜 샘플농장', 'KR', 'KR', 'INTEGRATED', 300)
ON CONFLICT DO NOTHING;

-- 임시 스테이징 테이블
CREATE TEMP TABLE stg_sows (
    ear_tag       VARCHAR(30),
    breed         VARCHAR(20),
    parity        INT,
    status_code   VARCHAR(10),
    entry_date    DATE,
    exit_date_raw VARCHAR(10)  -- '99991231' = 현재 활성
);

\COPY stg_sows FROM '/pigplan_data/sows.csv' CSV HEADER;

-- 상태 코드 변환 후 sows에 삽입
INSERT INTO sows (id, farm_id, ear_tag, breed, parity, status, entry_date, exit_date, entry_type)
SELECT
    gen_random_uuid(),
    'AAAAAAAA-0000-0000-0000-000000000010',
    ear_tag,
    breed,
    parity,
    CASE status_code
        WHEN '01' THEN 'GESTATING'
        WHEN '02' THEN 'LACTATING'
        WHEN '03' THEN 'WEANED'
        WHEN '09' THEN 'CULLED'
        ELSE 'ACTIVE'
    END,
    entry_date,
    CASE WHEN exit_date_raw = '99991231' THEN NULL
         ELSE TO_DATE(exit_date_raw, 'YYYYMMDD')
    END,
    'PURCHASE'
FROM stg_sows;
```

---

## 4. 검증 쿼리 (임포트 후 실행)

```sql
-- PSY 계산 (피그플랜 수치와 대조)
SELECT * FROM v_farm_psy
WHERE farm_id = 'AAAAAAAA-0000-0000-0000-000000000010';

-- NPD 계산
SELECT s.ear_tag, n.wei_days
FROM v_sow_npd n
JOIN sows s ON s.id = n.sow_id
WHERE s.farm_id = 'AAAAAAAA-0000-0000-0000-000000000010'
ORDER BY n.weaning_date DESC
LIMIT 20;

-- 두수 정합성 (이유두수 = born_alive + foster_in - foster_out - deaths)
SELECT * FROM fn_verify_piglet_count(
    (SELECT id FROM farrowings
     WHERE farm_id = 'AAAAAAAA-0000-0000-0000-000000000010'
     LIMIT 1)
);
```
