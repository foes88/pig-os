# PigOS 국가별 KPI 정의·벤치마크 거버넌스 문서 v3.1

> 목적: 국가별 KPI 임계값 시드 전, 각 지표의 **분자/분모/기간/포함범위/모집단/단위 정의가 출처마다 어떻게 다른지** 1차자료로 검증하고, PigOS 정의와의 호환성을 판정한다. **시드 게이트 + schema migration + seed validator 구현 지시 기준 문서.**
> 작성 기준일: 2026-06-25 / 검증 방식: 1차·준1차 자료 웹검증
> **v3.1 변경점 (GPT 2차 보완 = DB제약/validator 규칙 반영)**: ⑦ benchmark_status↔is_provisional 충돌 금지 ⑧ normalized_verified 6조건 DB 강제 ⑨ period_start/end/publication_date 추가(KR 22.3/22.4/22.5 혼선 차단) ⑩ 다중 원문필드는 obs_group_id+raw_fields_json 보존 명문화 ⑪ threshold 방향별 해석 규칙 고정 ⑫ seed validator 모순 6종 실패처리. → §3.5·§6.1·§7.1 신설.
> **v3 변경점**: ① threshold 단일→min/max 4값 ② value_scale 컬럼 ③ comparison_status 5단계 ④ (kpi_code,definition_id) 복합 FK ⑤ obs_group_id ⑥ 테스트 8종
> 핵심 원칙: **국가 단위 verified가 아니라 KPI 단위 verified.** 출처가 신뢰 가능해도 정의가 다르면 verified 금지. **원문(source_observations)과 PigOS 변환값(benchmarks)은 분리 저장.** transform_formula 없으면 normalized_verified 금지.
>
> **상태: 구조 토론 수렴 완료. 이 문서는 구현 직전 최종본.** 남은 블로커(D-6 한돈팜스 PDF, D-7/D-8 코드확인)는 문서 토론으로 풀 수 없으며 1차자료·코드확인 필요.

---

## 0. 요약 (3줄)

1. **PSY 분모가 국가별로 갈린다.** 한국·EU=평균사육모돈, 미국=교배모돈. 이름 같아도 분모 다르면 다른 KPI. → comparison_status로 차단.
2. **사산율은 PigOS 정의(미라 포함)와 완전일치 출처는 드물지만, 사산·미라 분리 제공 출처(PigCHAMP 등)는 재정규화로 normalized_verified.** "무조건 missing"은 과한 단정(v2 수정).
3. **direction·value_scale·threshold범위는 KPI 본질 속성.** 없으면 lower_better 역발화(NPD 역전), 100배 오류(9.93%↔0.0993), range_target(도태율) 표현불가. → kpi_definitions에 박고 benchmark는 참조·검증.

### 현재 상태 (GPT 토론용)

| 항목 | 상태 |
|---|---|
| 구조·스키마·정의 | ✅ 수렴 완료 (v1→v3.1, 4라운드) |
| DB제약·validator 규칙 | ✅ v3.1에서 명문화 (§3.5) |
| 다음 단계 | schema migration SQL + seed validator 코드 (문서 토론 아님) |
| **미해결 — 1차자료 필요** | D-6 한돈팜스 공식 PDF (KR 22.3/22.4/22.5 확정) |
| **미해결 — 코드 확인 필요** | D-7 KR전용 6종 발화룰 여부 / D-8 validator 7 vs 8 |
| **미확보 — 시드 금지** | BR(Agriness)·VN(WEPIG)·CN·TH·MX 1차 수치 |

> GPT에게: 이 문서에서 **새로운 P0 구조결함**이 보이면 지적해 주십시오. 단 컬럼 네이밍·"추가하면 좋은" 수준이면 구현 단계로 넘어가는 게 맞습니다(토론 한계효용 수렴). 미해결 3종(D-6/7/8)은 토론으로 못 푸는 항목이니 제외.

---

## 1. 핵심 쟁점

### 쟁점 A — PSY 분모 불일치

| 출처 | 지표명 | 분자 | 분모 | denominator_type | period_basis |
|---|---|---|---|---|---|
| 한국 한돈팜스 | PSY | 이유자돈수 | 상시모돈(평균사육모돈) | avg_inventory_sow | annual(×12) |
| EU/GB InterPIG | pigs weaned/sow/yr | 이유두수 | 평균사육모돈(연중일평균) | avg_inventory_sow | annual |
| 미국 PigCHAMP/SMS | PW**M**FY | 이유두수 | **교배모돈** | mated_female | rolling_365환산 |

- 한국 PSY ↔ EU PWSY: 분모 호환(둘 다 avg_inventory_sow). InterPIG "average present sows 기준" 표준화 명시.
- 미국 PWMFY ↔ 한국/EU PSY: **분모 비호환.** + 미국 내부 계산식 3종(NPPC/litters×pigs/재고140일전), 동일농장 26.32 vs 26.66.
- 조치: denominator_type 불일치 → comparison_status='incompatible' → 발화 금지.

### 쟁점 B — 사산율 (재정규화 가능)

PigOS = (사산+미라)/총산. 외부 대부분 미라 제외하나, **분리 제공 시 재정규화.**

| 출처 | 분자 | PigOS 직접일치 | 재정규화 |
|---|---|---|---|
| PigOS | 사산+미라 | (기준) | — |
| **PigCHAMP USA** | 사산·미라 **분리** | ✗(집계는 미라제외) | **○ normalized_verified** |
| 표준 학술/요약 | 사산만 | ✗ | 분리 안되면 ✗ |
| AHDB/NADIS | 사산만(목표5~7%) | ✗ | 원자료 분리 시 |

**1차 검증 (PigCHAMP USA 2025 Spring 원문):**
- Total pigs born = 86157.32 / Total stillborn = 5526.13 / Total mummified = 3031.06 (분리 제공 확인)
- PigOS식 재계산: (5526.13+3031.06)/86157.32 ≈ **9.93%** (집계합산 기반. 정밀도는 농장단위 가중 권장 — D-5)
- transform_formula 필수 기록.

### 쟁점 C — direction은 KPI 정의 원천값

국가별로 안 변함. kpi_definitions에 1번, benchmark override 금지(불일치 시 fail).

| direction | KPI |
|---|---|
| higher_better | PSY, MSY, 분만율, 이유두수, 모돈회전율, 이유전/후육성률 |
| lower_better | NPD, 사산율, 미라율, 이유전/후폐사율, 도폐사율, FCR, WSI |
| range_target | 후보돈 갱신율/도태율(상·하단 양쪽) |

규칙: direction 없는 KPI는 비교 금지 + verified 금지.

### 쟁점 D — 모집단·기간 메타

같은 avg_inventory_sow라도 period(연간/분기/rolling)·population(전국/조합/전문사용자/상위10%) 다르면 비교 불가. 실증: 부경 27.3(조합) vs 전국 22.4. → period_basis·population_scope·comparison_status.

### 쟁점 E — value_scale (100배 오류) ★v3 신규

사산율 9.93이 9.93%(percent_0_100)인지 0.0993(ratio_0_1)인지 컬럼만으론 불명. Rule Engine이 혼동하면 993% 해석 → 전 농장 오탐. → **value_scale 컬럼 필수. 없으면 비교 금지.**

### 쟁점 F — threshold 범위 (range_target 표현) ★v3 신규

단일 threshold로는 range_target(도태율: 너무 낮아도 노령화, 너무 높아도 비용) 표현 불가. → warning_min/max·critical_min/max.

---

## 2. KPI 정의서 (kpi_definitions 원천)

### 2.1 higher_better

| kpi_code | 한글명 | 분자 | 분모 | denom_type | period | direction | unit | value_scale |
|---|---|---|---|---|---|---|---|---|
| psy | 모돈두당연간이유두수 | 총이유두수 | 평균사육모돈 | avg_inventory_sow | rolling_365 | higher_better | head_per_sow_year | n/a |
| msy | 모돈두당연간출하두수 | 총출하두수 | 평균사육모돈 | avg_inventory_sow | rolling_365 | higher_better | head_per_sow_year | n/a |
| farrowing_rate | 분만율 | 분만복수 | 교배복수 | litter | period | higher_better | percent | percent_0_100 |
| weaned_per_litter | 복당이유두수 | 이유두수 | 이유복수 | litter | period | higher_better | head | n/a |
| sow_turnover | 모돈회전율 | 분만복수 | 평균사육모돈 | avg_inventory_sow | rolling_365 | higher_better | turns | n/a |
| prewean_survival | 이유전육성률 | 이유두수 | 포유개시두수 | piglet | period | higher_better | percent | percent_0_100 |
| postwean_survival | 이유후육성률 | 출하두수 | 이유두수 | piglet | period | higher_better | percent | percent_0_100 |

### 2.2 lower_better

| kpi_code | 한글명 | 분자 | 분모 | denom_type | direction | unit | value_scale | 비고 |
|---|---|---|---|---|---|---|---|---|
| npd | 비생산일수 | 비생산일수합 | 평균사육모돈 | avg_inventory_sow | lower_better | days | n/a | gilt_entry_included 플래그(D-1) |
| stillbirth_rate | 사산율 | 사산+미라 | 총산 | total_born | lower_better | percent | percent_0_100 | PigOS 비표준 분자 |
| mummy_rate | 미라율 | 미라 | 총산 | total_born | lower_better | percent | percent_0_100 | |
| prewean_mortality | 이유전폐사율 | 이유전폐사 | 포유개시두수 | piglet | lower_better | percent | percent_0_100 | US14~17/GB12.5/DK20 |
| postwean_mortality | 이유후폐사율 | 이유후폐사 | 이유두수 | piglet | lower_better | percent | percent_0_100 | |
| sow_mortality | 모돈폐사율 | 모돈폐사 | 평균사육모돈 | avg_inventory_sow | lower_better | percent | percent_0_100 | US12.6 상승 |
| fcr | 사료요구율 | 사료급여량 | 증체량 | weight | lower_better | kg_per_kg | ratio | 체중구간 정의필요 |
| wsi | 이유후재교배간격 | 이유~초교배일수 | 교배모돈수 | mated_female | lower_better | days | n/a | KR임계7일 |

### 2.3 range_target

| kpi_code | 한글명 | 분자 | 분모 | direction | unit | value_scale |
|---|---|---|---|---|---|---|
| culling_rate | 모돈도태율/갱신율 | 도태(갱신)모돈수 | 평균사육모돈 | range_target | percent | percent_0_100 |

---

## 3. 스키마 (3-테이블) ★v3 6개 보완 반영

### 3.1 kpi_definitions — KPI 본질 (국가 무관)

```sql
CREATE TABLE kpi_definitions (
  kpi_code          TEXT NOT NULL,
  definition_id     TEXT NOT NULL,        -- 예: PIGOS_PSY_V1
  name_ko           TEXT,
  numerator_def     TEXT NOT NULL,
  denominator_def   TEXT NOT NULL,
  denominator_type  TEXT NOT NULL,        -- avg_inventory_sow|mated_female|farrowed_female|litter|piglet|total_born|weight
  period_basis      TEXT NOT NULL,        -- rolling_365|annual|quarterly|period
  direction         TEXT NOT NULL CHECK (direction IN ('higher_better','lower_better','range_target')),
  unit              TEXT NOT NULL,        -- percent|ratio|head|head_per_sow_year|days|kg_per_kg|turns
  value_scale       TEXT,                 -- percent_0_100|ratio_0_1|n/a  ★⑥ 없으면 Rule Engine 비교 금지
  notes             TEXT,
  PRIMARY KEY (kpi_code, definition_id),  -- ★④ 복합키
  UNIQUE (kpi_code, definition_id)
);
```

### 3.2 source_observations — 외부 원문 (변환 전, 가공 금지)

```sql
CREATE TABLE source_observations (
  obs_id            SERIAL PRIMARY KEY,
  obs_group_id      TEXT,                 -- ★⑤ 변환근거 묶음. 예: PIGCHAMP_USA_2025_SPRING_REPRO_TABLE
  source_id         TEXT NOT NULL,        -- 예: PIGCHAMP_USA_2025
  source_name       TEXT, source_year INT, source_url TEXT,
  -- ★⑨ period 식별 (KR 22.3/22.4/22.5 혼선 차단: 4분기 vs 12개월 vs 기사요약 vs 1~9월잠정)
  period_start      DATE,
  period_end        DATE,
  publication_date  DATE,
  country_code      TEXT,
  source_kpi_code   TEXT, source_kpi_label TEXT,
  source_value      NUMERIC,              -- 원문 수치 그대로
  source_numerator  TEXT, source_denominator TEXT,
  source_denominator_raw TEXT,            -- present_sow 등 모호표기 보존
  population_scope  TEXT,                 -- national_avg|coop_avg|pro_user|top10|top1|...
  period_basis      TEXT,
  source_value_scale TEXT,                -- 원문 단위 스케일
  is_provisional    BOOLEAN DEFAULT FALSE,
  confidence_level  TEXT,                 -- A|B|C
  raw_fields_json   JSONB,                -- ★⑩ 분리항목(stillborn/mummified/total_born). normalized 계산에 필요한 다중 원문필드는 동일 obs_group_id의 이 컬럼에 보존. source_obs_id 단일참조만으로 transform_formula 검증 완료로 보지 않는다.
  notes             TEXT
);
```

> ★⑩ 명문 규칙: 사산율처럼 여러 원문 필드(total_born, stillborn, mummified)로 1개 KPI를 만드는 경우, 같은 `obs_group_id`로 묶고 `raw_fields_json`에 전 필드를 보존한다. `source_obs_id` 단일 참조만으로 normalized 계산 근거를 검증한 것으로 처리하지 않는다. (B안 benchmark_sources 테이블 신설 대신 현 구조 A안 채택 — 사산율 3필드 때문에 테이블 추가는 과함.)

### 3.3 benchmarks — PigOS 변환값만

```sql
CREATE TABLE benchmarks (
  bench_id          SERIAL PRIMARY KEY,
  country_code      TEXT NOT NULL,
  production_system TEXT DEFAULT 'all',   -- MVP 'all', GB만 예외(D-3)
  farm_size_band    TEXT DEFAULT 'all',
  kpi_code          TEXT NOT NULL,
  definition_id     TEXT NOT NULL,
  transformed_value NUMERIC,              -- PigOS 정의로 변환된 값(원문 아님)
  transform_formula TEXT,                 -- 예: '(stillborn+mummified)/total_born*100'. 없으면 normalized_verified 금지
  value_scale       TEXT,                 -- ★⑥ transformed_value 스케일. percent_0_100|ratio_0_1
  source_obs_id     INT REFERENCES source_observations(obs_id),
  obs_group_id      TEXT,                 -- ★⑤ 변환근거 추적
  -- ★① threshold 범위 (range_target 지원)
  warning_min       NUMERIC, warning_max  NUMERIC,
  critical_min      NUMERIC, critical_max NUMERIC,
  target            NUMERIC,
  -- 검증 메타
  mapping_status    TEXT CHECK (mapping_status IN ('exact','normalized','incompatible','unknown')),
  comparison_status TEXT CHECK (comparison_status IN ('exact','compatible','normalized','incompatible','unknown')), -- ★③
  benchmark_status  TEXT DEFAULT 'missing'
                    CHECK (benchmark_status IN ('verified','normalized_verified','provisional','missing','global_fallback')),
  is_provisional    BOOLEAN DEFAULT FALSE,
  notes             TEXT,
  -- ★④ 복합 FK: kpi_code/definition_id 불일치 시 seed 실패
  FOREIGN KEY (kpi_code, definition_id) REFERENCES kpi_definitions(kpi_code, definition_id)
);
```

**★③ comparison_status 판정 (boolean 대체):**
- `exact`: denom_type·period·population 모두 일치 → 비교 가능
- `compatible`: 환산 가능(예: PigOS rolling_365 ↔ 외부 annual) → 비교 가능
- `normalized`: 정의 변환 완료(예: 사산율 재계산) → 비교 가능
- `incompatible`: 분모종류 다름(예: PWMFY) → **비교 금지**
- `unknown`: 정보 부족 → **비교 금지**
- Rule Engine: exact/compatible/normalized만 발화. incompatible/unknown 침묵.

### 3.4 적용 예시

**미국 PWMFY → PSY (분모 비호환):**
```
source_observations: {obs_group_id: PIGCHAMP_USA_2025_REPRO, source_kpi_code: PWMFY,
                      source_value: 27.1, source_denominator: mated_female, population_scope: national_avg}
benchmarks:          {kpi_code: psy, transformed_value: NULL, mapping_status: incompatible,
                      comparison_status: incompatible, benchmark_status: missing}
→ PSY칸 시드 금지, 발화 금지
```

**PigCHAMP 사산/미라 → stillbirth_rate (재정규화):**
```
source_observations: {obs_group_id: PIGCHAMP_USA_2025_REPRO, population_scope: national_avg,
                      raw_fields_json: {stillborn: 5526.13, mummified: 3031.06, total_born: 86157.32}}
benchmarks:          {kpi_code: stillbirth_rate, transformed_value: 9.93, value_scale: percent_0_100,
                      transform_formula: '(stillborn+mummified)/total_born*100',
                      mapping_status: normalized, comparison_status: normalized,
                      benchmark_status: normalized_verified}
→ 재계산 가능 → normalized_verified (transform_formula·value_scale 기록됨)
```

---

## 3.5 DB 제약 / Seed Validator 필수 규칙 ★v3.1 신설

> GPT 2차 보완. 문장이 아니라 DB CHECK·validator로 강제해야 새 seed가 뚫지 못함.

### ★⑦ benchmark_status ↔ is_provisional 충돌 금지

| benchmark_status | is_provisional | transformed_value |
|---|---|---|
| verified | **false 강제** | NOT NULL |
| normalized_verified | **false 강제** | NOT NULL |
| provisional | true 허용 | NOT NULL 권장 |
| missing | — | NULL 허용 |
| global_fallback | — | NULL 허용 |

→ `verified`/`normalized_verified`인데 `is_provisional=true`면 seed 실패.

### ★⑧ normalized_verified 6조건 (전부 충족, DB/validator 강제)

```
benchmark_status='normalized_verified' 이면 다음 전부:
  1. transform_formula IS NOT NULL
  2. mapping_status='normalized'
  3. comparison_status='normalized'
  4. transformed_value IS NOT NULL
  5. value_scale IS NOT NULL
  6. source_obs_id 또는 obs_group_id 존재
하나라도 누락 → seed 실패
```

### ★⑪ threshold 방향별 해석 규칙 (direction별 읽는 칸 고정)

> min/max 4칸을 만들어도 어느 direction이 어느 칸을 읽는지 안 박으면 구현자가 반대 해석.

| direction | warning 발화 | critical 발화 | 보통 NULL인 칸 |
|---|---|---|---|
| **higher_better** | 값 < warning_min | 값 < critical_min | warning_max, critical_max |
| **lower_better** | 값 > warning_max | 값 > critical_max | warning_min, critical_min |
| **range_target** | 값 < warning_min **또는** 값 > warning_max | 값 < critical_min **또는** 값 > critical_max | 없음(4칸 모두 사용) |

예: PSY(higher_better)는 warning_min 미만에서 경고. NPD(lower_better)는 warning_max 초과에서 경고. culling_rate(range_target)는 양방향.

### ★⑫ seed validator 모순 6종 실패처리

```
다음은 전부 seed 실패:
  1. benchmark_status='verified' 인데 comparison_status ∉ {exact, compatible}
  2. benchmark_status='normalized_verified' 인데 comparison_status≠'normalized'
  3. benchmark_status='verified' 인데 transform_formula가 필요한 KPI (정의불일치 재정규화 대상)
  4. benchmarks.value_scale ≠ kpi_definitions.value_scale
  5. transformed_value IS NOT NULL 인데 benchmark_status='missing'
  6. comparison_status ∈ {incompatible, unknown} 인데 transformed_value/threshold가 발화 가능 상태
```

---



## 4. 검증된 출처별 수치 (시드 후보 — 확정 아님)

### 4.1 EU/GB (InterPIG/AHDB 2024)

| 지표 | 값 | 연도 | 모집단 | 판정 |
|---|---|---|---|---|
| weaned/sow/yr (EU) | 30.27 | 2024 | InterPIG EU | provisional* |
| weaned/sow/yr (GB indoor) | 28.0 | 2024 | GB실내 | provisional* |
| weaned/sow/yr (GB outdoor) | 24.6 | 2024 | GB실외 | provisional* |
| finished/sow/yr (GB indoor) | 26.8 | 2024 | GB실내 | provisional* |
| finished/sow/yr (EU) | 29.22 | 2024 | InterPIG EU | provisional* |

*production_system 분리돼야 의미(indoor28.0 vs outdoor24.6, 4두차). MVP country단위 → D-3 결정 전 verified 불가. InterPIG 분모는 한국 상시모돈과 호환.

### 4.2 한국 (한돈팜스) — period/source 분리 필수, 전부 provisional

| 지표 | 값 | 기간/모집단 | 판정 |
|---|---|---|---|
| PSY | 22.4 | 2025 전국(기사) | is_provisional |
| PSY | 22.5(추정) | 2025 12개월평균(GPT주장) | **원문확인필요** |
| PSY | 22.3(추정) | 2025 4분기 | **원문확인필요** |
| MSY | 18.9 | 2025 전국(기사) | is_provisional |
| MSY | 18.8(추정) | 2025 12개월(GPT주장) | **원문확인필요** |
| 분만율 | 85.7% | 2025 전국 | is_provisional |
| PSY(전문사용자) | 24.2 | 2025 | population_scope=pro_user |
| PSY/NPD(상위1%) | 32.3/29.9일 | 2025 | population_scope=top1, 임계참고 |
| PSY(부경조합) | 27.3 | 2025 조합 | population_scope=coop, 전국과 분리 |

→ 22.3/22.4/22.5 셋 다 출처·기간 다름, 1차 발표자료 원문 미확인. **전부 provisional. 한돈팜스 공식 PDF 확보 후 period별 verified.** KR은 한국 내수 제외 → 데이터 출처로만, 발화 룰은 분리(D-7).
**★v3.1**: 위 혼선은 `period_start`/`period_end`/`publication_date`로 구분 저장(§3.5 ⑨). 예: (2025-01-01~2025-12-31, 12개월평균) vs (2025-10-01~2025-12-31, 4분기) vs (2024-01-01~2024-09-30, 잠정). source_year만으로는 전부 "2025"라 구분 불가.

### 4.3 미국 (PigCHAMP USA 2025) — 1차 검증 완료

| 원문 지표 | 값 | PigOS 매핑 | 판정 |
|---|---|---|---|
| Total pigs born | 86157.32 | (사산율 입력) | source_observations |
| Total stillborn | 5526.13 | (사산율 분자) | source_observations |
| Total mummified | 3031.06 | (사산율 분자) | source_observations |
| → stillbirth_rate 재계산 | ≈9.93% | stillbirth_rate | **normalized_verified 후보** |
| Farrowing rate | 83.81% | farrowing_rate | verified 후보 |
| Pre-weaning mortality | 14.17% | prewean_mortality | verified 후보(모집단주의) |
| Average total pigs/litter | 15.96 | 복당총산 | verified 후보 |
| PWMFY | 27.1(2024) | psy **금지** | missing(분모=교배모돈) |

→ 같은 출처에서 KPI별 판정 갈림(사산율 normalized / 분만율 verified / PWMFY missing) = "KPI 단위 verified" 실증.

### 4.4 BR/VN/CN/TH/MX — 1차자료 미확보, 시드 금지

Agriness(BR)·WEPIG(VN)·중국·태국·멕시코 미확인. 등급배분 방향(BR=Agriness, VN/CN혼합, TH/MX fallback) 동의하나 수치 원문 확보 후. 미확보 시드 금지(위조 0).

---

## 5. 미해결 결정 질문 (사용자/현장 확인 필요 — 코드 임의결정 금지)

> ★ 이 절이 v3에서 가장 중요. 문서 토론으로는 더 못 풀고, **실측·코드확인·1차자료**만 풀 수 있는 것들.

| # | 질문 | 푸는 방법 | 잠정 권고 |
|---|---|---|---|
| D-1 | NPD 후보돈 초교배까지 포함? | **코드/내부정책 확인** | 내부정의 1개 고정 + gilt_entry_included 플래그 |
| D-2 | MSY "출하" 기준시점? | 내부정의 확인 | 판매두수 고정, EU finished 대응 |
| D-3 | GB country단위 시 indoor/outdoor/평균? | 결정 | MVP 'GB_indoor' 명시 또는 system 예외 |
| D-4 | 미국 PWMFY를 PSY 재정규화 vs 별도? | 결정 | 별도 pwmfy, PSY missing(분모변환계수 농장마다 달라 불가) |
| D-5 | 사산율 normalized: 농장단위가중 vs 집계합산? | 결정 | 가능하면 농장단위 가중, formula 명시 |
| D-6 | KR 2025 PSY 22.3/22.4/22.5 중? | **한돈팜스 공식 PDF 1차확보** | period별 분리, 전부 provisional까지 |
| D-7 | KR전용 6종 = 발화룰 vs 데이터출처? | **코드 확인** | 발화룰이면 글로벌서 분리 |
| D-8 | validator 7개 vs 8개? 8번째? | **코드 확인** | 미해결(3라운드째) |
| D-9 | production_system MVP 'all'고정, GB예외? | 결정 | 컬럼생성, GB만 주석 |
| D-10 | 손실액(MSD) MVP vs P2? | 결정 | P2(연도·환율·가정 민감) |
| D-11 | source_obs↔benchmarks 분리 시점? | 결정 | MVP부터 분리(채택) |
| D-12 | comparison_status 판정 로직? | 결정 | 5단계, exact/compatible/normalized만 발화(v3 반영) |

---

## 6. verified 게이트 (KPI 단위)

전부 충족해야 `verified`:
1. source_name/year/url 확인
2. 모집단 확인(country·production_system·population_scope·size)
3. source_kpi_code ↔ pigos_kpi_code 매핑 확인
4. 분자/분모/기간/포함범위가 kpi_definitions와 일치(불일치→재정규화→normalized_verified)
5. direction이 kpi_definitions와 일치(override 금지)
6. denominator_type 일치
7. period_basis·population_scope 일치 또는 comparison_status∈{exact,compatible,normalized}
8. **value_scale 명시** ★v3
9. Rule Engine 방향·스케일 테스트 존재(§7)

`normalized_verified` 추가조건: §3.5 ★⑧ 6조건 전부 충족(transform_formula가 source_observations/obs_group_id 기반 기록).
`verified`/`normalized_verified`는 §3.5 ★⑦에 따라 is_provisional=false 강제.
하나라도 빠지면 confidence 'A'여도 verified 금지.

---

## 7. 필수 테스트 (★⑥ 명시 — Codex/Claude가 빠뜨리지 못하게)

```
1. lower_better KPI: 값↑일수록 severity↑ (NPD/사산율/폐사율/FCR)
2. higher_better KPI: 값↓일수록 severity↑ (PSY/MSY/분만율)
3. range_target KPI: warning_min 미만·warning_max 초과에서 severity↑ (도태율)
4. comparison_status∈{incompatible,unknown}이면 insight 생성 금지
5. benchmark_status별(missing/global_fallback/provisional/verified/normalized_verified) UI 표시 확인
6. normalized_verified인데 transform_formula 없으면 seed 실패
7. (kpi_code, definition_id) 불일치 시 seed 실패 (복합 FK)
8. value_scale 누락 또는 percent_0_100↔ratio_0_1 혼용 시 비교 차단
```

### 7.1 추가 테스트 ★v3.1 (DB제약/validator 모순)

```
9.  benchmark_status='verified'인데 is_provisional=true → seed 실패 (★⑦)
10. normalized_verified인데 6조건(★⑧) 중 하나라도 누락 → seed 실패
11. higher_better는 warning_min, lower_better는 warning_max, range_target은 양방향 칸을 읽는지 (★⑪)
12. benchmarks.value_scale ≠ kpi_definitions.value_scale → seed 실패 (★⑫-4)
13. transformed_value 있는데 benchmark_status='missing' → seed 실패 (★⑫-5)
14. comparison_status∈{incompatible,unknown}인데 threshold 발화가능 상태 → seed 실패 (★⑫-6)
15. period_start/end 다른데 같은 (country,kpi)로 verified 중복 → 경고 (KR 22.3/22.4/22.5 케이스)
```

---

## 8. 권고 작업 순서

```
1. KR 27종 역검증 (이미 시드됨 → 정의·방향·분모·모집단·value_scale 통과 여부)
   └ 우선: 사산율(미라포함?)·NPD(후보돈?)·lower_better방향·population_scope(전국vs조합)·percent스케일
2. KPI 정의서 확정 (§2 → docs/KPI_DEFINITIONS.md)
3. 3-테이블 스키마 + 복합FK + 제약 구축 (§3)
4. seed validator 작성 (§6 게이트 + §7 테스트)
5. D-1~D-12 결정 (특히 D-6/D-7/D-8은 1차자료·코드 확인)
6. US → source_observations 적재 → 사산율 normalized_verified, 분만율 verified, PWMFY missing
7. EU/GB → D-3 결정 후 provisional
8. KR → 한돈팜스 공식 PDF 확보 → period/scope 분리 시드
9. BR/VN/CN → 1차자료 확보 후
10. TH/MX → global_fallback
```

---

## 9. 출처 목록

| # | 출처 | 확인 내용 | 연도 |
|---|---|---|---|
| 1 | **PigCHAMP USA Benchmark 2025 Spring 원문** | total born 86157.32/stillborn 5526.13/mummified 3031.06/farrowing 83.81/prewean 14.17 — 사산·미라 분리 확인 | 2024데이터 |
| 2 | AHDB "2024 COP Overview" | EU30.27/GB indoor28.0/outdoor24.6/finished26.8·29.22 | 2024 |
| 3 | AHDB COP 2015·2021 | InterPIG 표준화 "sow=초교배~도태, average present sows" | 2015,21 |
| 4 | 한돈팜스/팜인사이트 | 2025 전국 PSY22.4·MSY18.9·분만율85.7%/상위1% NPD29.9일 | 24,25 |
| 5 | 돼지와사람 | KR PSY/MSY산식(상시모돈분모), NPD후보돈변수/부경27.3(조합) | 18,25 |
| 6 | National Hog Farmer/SMS | PWMFY분모=교배모돈, 계산식3종(26.32vs26.66) | 22~25 |
| 7 | NADIS/The Pig Site | 영국사산 총산5~7%(미라제외) | — |
| 8 | Porcine Health Mgmt(학술) | PWSY정의, 사산율=사산/총산 | 2017 |
| 9 | 학술(사산연구) | total born=생존+사산+미라 | 20~24 |

---

### 부기

- 본 문서 수치는 **시드 후보**. §5 결정·§6 게이트 통과 전 시드 금지.
- 원문은 source_observations, PigOS 변환값만 benchmarks. transform_formula·value_scale 없으면 normalized_verified 금지.
- 미확보 국가 추정·생성 금지(위조 0).
- KR 2025(22.3/22.4/22.5) 전부 provisional. 한돈팜스 공식 PDF 확보 후 verified.
- "MVP"는 외부 금지어(내부 문서라 사용). 대외 전환 시 "무료 출시/공개 출시".

---

### 변경 이력
- v1: 초안(정의·쟁점·D질문) — 문제의식 문서
- v2: 3-테이블 분리, direction→definitions, period/population, 사산율 normalized(PigCHAMP 1차검증), KR provisional — 구조 설계 문서
- v3: threshold범위(range_target), value_scale(100배오류방지), comparison_status 5단계, 복합FK, obs_group_id, 테스트8종 — 구현 가능 거버넌스 문서
- **v3.1: benchmark_status↔is_provisional 충돌금지, normalized_verified 6조건 DB강제, period_start/end/publication_date, 다중원문필드 명문화, threshold 방향규칙, validator 모순6종 — 구현 직전 최종본**

### 토론 수렴 기록
- 지적 성격이 라운드마다 한 단계씩 하강: **방향(v1) → 구조(v2) → 컬럼(v3) → DB제약·validator(v3.1)**. 다음 단계는 실제 SQL/코드이며 문서 토론 영역 아님.
- 남은 블로커는 토론 불가: **D-6**(한돈팜스 공식 PDF 1차확보), **D-7**(KR전용 6종 발화룰 여부 코드확인), **D-8**(validator 7 vs 8 코드확인). GPT·Claude 모두 한돈팜스 원문/PigOS 코드 접근 불가 → 사용자만 해결 가능.

---

## 10. v3.2 업데이트 — 한돈팜스 2025 공식 PDF 확보 (D-6 해결)

> 2026-06 1차자료 입수 반영. 기존 §1~§9는 PDF 입수 전 설계이며, 본 섹션이 KR 시드에 대한 **최신 확정 상태**다. 충돌 시 §10 우선.

### 10.1 입수 자료 (1차자료)

- **「한돈팜스 전국 한돈농가 2025년 전산성적」** (분석: 한돈연구소, 발행: 2026-05, 대한한돈협회/한돈자조금)
- **내부 입수본 — 외부 공개·재배포 금지.** source_observations에 메타데이터·검증수치만 저장, PDF 원본/이미지/캡처 저장 금지.
- KR 벤치마크는 **PigOS 내부 참조용(글로벌 fallback)**. PigOS 한국 서비스 노출 경로 없음(내수=PigPlan), PigSignal 외부 API 적재 금지.

### 10.2 D-6 해결 — KR 정의·기간·모집단 확정 (PDF p.12/p.11/p.20/p.90/p.96)

| 항목 | 확정값 | 근거 |
|---|---|---|
| **PSY 분모** | 상시모돈두수 (avg_inventory_sow) | p.12 "PSY=당월이유자돈수×12/상시모돈두수" |
| **MSY 분모/기준** | 상시모돈, "당월비육출하두수" 기반 | p.12 (D-2 KR 확인: 비육출하두수) |
| **평균 방식** | 가중하지 않은 농장단위 산술평균 | p.12 (D-5 사실관계: KR=비가중 단순평균) |
| **기간** | 2025-01-01~12-31 연간 확정치 | p.11 (10개월+ 등록), p.96 발행 2026-05 |
| **모집단** | 전국 일반사용자 2,655호 (등록3,818/모돈814천두) | p.11, p.20 |

→ **PSY=22.4는 전국 연간확정 단일값.** v3.1 §부기의 "22.3/22.4/22.5 케이스"는 **22.4(전국 연간)로 종결.** 22.3/22.5는 기사 짜깁기 허수로 1차자료에 없음. §7-15 period 중복경고 룰은 KR엔 해당 없음(단일 period).
→ denominator=상시모돈 → **EU/GB InterPIG(average present sows)와 호환** (comparison_status=compatible). 미국 PWMFY(mated_female) 비호환 유지.

### 10.3 KR 시드 확정 (작업 C)

**verified 승격 — population_scope=national_general (전국 일반사용자), comparison_status=compatible:**

| kpi_code | 값 | value_scale | direction |
|---|---|---|---|
| psy | 22.4 | n/a | higher_better |
| msy | 18.9 | n/a | higher_better |
| farrowing_rate | 85.7 | percent_0_100 | higher_better |
| preweaning_survival | 89.1 | percent_0_100 | higher_better |
| postweaning_survival | 84.3 | percent_0_100 | higher_better |
| weaned_per_litter | 10.45 | n/a | higher_better |
| sow_turnover | 2.14 | n/a | higher_better |

**드롭/제외 (시드 안 함):**
- `total_born`(복당총산 11.73): kpi_definitions에 KPI 코드 없음 — DENOMINATOR_TYPES 분모유형으로만 존재. **orphan, 코드 신설은 별건.**
- `market_age`(출하일령 195): PigOS rule engine 28종·kpi_definitions 16종 모두 미등록. PigPlan엔 SHIP_AGE 있으나 PigOS 타겟 부재 → **드롭.**
- `npd`: 전국 일반사용자 표에 NPD 컬럼 없음 → **missing 유지.**

### 10.4 사산율 — 정의 일치 확정, 단 전국은 missing 유지

**정의 일치 (잔차 구조):**
- KR 표준 항등식: **총산 = 실산(born alive) + 사산 + 미라**
- 잔차(총산−생존) = 사산+미라 — 라벨이 "복당사산"이어도 잔차라서 미라 자동 포함
- 전문사용자(p.64): 복당사산 1.27 / 복당총산 13.62 → **1.27/13.62 = 9.3% = (사산+미라)/총산 = PigOS stillbirth_rate 정의 일치**
- comparison_status: ~~unknown~~ → **compatible** (라벨 명명 문제 아니라 잔차 정의 일치)
- **검증 전제(메타 명시 필수): "복당생존=born alive(실산)" — KR표준 총산분해 잔차 해석. 복당이유(11.03)가 별도 컬럼이므로 생존=이유전 실산으로 판단.**

**단 — 전국 stillbirth_rate는 missing 유지:**
- 9.3%는 **전문사용자 229호 모집단** 값. 전국 일반사용자 표엔 사산 원자료 없음.
- → population_scope=`professional` 별도 obs_group으로만 normalized_verified 적재. transform_formula=복당사산/복당총산.
- **전국 대표 슬롯(national_general) 사산율을 9.3%로 채우기 금지** (모집단 혼입). B의 missing 판정 유지.

### 10.5 D-결정 현황 갱신 (PDF 반영 후)

| # | 질문 | 상태 | 비고 |
|---|---|---|---|
| **D-6** | KR 정의·period | ✅ **해결** | 전국 22.4 연간확정, 상시모돈 분모 (§10.2) |
| **D-2** | MSY 출하 기준 | ✅ KR 확인 | 비육출하두수 (US 정의 별도 재확인) |
| **D-5** | 사산율 가중/집계 | ⚠️ 사실확정 | 한돈팜스=비가중 농장단위 단순평균. PigOS 정책은 열림 |
| **D-1** | NPD 후보돈 포함 | 🟡 미해결 | **단 KR verified 무관** — 전국 NPD 데이터 없어 어차피 missing. 작업 C 안 막음 |
| **D-4** | PWMFY 별도 vs 재정규화 | 🟡 미해결 | 잠정: 별도(pwmfy), PSY missing. US 적재 전 |
| **D-3·D-9** | GB production_system | 🟡 미해결 | 잠정: GB_indoor. EU/GB 적재 전(후순위) |
| **D-7** | KR 원화누수 | ✅ 끝 | 출시前 분리, P2 일반화 |
| **D-8** | validator 개수 | ✅ 끝 | 8개(8번째 finisher) |
| **D-10~D-13** | (P2/분리/5단계/fcr) | ✅ 끝 | 손실액P2 / 원문·변환분리 / comparison 5단계 / fcr=n/a |

### 10.6 잔여 블로커 (1차자료 미확보 — 코드가 못 채움)

- **앵커마켓 BR(Agriness)·VN(WEPIG)·CN·TH·MX**: 1차 수치 없음 → 해당국 룰 침묵. 시드 금지(위조 0). PDF와 무관, 변동 없음.
- US(PigCHAMP): 확보됨 ✓ — 사산율 normalized 9.93%, 분만율 verified 83.81%, PWMFY→psy missing.

### 10.7 권고 작업 순서 (갱신)

```
[완료] 작업 A 스키마 / 작업 B KR27 재검증 / D-6 PDF 확보
1. 작업 C — KR 7종 verified 승격 + 전문사용자 사산율 obs_group (지금 실행 가능, D-1 무관)
   └ STEP1 kpi_code 존재확인 후 INSERT, STEP5 가드 무결성 재점검(mutation 재발)
2. Codex로 A·B·C 교차검증 (가드 무력화·DB CHECK 실작동) — US 적재 전 권장
3. US PigCHAMP 적재 (D-4 결정 후): 사산율 9.93% normalized / 분만율 83.81% verified / PWMFY→psy missing
4. EU/GB (D-3 결정 후) provisional
5. BR/VN/CN — 1차자료 확보 후 / TH/MX — global_fallback
```

### 변경 이력 (추가)
- **v3.2: 한돈팜스 2025 공식 PDF 확보 → D-6 해결(KR 전국 22.4 연간확정/상시모돈 분모). KR 7종 verified 승격 확정(작업 C). 사산율 정의일치(잔차구조)로 unknown→compatible, 단 전국 missing 유지(전문사용자 obs_group 한정). total_born/market_age 드롭. D-1이 KR verified 안 막음 확인. 내부자료 외부노출 차단 원칙 추가.**
