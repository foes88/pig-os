# RUN PROMPT E — US 국가 KPI 근거 수집 (Collector pass)

> 작성 2026-08-27 · **v2 (출처 계약 v2 반영)** · 상태 **의뢰 대기**
> 산출물 `docs/kpi/US_KPI_RESEARCH_<날짜>.md`
> 정본: [COUNTRY_KPI_EVIDENCE_ARCHITECTURE v1.1](../specs/COUNTRY_KPI_EVIDENCE_ARCHITECTURE_v1.1.md)
> 선행 완료: P1 US Template LOCK 게이트 L1~L6 통과 (`api/tests/integration/test_us_template_lock.py`)

> **v2 변경 (2026-08-27)** — v1 은 아키텍처 v1.1 과 4곳에서 충돌했고, 그 충돌이 정확히
> **1라운드 과잉기각**을 만든 규칙이었다:
> ① cohort 를 전 항목에 요구 → CN 完全成本 정의·MX PIC DHA 산식·TH PSY 산식이
>    "정의 근거인데 표본이 없다"는 이유로 통째로 버려졌다. PIC 산식을 검증하는 데
>    멕시코 단독 농장 표본이 있을 이유가 없다.
> ② `source_year` 단일 필드 → edition / reference_period / published_at 셋으로 분리.
> ③ 행 단위 단일 태그 → 축별 태그. benchmark VERIFIED + formula UNVERIFIED 가 정상이다.
> ④ "PigOS 코드에 매핑" → `kpi_code_candidate` 로만. 동치 판정은 D-8 소관.

---

## 0. 이 의뢰의 성격 — Collector pass 다

아키텍처 §0: **Collector pass 와 Verifier pass 를 분리한다. Collector 는 recall 우선.**

당신은 Collector 다. 원문에 인쇄된 것을 **있는 그대로 많이** 가져오는 것이 임무이고,
"이게 PigOS 의 무엇에 해당하는가"를 판정하는 것은 임무가 아니다(D-8 소관).

그래서 **버리지 마라.** 애매하면 애매하다고 적고 가져온다. 단, **원문이 말하지 않은 것을
출처의 주장으로 기록하는 것**은 금지다. 이 둘의 구분이 이 의뢰의 전부다.

```
가져오되 해석하지 않는다.
빈칸이 틀린 값보다 낫다.
원문 직접 열람 실패 → UNVERIFIED. 2차 인용은 검증이 아니다.
```

---

## ★ 1. 출처 계약 v2 — 증거 종류별 (위반 시 해당 항목 빈칸)

### 공통 (전 claim_type)

- `source_locator` : URL 또는 발간물명 + 페이지. **"업계 통념"·"일반적으로" 금지**
- `source_asset` / `source_edition`
- `source_published_at` : 발간·완료 시점
- `raw_claim_text` : 원문 그대로
- 원문 직접 열람 실패 → `UNVERIFIED`. 2차 인용은 검증이 아니다

> **세 날짜를 하나로 합치지 마라.** 실례: MetaFarms `source_edition = 2021–2025`,
> `reference_period = 2025`, `source_published_at = 2026-06-01`. 전부 다른 의미다.

### claim_type = TERMINOLOGY

- `local_label` : 원문에 인쇄된 표기 그대로. **기계번역·직역 금지**
- `script` : LATIN | HAN | THAI | CYRILLIC …
- **cohort 불요 · reference_period 불요**

### claim_type = FORMULA

- 분자 / 분모 / 포함·제외 규칙
- `source_linkage` : `SAME_SOURCE` | `SAME_EDITION` | `EXPLICIT_CROSS_REFERENCE`
  | `RELATED_SOURCE` | `UNLINKED` | `UNKNOWN`
- **cohort 불요 · reference_period 불요**
  (정의 근거에 표본을 요구하면 쓸 수 있는 자료를 계속 버리게 된다)

> `source_linkage` 가 필요한 이유: 타 문헌의 산식을 **현재 benchmark 출처의 산식으로
> 덮어쓰는 것**을 막는다. 같은 나라 논문이라고 같은 정의가 아니다.

### claim_type = BENCHMARK

- `value` / `source_statistic_label`(원문 라벨 그대로) / `statistic_position`
- `measure_kind` / `unit` / `unit_system`(원문 단위, **환산값 금지**) / `currency`
- `reference_period`
- `population_scope`
- **`cohort_or_population_basis` 필수** — 또는 `CENSUS` / `ADMIN_UNIVERSE` 명시
  (행정 전수통계에 억지 cohort 를 요구하지 않기 위함)

---

## 2. 태그 — 축별로 단다. 행 단위 단일 태그 금지

```
terminology : VERIFIED | UNVERIFIED
formula     : VERIFIED | UNVERIFIED | NOT_APPLICABLE
benchmark   : VERIFIED | UNVERIFIED
```

**한 지표에서 benchmark VERIFIED / formula UNVERIFIED 가 정상 상태다.**
미국이 지금 정확히 그 상태다 — 값은 많이 나와 있는데 산식이 인쇄돼 있지 않다.
행 하나에 태그 하나만 달면 이 정상 상태를 표현할 수 없어서, 값까지 같이 버리게 된다.

`formula = NOT_APPLICABLE` 은 **산식이 구조적으로 존재하지 않을 때만**이다.
"산식을 못 찾음" 은 `UNVERIFIED` 다. 이건 escape hatch 가 아니다.

## 3. kpi_code

`kpi_code_candidate` 로만 기재한다. PigOS 동치 판정은 **D-8 소관**이며
D-13 완료 전에는 전건 **`판단보류`** 다.

> 왜: `kpi_code` 는 source fact 가 아니라 **collector 의 해석**이다. identity 에 넣으면
> 후보를 정정할 때 source claim 의 정체성까지 흔들린다. 그리고 PigOS canonical 산식이
> 아직 실사(D-13) 전이라, 지금 매핑하면 **없는 기준에 맞추는 셈**이다.

---

## 4. 조사 대상

### 4-1. 지표 (terminology + formula + benchmark 3종을 각각)

미국 표준 출처는 **PigCHAMP Benchmark** 와 **MetaFarms / Swine Management
Services(SMS) Production Analysis Summary** 다. 두 곳이 같은 지표를 다르게 부르거나
다르게 계산하므로 **출처별로 행을 분리한다.** 합치지 마라 — 둘 다 옳을 수 있다.

각 지표에 대해 §1 의 claim_type 별 필수 항목을 채운다.

> ★ **단위 함정**: 미국 자료는 lb 를 쓴다. `unit_system: IMPERIAL`, `unit: lb` 로
> **원문 그대로** 적는다. kg 환산값을 `value` 에 넣지 마라 — 환산은 별도 derived 행이다.
>
> ★ **통계량 함정**: `source_statistic_label` 은 원문 라벨 그대로다
> ("Upper 10 percentile"). 이를 "상위 10%" 같은 성과등급으로 번역하면 **방향이
> 뒤집힌다** — PWM 의 Upper 10 percentile = 21.59 는 나쁜 쪽이다.
>
> ★ **COUNT/RATE 함정**: `Average stillborn pigs = 1.18` 은 COUNT 다. `%` 를 붙이지 마라.
>
> ★ **정의 함정**: "Pigs Weaned per **Sow** per Year" 와 "per **Mated Female** per
> Year" 는 분모가 다르다. 이름이 같다고 같은 지표가 아니다. 그래서 §3 대로
> `kpi_code_candidate` 로만 적고 판정하지 않는다.

### 4-2. 규제 요건 (부수)

`vfd_required_us` 컬럼이 코드에 있다 — Veterinary Feed Directive 때문이다.

- VFD 대상 약제 범위와 근거 규정 (CFR 조항 번호까지)
- 각 요건이 **농장 기록 시스템 저장을 요구**하는지, 수의사 측 의무인지

> ★ **조건부 적용 주의.** 9 CFR 166.9 는 licensed garbage treatment facility 한정,
> 9 CFR 71.19 는 interstate movement / production health plan 참여 조건부,
> 21 CFR 530.5 의 primary duty 는 veterinarian 이다.
> **일반 농장 기록의무로 일반화하지 마라.**

### 4-3. 미확보로 남겨도 되는 것

- 주(state)별 차이 · 통합업체 내부 기준 · 유료 보고서 안에만 있는 값

---

## 5. 산출물 형식

`docs/kpi/US_KPI_RESEARCH_<날짜>.md` 하나.

```markdown
# US KPI Research (<날짜>)

## A. 요약
    claim 건수 — TERMINOLOGY / FORMULA / BENCHMARK 각각
    축별 VERIFIED · UNVERIFIED · NOT_APPLICABLE 건수
    미확보 항목 수

## B. TERMINOLOGY claims   (§1 TERMINOLOGY 항목, claim 당 1행)
## C. FORMULA claims       (§1 FORMULA 항목, source_linkage 포함)
## D. BENCHMARK claims     (§1 BENCHMARK 항목, cohort 필수)

## E. 출처 목록 — 실제로 열어본 것만. 열지 못한 것은 "미열람"으로 분리
## F. 규제 요건 (§4-2)
## G. 조사자가 판단하지 못한 것 — 질문 형태로
```

> **§G 를 비워서 보내지 마라.** 애매한 것이 하나도 없었다면 조사를 얕게 한 것이다.

---

## 6. 이 결과가 어디로 가는가

```
Collector 산출물 (이 문서)
   ↓  Verifier pass — 원문 직접 확인, append-only overlay (원행 수정 금지)
   ↓  D-13 완료 후  D-8 mapping 판정 (PigOS canonical ↔ source, 항상 1:1)
   ↓  G2 rights × policy 판정 (source asset / edition 단위)
   ↓  Decision Register APPROVED
   ↓
INSERT (selected_evidence_id 동반)
   ↓  G3 회귀 통과 확인
미국 농장 대시보드
```

★ **`benchmark = VERIFIED` 만으로는 절대 활성화되지 않는다.** 아키텍처 §4-4.
그러니 "이 값이 제품에 쓰일 만한가"를 걱정하며 걸러내지 마라 — 거르는 것은 뒤 단계의
일이고, 지금 버린 것은 되살아나지 않는다.

**benchmark 가 하나도 안 나와도 미국은 런치 가능하다** (아키텍처 §6-1
NO-BENCHMARK COUNTRY LAUNCH). 그러니 값을 못 찾았다고 없는 값을 만들지 마라.
