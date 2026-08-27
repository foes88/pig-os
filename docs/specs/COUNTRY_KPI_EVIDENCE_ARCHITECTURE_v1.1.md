# COUNTRY_KPI_EVIDENCE_ARCHITECTURE v1.1

> 상태: **PROPOSED** — ADR 승인 전. 이 문서의 어떤 항목도 APPROVED가 아니다.
> 범위: 국가별 KPI 근거 수집 → 정의 대조 → 거버넌스 → 표시까지의 개발 구조.
> 대상 국가: US·BR(진행) / CN·VN·TH·MX·PH(예정) / KR(레퍼런스 전용, A-rule 적용)

---

## 0. 불변조건

전 계층에 적용된다. 예외 없음.

```
VERIFIED = 원문이 그 주장을 실제로 뒷받침한다.
VERIFIED ≠ 그 나라 전체를 대표한다.
VERIFIED ≠ PigOS 정의와 동치다.
VERIFIED ≠ 제품에 표시하도록 승인됐다.
DERIVED value does not inherit benchmark_verified from its inputs.
```

추가 원칙 4가지.

- **Collector claim은 immutable.** verifier는 원행을 수정·삭제하지 않고 event를 append한다.
- **source fact와 verifier interpretation을 분리한다.** 출처가 선언하지 않은 것을 출처의 주장으로 기록하지 않는다.
- **빈칸이 틀린 값보다 낫다.** 미확보는 미확보로 남긴다.
- **Collector pass와 Verifier pass를 분리한다.** Collector는 recall 우선, Verifier는 원문 직접 확인과 승격 규율 우선. (모델명으로 고정하지 않는다.)

---

## 1. 계층 모델

역순 진행 금지.

```
[1] PigOS Canonical Formula      ← D-13. 내부 SSOT
        ↓
[2] External Evidence            ← 국가별 수집. claim + verifier overlay
        ↓
[3] Definition Mapping           ← PigOS ↔ 개별 source, 항상 1:1
        ↓
[4] Governance                   ← G1 정의 / G2 권리 / G3 표시안전
        ↓
[5] Serving / Presentation       ← selected_evidence_id 로 provenance 유지
        ↓
[6] Product / Entitlement        ← 무료·유료 경계
```

기존 ADR-KPI-00의 3축 활성화 게이트는 **유지한다.** 아래는 신규 축이 아니라 기존 축의 내부 분해다.

```
definition_compatible  ← formula_status + mapping_status
rights_cleared         ← rights_scope[requested] + policy_scope[requested]
evidence_verified      ← benchmark_status + terminology_status
```

> ADR 문안에 "3축 → N축 확장"이라고 쓰지 않는다. 판정 근거의 세분화다.

---

## 2. Evidence 모델

### 2-1. Collector claim (immutable)

**식별자는 `claim_id` (UUID) 단일 PK다. 자연키를 identity로 쓰지 않는다.**

이유 둘.
- 한 source·edition·period·KPI 안에 `MEAN` / `MEDIAN` / `UPPER_10` / `LOWER_10`이 동시에 존재한다 → 자연키가 전부 충돌한다.
- `kpi_code_candidate`는 source fact가 아니라 **collector의 해석**이다. identity에 넣으면 후보를 정정할 때 source claim identity까지 흔들린다.

중복 수집 방지는 identity가 아니라 **fingerprint**로 한다:

```
fingerprint = source_asset_id + source_edition + reference_period
            + source_locator + source_statistic_label
            + statistic_position + geography
```

### claim_type — 3종 (benchmark 전용 스키마 금지)

국가별로 수집하는 것은 terminology / formula / benchmark 3종이다. 셋을 한 스키마에 넣으면 formula claim에는 `value`도 `statistic_position`도 없어 NULL 천지가 되거나 억지값이 들어간다.

```yaml
# 공통 (전 claim_type)
claim_id:                  # UUID, PK, immutable
claim_type:                # TERMINOLOGY | FORMULA | BENCHMARK
country:
kpi_code_candidate:        # 매핑 후보. identity 아님. 정정 가능
source_asset_id:
source_edition:
source_published_at:       # 발간·완료 시점
reference_period:          # 데이터가 가리키는 기간
source_locator:            # URL / 발간물명 + 페이지 / 표 위치
raw_claim_text:            # 원문 그대로
```

> **세 날짜 필드를 하나로 합치지 않는다.** 실례: MetaFarms `source_edition = 2021–2025`, `reference_period = 2025`, `source_published_at = 2026-06-01`. 전부 다른 의미다. `period`와 `source_edition`으로 `source_year`를 대체할 수 없다.

**타입별 필수 필드**

```yaml
# claim_type = TERMINOLOGY
local_label:               # 원문에 인쇄된 표기 그대로. 기계번역 금지
script:                    # LATIN | HAN | THAI | CYRILLIC ...

# claim_type = FORMULA
numerator:
denominator:
included_components:
excluded_components:
inclusion_exclusion_rules:
source_linkage:            # SAME_SOURCE | SAME_EDITION | EXPLICIT_CROSS_REFERENCE
                           # | RELATED_SOURCE | UNLINKED | UNKNOWN

# claim_type = BENCHMARK
value:
source_statistic_label:    # 원문 라벨 그대로 ("Upper 10 percentile")
statistic_position:        # UPPER_10 | MEDIAN | MEAN | TOP_10 ...
performance_direction:     # HIGHER_IS_BETTER | LOWER_IS_BETTER | NEUTRAL | UNKNOWN
measure_kind:              # COUNT | RATE | RATIO | DURATION | INDEX | COST
                           # | OBSERVED_COUNT | OTHER | UNKNOWN
unit:
unit_system:               # METRIC | IMPERIAL | NONE — 원문 단위. 환산값 금지
currency:                  # COST 일 때만
population_scope:          # NATIONAL | ADMIN_UNIVERSE | ENTERPRISE | RESEARCH_CENTER
                           # | GENETIC_LINE | FARM_COHORT | REGIONAL | MARKETING_TARGET
cohort_or_population_basis:
geography:
```

**cohort 요구는 `claim_type = BENCHMARK` 에만 적용된다.** TERMINOLOGY / FORMULA는 cohort 면제 — 정의 근거에 표본을 요구하면 쓸 수 있는 자료를 계속 버리게 된다.

### DERIVED value 저장 경로

원문 값을 정규화값으로 **덮어쓰지 않는다.** 환산은 별도 행이다.

```yaml
# source claim (immutable)
claim_id: <A>
value: 285.19
unit_system: IMPERIAL
unit: lb

# derived (별도 행)
derived_id:
source_claim_id: <A>
transform_spec_id: LB_TO_KG_V1
value: 129.36
unit: kg
derivation_status: VERIFIED      # 변환 자체는 검증됨
benchmark_verified: false        # 입력에서 자동 상속 금지
```

### 금지 규칙

- `MARKETING_TARGET`(벤더 목표치·컨설턴트 target)을 실측 national benchmark로 승격 금지.
- 원문에 없는 통계량(상위25%, target 등)을 생성 금지.
- `statistic_position`을 성과등급으로 번역 금지. PigCHAMP `Upper 10 percentile = 21.59`(PWM)를 `TOP_10`으로 바꾸면 방향이 뒤집힌다.
- COUNT를 RATE로 변환 금지. PigCHAMP `Average stillborn pigs = 1.18`에 `%`를 붙이지 않는다.
- 환산값을 source claim의 `value`에 기록 금지 (위 DERIVED 경로 사용).

### 2-2. Verifier overlay (append-only)

collector 행을 덮어쓰지 않는다.

```yaml
evidence_verifier_event:
  event_id:
  event_seq:                 # (claim_id, axis) 내 단조증가
  supersedes_event_id:       # nullable
  claim_id:                  # 참조
  axis:                      # terminology | formula | benchmark   ← mapping 없음
  verdict:                   # VERIFIED | UNVERIFIED | CONTRADICTED
                             # | CONSISTENT_WITH | SUPERSEDED_BY_NEW_EVIDENCE
  evidence:                  # 무엇을 직접 열어 확인했는가
  verified_at:
```

**현재 상태(current verifier state) 정의:**

```
(claim_id, axis) 별 최대 event_seq 를 가진 event = 현재 상태
```

`verified_at` 최신값으로 읽지 않는다 — 동시성·재검토에서 순서가 뒤집힌다.

**`axis = mapping`은 없다.** mapping은 claim 하나의 속성이 아니라 **PigOS canonical formula version ↔ external evidence의 관계**이므로 별도 엔티티다(§3-0).

**cross-edition 관찰** (같은 source, 다른 edition):

```yaml
cross_edition_value_changed: true
change_reason: UNKNOWN       # source가 스스로 correction 을 선언하지 않았으면 UNKNOWN
```

> `restated_from_edition`은 사용하지 않는다. "restated"는 출처의 의도를 주장하는 단어다. 출처가 명시적으로 정정을 선언했을 때만 쓴다.

**cross-source 관찰** (같은 country/kpi, 다른 source):

```yaml
cross_source_observation:
  comparability_status:      # PENDING_MAPPING / COMPARABLE / NOT_COMPARABLE
  discrepancy_status:        # NOT_EVALUATED / PRESENT / NOT_PRESENT
  discrepancy_reason:        # UNKNOWN / COHORT / DEFINITION / SOURCE_METHOD / PERIOD
```

`COMPARABLE` 최소 조건: same period · same statistic_position · same measure_kind · same unit · mapping compatible.

**mapping 확정 전에는 숫자 차이를 discrepancy라고 부르지 않는다.** 실례: MetaFarms 2024 PWMFY 27.27과 PigCHAMP 2023 mated-female 28.60의 차이 1.33은 **연도가 다르므로 discrepancy가 아니다.** 같은 2023으로 맞추면 26.51 vs 28.60(=2.09)이나, 이 역시 D-13 전에는 `comparability_status = PENDING_MAPPING`이다.

---

## 3. Definition Mapping

### 3-0. mapping은 별도 엔티티다

claim의 속성이 아니라 **관계**다. claim verifier event에 `axis=mapping`을 억지로 넣지 않는다.

```yaml
definition_mapping:
  mapping_id:
  pigos_formula_id:          # CANONICAL_FORMULA_SPEC (D-13)
  pigos_formula_version:
  external_claim_id:         # claim_type = FORMULA 또는 BENCHMARK
  mapping_status:            # §3-2
  transform_spec_id:         # APPROVED_TRANSFORM 일 때만
  decided_by:  decided_at:
```

`pigos_formula_version`이 올라가면 기존 mapping은 자동 승계되지 않는다 — 재판정 대상이다.

**mapping 자격:** PigOS 쪽 `implementation_status`가 `CONFIRMED` 또는 valid `NOT_APPLICABLE`인 항목만. `AMBIGUOUS` / `UNRESOLVED_OUTSIDE_SCOPE`는 mapping 금지.

### 3-1. 항상 1:1

```
PigOS canonical ↔ PigCHAMP USA 2023
PigOS canonical ↔ MetaFarms 2020–2024
PigOS canonical ↔ MetaFarms 2021–2025
PigOS canonical ↔ (CN/VN/TH/MX source ...)
```

**N자 mapping을 만들지 않는다.** 출처가 늘어나면 행이 늘 뿐 구조는 그대로다. 출처 간 일치는 요구사항이 아니다 — cohort·정의·edition이 다르면 둘 다 옳을 수 있다.

"US 제품에 어느 source/edition을 쓸 것인가"는 mapping이 아니라 **§4-4 Benchmark Selection** 결정이다.

### 3-2. mapping_status

```
EXACT                      공식·단위·모집단·기간 기준 동일
STRUCTURAL_EQUIVALENCE     산식이 구조적으로 N/A 인 지표끼리 동일
APPROVED_TRANSFORM         변환 승인됨 (아래 필수 필드 동반)
NOT_EQUIVALENT             동치 아님이 확인됨
UNKNOWN                    판정 불가
```

`formula_status = NOT_APPLICABLE` → `mapping = EXACT` **금지.** `STRUCTURAL_EQUIVALENCE` 대상이다.

### 3-3. formula_status

```
VERIFIED / UNVERIFIED / NOT_APPLICABLE / AMBIGUOUS
```

`NOT_APPLICABLE` 허용 조건: `source.measure_kind ∈ {INDEX, OBSERVED_COUNT}` **그리고** PigOS canonical도 동일 의미에서 N/A. 그 외 "산식을 못 찾음"은 `UNVERIFIED`다.

`source_linkage` 필수 (타 문헌 산식을 현재 benchmark의 산식으로 덮어쓰기 방지):

```
SAME_SOURCE / SAME_EDITION / EXPLICIT_CROSS_REFERENCE
/ RELATED_SOURCE / UNLINKED / UNKNOWN
```

### 3-4. APPROVED_TRANSFORM 필수 동반 필드

한 줄만 저장하면 loophole이 된다.

```yaml
transform_spec_id:
transform_formula:
source_measure_kind:  target_measure_kind:
source_unit:          target_unit:
required_components:
component_verification_status:
approved_by:  approved_at:  approval_reason:
```

**현재 후보 3건:**

| 사례 | 상태 |
|---|---|
| `preweaning_survival = 1 − pre-weaning mortality` + direction 반전 | 후보. D-13 후 판정 |
| PigOS 사산공식 `(stillborn+mummified) ÷ total born` ↔ PigCHAMP 구성요소 | 후보. 구성요소는 확보(아래) |
| MetaFarms `Piglet Survival = 100 − %stillborn − %PWM` | **NOT_EQUIVALENT 후보.** 이름 유사에 의한 오매핑 차단 대상 |

**PigCHAMP 사산 구성요소 (USA 2023, 167농장):**

```
Average total pigs per litter   15.84
Average pigs born alive/litter  14.15
Average stillborn pigs           1.18   ← measure_kind = COUNT
Average mummies per litter       0.50
                                 ─────
14.15 + 1.18 + 0.50 = 15.83 ≈ 15.84
```

판정: `denominator_semantics = CONSISTENT_WITH(PER_LITTER)`, `CONFIRMED = false`.
근거는 반올림이 아니라 **비배타성** — 합은 평균에 대해 선형이므로 항등식 성립은 강한 증거지만, 구성요소가 이 셋뿐이라는 유일성은 증명되지 않는다.

---

## 4. 거버넌스 게이트

### G1 — Definition

```
formula_status  ∈ {VERIFIED, valid NOT_APPLICABLE}
AND mapping_status ∈ {EXACT, STRUCTURAL_EQUIVALENCE, APPROVED_TRANSFORM}
```

선행: **D-13 완료.** canonical formula 없이 mapping 판정 불가.

### G2 — Rights × Policy (두 메커니즘, 병합 금지)

권리는 단일 사다리(enum ladder)가 **아니다.** 권리자가 "내부 분석 허용 / 대시보드 출처표시 인용 허용 / API 재배포 불허"를 선언할 수 있다.

```yaml
# ① 라이선서 권리 — source asset / edition 단위
rights_scope:
  INTERNAL_ANALYSIS : ALLOW | REVIEW | BLOCK
  PRODUCT_VISIBLE   : ALLOW | REVIEW | BLOCK
  EXTERNAL_API      : ALLOW | REVIEW | BLOCK

# ② 우리 자신의 정책 — 데이터 소유가 우리여도 적용
policy_scope:
  INTERNAL_ANALYSIS : ALLOW
  PRODUCT_VISIBLE   : ALLOW | BLOCK
  EXTERNAL_API      : ALLOW | BLOCK
```

판정:

```
rights_cleared(scope) =
     rights_scope[scope] == ALLOW
 AND policy_scope[scope] == ALLOW
```

**두 축이 필요한 이유 (KR A-rule):** 한국 벤치마크 데이터는 우리 소유다. 라이선서 권리 문제가 아니라 **포지셔닝 정책**이다. 따라서 KR은 `rights_scope` 전항 ALLOW여도 `policy_scope.PRODUCT_VISIBLE = BLOCK`, `EXTERNAL_API = BLOCK`으로 고정된다. 두 축을 병합하면 A-rule이 권리 판정에 묻혀 사라진다.

기본값은 **default-deny**: `policy_scope.PRODUCT_VISIBLE / EXTERNAL_API = BLOCK`. 명시적 승격만 허용.

판정 단위는 publisher가 아니라 **source asset / edition**이다. 같은 발행사라도 edition별 권리 문구가 다를 수 있다.

### G3 — Presentation Safety (전역 불변조건)

**이것이 국가 확장을 가능하게 하는 게이트다.** US 전용이 아니다.

benchmark가 없다고 카드를 숨기지 않는다. 농장 자기 값은 계속 보여주고 비교만 없앤다.

**API 계약 (`/kpi/presentation`, `/kpi/*`):**

```json
{
  "kpi_code": "npd",
  "value": 42,
  "benchmark_enabled": false,
  "benchmark_value": null,
  "benchmark_status": "NO_VERIFIED_BENCHMARK",
  "comparison_status": "UNAVAILABLE"
}
```

**절대 금지:**

- `benchmark_value: 0`
- GLOBAL 값 자동 대체 (silent fallback)
- KR 값 대체
- benchmark가 있는 것처럼 severity 계산
- `NaN` / 500 / 카드 소실

**benchmark와 severity는 별개다.** 이는 이미 잠긴 two-resolver 구조의 응답 레벨 표현이다.

```
Threshold Resolver          → severity/색상의 유일한 권한 (rule_configs / operational_default)
Benchmark Context Resolver  → 비교 맥락만. 색상·판정 없음
```

US NPD처럼 benchmark가 없어도 **별도 APPROVED된 threshold가 있으면 severity는 가능하다.** 반대로 threshold도 없으면 색도 내지 않는다.

**모바일까지 적용된다.** 백엔드가 null을 반환해도 모바일이 KPI 목록을 하드코딩하고 null 미처리면 거기서 깨진다. D-13 STEP 3의 모바일 실사 결과가 이 게이트의 입력이다.

**회귀 불변조건 3건:**

```
① visible KPI + benchmark 없음
   → HTTP 200 / farm value 유지 / benchmark=null
   → silent GLOBAL fallback 없음 / benchmark 기반 severity 없음

② registry 에 KPI 추가 시
   country_kpi_presentation 행이 없거나 priority_class IS NULL 이면
   /kpi/presentation 응답 카드 수가 자동 증가하지 않는다

③ threshold_source ∈ {rule_configs, operational_default} 인 경우에만 severity 발화
   threshold_source = code_default  →  severity 없음
     · 기존 활성 국가 : FLAGGED_FOR_REVIEW (자동 revoke 금지 — G0 와 동일 처리)
     · 신규 국가 활성화 : 차단
```

> **③ 은 2026-08-27 실측에서 나왔다.** benchmark 쪽에서 ① 이 막은 silent fallback 이
> threshold 쪽에는 그대로 열려 있었다.
>
> ```
> benchmark  : GLOBAL silent fallback  → ① 이 금지          ✅
> threshold  : code_default fallback   → 아무도 안 막음      ❌
> ```
>
> `threshold_resolver` 의 해소 순서는 `rule_configs → operational_defaults →
> code_default` 이고, 등록 룰 40개 대비 `operational_defaults` 시드는 29키다.
> 나머지는 **룰 함수 안의 하드코딩 상수**로 색을 낸다 — 국가 인식도 결재 기록도 없다.
> 그 상태로 §6-1 의 "APPROVED threshold 필수" 판정을 통과한 것처럼 보이는 것이 문제다.
>
> ★ ③ 을 소급 적용하면 **운영 중인 BR 이 색을 잃는다.** 그래서 G0 와 같은 처리를 한다 —
> 기존 활성 국가는 유지·FLAGGED, 신규 국가만 차단. 게이트는 전방향 통제 장치다.
>
> ★ 그리고 **Track 4 전체를 끝낼 필요는 없다.** US 런치에 필요한 사실은 하나다 —
> *커버 안 된 11룰 중 US 에서 visible 한 KPI 를 건드리는 것이 몇 개인가.*
> 0개면 US 는 Track 4 와 무관하게 진행하고, N개면 그 KPI 만 severity 없이 출발하거나
> (① 이 정상 처리한다) **그 룰만** operational_default 로 추출한다. 전체 추출이 아니라
> US 교집합만이다. → **D-19**

검증은 **API 응답 레벨**에서. 프론트는 registry-map 렌더링이므로 country branching을 추가하지 않는다.

### G0 — 기존 APPROVED 행의 소급 처리

D-13이 어떤 KPI를 `AMBIGUOUS`로 판정했을 때, 그 KPI를 쓰는 **이미 배포된 국가(BR 등)의 APPROVED 행이 자동 무효화되지 않는다.**

```
D-13 AMBIGUOUS / LIVE_DIVERGENCE 발견
   → 기존 APPROVED 행: 유지 (자동 revoke 금지)
   → 상태: FLAGGED_FOR_REVIEW
   → 신규 INSERT: 해당 KPI 차단
   → P0-2 / P0-1B 종료 후 재판정
```

이유: 게이트는 전방향(forward) 통제 장치다. 소급 자동 무효화를 허용하면 감사 한 번이 운영 중인 국가를 내려버릴 수 있다. 반대로 `LIVE_DIVERGENCE`가 확인되면 그것은 별도 운영 이슈로 즉시 에스컬레이션한다 — 게이트가 아니라 인시던트 경로다.

### 4-4. Benchmark Selection (별도 결정)

G1~G3 통과 후에도 자동 활성화되지 않는다.

```
benchmark_enabled(country, kpi) = true
  ONLY IF  G1 통과
      AND  G2 통과 (requested scope 기준)
      AND  G3 통과
      AND  benchmark scope 가 이 제품 용도로 수용됨
      AND  Decision Register = APPROVED
```

가장 중요한 문장: **`benchmark_status = VERIFIED` 만으로는 절대 활성화되지 않는다.**

---

## 5. Serving 계층 — provenance 유지

**D-14가 evidence 테이블에서 끝나면 반쪽이다.**

evidence에 `source_edition = 2020-2024 / period = 2023 / PWMFY = 26.51`을 완벽히 보존해도, serving에 `US / PWMFY / 26.51`만 INSERT하면 production에서 provenance가 다시 소실된다. 내년에 2021–2025 값을 넣을 때 "이 26.51은 어느 edition인가"를 알 수 없다.

```
Evidence (claim_id, source, source_edition, period, value)
        ↓
Decision Register  APPROVED
        ↓
serving row:
  selected_evidence_id      FK → evidence_claim.claim_id      ← 필수
  applied_transform_spec_id FK → transform_spec (nullable)    ← 변환 적용 시
  applied_mapping_id        FK → definition_mapping (nullable)
  decision_id
  effective_from / effective_to
```

`selected_evidence_id` 하나로는 부족하다. `APPROVED_TRANSFORM`이 적용되면 serving 값은 raw claim이 아니라 derived value이므로, **어떤 변환·어떤 mapping이 승인되어 그 값이 나왔는지**가 함께 남아야 한다. (예: claim은 lb, serving은 kg.)

**Phase 1 범위 한정:** 평균 + Top10 + Median을 하나의 benchmark package로 묶는 selection entity는 **지금 만들지 않는다.** 단일 claim 참조로 시작하고, 실제 번들 요구가 생길 때 추가한다.

**기존 리졸버 경로와의 관계:** 리졸버는 `decision_status = 'APPROVED'` 행만 읽고, 그 fail-closed 동작은 게이트 L5로 잠겨 있다. `selected_evidence_id`는 **이 경로를 대체하지 않는다.** APPROVED 행에 provenance 포인터를 추가하는 것이며, 승인 여부 판정은 계속 `decision_status`가 한다. 두 개의 병렬 승인 메커니즘을 만들지 않는다.

**benchmark_point / benchmark_trend / threshold 3분리:**

```
benchmark_point   현재 비교값 (단일 edition, 단일 period)
benchmark_trend   산업 추세 (다년, context 전용)
threshold         별도 승인된 판정 기준
```

추세를 threshold에 반영하면 **moving goalpost**가 된다. 실례: MetaFarms US PWM 12.9%(2020) → 14.5 → 14.6 → 14.7 → 16.4%(2024). 산업이 악화됐다고 good threshold를 12.9%→16.4%로 완화하면 기준 자체가 무너진다. 추세는 `"US industry PWM has worsened for 5 consecutive years"` 같은 contextual insight로 쓴다 — 단일 평균보다 제품 가치가 크다.

---

## 6. 국가 확장 플레이북

### 6-1. 국가별 최소 요건

**benchmark는 런치 필수가 아니다.** G3가 서 있으면 benchmark 0개로도 국가를 켤 수 있다.

| 요소 | 런치 필수 | 비고 |
|---|---|---|
| terminology (현지 명칭) | ✅ | 표시에 필요 |
| presentation policy (priority_class / display_order) | ✅ | 없으면 GLOBAL 기본 |
| threshold (rule_configs 또는 operational_default) | ✅ | severity 권한. **`code_default` 는 이 요건을 충족하지 않는다** — G3 ③ |
| formula mapping | benchmark 쓸 때만 | |
| benchmark | ❌ | 없으면 `NO_VERIFIED_BENCHMARK` 로 정상 렌더 |
| rights × policy clearance | benchmark 쓸 때만 | |

### NO-BENCHMARK COUNTRY LAUNCH (정식 정의)

```
PigOS canonical KPI 존재 (D-13 CONFIRMED 또는 valid NOT_APPLICABLE)
+ terminology
+ presentation policy
+ APPROVED threshold
+ G3 presentation safety
= 국가 런치 가능

external formula mapping / benchmark / benchmark rights
= 불필요
```

> **PH가 증명 사례다.** 검증된 농장 단위 benchmark가 사실상 없다. G3 없이는 런치 불가, 위 5개가 있으면 런치 가능하다.
>
> 주의: "benchmark 없이 런치 가능"이 "terminology + G3만으로 국가 ON"을 뜻하지 않는다. **canonical KPI와 APPROVED threshold는 여전히 필수다.** threshold 없이는 severity를 낼 권한 자체가 없다.

### 6-2. 국가별 현황 (evidence 축)

| 국가 | terminology | formula | benchmark | 주요 제약 |
|---|---|---|---|---|
| **BR** | VERIFIED | — | 반영 완료 | 파일럿 3개 잠금 유지. 확대는 별도 결정 |
| **US** | VERIFIED | UNVERIFIED | VERIFIED 다수 | D-13 전 mapping BLOCKED. NPD/WSI/MSY는 승인 source set 내 annual benchmark 미확보 |
| **CN** | VERIFIED | 부분 | ENTERPRISE scope | 상장사 IR ≠ national. 完全成本은 `measure_kind=COST`, `currency=CNY`, `unit=per_kg` |
| **VN** | VERIFIED | **분모 미확인** | GENETIC_LINE / RESEARCH_CENTER | 값 존재하나 national applicability 미확립 |
| **TH** | VERIFIED | PWM만 VERIFIED | PWM만 (47 commercial herds) | PSY 산업평균 미확보. source별로 행 분리 |
| **MX** | VERIFIED | VERIFIED (PIC, inventory 분모) | MX 단독 미확보 | PIC는 다국 혼합. edition별 cohort 상이 → benchmark 채택만 동결, formula는 유효 |
| **PH** | UNVERIFIED | 미확보 | 미확보 | ADMIN_UNIVERSE(PSA 농장분류)만 확보. G3 증명 사례 |
| **KR** | — | — | 내부 보유 | **policy_scope: PRODUCT_VISIBLE=BLOCK, EXTERNAL_API=BLOCK (A-rule)** |

### 6-3. 국가 추가 절차 (반복 가능)

```
1. terminology 수집        (Collector pass, cohort 불요)
2. formula evidence 수집   (Collector pass, cohort 불요 — 정의 근거는 cohort 면제)
3. benchmark 수집          (source_year + cohort_or_population_basis 필수)
4. Verifier pass           (원문 직접 확인, append-only overlay)
5. mapping 판정            (PigOS canonical ↔ source, 1:1)
6. rights × policy 판정    (source asset / edition 단위)
7. Decision Register       (PROPOSED → APPROVED)
8. INSERT                  (selected_evidence_id 동반)
9. G3 회귀 통과 확인
```

3번(benchmark 수집)이 비어 있어도 런치 가능하다. 단 §6-1의 NO-BENCHMARK LAUNCH 5개 조건을 전부 만족해야 한다 — canonical KPI · terminology · presentation policy · APPROVED threshold · G3.

### 6-4. 출처 계약 (증거 종류별)

| evidence | 필수 | cohort |
|---|---|---|
| terminology | 원문 source, 연도, 국가/업계 context, 실제 사용 label | 불요 |
| formula | 원문 source, year/version, 분자·분모·포함/제외, `source_linkage` | **불요** |
| benchmark | 원문 source, period, statistic, geography, population_scope, coverage | **필수 또는 CENSUS/ADMIN_UNIVERSE 명시** |
| mapping | external canonical formula + PigOS canonical formula + unit/denominator/component 비교 | 외부 cohort 무관 |

정의 근거에 cohort를 요구하면 쓸 수 있는 자료를 계속 버리게 된다(1라운드 과잉기각의 원인).

---

## 7. 회귀 fixture

각 항목은 **실제로 발생했거나 발생 직전이었던 오류**에서 나왔다.

| fixture | 막는 것 |
|---|---|
| PWM `Upper 10 = 21.59` / `Lower 10 = 9.85` | percentile 방향 반전 |
| `Average stillborn pigs = 1.18` | COUNT → RATE 오인 |
| TH PWM 논문 ↔ TH 2010 방법론 논문 | 타 문헌 산식을 benchmark source 산식으로 결합 |
| CN 상장사 IR | ENTERPRISE → NATIONAL 승격 |
| VN YVN1/YVN2 (35+35두) | GENETIC_LINE → national benchmark 승격 |
| MetaFarms 2023: 25.91 vs 26.51 | edition 혼합. 임의 선택 |
| PIC Q3-2023 / Q4-2023 / T1-2024 | edition별 cohort 혼합 |
| registry 확장 | 자동 노출 |
| `formula = N/A` | 미확인 산식의 N/A 처리 |
| `APPROVED_TRANSFORM` | 승인정보 없는 transform 통과 |
| **benchmark 없는 KPI 렌더링** | silent fallback / 카드 소실 / 500 |
| **DERIVED value** | 입력의 `benchmark_verified` 상속 |
| **KR benchmark** | policy_scope 무시하고 제품·API 노출 |

---

## 8. 결정 등록부 (전건 PROPOSED)

| ID | 내용 | 우선 |
|---|---|---|
| **D-13** | PigOS canonical formula 코드 실사 → `CANONICAL_FORMULA_SPEC` | **P0** |
| **D-15** | MetaFarms 2021–2025 (488농장 / 1,356,931두, 2026-06-01) 원문 실사 | **P0 (D-13과 병렬)** |
| D-8 | PigOS canonical ↔ 개별 external evidence 정의 호환. **source별 1:1** | P1 |
| D-9 | 4축 분해 + evidence 최소 스키마. 기존 3축 내부 분해로 표현 | P1 |
| D-10 | `source_statistic_label` + `statistic_position` + `performance_direction` 3층 | P1 |
| D-11 | `measure_kind` COUNT≠RATE validator | P1 |
| D-12 | `source_year + cohort_or_population_basis` + `source_linkage` | P1 |
| D-14 | `source_edition` 필수 + **serving 계층 `selected_evidence_id`** | P1 |
| **D-17** | **G3 표시 안전 계약** — API 응답 스키마 + 회귀 2건 + 모바일 | **P1 (US 런치 필수)** |
| **D-18** | **`rights_scope` / `policy_scope` 2축 분리.** A-rule을 policy_scope로 강제 | P1 |
| **D-19** | **threshold source 감사** — 40룰 각각이 `rule_configs` / `operational_default` / `code_default` 중 무엇으로 해소되는지 + 각 룰이 붙는 KPI. read-only | **P0 (D-13 직후)** |
| D-16 | `vfd_required_us` 재설계 — `country=US AND condition=USES_VFD_FEED` | **병렬 트랙** |

> **D-19 를 D-13 과 같은 run 에 넣지 않는다.** 목적과 STOP 조건이 다르고,
> "한 배포 스텝에 변수 하나" 원칙에 걸린다. D-13 종료 후 별도로 돌린다.
> 산출물은 G3 불변조건 ③ 과 §6-1 "APPROVED threshold" 판정의 입력이다.

`D-15` 실사 범위 (한 번에 끝낼 것): KPI values · cohort definition · inclusion/exclusion · calculation notes · **copyright/rights wording** · cross-edition historical values.

---

## 9. 실행 순서

```
D-13  canonical formula 실사 (bjh, read-only)  ┐
                                               ├─ 병렬
D-15  MetaFarms 2021–2025 원문 실사             ┘
        ↓
D-19  threshold source 감사 (D-13 직후, 별도 run)
        ↓  ★ US 교집합만 판정 — Track 4 전체를 끝내지 않는다
D-8   source별 1:1 mapping 판정
        ↓
D-14  versioned evidence + selected_evidence_id
        ↓
benchmark source / edition 선택
        ↓
G2  scope별 rights × policy 판정
        ↓
Decision Register APPROVED
        ↓
INSERT
        ↓
US 농장 활성화

[병렬 · US 런치 필수]  D-17 G3 표시안전 게이트
[병렬 · critical path 외]  D-16 VFD conditional rule
```

**DB 제약 변경과 신규 국가 데이터 적재를 같은 commit/deploy에 넣지 않는다.**

---

## 10. Non-goals (이번 범위 아님)

```
✗ representativeness 점수화 / evidence confidence score
✗ 20필드짜리 범용 provenance ontology
✗ 신규 국가 benchmark 대량 적재
✗ BR 파일럿 3개 → 7~8개 확대
✗ MX PIC benchmark 대표값 확정
✗ ADR 승인 전 benchmark_enabled DB gate 수정
✗ UNKNOWN 을 N/A 로 치환
✗ 코드에서 못 찾은 산식 추론
✗ Track 4 / D-7 KRW leak gate 병행
✗ operational_default 추출 / Rule Engine inline default 정비
✗ FCR 유료 확정 — rights × policy 판정 전 제품화 금지 (high-value candidate 까지만)
```

---

## 부록 A — 소실행 1회 복구 목록

verifier overlay 규칙은 앞으로만 적용된다. 병합 과정에서 떨어진 collector 원행을 **확정 전 1회 복구**하고, 이후부터 append-only.

PigCHAMP USA 2023 (167농장):
```
Average total pigs per litter   15.84   ← 우리 사산공식 분모
Average mummies per litter       0.50   ← 우리 사산공식 분자 구성요소
Culling rate                    42.49%
Liveborn/female/yr              32.22
```

MetaFarms 2020–2024 (US):
```
Nursery FCR 1.58 / Finish FCR 2.82 / Wean-to-Finish FCR 2.60   (중량 전부 lb)
5년 추세: PWMFY 25.42→27.27, PWM 12.9→14.5→14.6→14.7→16.4%
```

규제 타임라인: GFI #213 (2017-01) · GFI #263 (2023-06-11) · PQA Plus 6.0 (2025-06).

## 부록 B — 미해결 관찰

- **PigCHAMP `Pigs wnd / female / year` 분모 정의 미확보.** 공개 변수맵의 `Total sows = Ave female inv − Ave gilt pool inv` 항등식이 mated female의 gilt pool 제외를 시사하나 명시 산식 아님. `[UNVERIFIED, 추정]`.
- **MetaFarms 2020–2024 내부 cohort 기준 모순.** 같은 p.2에서 전체 dataset은 "5년+ 이력", SOW 부분은 "3년+ / start-up 제외". 임의 통합 금지.
- **PigCHAMP `Average litter weaning weight = 137.28` (n=17) 단위 미인쇄.** lb 추정 금지 → benchmark 후보 제외.
- **PigCHAMP 북미 통합본:** 2024 Year Summary = US & Canada 174농장, 2025 = 149농장. 정상 두 edition이며 둘 다 US-only 값으로 승격 금지.
- **US 규제는 조건부 적용.** 9 CFR 166.9는 licensed garbage treatment facility 한정, 9 CFR 71.19는 interstate movement / production health plan 참여 조건부, 21 CFR 530.5의 primary duty는 veterinarian. 일반 농장 기록의무로 일반화 금지.
