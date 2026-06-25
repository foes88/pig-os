# 작업 C — KR 벤치마크 verified 승격 (1차자료: 한돈팜스 2025 전산성적)

## 0. 컨텍스트 / 전제

작업 A(스키마 마이그레이션)·작업 B(KR 27종 재검증) 완료 상태에서 수행한다.
B에서 KR provisional 10종으로 보류했던 항목을, **1차자료(한돈팜스 전국 한돈농가 2025년 전산성적, 한돈연구소, 발행 2026-05)**로 검증하여 verified 승격한다.

**중요 — 1차자료 취급 원칙 (반드시 준수):**
- 이 자료는 **내부 입수본**이다. 외부 공개·재배포 금지.
- `source_observations`에는 **출처 메타데이터와 검증된 수치만** 저장한다. PDF 원본·표 이미지·페이지 캡처를 DB나 repo에 저장하지 말 것.
- KR 벤치마크는 **PigOS 내부 참조용(글로벌 fallback 기준선)**이다. PigOS 한국 서비스 노출 경로 없음(한국 내수는 PigPlan), PigSignal 외부 API에도 적재 금지.

**위조 0 원칙 유지:** 아래 명시된 값·정의 외에 추정/보간 금지. 데이터 없는 KPI는 missing 유지.

**거버넌스 단일 진실소스:** `docs/KPI_GOVERNANCE_v3.1.md` §10(v3.2). 본 프롬프트와 충돌 시 거버넌스 §10 우선. 이 작업은 거버넌스 §10.7 작업순서의 **1번(작업 C)**에 해당.

**D-1(NPD 후보돈 초교배 포함)은 이 작업의 블로커가 아니다.** KR 전국 일반사용자 표에 NPD 컬럼 자체가 없어 NPD는 D-1 결정과 무관하게 missing이다. D-1 미해결을 이유로 작업 C를 중단하지 말 것. (D-1은 NPD를 실제 시드할 모집단/국가가 생길 때 별도 해결)

**후속 작업순서 (이 작업 이후):** 작업 C 완료 → ② Codex로 A·B·C 교차검증(가드 무력화·DB CHECK 실작동) → ③ US PigCHAMP 적재(D-4 결정 후). 본 작업은 운영 미배포 상태로 두고 A·B와 함께 배포 권장.

---

## 1. 검증 결과 요약 (이미 1차자료로 확정됨)

PDF p.12 「항목 계산식」에서 다음이 명시 확인됨:
- **PSY = 당월이유자돈수 × 12 / 상시모돈두수** → denominator_type = `avg_inventory_sow`(상시모돈)
- **MSY = 당월비육출하두수 × 12 / 상시모돈두수**
- **분만율 = 분만복수 / 교배복수 × 100**
- **이유전육성률 = 복당이유두수 / 복당총산자수 × 100**
- **이유후육성률 = MSY / PSY × 100**
- **모돈회전율 = 분만복수 × 12 / 상시모돈두수**
- **평균값은 가중하지 않은 농장단위 산술평균** (단순평균)

→ denominator=상시모돈 → **EU/GB InterPIG(average present sows)와 호환**. 미국 PWMFY(mated_female)와는 비호환(기존 판정 유지).

**모집단/기간 (p.11, p.20, p.90, p.96):**
- 모집단: 전국 **일반사용자 2,655호** (등록 3,818 / 모돈 814천두), 10개월 이상 등록 농가
- 기간: **2025-01-01 ~ 2025-12-31 연간 확정치** (분기·잠정 아님)
- publication_date: 2026-05

---

## 2. 시드 대상 — 전국 일반사용자 verified (7종)

population_scope = `national_general` (전국 일반사용자 2,655호)
benchmark_status = `verified`
comparison_status = `compatible` (denominator=상시모돈, EU/GB와 호환)
period_start = 2025-01-01, period_end = 2025-12-31, publication_date = 2026-05
source = "한돈팜스 전국 한돈농가 2025년 전산성적 (한돈연구소, 2026-05)"

| kpi_code (확인 필요) | KR 전국값 | value_scale | direction | 비고 |
|---|---|---|---|---|
| psy | 22.4 | n/a | higher_better | p.20/90 |
| msy | 18.9 | n/a | higher_better | p.20/90 |
| farrowing_rate | 85.7 | percent_0_100 | higher_better | 분만율, p.20/90 |
| preweaning_survival | 89.1 | percent_0_100 | higher_better | 이유전육성률, p.20 |
| postweaning_survival | 84.3 | percent_0_100 | higher_better | 이유후육성률, p.20 |
| weaned_per_litter | 10.45 | n/a | higher_better | 복당이유, p.20 |
| sow_turnover | 2.14 | n/a | higher_better | 모돈회전율, p.20 |

**※ kpi_code 명칭은 위가 추정치다. 반드시 §5 STEP 1에서 kpi_definitions 실제 등록 코드와 대조 후 사용할 것.**
사전 확인된 정보(직전 점검): `sow_turnover`, `weaned_per_litter`는 kpi_definitions 등록됨. 나머지 5종도 SELECT로 재확인.

---

## 3. 드롭 / missing 유지 (시드하지 않음)

| 항목 | KR 값 | 처리 | 근거 |
|---|---|---|---|
| total_born (복당총산) | 11.73 | **시드 제외(orphan)** | kpi_definitions에 KPI 코드 없음 — DENOMINATOR_TYPES의 분모유형으로만 존재. 복당총산 KPI 신설은 별건. |
| market_age (출하일령) | 195 | **드롭** | PigOS rule engine 28종·kpi_definitions 16종 모두에 출하일령 KPI 없음. (PigPlan엔 SHIP_AGE 있으나 PigOS 타겟 부재) |
| npd (비생산일수) | — | **missing 유지** | 전국 일반사용자 표에 NPD 컬럼 없음(전문사용자만 47.7). **D-1과 무관하게 데이터 부재로 missing** — D-1은 이 작업 블로커 아님. |

**total_born / market_age: kpi_definitions에 신규 코드를 만들지 말 것.** 이번 작업 범위 밖. 단순 시드 제외로 처리하고, 리포트에 "KPI 미등록으로 제외"로 기록.

---

## 4. 전문사용자 사산율 — 별도 obs_group (전국 슬롯 금지)

**전국(일반사용자) 사산율은 missing 유지.** 일반사용자 표에 사산 원자료 자체가 없음. B 판정 유지.

단, **전문사용자(229호) 표에는** 사산 분해가 있어 별도 population obs_group으로 normalized_verified 적재 가능:
- p.64: 복당총산 13.62 / 복당생존 12.35 / 복당사산 1.27 / 복당이유 11.03

**정의 일치 근거 (검증 메타에 반드시 기록):**
- KR 표준 항등식: **총산 = 실산(born alive) + 사산 + 미라**
- 따라서 잔차(총산 − 생존) = 사산 + 미라 — 라벨이 "복당사산"이어도 잔차 구조상 미라 포함
- 1.27 / 13.62 = **9.3% = (사산+미라)/총산 = PigOS stillbirth_rate 정의와 일치**
- **전제(메타에 명시): "복당생존 = born alive(실산)" — KR 표준 총산분해의 잔차 해석. 복당이유(11.03)가 별도 컬럼이므로 생존=이유전 실산으로 판단.**

| 항목 | 값 | population_scope | status | transform_formula | comparison_status |
|---|---|---|---|---|---|
| stillbirth_rate | 9.3% (1.27/13.62) | `professional` (전문사용자 229호) | normalized_verified | 복당사산/복당총산 | compatible |

**제약:** 이 9.3%는 **population_scope=professional 한정**. 전국 대표 슬롯(national_general)의 stillbirth_rate를 이 값으로 채우지 말 것. 전국은 missing 유지.

value_scale = percent_0_100, direction = lower_better.

---

## 5. 실행 절차 (방어적 — 확인 후 INSERT)

mutation 이력(작업 B에서 ★⑧ 가드 `if False` 무력화 적발)이 있는 코드베이스다. **가정하고 INSERT 금지. 확인하고 INSERT.**

### STEP 1 — kpi_code 존재 확인 (필수, INSERT 전)
```sql
SELECT kpi_code, direction, value_scale, denominator_type
FROM kpi_definitions
WHERE kpi_code IN (
  'psy','msy','farrowing_rate','preweaning_survival',
  'postweaning_survival','weaned_per_litter','sow_turnover'
);
```
- §2의 7종 kpi_code가 **모두 존재하는지** 확인.
- 존재하지 않는 코드는 **시드 제외하고 리포트에 orphan으로 기록**. (임의 신설 금지)
- 각 코드의 기존 `direction`·`value_scale`이 §2 표와 **불일치하면 INSERT 중단하고 리포트**. (benchmark가 kpi_definitions를 override하면 안 됨 — v3.1 원칙)

### STEP 2 — 기존 KR provisional 행 확인
```sql
SELECT b.kpi_code, b.benchmark_status, b.comparison_status, b.population_scope
FROM benchmarks b
WHERE b.country = 'KR' AND b.benchmark_status = 'provisional';
```
- B에서 넣은 provisional 10종 현황 파악. 승격 대상(§2의 7종)과 대조.

### STEP 3 — source_observations 기록 (원문 메타만)
- obs_group 2개 생성:
  - `KR_2025_national_general` (전국 일반사용자 2,655호)
  - `KR_2025_professional` (전문사용자 229호, 사산율용)
- 각 obs에 period_start/end, publication_date, population_scope, source 문자열 기록.
- **raw_fields_json에는 검증된 수치만**. PDF 바이너리·이미지 저장 금지.

### STEP 4 — benchmarks 승격/삽입
- §2의 7종: provisional → verified UPDATE (또는 신규 INSERT). comparison_status=compatible.
- §4 사산율: population_scope=professional 신규 INSERT, normalized_verified, transform_formula 기록, 검증 메타에 "생존=실산, KR표준 총산분해 잔차" 한 줄 명시.
- threshold 방향규칙 준수: higher_better → warning/critical을 min 칸, lower_better(사산율) → max 칸.

### STEP 5 — 가드 무결성 재확인 (mutation 재발 점검)
- benchmark_seed validator의 ★⑦⑧⑪⑫ 가드가 `if False`/`if True`/주석처리로 무력화된 곳 없는지 **grep 점검**.
- 특히 ★⑧(transform_formula 필수) 가드가 살아있는지 확인 — 이번에 normalized_verified를 INSERT하므로 ★⑧이 실제 작동해야 함.
- DB CHECK 제약(active-verified unique, 복합 FK)이 실제로 INSERT를 막는지 1건 의도적 위반 테스트로 확인.

### STEP 6 — 테스트 + 회귀
- 신규 시드 검증 테스트 추가(7종 verified + 사산율 obs_group 분리).
- 전국 stillbirth_rate가 여전히 missing인지 확인하는 테스트 추가(전문사용자 값이 전국으로 새지 않았는지).
- 전체 pytest 회귀(직전 519 green 기준). RED 발생 시 INSERT 롤백.

---

## 6. 완료 리포트 형식

```
## 작업 C 완료 — KR verified 승격

승격 (national_general, verified): [실제 INSERT된 kpi_code 목록과 값]
제외 (orphan/드롭): total_born(분모유형), market_age(KPI없음), npd(전국데이터없음)
별도 obs_group (professional, normalized_verified): stillbirth_rate 9.3%
  - 검증전제: 복당생존=실산, KR표준 총산분해 잔차
전국 stillbirth_rate: missing 유지 확인 [✓/✗]

STEP1 kpi_code 확인 결과: [존재/불일치 내역]
STEP5 가드 무결성: [★⑦⑧⑪⑫ 상태, DB CHECK 작동 여부]
테스트: [N passed, 회귀 결과]
미배포 여부: [운영 미반영 확인 — A·B와 함께 배포 권장]
```

---

## 7. 절대 하지 말 것 (가드레일)

- ❌ total_born / market_age kpi_definitions 신규 코드 생성 (범위 밖)
- ❌ 전국 stillbirth_rate를 전문사용자 9.3%로 채우기 (모집단 혼입)
- ❌ benchmark에서 direction/value_scale를 kpi_definitions와 다르게 박기 (override 금지)
- ❌ PDF 원본·이미지를 source_observations/repo에 저장
- ❌ KR 벤치마크를 PigSignal 외부 API·PigOS 한국 노출 경로에 연결
- ❌ kpi_code 존재 확인(STEP1) 없이 INSERT
- ❌ 추정·보간으로 빈 KPI 채우기 (없으면 missing)
- ❌ NPD를 전문사용자 47.7로 전국 시드 (D-1 미해결, 모집단 다름)
