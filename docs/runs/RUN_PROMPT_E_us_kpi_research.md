# RUN PROMPT E — US 국가 KPI 확정 리서치

> 작성 2026-08-27 · 상태 **의뢰 대기** · 산출물 `docs/kpi/US_KPI_RESEARCH_<날짜>.md`
> 선행 완료: P1 US Template LOCK 게이트 L1~L6 통과 (`api/tests/integration/test_us_template_lock.py`)

---

## 0. 왜 이 리서치가 필요한가 — 먼저 읽을 것

Template LOCK 검증이 끝나서 **US 를 켜는 데 필요한 것은 INSERT 뿐**임이 증명됐다.
남은 것은 "무엇을 INSERT 할 것인가" 이고, 그게 이 리서치다.

그런데 이전에 같은 목적으로 받은 `gpt_country_draft_UNVERIFIED.md` 는 격리됐다.
**표는 전부 채워져 왔는데 인용 기관이 원문 대조된 적이 없었다.** 그런 값이 코드에
들어가면 미국 농장에 잘못된 기준으로 경고가 뜬다. 그래서 이번에는 규칙을 먼저 건다.

**빈칸으로 오는 것이 틀린 값으로 오는 것보다 낫다.** 이 문장이 이 의뢰의 전부다.

---

## 1. 하드 규칙 — 위반 시 산출물 전체 폐기

```
출처      URL 또는 발간물명 + 페이지 번호. "업계 통념"·"일반적으로" 금지
연도      source_year 명시. 없으면 그 행은 UNVERIFIED
표본      cohort(농장 수·지역·기간) 명시. 없으면 UNVERIFIED
빈칸      모르면 "미확보". 추정·보간·유추·평균내기 전부 금지
현지명    미국 양돈업계가 실제로 쓰는 표기만. 기계번역·직역 금지
국가묶기  금지. "북미 공통" 같은 것 없음. US 만
```

- 항목마다 **`[VERIFIED]` / `[UNVERIFIED]` 태그를 반드시** 단다.
- 하나의 수치에 출처가 둘이고 값이 다르면 **둘 다 적고 차이를 서술**한다. 고르지 마라.
- 원문을 직접 열어보지 못했으면 `[UNVERIFIED]` 다. 2차 인용은 검증이 아니다.

---

## 2. 조사 대상

### 2-1. 지표 집합 (필수)

미국 양돈 생산성 벤치마크의 표준 출처는 **PigCHAMP Benchmark** 와 **MetaFarms /
Swine Management Services(SMS) Production Analysis Summary** 다. 두 곳이 같은 지표를
다르게 부르거나 다르게 계산하는 경우가 있으므로 **정의까지 같이** 가져온다.

각 지표에 대해:

| 필요 항목 | 설명 |
|---|---|
| `kpi_code` | PigOS 코드에 매핑 (PSY, FARROWING_RATE, NPD, PWMR, BORN_ALIVE, WSI, ...) |
| 미국 현지 명칭 | 업계 문서에 실제로 인쇄된 표기 (예: "Pigs Weaned/Mated Female/Year") |
| 정의·계산식 | 분자·분모를 문장으로. PigOS 계산식과 다르면 **그 차이를 명시** |
| 대표값 | 평균 / 상위 10% / 하위 10% 중 원문이 제공하는 것 |
| 단위 | 마리·%·일·kg(lb 인지 kg 인지 반드시) |
| source_year | |
| cohort | 농장 수, 지역, 기간 |
| 출처 | URL 또는 발간물명 + 페이지 |
| 태그 | `[VERIFIED]` / `[UNVERIFIED]` |

> ★ **단위 함정**: 미국 자료는 lb 를 쓴다. kg 로 환산했으면 환산했다고 적어라.
> 환산값을 원문 값인 것처럼 적으면 그것도 위조다.

> ★ **정의 함정**: PSY 만 해도 "Pigs Weaned per Sow per Year" 와 "per **Mated
> Female** per Year" 는 분모가 다르다. 이름이 같다고 같은 지표가 아니다.
> PigOS 의 PSY 정의는 `docs/specs/` 의 KPI 계산식을 열어 대조한다.

### 2-2. 규제 요건 (부수)

`vfd_required_us` 컬럼이 코드에 이미 있다 — US 의 **Veterinary Feed Directive**
때문이다. 관련해 확인할 것:

- VFD 대상 약제의 범위와 근거 규정 (FDA CFR 조항 번호까지)
- VFD 외에 미국 양돈 농장 기록에 법적으로 요구되는 항목이 있는가
- 각 항목이 **농장 기록 시스템에 저장을 요구**하는지, 아니면 수의사 측 의무인지

### 2-3. 미확보로 남겨도 되는 것

조사해서 안 나오면 **"미확보"로 적고 넘어간다.** 이것들은 없어도 US 를 켤 수 있다:
- 주(state)별 차이
- 통합업체(integrator)별 내부 기준
- 유료 보고서 안에만 있는 값 (구매 여부는 대표 결정)

---

## 3. 산출물 형식

`docs/kpi/US_KPI_RESEARCH_<날짜>.md` 하나. 아래 구조를 지킨다.

```markdown
# US KPI Research (<날짜>)

## A. 요약 — VERIFIED 몇 건 / UNVERIFIED 몇 건 / 미확보 몇 건

## B. 지표표 (§2-1 항목 전부, 지표당 1행)

## C. 정의 차이 — PigOS 계산식과 US 관행이 다른 지점만

## D. 규제 요건 (§2-2)

## E. 출처 목록 — 실제로 열어본 것만. 열지 못한 것은 "미열람"으로 분리

## F. 조사자가 판단하지 못한 것 — 질문 형태로
```

> **§F 를 비워서 보내지 마라.** 애매한 것이 하나도 없었다면 조사를 얕게 한 것이다.

---

## 4. 이 결과가 어디로 가는가 (조사자는 몰라도 되지만, 무게를 알기 위해)

```
리서치 산출물 (docs/kpi/, UNVERIFIED 포함 전량 격리 보관)
   ↓  대표 결재 (Decision Register APPROVED)
   ↓  ★ VERIFIED 항목만 통과
country_kpi_policy / country_kpi_presentation / default_metric_values 에 INSERT
   ↓
미국 농장 대시보드 · 경고 임계값
```

UNVERIFIED 는 `docs/kpi/` 에 **격리 보관만** 하고 코드·seed 에 반영하지 않는다.
결재 없이 코드에 들어가는 경로는 없다 — 리졸버가 `decision_status='APPROVED'` 행만
읽고, 그 fail-closed 동작은 게이트 L5 로 잠겨 있다.
