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

---

## 1. 핵심 쟁점

### 쟁점 A — PSY 분모 불일치

| 출처 | 지표명 | 분자 | 분모 | denominator_type | period_basis |
|---|---|---|---|---|---|
| 한국 한돈팜스 | PSY | 이유자돈수 | 상시모돈(평균사육모돈) | avg_inventory_sow | annual(×12) |
| EU/GB InterPIG | pigs weaned/sow/yr | 이유두수 | 평균사육모돈(연중일평균) | avg_inventory_sow | annual |
| 미국 PigCHAMP/SMS | PW**M**FY | 이유두수 | **교배모돈** | mated_female | rolling_365환산 |

- 한국 PSY ↔ EU PWSY: 분모 호환(둘 다 avg_inventory_sow).
- 미국 PWMFY ↔ 한국/EU PSY: **분모 비호환.** → comparison_status='incompatible' → 발화 금지.

### 쟁점 B — 사산율 (재정규화 가능)

PigOS = (사산+미라)/총산. 외부 대부분 미라 제외하나, **분리 제공 시 재정규화.**
PigCHAMP USA 2025 Spring: total born 86157.32 / stillborn 5526.13 / mummified 3031.06 → (5526.13+3031.06)/86157.32 ≈ **9.93%**. transform_formula 필수 기록.

### 쟁점 C — direction은 KPI 정의 원천값

| direction | KPI |
|---|---|
| higher_better | PSY, MSY, 분만율, 이유두수, 모돈회전율, 이유전/후육성률 |
| lower_better | NPD, 사산율, 미라율, 이유전/후폐사율, 도폐사율, FCR, WSI |
| range_target | 후보돈 갱신율/도태율(상·하단 양쪽) |

### 쟁점 D — 모집단·기간 메타
period(연간/분기/rolling)·population(전국/조합/전문사용자/상위10%) 다르면 비교 불가. 부경 27.3(조합) vs 전국 22.4.

### 쟁점 E — value_scale (100배 오류) ★v3 신규
9.93이 9.93%(percent_0_100)인지 0.0993(ratio_0_1)인지 불명 → value_scale 필수. 없으면 비교 금지.

### 쟁점 F — threshold 범위 (range_target) ★v3 신규
단일 threshold로 range_target 표현 불가 → warning_min/max·critical_min/max.

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

## 3. 스키마 (3-테이블)

### 3.1 kpi_definitions
```sql
CREATE TABLE kpi_definitions (
  kpi_code TEXT NOT NULL, definition_id TEXT NOT NULL, name_ko TEXT,
  numerator_def TEXT NOT NULL, denominator_def TEXT NOT NULL,
  denominator_type TEXT NOT NULL,  -- avg_inventory_sow|mated_female|farrowed_female|litter|piglet|total_born|weight
  period_basis TEXT NOT NULL,      -- rolling_365|annual|quarterly|period
  direction TEXT NOT NULL CHECK (direction IN ('higher_better','lower_better','range_target')),
  unit TEXT NOT NULL,              -- percent|ratio|head|head_per_sow_year|days|kg_per_kg|turns
  value_scale TEXT,                -- percent_0_100|ratio_0_1|n/a ★⑥
  notes TEXT,
  PRIMARY KEY (kpi_code, definition_id), UNIQUE (kpi_code, definition_id)
);
```

### 3.2 source_observations
```sql
CREATE TABLE source_observations (
  obs_id SERIAL PRIMARY KEY, obs_group_id TEXT, source_id TEXT NOT NULL,
  source_name TEXT, source_year INT, source_url TEXT,
  period_start DATE, period_end DATE, publication_date DATE,  -- ★⑨
  country_code TEXT, source_kpi_code TEXT, source_kpi_label TEXT,
  source_value NUMERIC, source_numerator TEXT, source_denominator TEXT,
  source_denominator_raw TEXT, population_scope TEXT, period_basis TEXT,
  source_value_scale TEXT, is_provisional BOOLEAN DEFAULT FALSE, confidence_level TEXT,
  raw_fields_json JSONB,  -- ★⑩ 분리항목 보존
  notes TEXT
);
```
> ★⑩ 사산율처럼 여러 원문필드(total_born/stillborn/mummified)로 1 KPI 생성 시 동일 obs_group_id + raw_fields_json에 전 필드 보존. source_obs_id 단일참조만으로 transform_formula 검증 완료로 보지 않는다.

### 3.3 benchmarks
```sql
CREATE TABLE benchmarks (
  bench_id SERIAL PRIMARY KEY, country_code TEXT NOT NULL,
  production_system TEXT DEFAULT 'all', farm_size_band TEXT DEFAULT 'all',
  kpi_code TEXT NOT NULL, definition_id TEXT NOT NULL,
  transformed_value NUMERIC, transform_formula TEXT, value_scale TEXT,  -- ★⑥
  source_obs_id INT REFERENCES source_observations(obs_id), obs_group_id TEXT,
  warning_min NUMERIC, warning_max NUMERIC, critical_min NUMERIC, critical_max NUMERIC, target NUMERIC,  -- ★①
  mapping_status TEXT CHECK (mapping_status IN ('exact','normalized','incompatible','unknown')),
  comparison_status TEXT CHECK (comparison_status IN ('exact','compatible','normalized','incompatible','unknown')),  -- ★③
  benchmark_status TEXT DEFAULT 'missing'
    CHECK (benchmark_status IN ('verified','normalized_verified','provisional','missing','global_fallback')),
  is_provisional BOOLEAN DEFAULT FALSE, notes TEXT,
  FOREIGN KEY (kpi_code, definition_id) REFERENCES kpi_definitions(kpi_code, definition_id)  -- ★④
);
```

**★③ comparison_status**: exact/compatible/normalized = 비교가능(발화). incompatible/unknown = 비교금지(침묵).

## 3.5 DB 제약 / Seed Validator (★v3.1)

- **★⑦** verified/normalized_verified → is_provisional=false 강제 + transformed_value NOT NULL.
- **★⑧** normalized_verified 6조건 전부: transform_formula NOT NULL / mapping_status='normalized' / comparison_status='normalized' / transformed_value NOT NULL / value_scale NOT NULL / (source_obs_id 또는 obs_group_id).
- **★⑪** threshold 방향: higher_better=값<warning_min(crit<critical_min) / lower_better=값>warning_max(crit>critical_max) / range_target=양방향.
- **★⑫** seed 실패 6종: ①verified인데 comparison_status∉{exact,compatible} ②normalized_verified인데 comparison_status≠normalized ③verified인데 transform_formula 존재(재정규화 대상) ④benchmarks.value_scale≠kpi_definitions.value_scale ⑤transformed_value 있는데 missing ⑥comparison_status∈{incompatible,unknown}인데 발화가능(threshold/transformed_value).

## 6. verified 게이트 (KPI 단위) — 9조건 전부 충족
1.source 2.모집단 3.kpi매핑 4.정의일치(불일치→normalized_verified) 5.direction일치 6.denominator_type일치 7.period/population 또는 comparison_status∈{exact,compatible,normalized} 8.value_scale명시 9.테스트존재.

## 7. 필수 테스트 (15종) — §7 8종 + §7.1 7종
1.lower_better 값↑→severity↑ 2.higher_better 값↓→severity↑ 3.range_target 양방향 4.incompatible/unknown→insight금지 5.benchmark_status별 UI 6.normalized_verified인데 transform_formula없으면 실패 7.(kpi,def)불일치 복합FK실패 8.value_scale누락/혼용 비교차단 9.verified인데 is_provisional=true 실패 10.normalized_verified 6조건누락 실패 11.방향별 칸읽기 12.value_scale≠kpi_def 실패 13.transformed_value 있는데 missing 실패 14.incompatible/unknown인데 발화가능 실패 15.period 다른데 같은(country,kpi) verified중복 경고.

---

## 부기 / 미해결
- 본 문서 수치는 시드 후보. §5 결정·§6 게이트 통과 전 시드 금지. 미확보 국가(BR/VN/CN/TH/MX) 위조 0.
- KR 2025(22.3/22.4/22.5) 전부 provisional. 한돈팜스 공식 PDF(D-6) 확보 후 verified.
- 미해결: D-6(한돈팜스 PDF) / D-7(KR전용 6종 발화룰 여부) / D-8(validator 7 vs 8) — 1차자료·코드확인 필요.

> 전체 원문(쟁점 상세·출처표·D-1~D-12·적용예시)은 사용자 제공 원본 채팅 기준. 본 파일은 구현에 필요한 핵심을 보존한 작업본.
