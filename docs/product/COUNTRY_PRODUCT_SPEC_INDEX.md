# Country Product Spec — 인덱스

> **v0.1** · 2026-08-24 · 전 국가 표시 정책의 지도
> 국가를 켤 때 **무엇이 있고 무엇이 비었는지**를 한 표로 본다.
> 빈칸은 빈칸으로 둔다 — 채워 넣은 추정값이 틀린 기준으로 경고를 띄우는 것보다 낫다.

---

## 0. 문서 4층 — 무엇이 어디에 있나

같은 "국가별 KPI" 라는 말이 네 가지 다른 것을 가리킨다. 섞으면 안 된다.

| 층 | 질문 | 문서 | 상태 |
|---|---|---|---|
| 기술 | 상속·게이트·런타임이 어떻게 도나 | `specs/COUNTRY_KPI_RULE_SPEC_v0.3.1.md` | DRAFT (v0.4 개정 중) |
| 값 | 나라별 벤치마크 수치가 얼마인가 | `specs/2026-06-17_country-kpi-differences.md` | 부분 확보(아래 §2) |
| 정의 | 분모·포함규칙이 나라마다 다른가 | `specs/COUNTRY_KPI_DEFINITION_MATRIX.md` | Phase B, **미구현** |
| **표시** | **뭘 보여주고 뭐라 부를 것인가** | `product/COUNTRY_PRODUCT_SPEC_<CC>.md` | **BR 만 존재** |

⚠️ `docs/kpi/gpt_country_draft_UNVERIFIED.md` 는 **격리 문서**다. GPT 가 만든 국가별 KPI 표인데
인용 기관이 원문 대조된 적이 없다. 어떤 값도 사실로 쓰지 않는다.

---

## 1. 국가별 현황 (프로덕션 실측 2026-08-24)

| 국가 | 농장 | 타겟 | 표시 정책 | headline | 현지명 | 상태 |
|---|---|---|---|---|---|---|
| **BR** | 6 | ✅ LatAm | **PSY · FARROWING_RATE · NPD** | PSY | 확정 3 | **ACTIVE** |
| US | 17 | ✅ | — | — | — | GLOBAL 상속 |
| CN | 10 | ✅ | — | — | — | GLOBAL 상속 |
| VN | 4 | ✅ SEA | — | — | — | GLOBAL 상속 |
| TH | 3 | ✅ SEA | — | — | — | GLOBAL 상속 |
| KR | 8 | 레퍼런스 전용 | — | — | — | GLOBAL 적용 (K-01-4) |
| MX | 5 | ❌ 비타겟 | — | — | — | **UNKNOWN** (K-01-3) |
| PH | 4 | ❌ | — | — | — | **UNKNOWN** |
| DE | 2 | ❌ | — | — | — | **UNKNOWN** |
| ES | 2 | ❌ | — | — | — | **UNKNOWN** |
| DK | 1 | ❌ | — | — | — | **UNKNOWN** |
| NL | 1 | ❌ | — | — | — | **UNKNOWN** |

**12개국 65농장 중 표시 정책이 있는 건 BR 하나뿐이다.** 나머지는 GLOBAL 기본값
(`PSY`·`NPD`·`FARROWING_RATE` 3개, K-01-1)을 상속한다.

> UNKNOWN 6개국(MX·PH·DE·ES·DK·NL, 21농장)은 농장 성격이 확인되지 않았다.
> 하베스트 산물인지 실고객인지 모르는 상태에서 어느 쪽으로도 단정하지 않는다.
> 분류(CUSTOMER/PILOT/HARVEST/TEST/INTERNAL/UNKNOWN) 전까지 노출 확대 금지.

---

## 2. 값(벤치마크) 확보 현황

`specs/2026-06-17_country-kpi-differences.md` 기준. **검증 출처가 있는 것만** 실린다.

| 국가 | 확보 지표 수 | 출처 |
|---|---|---|
| US | 9 | PigCHAMP / SMS |
| KR | 8 | PigPlan 실데이터 + 한돈팜스 |
| BR | 7 | Agriness 2024 |
| CN | 6 | WEPIG 2025 |
| VN | 6 | Agriness VIE (29농장 proxy, **low confidence**) |

미확보 표시 **14곳**. TH·MX·PH·DE·ES·DK·NL 은 **자료 자체가 없다.**

다루는 지표: `PSY` · `FARROWING_RATE` · `BORN_ALIVE` · `WEANED_COUNT` ·
`PRE_WEANING_MORTALITY` · `WSI` · `RTS_RATE` · `STILLBORN_RATE` · `SOW_MORTALITY`

---

## 3. 국가 하나를 켜는 데 필요한 것

BR 을 켤 때 실제로 필요했던 것들이다. 다음 국가도 같다.

```
1  표시할 KPI 결정        제품 판단 — 외부 조사로 대체 불가
2  표시 순서 · headline    〃
3  현지 명칭 확정          외부 조사 필요. ★ 기계번역 금지, 업계 실사용 용어만
4  대시보드 페이로드 확인   그 KPI 값이 실제로 내려오는가 (metrics 맵)
5  벤치마크·임계 확보 여부  없으면 severity 를 그 나라 기준인 것처럼 만들면 안 됨
6  COUNTRY_PRODUCT_SPEC_<CC>.md 작성 → seed → 게이트 → 배포
```

**4번이 자주 걸린다.** BR full target 7개 중 3개가 페이로드에 값이 없어 못 켰다
(`1d07768` 로 해소). 새 지표를 켜기 전에 `metrics` 에 실리는지 먼저 확인한다.

**5번을 건너뛰면 위조가 된다.** 카드를 표시하는 것과 "이 나라 기준으로 정상/주의"를
판정하는 것은 다른 축이다. benchmark 미승인 상태에서 severity·비교문구를 만들지 않는다.

---

## 4. 다음에 켤 국가 — 준비도

| 국가 | 값 자료 | 현지명 | 표시 결정 | 판단 |
|---|---|---|---|---|
| **US** | ✅ 9지표 (PigCHAMP/SMS) | ❌ | ❌ | **가장 준비됨.** 영어권이라 현지명 부담도 적다 |
| CN | ✅ 6지표 (WEPIG 2025) | ❌ | ❌ | 값은 있음. 중국어 명칭 조사 필요 |
| VN | △ 6지표 (proxy, low conf) | ❌ | ❌ | 표본 29농장 proxy — 신뢰도 확인 필요 |
| TH | ❌ 없음 | ❌ | ❌ | 조사부터 |

**US 가 다음 순서다.** 그리고 US 는 Template LOCK 의 시험대이기도 하다 —
**코드 변경 0으로 데이터만 넣어서 되는지**가 이 구조 전체의 합격 기준이다.

---

## 5. 외부 조사 의뢰 시 지켜야 할 것

`gpt_country_draft_UNVERIFIED.md` 가 왜 격리됐는지가 답이다. 표는 다 채워져 왔는데
인용 기관이 원문 대조된 적이 없었다. 그런 값이 코드에 들어가면 **미국 농장에 잘못된
기준으로 경고가 뜬다.**

```
출처       URL 또는 발간물명 + 페이지. "업계 통념" 금지
연도       source_year 없으면 UNVERIFIED
표본       cohort(농장 수·지역·기간) 없으면 UNVERIFIED
빈칸       모르면 "미확보". 추정·보간·유추 금지
현지명     그 나라 업계가 실제 쓰는 용어만. 기계번역 금지
국가 묶기   금지("EU 공통" 같은 것). 나라별로 따로
```

조사 결과는 **[VERIFIED] / [UNVERIFIED] 태그를 항목마다** 달아 받는다.
UNVERIFIED 는 `docs/kpi/` 에 격리 보관하고 코드·seed 에 반영하지 않는다.

---

## 6. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v0.1 | 2026-08-24 | 신설. 프로덕션 12개국 65농장 실측 · 문서 4층 정리 · US 를 다음 순서로 판정 |
