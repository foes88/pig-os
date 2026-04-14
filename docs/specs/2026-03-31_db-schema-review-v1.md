# PigOS — DB Schema v1.0 검증 리포트

> 작성일: 2026-03-31
> 대상: `docs/specs/2026-03-19_db-schema-v1.sql` (49 tables + 2 views)
> 검증 기준: 피그플랜 27년 운영 데이터 모델 (Oracle) + 양돈 생산 주기 도메인 지식

---

## 1. 검증 개요

### 1.1 검증 목적
PigOS의 DB 스키마가 실제 양돈 생산 주기(번식 사이클)를 정확하게 표현할 수 있는지,
기존 피그플랜의 운영 검증된 데이터 모델과 대조하여 구조적 결함을 사전 식별한다.

### 1.2 검증 범위
- 테이블 관계 및 FK 정합성
- 번식 사이클 워크플로우 커버리지
- 산차(Parity) 추적 체계
- 두수(Head Count) 추적 정확성
- 작업 전후관계(Sequence) 보장
- 글로벌 운영 적합성 (6개 권역)
- 모듈화 / 독립 배포 가능성
- 제약조건 (CHECK, NOT NULL, UNIQUE)
- 인덱스 전략
- 뷰 로직 정합성

### 1.3 검증 기준 (피그플랜 레거시 모델)

| 테이블 | 역할 | 레코드 수 |
|--------|------|-----------|
| TB_MODON | 모돈 마스터 | 3.32M (일 562건 증가) |
| TB_MODON_WK | 작업 이력 (모든 이벤트 중심) | 40.5M (일 6,198건) |
| TB_GYOBAE | 교배 상세 | 14.9M |
| TB_BUNMAN | 분만 상세 | 11.5M |
| TB_EU | 이유 상세 | 11.4M |
| TB_SAGO | 사고 (재발정/유산) | 2.7M |
| TB_MODON_JADON_TRANS | 포유중 자돈 이동/폐사 | 10.0M |

---

## 2. 심각도 분류

| 등급 | 의미 | 기준 |
|------|------|------|
| **CRITICAL** | 데이터 무결성 파괴 가능 | 잘못된 데이터 입력이 방지 안 됨, 핵심 KPI 계산 오류 |
| **MAJOR** | 운영에 지장, 우회 필요 | 도메인 규칙 누락, 추적 불가능한 이벤트 존재 |
| **MINOR** | 개선 권장 | 성능, 일관성, 유지보수 관련 |
| **INFO** | 참고 사항 | 설계 선택에 대한 코멘트 |

---

## 3. CRITICAL 이슈

### 3.1 [C-01] 재발정/유산(사고) 기록 테이블 없음

**현상**: 피그플랜의 TB_SAGO에 해당하는 테이블이 PigOS에 없음.

**영향**:
- 임신 중 재발정(Return to Estrus), 유산(Abortion), 공태(Empty) 이벤트를 기록할 수 없음
- NPD(비생산일수) 계산 시 사고 기간이 누락됨
- AI Agent의 손실 감지에서 "재발정 모돈 손실" 추적 불가
- pregnancy_checks.result='NEGATIVE'로 간접 추론만 가능 → 재발정과 유산 구분 불가

**피그플랜 참고**:
```
TB_SAGO: SAGO_GUBUN_CD
  050001 = 재발정 (Return to Heat)
  050002 = 유산 (Abortion/Loss)
  050003 = 부임 (Non-conceived)
  050004 = 공태 (Empty after check)
  050005 = 도태 (Culled during pregnancy)
  050006 = 폐사 (Death during pregnancy)
  050007 = 전출 (Transfer out)
  050008 = 판매 (Sold)
  050009 = 불임 (Infertile)
```

**권장 조치**: `reproductive_events` 테이블 신규 추가
```sql
CREATE TABLE reproductive_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    mating_id       UUID REFERENCES matings(id),
    event_date      DATE NOT NULL,
    event_type      VARCHAR(20) NOT NULL,
        -- RETURN_TO_ESTRUS / ABORTION / EMPTY / INFERTILE
    detected_method VARCHAR(20),
        -- ULTRASOUND / VISUAL / BEHAVIOR / BLOOD_TEST
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 3.2 [C-02] 포유중 자돈 이동/폐사 추적 테이블 없음

**현상**: 피그플랜의 TB_MODON_JADON_TRANS에 해당하는 테이블이 없음.

**영향**:
- 분만(born_alive) → 이유(weaned_count) 사이의 자돈 폐사를 일별로 추적 불가
- 위탁(cross-fostering) 이력이 farrowings 테이블의 INT 컬럼(cross_fostered_in/out)으로만 기록
  → "언제, 어떤 모돈에게서, 몇 두를" 추적 불가
- pre-weaning mortality KPI의 사유별 분석 불가능

**피그플랜 참고**:
```
TB_MODON_JADON_TRANS.GUBUN_CD:
  160001 = 생시도태 (Stillborn at birth)
  160002 = 포유중 폐사 (Pre-weaning death)
  160003 = 지입 (Fostering in — 다른 모돈 자돈 받음)
  160004 = 지출 (Fostering out — 내 자돈 다른 모돈에게)
```

**권장 조치**: `piglet_events` 테이블 신규 추가
```sql
CREATE TABLE piglet_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    farrowing_id    UUID NOT NULL REFERENCES farrowings(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    event_date      DATE NOT NULL,
    event_type      VARCHAR(20) NOT NULL,
        -- DEATH / FOSTER_IN / FOSTER_OUT / STILLBORN_REMOVAL
    piglet_count    INT NOT NULL DEFAULT 1,
    reason          VARCHAR(50),
        -- CRUSHING / SCOURS / STARVATION / CONGENITAL / OTHER
    target_sow_id   UUID REFERENCES sows(id),  -- 위탁 대상/원 모돈
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 3.3 [C-03] 산차(Parity) 추적 체계 불완전

**현상**:
- `sows.parity`만 존재하고, 각 이벤트(교배/분만/이유)가 몇 산차인지 기록 안 됨
- `farrowings.parity_at_birth`만 유일하게 산차 정보를 가짐
- `matings`, `weanings`에는 산차 정보 없음

**영향**:
- "이 교배가 3산차 첫 번째 교배인지, 재교배인지" 판단 불가
- 산차별 성적 분석 (산차별 PSY, 산차별 실산수 등) 시 복잡한 역추적 필요
- 피그플랜은 TB_MODON_WK.SANCHA + GYOBAE_CNT로 명확히 추적

**피그플랜 참고**:
```
TB_MODON_WK:
  SANCHA = 현재 산차 (분만 시 +1)
  GYOBAE_CNT = 해당 산차 내 교배 횟수 (재교배 시 +1, 새 산차에서 1로 리셋)
```

**권장 조치**: `breeding_cycles` 테이블 추가로 산차별 사이클 관리
```sql
CREATE TABLE breeding_cycles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    parity          INT NOT NULL,
    cycle_status    VARCHAR(20) NOT NULL DEFAULT 'MATED',
        -- MATED / CONFIRMED / FARROWED / WEANED / FAILED
    started_at      DATE NOT NULL,      -- 첫 교배일
    ended_at        DATE,               -- 이유일 또는 사고일
    mating_count    INT NOT NULL DEFAULT 1,  -- 해당 산차 교배 횟수
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(sow_id, parity)
);
-- matings, farrowings, weanings에 breeding_cycle_id FK 추가
```

---

### 3.4 [C-04] 작업 전후관계(Sequence) 보장 메커니즘 없음

**현상**:
- 피그플랜의 TB_MODON_WK.SEQ에 해당하는 순번 체계가 없음
- 각 이벤트 테이블(matings, farrowings, weanings)이 완전히 독립적
- FK가 대부분 NULLABLE → 교배 없이 분만 기록 가능, 분만 없이 이유 기록 가능

**영향** (실제 발생 가능한 데이터 오류):
```
시나리오 1: farrowings INSERT 시 mating_id = NULL
  → 교배 기록 없이 분만만 기록됨
  → 임신 기간 계산 불가, PSY 계산 왜곡

시나리오 2: weanings INSERT 시 farrowing_id = NULL
  → 분만 기록 없이 이유만 기록됨
  → 포유 기간 계산 불가, 자돈 생존율 추적 불가

시나리오 3: 같은 모돈에 분만 2건 연속 (이유 없이)
  → 현재 스키마에서 차단 안 됨
```

**피그플랜 참고**:
```
TB_MODON_WK.SEQ: 순차번호
  - 이전 작업 = SEQ - 1 으로 조회
  - 작업 순서: A → G → (F) → B → E → G → ... → Z
  - 분만(B) 전에 반드시 교배(G)가 있어야 함
  - 이유(E) 전에 반드시 분만(B)이 있어야 함
```

**권장 조치**:
1. `matings.mating_id`를 `farrowings`에서 NOT NULL로 변경 (또는 breeding_cycle_id 필수)
2. `farrowings.id`를 `weanings.farrowing_id`에서 NOT NULL로 변경
3. DB 트리거 또는 API 레벨에서 순서 검증:
```sql
-- 분만 전 교배 존재 확인 트리거 예시
CREATE OR REPLACE FUNCTION validate_farrowing_sequence()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM matings
        WHERE sow_id = NEW.sow_id
        AND mating_date < NEW.farrowing_date
        AND deleted_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Cannot record farrowing without prior mating for sow %', NEW.sow_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

### 3.5 [C-05] CHECK 제약조건 전무

**현상**: 모든 VARCHAR 상태/유형 필드에 유효값이 SQL 주석으로만 정의됨. DB 레벨 검증 없음.

**영향**: 오타, 잘못된 코드, 대소문자 불일치 등이 그대로 저장됨

**대상 필드 (20+ 개)**:

| 테이블 | 컬럼 | 유효값 |
|--------|------|--------|
| sows | status | ACTIVE/GESTATING/LACTATING/WEANED/DRY/CULLED/DEAD |
| sows | entry_type | GILT/PURCHASE/TRANSFER/BORN |
| matings | mating_type | AI/NATURAL |
| pregnancy_checks | result | POSITIVE/NEGATIVE/UNCERTAIN |
| removals | removal_type | CULL/DEAD/SOLD/TRANSFER |
| removals | reason_category | REPRODUCTIVE/LAMENESS/DISEASE/AGE/... |
| health_events | event_type | DISEASE/INJURY/OBSERVATION/DEATH/CULLING |
| health_events | severity | MILD/MODERATE/SEVERE/FATAL |
| buildings | building_type | GESTATION/FARROWING/NURSERY/FINISHER/... |
| (기타 15+ 필드) | ... | ... |

**권장 조치**: 모든 상태/유형 필드에 CHECK 제약조건 추가
```sql
ALTER TABLE sows ADD CONSTRAINT chk_sow_status
    CHECK (status IN ('ACTIVE','GESTATING','LACTATING','WEANED','DRY','CULLED','DEAD'));
ALTER TABLE sows ADD CONSTRAINT chk_sow_entry_type
    CHECK (entry_type IN ('GILT','PURCHASE','TRANSFER','BORN'));
-- ... 나머지 전부
```

---

### 3.6 [C-06] 숫자 범위 제약 없음

**현상**: 두수, 산차, 체중 등 숫자 필드에 음수/비정상 값 차단 없음.

**대상 필드**:

| 테이블.컬럼 | 필요한 제약 |
|-------------|-------------|
| sows.parity | CHECK (parity >= 0 AND parity <= 20) |
| farrowings.total_born | CHECK (total_born >= 0 AND total_born <= 30) |
| farrowings.born_alive | CHECK (born_alive >= 0 AND born_alive <= total_born) |
| farrowings.stillborn | CHECK (stillborn >= 0) |
| farrowings.mummified | CHECK (mummified >= 0) |
| weanings.weaned_count | CHECK (weaned_count >= 0 AND weaned_count <= 25) |
| weanings.weaning_age_days | CHECK (weaning_age_days >= 10 AND weaning_age_days <= 60) |
| matings.mating_number | CHECK (mating_number >= 1 AND mating_number <= 5) |

**비즈니스 룰 제약**:
```sql
-- 실산 = 생존 + 사산 + 미라
ALTER TABLE farrowings ADD CONSTRAINT chk_total_born
    CHECK (total_born = born_alive + stillborn + mummified);
```

---

### 3.7 [C-07] pregnancy_checks에 farm_id 없음

**현상**: 모든 운영 테이블에 farm_id가 있으나, pregnancy_checks만 빠져 있음.

**영향**:
- Schema-per-tenant 환경에서 직접 쿼리 시 farm 필터링 불가
- 다른 테이블과의 일관성 깨짐
- sow_id → sows.farm_id로 JOIN해야 해서 성능 저하

**권장 조치**:
```sql
ALTER TABLE pregnancy_checks ADD COLUMN farm_id UUID NOT NULL REFERENCES farms(id);
```

---

## 4. MAJOR 이슈

### 4.1 [M-01] 모돈 상태 전이 규칙 없음

**현상**: sows.status를 아무 값으로나 UPDATE 가능. 도메인상 불가능한 전이가 허용됨.

**허용되면 안 되는 전이 예시**:
```
CULLED → GESTATING  (도태된 모돈이 임신?)
DEAD → ACTIVE       (죽은 모돈이 활성?)
LACTATING → GESTATING (포유 중 임신?)
WEANED → LACTATING  (이유한 모돈이 다시 포유?)
```

**피그플랜 참고**: SF_GET_MODONGB_STATUS() 함수가 최종 작업에서 상태를 계산.
직접 UPDATE가 아니라 작업 기록에서 파생됨.

**권장 조치**: 상태 전이 매트릭스 + 트리거
```sql
-- 허용 전이 정의
-- ACTIVE → GESTATING (교배 시)
-- GESTATING → LACTATING (분만 시)
-- GESTATING → ACTIVE (재발정/유산 시)
-- LACTATING → WEANED (이유 시)
-- WEANED → GESTATING (재교배 시)
-- WEANED → DRY (건기)
-- DRY → GESTATING (재교배 시)
-- ANY → CULLED (도태 시)
-- ANY → DEAD (폐사 시)
-- CULLED, DEAD → (전이 불가, 최종 상태)
```

---

### 4.2 [M-02] 발정 감지(Heat Detection) 기록 없음

**현상**: matings.estrus_detected_at 컬럼만 존재. 독립적인 발정 기록 불가.

**영향**:
- 발정이 감지되었지만 교배하지 않은 경우 기록 불가
- WEI (Wean-to-Estrus Interval) 추적 불가 — 핵심 번식 성능 지표
- AI Agent 2(액션 스케줄러)에서 "발정 감지 → 교배 실행" 워크플로우 데이터 없음

**권장 조치**: `heat_detections` 테이블 추가 또는 reproductive_events에 통합
```sql
-- reproductive_events.event_type에 'HEAT_DETECTED' 추가로 통합 가능
-- 또는 독립 테이블:
CREATE TABLE heat_detections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    detected_at     TIMESTAMPTZ NOT NULL,
    detection_method VARCHAR(20),    -- VISUAL / BOAR_EXPOSURE / SENSOR
    action_taken    VARCHAR(20),     -- MATED / SKIPPED / SCHEDULED
    mating_id       UUID REFERENCES matings(id),  -- 교배로 이어진 경우
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

### 4.3 [M-03] 농장별 번식 파라미터 설정 테이블 없음

**현상**: 임신 기간(114일), 포유 기간(21일), 이유→교배 간격(7일) 등이 하드코딩 필요.

**피그플랜 참고**: TC_FARM_CONFIG 테이블에서 농장별 커스텀 설정
```
CODE 901001 = 임신 기간 (기본 114일)
CODE 901002 = 포유 기간 (기본 21일)
CODE 901003 = 이유→교배 간격 (기본 7일)
```

**권장 조치**: `farm_configs` 테이블 추가
```sql
CREATE TABLE farm_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    config_key      VARCHAR(50) NOT NULL,
        -- GESTATION_DAYS / LACTATION_DAYS / WEI_TARGET_DAYS
        -- PREGNANCY_CHECK_DAY / FARROWING_ALERT_DAYS / WEANING_ALERT_DAYS
    config_value    VARCHAR(100) NOT NULL,
    description     TEXT,
    UNIQUE(farm_id, config_key)
);
-- 기본값 예시
-- GESTATION_DAYS = 114
-- LACTATION_DAYS = 21
-- WEI_TARGET_DAYS = 7
-- PREGNANCY_CHECK_DAY = 25  (교배 후 25일에 임신확인)
```

---

### 4.4 [M-04] 단위 이중 저장 문제

**현상**: m2/sqft, kg/lbs를 두 컬럼에 동시 저장.

**대상**:
- buildings: `area_per_pig_m2` + `area_per_pig_sqft`
- feed_deliveries: `quantity_kg` + `quantity_lbs`

**문제**: 두 값이 불일치할 때 어느 것이 원본인지 알 수 없음. 업데이트 시 둘 다 갱신해야 함.

**권장 조치**: 원본 단위 하나만 저장 + `country_configs.weight_unit`으로 앱 레이어 환산
```sql
-- 제거: area_per_pig_sqft, quantity_lbs
-- 유지: area_per_pig_m2, quantity_kg (내부 표준: SI 단위)
-- 앱에서: IF farm.unit_system = 'IMPERIAL' THEN display = value * 2.20462
```

---

### 4.5 [M-05] 지역 전용 컬럼 산재

**현상**: EU/US/KR/SEA 전용 필드가 모든 테이블에 혼재. 대부분의 농장에서 NULL.

**대표 사례**:
```sql
-- carcass_records 테이블에 4개 지역 등급이 모두 존재:
grade_kr             -- 한국
seurop_grade         -- EU
carcass_merit_score  -- 미국
sif_inspection_id    -- 브라질

-- medications 테이블:
ddda_value           -- EU
mg_pcu               -- EU (ESVAC)
mg_animal_biomass    -- 한국 (2029~)
vfd_number           -- 미국
vfd_vet_license      -- 미국
vfd_issued_date      -- 미국
vfd_expiry_date      -- 미국
collective_treatment -- EU
```

**권장 조치**: 2가지 옵션
- **옵션 A**: 지역 전용 데이터를 `JSONB region_data` 컬럼 하나로 통합
- **옵션 B**: 확장 테이블 분리 (carcass_records_kr, carcass_records_eu 등)
- **권장**: 옵션 A (MVP 단순성)

---

### 4.6 [M-06] NPD 뷰(v_sow_npd) 로직 오류

**현상**: 이유 후 다음 교배를 60일 이내로 매칭하는 JOIN에서 중복 카운트 발생 가능.

```sql
-- 현재 (문제):
LEFT JOIN matings m ON m.sow_id = s.id
    AND m.mating_date > w.weaning_date
    AND m.mating_date <= w.weaning_date + INTERVAL '60 days'
-- → 하나의 이유에 여러 교배가 매칭 → NPD 합산 중복
```

**권장 조치**: LATERAL + LIMIT 1로 가장 가까운 교배만 매칭
```sql
LEFT JOIN LATERAL (
    SELECT mating_date FROM matings
    WHERE sow_id = s.id
    AND mating_date > w.weaning_date
    AND mating_date <= w.weaning_date + INTERVAL '60 days'
    AND deleted_at IS NULL
    ORDER BY mating_date ASC
    LIMIT 1
) m ON TRUE
```

---

### 4.7 [M-07] PSY 뷰(v_farm_psy) soft delete 미반영

**현상**: v_farm_psy 뷰에서 `deleted_at IS NULL` 조건이 없음.

```sql
-- 현재: 삭제된 모돈/이유 기록도 PSY 계산에 포함됨
FROM sows s
LEFT JOIN farrowings f ON f.sow_id = s.id
LEFT JOIN weanings w ON w.sow_id = s.id
-- deleted_at 필터 없음!
```

**권장 조치**:
```sql
FROM sows s
LEFT JOIN farrowings f ON f.sow_id = s.id AND f.deleted_at IS NULL
LEFT JOIN weanings w ON w.sow_id = s.id AND w.deleted_at IS NULL
WHERE s.deleted_at IS NULL
```

---

## 5. MINOR 이슈

### 5.1 [m-01] FK 인덱스 누락

PostgreSQL은 FK 컬럼에 자동 인덱스를 생성하지 않음. 누락된 FK 인덱스:

| 테이블 | 컬럼 | 영향 |
|--------|------|------|
| matings | boar_id | 씨수퇘지별 교배 이력 조회 느림 |
| matings | technician_id | 기술자별 성적 분석 느림 |
| farrowings | mating_id | 교배→분만 연결 조회 느림 |
| farrowings | building_id | 돈방별 분만 조회 느림 |
| weanings | farrowing_id | 분만→이유 연결 조회 느림 |
| medications | sow_id | 모돈별 투약 이력 느림 |
| medications | group_id | 그룹별 투약 이력 느림 |
| vaccinations | sow_id | 모돈별 백신 이력 느림 |
| vaccinations | group_id | 그룹별 백신 이력 느림 |

---

### 5.2 [m-02] Soft Delete 불일치

`deleted_at` 추가된 테이블:
sows, boars, matings, farrowings, weanings, removals, animal_groups, health_events, vaccinations, medications, feed_records, individual_pigs

**빠진 테이블** (삭제 가능한 엔티티):
- buildings
- pregnancy_checks
- shipments
- feed_bins
- feed_formulas

---

### 5.3 [m-03] updated_at 불일치

`updated_at` 있는 테이블: organizations, farms, sows, boars, buildings, animal_groups

**빠진 테이블**: matings, farrowings, weanings, removals, health_events, vaccinations, medications 등
→ 업데이트 가능한 모든 테이블에 updated_at + 트리거 필요

---

### 5.4 [m-04] animal_groups.source_farrowing_ids UUID[] 타입

**현상**: UUID 배열로 분만 ID를 저장 → FK 무결성 보장 불가
**권장**: 별도 매핑 테이블 `group_farrowing_sources(group_id, farrowing_id)`

---

### 5.5 [m-05] alert_rules.notify_roles 쉼표 구분 문자열

**현상**: `VARCHAR(100)` — 예: "FARM_OWNER,FARM_MANAGER"
**권장**: `VARCHAR[]` 배열 또는 별도 매핑 테이블

---

### 5.6 [m-06] 테이블 수 불일치

- 스키마 본문 Summary: 38 tables
- v1.1 Summary: 49 tables
- 실제 카운트: ~51개 (Supplement 포함)

→ Summary 갱신 필요

---

### 5.7 [m-07] ear_tag NOT NULL — SEA 소농 대응 불가

**현상**: `sows.ear_tag VARCHAR(30) NOT NULL`
**문제**: 베트남/필리핀 소농은 이어태그 없이 "1번 돼지, 2번 돼지"로 관리
**권장**: NULLABLE로 변경하거나, 시스템 자동 부여 옵션 제공

---

## 6. 모듈 독립성 분석

### 6.1 FK 의존성 그래프

```
Module 0: Platform ← 모든 모듈이 의존 (organizations, farms, users)
    ↑
Module 1: Sow ← Module 2, 3, 4, 5, 6, 7, 8이 의존
    │  (buildings, boars, sows, matings, farrowings, weanings, removals)
    │
    ├──→ Module 2: Growing (animal_groups → farrowings)
    ├──→ Module 3: Feed (feed_records → sows, animal_groups)
    ├──→ Module 4: Health (health_events → sows, animal_groups)
    ├──→ Module 5: Genetics (genetics → sows, boars)
    └──→ Module 8: KPI (v_farm_psy → sows, farrowings, weanings)

Module 6: Compliance → farms만 참조 (독립적)
Module 9: Market → 완전 독립
Module 10: Data → farms만 참조 (독립적)
```

### 6.2 평가

**"각 도메인 독립 배포 가능 (마이크로서비스 대응)"** → **현실적으로 불가능**

Module 1(Sow)이 사실상 모놀리스 허브. 4개 모듈이 sows 테이블에 직접 FK.
마이크로서비스 분리 시 cross-service FK가 되어 분산 트랜잭션 필요.

**권장 구조**:
```
Core (Module 0 + 1): 항상 함께 배포
  - Platform + Sow Management
Extensions (나머지): Core API를 통해 간접 참조
  - Health, Feed, Growing, KPI 등
Independent (Module 6, 9, 10): 완전 독립 가능
  - Compliance, Market, Data
```

---

## 7. 글로벌 운영 적합성

### 7.1 커버되는 항목 ✅
- 단위 전환 (kg/lb, ℃/℉) — country_configs
- 통화/날짜 포맷 — 11개국 정의
- 알림 채널 — 카카오톡/Zalo/WeChat/WhatsApp
- 도체 등급 — 한국/EU/미국/브라질 4종
- 규제 플래그 — 항생제/동물복지/ASF/Prop12
- 다국어 — code_translations
- 생물보안 — ASF/PRRS 특화 필드

### 7.2 미커버 항목 ❌
- 중국 다층 양돈 빌딩 (7-26층) — buildings.floor_number만으로 부족
- 베트남 소농 — ear_tag NOT NULL 문제
- EU 2022년 집단 항생제 투약 금지 — 플래그만 있고 검증 로직 없음
- 시장별 가격 단위 차이 — 한국(kg), 미국(cwt), EU(kg) 혼재

---

## 8. 두수(Head Count) 정합성 상세 분석

### 8.1 모돈 재고 두수 (Sow Inventory)

**정의**: 특정 시점의 활성 모돈 수

**현재 스키마에서의 계산**:
```sql
SELECT COUNT(*) FROM sows
WHERE farm_id = ? AND status NOT IN ('CULLED', 'DEAD') AND deleted_at IS NULL
```

**문제점**:

| # | 이슈 | 설명 | 심각도 |
|---|------|------|--------|
| H-01 | **시점별 재고 추적 불가** | sows.status는 현재 상태만 저장. "2026년 1월 1일 시점 모돈 수"를 역추적하려면 audit_log를 뒤져야 함. 피그플랜은 `IN_DT ≤ 기준일 AND OUT_DT > 기준일`로 즉시 계산 | ❌ CRITICAL |
| H-02 | **입식 시점 확정 안 됨** | sows.entry_date + sows.entry_type으로 입식은 기록되지만, 도태/폐사 시점은 removals 테이블에만 존재. sows 테이블에는 "나간 날짜" 없음 | ❌ CRITICAL |
| H-03 | **상태별 두수 집계 불정확** | soft delete된 모돈이 status='ACTIVE'를 유지할 수 있음 (deleted_at만 채워지고 status는 안 바뀜) | ⚠️ MAJOR |

**피그플랜 참고**:
```
TB_MODON:
  IN_DT  = 입식일
  OUT_DT = 퇴역일 (9999-12-31 = 현재 활성)

특정 시점 재고 = SELECT COUNT(*)
  WHERE IN_DT <= '기준일' AND OUT_DT > '기준일'

→ 과거 어느 시점이든 정확한 재고 추적 가능
```

**권장 조치**:
```sql
-- sows 테이블에 exit_date 추가
ALTER TABLE sows ADD COLUMN exit_date DATE;
-- 활성 모돈: exit_date IS NULL
-- 특정 시점 재고: entry_date <= 기준일 AND (exit_date IS NULL OR exit_date > 기준일)
-- removals INSERT 시 sows.exit_date 자동 갱신 트리거
```

---

### 8.2 모돈 상태별 두수 추이

양돈장 운영에서 핵심 관리 지표:

```
전체 활성 모돈 = 후보돈 + 임신돈 + 포유돈 + 이유돈 + 건기돈
                (GILT)  (GESTATING)(LACTATING)(WEANED) (DRY)
```

**현재 스키마 문제**:

| 상태 | 전이 시점 | 현재 구현 | 문제 |
|------|-----------|-----------|------|
| ACTIVE → GESTATING | 교배 시 | sows.status 직접 UPDATE | 트리거 없음, API에서만 변경 |
| GESTATING → LACTATING | 분만 시 | sows.status 직접 UPDATE | 트리거 없음 |
| LACTATING → WEANED | 이유 시 | sows.status 직접 UPDATE | 트리거 없음 |
| WEANED → GESTATING | 재교배 시 | sows.status 직접 UPDATE | 트리거 없음 |
| ANY → CULLED/DEAD | 도태/폐사 시 | removals INSERT + sows UPDATE | 두 테이블 동시 UPDATE 필요, 트랜잭션 미보장 |

**위험 시나리오**:
```
1. matings에 교배 INSERT → sows.status UPDATE 누락
   → 교배 기록은 있는데 모돈은 아직 ACTIVE
   → 임신돈 두수 = 실제보다 적게 집계

2. removals에 도태 INSERT → sows.status UPDATE 누락
   → 도태 기록은 있는데 모돈은 아직 ACTIVE
   → 활성 모돈 두수 = 실제보다 많게 집계

3. sows.status를 CULLED로 변경 → removals INSERT 누락
   → 모돈은 사라졌는데 도태 사유/날짜 미기록
```

**권장 조치**: 이벤트 테이블 INSERT 시 sows.status 자동 전이 트리거
```sql
-- matings INSERT → sows.status = 'GESTATING'
CREATE OR REPLACE FUNCTION trg_mating_status() RETURNS TRIGGER AS $$
BEGIN
    UPDATE sows SET status = 'GESTATING' WHERE id = NEW.sow_id;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- farrowings INSERT → sows.status = 'LACTATING', sows.parity += 1
-- weanings INSERT → sows.status = 'WEANED'
-- removals INSERT → sows.status = removal_type 기반, sows.exit_date = removal_date
```

---

### 8.3 자돈 두수 추적 (Piglet Head Count) — 가장 심각한 GAP

양돈에서 자돈 두수는 **매일** 변동합니다:

```
분만 시:
  total_born = born_alive + stillborn + mummified
  유효 자돈 = born_alive

포유 기간 (~21일) 중 변동:
  + 위탁 지입 (foster_in) — 다른 모돈의 자돈을 받음
  - 위탁 지출 (foster_out) — 내 자돈을 다른 모돈에게 보냄
  - 포유중 폐사 (pre_weaning_death) — 압사/설사/아사/선천결함 등
  = 현재 포유 두수

이유 시:
  weaned_count = born_alive + foster_in - foster_out - pre_weaning_deaths
```

**현재 스키마의 자돈 추적 능력**:

| 이벤트 | 추적 가능? | 방법 | 문제 |
|--------|-----------|------|------|
| 분만 시 생존산자 | ✅ | farrowings.born_alive | OK |
| 분만 시 사산 | ✅ | farrowings.stillborn | OK |
| 분만 시 미라 | ✅ | farrowings.mummified | OK |
| 위탁 지입 두수 | ⚠️ | farrowings.cross_fostered_in (INT) | 날짜/원모돈 미기록 |
| 위탁 지출 두수 | ⚠️ | farrowings.cross_fostered_out (INT) | 날짜/대상모돈 미기록 |
| 포유중 폐사 | ❌ | **없음** | 추적 자체 불가 |
| 포유중 폐사 사유 | ❌ | **없음** | 사유별 분석 불가 |
| 일별 포유 두수 | ❌ | **없음** | 일별 현황 파악 불가 |
| 이유 두수 | ✅ | weanings.weaned_count | OK |
| 이유 두수 검증 | ❌ | **검증 로직 없음** | 아래 상세 |

**두수 정합성 검증 공식** (반드시 성립해야 함):
```
weanings.weaned_count
  = farrowings.born_alive
  + farrowings.cross_fostered_in
  - farrowings.cross_fostered_out
  - (포유중 폐사 합계)          ← 현재 추적 불가!
```

**현재 스키마에서 검증 불가능한 이유**:
1. 포유중 폐사 데이터가 아예 없음
2. cross_fostered_in/out의 타이밍이 불명확 (분만 직후? 포유 3일 후?)
3. weaned_count가 born_alive보다 클 수도 있음 (위탁 지입 시) → CHECK 제약 불가
4. 결국 `weaned_count`가 임의의 숫자로 들어갈 수 있음

**피그플랜 참고 (TB_MODON_JADON_TRANS)**:
```
분만 #A-042, 산차 3:
  2026-03-01 born_alive = 14
  2026-03-02 160001(생시도태) -1두 = 13
  2026-03-03 160004(지출)    -2두 = 11 → #A-055에게
  2026-03-03 160003(지입)    +1두 = 12 ← #A-030에서
  2026-03-08 160002(폐사)    -1두 = 11 (사유: 압사)
  2026-03-15 160002(폐사)    -1두 = 10 (사유: 설사)
  2026-03-22 이유(TB_EU)     10두 ✅ = 14 - 1 - 2 + 1 - 1 - 1 = 10

→ 매 건마다 날짜, 사유, 두수, 대상 모돈 기록
→ 이유 시점에 자동 검증 가능
```

**권장 조치**: piglet_events 테이블 + 두수 검증 함수
```sql
-- 1. piglet_events 테이블 (C-02에서 제안한 것의 확장)
CREATE TABLE piglet_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id         UUID NOT NULL REFERENCES farms(id),
    farrowing_id    UUID NOT NULL REFERENCES farrowings(id),
    sow_id          UUID NOT NULL REFERENCES sows(id),
    event_date      DATE NOT NULL,
    event_type      VARCHAR(20) NOT NULL
        CHECK (event_type IN ('STILLBORN_REMOVAL','DEATH','FOSTER_IN','FOSTER_OUT')),
    piglet_count    INT NOT NULL CHECK (piglet_count > 0),
    reason          VARCHAR(50),
        -- DEATH 사유: CRUSHING / SCOURS / STARVATION / CONGENITAL / HYPOTHERMIA / OTHER
    target_sow_id   UUID REFERENCES sows(id),
    target_farrowing_id UUID REFERENCES farrowings(id),
    notes           TEXT,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- 2. 두수 검증 함수
CREATE OR REPLACE FUNCTION fn_verify_piglet_count(p_farrowing_id UUID)
RETURNS TABLE(
    born_alive INT,
    foster_in INT,
    foster_out INT,
    deaths INT,
    expected_weaned INT,
    actual_weaned INT,
    is_balanced BOOLEAN
) AS $$
    SELECT
        f.born_alive,
        COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)::INT,
        COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)::INT,
        COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type IN ('DEATH','STILLBORN_REMOVAL')), 0)::INT,
        (f.born_alive
         + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)
         - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
         - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type IN ('DEATH','STILLBORN_REMOVAL')), 0)
        )::INT,
        w.weaned_count,
        (f.born_alive
         + COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_IN'), 0)
         - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type = 'FOSTER_OUT'), 0)
         - COALESCE(SUM(pe.piglet_count) FILTER (WHERE pe.event_type IN ('DEATH','STILLBORN_REMOVAL')), 0)
        ) = w.weaned_count
    FROM farrowings f
    LEFT JOIN piglet_events pe ON pe.farrowing_id = f.id AND pe.deleted_at IS NULL
    LEFT JOIN weanings w ON w.farrowing_id = f.id AND w.deleted_at IS NULL
    WHERE f.id = p_farrowing_id
    GROUP BY f.born_alive, w.weaned_count;
$$ LANGUAGE sql;
```

---

### 8.4 비육돈 두수 추적 (Growing/Finisher Head Count)

비육 구간에서도 두수 정합성이 필요합니다:

```
입식: animal_groups.entry_count
  - 폐사: grow_records.mortality_count (누적)
  - 출하: shipments.head_count
  = 현재 재고: animal_groups.current_count
```

**현재 스키마 문제**:

| # | 이슈 | 설명 |
|---|------|------|
| H-04 | current_count 수동 관리 | animal_groups.current_count를 직접 UPDATE → grow_records/shipments와 불일치 가능 |
| H-05 | 그룹 간 이동 없음 | 자돈사 → 육성사 → 비육사 이동 시 animal_groups 간 두수 이전 메커니즘 없음 |
| H-06 | 그룹 종료 검증 없음 | current_count = 0인데 status = 'ACTIVE'일 수 있음 |

**검증 공식**:
```sql
-- 반드시 성립:
animal_groups.current_count
  = animal_groups.entry_count
  - SUM(grow_records.mortality_count)
  - SUM(shipments.head_count WHERE group_id = ?)
  + (그룹 간 전입)  ← 현재 추적 불가
  - (그룹 간 전출)  ← 현재 추적 불가
```

---

### 8.5 농장 전체 두수 대시보드 요구사항

운영자가 필요로 하는 실시간 두수:

```
┌─ 농장 전체 ─────────────────────────────────────────┐
│                                                     │
│  모돈 재고: 680두                                    │
│    후보돈(Gilt):     45 (6.6%)                       │
│    임신돈(Gestating): 340 (50.0%)                    │
│    포유돈(Lactating): 85 (12.5%)                     │
│    이유돈(Weaned):    120 (17.6%)                    │
│    건기돈(Dry):       90 (13.2%)                     │
│                                                     │
│  씨수퇘지: 15두                                      │
│                                                     │
│  자돈 (포유중): 1,020두                              │
│    → 이번 주 분만 예정: 12복                         │
│    → 포유중 폐사율: 12.5%                            │
│                                                     │
│  비육돈: 4,500두                                     │
│    자돈사: 1,200                                    │
│    육성사: 1,500                                    │
│    비육사: 1,800                                    │
│    → 이번 주 출하 예정: 200두                        │
│                                                     │
│  금월 도태: 8두 / 폐사: 2두                          │
└─────────────────────────────────────────────────────┘
```

**현재 스키마로 계산 가능한 것**:
- ✅ 모돈 상태별 두수 (sows.status 기반)
- ✅ 씨수퇘지 두수 (boars.status 기반)
- ❌ 자돈 포유중 두수 — piglet_events 없어서 불가
- ⚠️ 비육돈 두수 — animal_groups.current_count 수동 관리 의존
- ✅ 도태/폐사 — removals 테이블에서 집계 가능

---

## 9. 날짜 논리 및 시간 제약 상세 분석

### 9.1 번식 사이클 날짜 규칙

양돈 번식에는 생물학적으로 정해진 기간이 있습니다:

```
교배일 (mating_date)
  │
  ├─ +21~25일: 임신확인 (pregnancy_check_date)
  │   └─ 양성 → 계속 임신
  │   └─ 음성 → 재발정 (return: ~21일 주기)
  │
  ├─ +110~120일 (평균 114일): 분만 (farrowing_date)
  │   └─ 정상 범위: 교배 후 110~120일
  │   └─ 유도분만: 112~114일
  │
  └─ +114+18~28일 (평균 21일): 이유 (weaning_date)
      └─ 정상 범위: 분만 후 14~35일 (지역별 차이)
      └─ 조기이유: EU 최소 28일, 미국 17~21일
```

### 9.2 현재 스키마에서 누락된 날짜 제약

| # | 제약 규칙 | 필요한 CHECK/트리거 | 현재 상태 |
|---|----------|-------------------|----------|
| D-01 | 분만일 > 교배일 | `farrowings.farrowing_date > matings.mating_date` | ❌ 없음 |
| D-02 | 분만일 - 교배일 = 100~130일 | 범위 검증 (생물학적 한계) | ❌ 없음 |
| D-03 | 이유일 > 분만일 | `weanings.weaning_date > farrowings.farrowing_date` | ❌ 없음 |
| D-04 | 이유일 - 분만일 = 14~60일 | 범위 검증 (최소 포유기간) | ❌ 없음 |
| D-05 | 이유일령 = 이유일 - 분만일 | `weaning_age_days` 자동 계산 검증 | ❌ 없음 |
| D-06 | 임신확인일 > 교배일 | `pregnancy_checks.check_date > matings.mating_date` | ❌ 없음 |
| D-07 | 도태/폐사일 ≥ 입식일 | `removals.removal_date >= sows.entry_date` | ❌ 없음 |
| D-08 | 다음 교배일 ≥ 이유일 | 이유 전 재교배 방지 | ❌ 없음 |
| D-09 | 같은 모돈 동시 임신 불가 | 활성 분만 사이클 중복 방지 | ❌ 없음 |
| D-10 | 분만일 < 이유일 < 다음 교배일 | 시간 순서 강제 | ❌ 없음 |

**위험 시나리오**:
```
시나리오 1: 교배일 = 2026-03-01, 분만일 = 2026-02-15
  → 교배보다 분만이 먼저? 현재 스키마에서 허용됨

시나리오 2: 분만일 = 2026-03-01, 이유일 = 2026-03-01
  → 분만 당일 이유? 현재 스키마에서 허용됨

시나리오 3: 모돈 A-042에 분만이 2건 연속 (이유 없이)
  → 현재 스키마에서 차단 안 됨

시나리오 4: 교배일 = 2026-01-01, 분만일 = 2026-10-01 (270일)
  → 임신 9개월? 돼지 임신 기간은 114일. 현재 검증 없음
```

**권장 조치**: 날짜 검증 트리거
```sql
-- 분만 시 교배 날짜 검증
CREATE OR REPLACE FUNCTION validate_farrowing_dates()
RETURNS TRIGGER AS $$
DECLARE
    v_mating_date DATE;
    v_gestation_days INT;
BEGIN
    -- 연결된 교배 날짜 조회
    SELECT mating_date INTO v_mating_date
    FROM matings WHERE id = NEW.mating_id;

    IF v_mating_date IS NOT NULL THEN
        v_gestation_days := NEW.farrowing_date - v_mating_date;

        IF v_gestation_days < 100 OR v_gestation_days > 130 THEN
            RAISE EXCEPTION 'Invalid gestation period: % days (expected 100-130)',
                v_gestation_days;
        END IF;

        IF NEW.farrowing_date <= v_mating_date THEN
            RAISE EXCEPTION 'Farrowing date must be after mating date';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 이유 시 분만 날짜 검증
CREATE OR REPLACE FUNCTION validate_weaning_dates()
RETURNS TRIGGER AS $$
DECLARE
    v_farrowing_date DATE;
    v_nursing_days INT;
BEGIN
    SELECT farrowing_date INTO v_farrowing_date
    FROM farrowings WHERE id = NEW.farrowing_id;

    IF v_farrowing_date IS NOT NULL THEN
        v_nursing_days := NEW.weaning_date - v_farrowing_date;

        IF NEW.weaning_date <= v_farrowing_date THEN
            RAISE EXCEPTION 'Weaning date must be after farrowing date';
        END IF;

        IF v_nursing_days < 10 OR v_nursing_days > 60 THEN
            RAISE EXCEPTION 'Invalid nursing period: % days (expected 10-60)',
                v_nursing_days;
        END IF;

        -- weaning_age_days 자동 계산
        NEW.weaning_age_days := v_nursing_days;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

### 9.3 동시 사이클 방지 (Overlapping Cycles)

**규칙**: 하나의 모돈은 동시에 하나의 번식 사이클만 활성화 가능.

**현재 스키마 문제**: 아무런 방지 메커니즘 없음.

```sql
-- 아래가 현재 가능 (이상 상황):
-- 모돈 A-042: 2026-01-01 교배 (임신 중)
-- 모돈 A-042: 2026-02-01 또 교배 (이미 임신 중인데?)
-- → matings 테이블에 둘 다 INSERT 됨

-- 피그플랜에서는?
-- TB_MODON_WK.SEQ 순번으로 관리
-- 마지막 작업이 G(교배)이면 다음 G는 "재교배"로 GYOBAE_CNT+1
-- 마지막 작업이 B(분만)이면 다음 G 전에 E(이유)가 와야 함
```

**권장 조치**: breeding_cycles 테이블의 UNIQUE 제약 + 상태 검증
```sql
-- 활성 사이클은 모돈당 최대 1개
CREATE UNIQUE INDEX idx_one_active_cycle
ON breeding_cycles (sow_id)
WHERE cycle_status NOT IN ('WEANED', 'FAILED');
```

---

## 10. 테이블별 상관관계 상세 분석

### 10.1 관계 매트릭스 (핵심 운영 테이블)

```
              org  farm user  bldg boar  sow  mate preg farr wean remv hlth vacc med  grp  feed
organizations  -    →
farms          ←    -    →    →         →
users          ←    ←    -                                                              
buildings      ←    ←         -         →
boars               ←              -    
sows                ←    ←    ←    ←    -    →    →    →    →    →    →    →    →
matings             ←    ←         ←    ←    -    ←    ←
pregnancy_ch        ?              ←         ←    -
farrowings          ←    ←    ←         ←    ←         -    ←
weanings            ←    ←              ←              ←    -
removals            ←    ←              ←                        -
health_events       ←    ←    ←         ←                             -              ←
vaccinations        ←    ←              ←                                  -         ←
medications         ←    ←              ←                                       -    ←
animal_groups       ←         ←                                                      -    ←
feed_records        ←         ←         ←                                       ←    ←    -

→ = FK 참조   ← = 참조 받음   ? = farm_id 누락
```

### 10.2 FK Nullable 분석 — 데이터 무결성 위험도

| FK | Nullable? | 문제 | 권장 |
|----|-----------|------|------|
| **farrowings.mating_id** | ✅ NULL 가능 | 교배 없는 분만 허용 | NOT NULL |
| **weanings.farrowing_id** | ✅ NULL 가능 | 분만 없는 이유 허용 | NOT NULL |
| **matings.boar_id** | ✅ NULL 가능 | AI(인공수정) 시 NULL 가능 → OK | OK (AI 허용) |
| **matings.technician_id** | ✅ NULL 가능 | 기록자 없이 교배 → OK | OK |
| **pregnancy_checks.mating_id** | ✅ NULL 가능 | 어떤 교배의 임신확인인지 불명 | NOT NULL 권장 |
| **farrowings.building_id** | ✅ NULL 가능 | 분만사 미지정 → OK (소농) | OK |
| **health_events.sow_id** | ✅ NULL 가능 | 그룹 단위 이벤트 시 → OK | OK (group_id와 XOR) |
| **health_events.group_id** | ✅ NULL 가능 | 개체 단위 이벤트 시 → OK | OK (sow_id와 XOR) |
| **feed_records.sow_id** | ✅ NULL 가능 | 그룹 급이 시 → OK | OK (group_id와 XOR) |
| **feed_records.group_id** | ✅ NULL 가능 | 개체 급이 시 → OK | OK (sow_id와 XOR) |

**XOR 제약 누락** — health_events, feed_records에서 sow_id와 group_id가 둘 다 NULL이거나 둘 다 채워질 수 있음:
```sql
-- 필요한 제약: 둘 중 하나는 반드시 있어야 함
ALTER TABLE health_events ADD CONSTRAINT chk_target
    CHECK (sow_id IS NOT NULL OR group_id IS NOT NULL);
ALTER TABLE feed_records ADD CONSTRAINT chk_feed_target
    CHECK (sow_id IS NOT NULL OR group_id IS NOT NULL);
```

### 10.3 Cascading 영향 분석

**모돈 삭제 시 영향 범위** (soft delete):

```
sows.deleted_at 설정 시, 아래 테이블의 데이터는 어떻게 되는가?

sows (deleted_at = NOW())
  ├─ matings (sow_id FK) → CASCADE 설정 없음 → 고아 레코드
  ├─ pregnancy_checks (sow_id FK) → 고아 레코드
  ├─ farrowings (sow_id FK) → 고아 레코드
  │   └─ weanings (farrowing_id FK) → 이중 고아
  ├─ weanings (sow_id FK) → 고아 레코드
  ├─ removals (sow_id FK) → 고아 레코드
  ├─ health_events (sow_id FK) → 고아 레코드
  ├─ vaccinations (sow_id FK) → 고아 레코드
  └─ medications (sow_id FK) → 고아 레코드
```

**문제**: Soft delete 시 관련 레코드를 함께 soft delete할지, 유지할지 정책이 없음.
**권장**: 모돈 soft delete 시 관련 이벤트는 유지 (과거 기록 보존). 단, 조회 시 `sows.deleted_at IS NULL` JOIN 조건 필수.

### 10.4 교배-분만-이유 체인 무결성

**정상 체인**:
```
matings[M1] ←── farrowings[F1] ←── weanings[W1]
(sow_id=A)      (sow_id=A,          (sow_id=A,
                  mating_id=M1)       farrowing_id=F1)
```

**현재 스키마에서 가능한 비정상 체인**:

```
Case 1: 끊어진 체인
  matings[M1](sow_id=A)
  farrowings[F1](sow_id=A, mating_id=NULL)  ← 어떤 교배의 분만?
  weanings[W1](sow_id=A, farrowing_id=NULL) ← 어떤 분만의 이유?

Case 2: 교차 참조
  matings[M1](sow_id=A)
  farrowings[F1](sow_id=B, mating_id=M1)  ← 모돈 A의 교배인데 모돈 B의 분만?
  → 현재 스키마에서 방지 안 됨!

Case 3: 다중 이유
  farrowings[F1](sow_id=A)
  weanings[W1](sow_id=A, farrowing_id=F1)
  weanings[W2](sow_id=A, farrowing_id=F1)  ← 같은 분만에 이유가 2번?
  → 현재 스키마에서 방지 안 됨!

Case 4: 모돈 불일치
  matings[M1](sow_id=A)
  farrowings[F1](sow_id=A, mating_id=M1)
  weanings[W1](sow_id=B, farrowing_id=F1)  ← 분만은 A인데 이유는 B?
  → 현재 스키마에서 방지 안 됨!
```

**권장 조치**:
```sql
-- 1. farrowings: mating과 sow 일치 검증
CREATE OR REPLACE FUNCTION validate_farrowing_sow_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.mating_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM matings
            WHERE id = NEW.mating_id AND sow_id = NEW.sow_id
        ) THEN
            RAISE EXCEPTION 'Farrowing sow_id must match mating sow_id';
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- 2. weanings: farrowing과 sow 일치 검증
CREATE OR REPLACE FUNCTION validate_weaning_sow_match()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.farrowing_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM farrowings
            WHERE id = NEW.farrowing_id AND sow_id = NEW.sow_id
        ) THEN
            RAISE EXCEPTION 'Weaning sow_id must match farrowing sow_id';
        END IF;
    END IF;
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- 3. weanings: 같은 분만에 이유 1건만
CREATE UNIQUE INDEX idx_one_weaning_per_farrowing
ON weanings (farrowing_id)
WHERE farrowing_id IS NOT NULL AND deleted_at IS NULL;
```

---

## 11. 번식 사이클 시뮬레이션 테스트 계획

### 8.1 테스트 시나리오 (SQL 스크립트로 검증)

| # | 시나리오 | 기대 결과 | 검증 항목 |
|---|----------|-----------|-----------|
| T-01 | 후보돈 입식 → 첫 교배 | sow.status = GESTATING, parity = 0 | 입식 플로우 |
| T-02 | 교배 → 임신확인(양성) | pregnancy_check.result = POSITIVE | 임신확인 |
| T-03 | 교배 → 분만 (114일 후) | farrowing 기록, parity +1 | 산차 증가 |
| T-04 | 분만 → 이유 (21일 후) | weaning 기록, weaned_count ≤ born_alive | 두수 정합 |
| T-05 | 이유 → 재교배 (7일 후) | 다음 사이클 시작, mating_number = 1 | 사이클 반복 |
| T-06 | 임신확인 음성 → 재교배 | 재발정 기록, mating_number +1 | 재교배 추적 |
| T-07 | 포유 중 자돈 폐사 3두 | weaned = born_alive - 3 | 자돈 추적 |
| T-08 | 위탁 (2두 지출, 3두 지입) | cross-foster 추적 | 위탁 추적 |
| T-09 | 8산차 모돈 도태 | removal 기록, status = CULLED | 도태 플로우 |
| T-10 | 산차별 PSY 계산 | v_farm_psy 결과 = 수동 계산과 일치 | KPI 정합성 |
| T-11 | NPD 계산 (재발정 포함) | v_sow_npd = 이유~재교배 일수 합 | NPD 정합성 |
| T-12 | 월마감 후 데이터 수정 시도 | period_lock으로 차단 | 잠금 검증 |
| T-13 | 교배 없이 분만 기록 시도 | 에러 발생 (또는 경고) | 순서 검증 |
| T-14 | 분만 없이 이유 기록 시도 | 에러 발생 (또는 경고) | 순서 검증 |
| T-15 | 죽은 모돈에 교배 시도 | 에러 발생 | 상태전이 검증 |

### 8.2 테스트 데이터

피그플랜 기존 데이터에서 대표 사례 추출:
- 정상 사이클 모돈 5두 (1~8산차)
- 재발정 경험 모돈 2두
- 유산 경험 모돈 1두
- 위탁 모돈 1두
- 도태/폐사 모돈 2두

---

## 9. 권장 조치 요약

### 9.1 v2 스키마에서 반영 필요

| 우선순위 | 항목 | 이슈 번호 |
|----------|------|-----------|
| **P0** | reproductive_events 테이블 추가 (재발정/유산) | C-01 |
| **P0** | piglet_events 테이블 추가 (포유중 자돈 추적) | C-02 |
| **P0** | breeding_cycles 테이블 추가 (산차별 사이클) | C-03 |
| **P0** | 작업 순서 검증 (FK NOT NULL 또는 트리거) | C-04 |
| **P0** | CHECK 제약조건 전수 추가 | C-05, C-06 |
| **P0** | pregnancy_checks.farm_id 추가 | C-07 |
| **P1** | 상태 전이 매트릭스 트리거 | M-01 |
| **P1** | farm_configs 테이블 추가 | M-03 |
| **P1** | NPD/PSY 뷰 로직 수정 | M-06, M-07 |
| **P1** | 단위 이중 저장 제거 | M-04 |
| **P2** | FK 인덱스 전수 추가 | m-01 |
| **P2** | soft delete / updated_at 일관성 | m-02, m-03 |
| **P2** | UUID[] → 매핑 테이블 변경 | m-04 |
| **P2** | 모듈 구조 재정의 (Core/Extension/Independent) | 6.2 |

### 9.2 예상 테이블 변경

```
현재 v1: 49 tables + 2 views
v2 예상: ~53 tables + 2 views (수정)

신규 추가:
  + breeding_cycles        (산차별 사이클 관리)
  + reproductive_events    (재발정/유산/사고)
  + piglet_events          (포유중 자돈 이동/폐사)
  + farm_configs           (농장별 번식 파라미터)

기존 수정:
  ~ pregnancy_checks       (farm_id 추가)
  ~ matings                (breeding_cycle_id 추가)
  ~ farrowings             (breeding_cycle_id 추가, mating_id NOT NULL)
  ~ weanings               (breeding_cycle_id 추가, farrowing_id NOT NULL)
  ~ 전체                   (CHECK 제약조건 추가)
  ~ buildings              (deleted_at 추가)
  ~ v_farm_psy             (deleted_at 필터 추가)
  ~ v_sow_npd              (LATERAL 조인으로 수정)

제거:
  - buildings.area_per_pig_sqft
  - feed_deliveries.quantity_lbs
```

---

## 10. 다음 단계

1. **이 리포트 검토/승인** → 수정 범위 확정
2. **스키마 v2 SQL 작성** → 이슈 반영
3. **PostgreSQL 실행 검증** → Docker로 CREATE 실행, 문법 오류 확인
4. **시뮬레이션 테스트** → 위 15개 시나리오 SQL 스크립트 실행
5. **KPI 교차 검증** → 기존 피그플랜 샘플 데이터로 PSY/NPD 대조

---

> 본 리포트는 피그플랜 27년 운영 데이터 모델(Oracle)과 양돈 생산 주기 도메인 지식을
> 기준으로 PigOS DB Schema v1.0을 검증한 결과입니다.
> 스키마 구조는 참고하지 않았으며, 비즈니스 규칙과 데이터 흐름만 대조했습니다.
