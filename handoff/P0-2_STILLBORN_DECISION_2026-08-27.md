# P0-2 결재 — 사산율 정의 + 임계값 (묶음 결정)

> # ⚠ §3 정정 (2026-08-27, Codex 독립검증)
>
> §3 이 44농장 전체를 "하베스트 참조" 로 표기했으나 실제는 **42 internal + 2 live** 다.
> 그리고 **live 2/2 가 모두 등급이 바뀐다**(`NONE→WARNING`, `NONE→CRITICAL`,
> 평균 gap 5.49%p — internal 2.37%p 의 2배 이상).
>
> → 이 결재는 "참조 데이터 정리" 가 아니라 **실고객이 이미 겪고 있는 표시 불일치의
> 해소**다. 우선순위가 올라간다. 상세: `docs/kpi/D20_DIVERGENCE_IMPACT.md` 상단.

```
작성    2026-08-27 · 대상 커밋 a2e813c
근거    D-13 §4-8 (LIVE_DIVERGENCE) · D-19 (threshold source) · D-20 (영향 정량화)
성격    ★ 두 항목을 한 묶음으로 결재한다. 산식만 고르면 반쪽 결재다 (§4)
population_scope  통계는 INTERNAL_REFERENCE (하베스트) 기준 — 실고객 표본 부족 (§3)
```

---

## 0. 결재받을 것 — 두 개다

```
① 사산율(STILLBORN_RATE) 정의를 무엇으로 확정할 것인가
② 그 정의에 적용할 warning / critical 임계값을 무엇으로 승인할 것인가
```

**①만 결재하면 승인 안 된 기준에 승인된 산식을 붙이는 상태가 된다.**
그리고 두 산식은 분자가 다르므로(미라 포함/제외) 같은 임계가 양쪽에 동시에 타당할 수 없다.

---

## 1. 현재 상태 — 코드에 두 산식이 동시에 live 다

| | 경로 ① | 경로 ② |
|---|---|---|
| 산식 | `stillborn ÷ total_born` | `(stillborn + mummified) ÷ total_born` |
| 위치 | `services/kpi_service.py:523` | `services/insight_service.py:211` |
| 진입 | 대시보드 · KPI · 룰엔진 | `POST /events/farrowings` 직후 인사이트 |
| 미라 | 제외 (`MUMMIFIED_RATE` 별도 지표 존재) | 포함 |
| 도달성 | LIVE | LIVE |

둘 다 **같은 metric_code** 로 **같은 임계값**에 대조된다.

---

## 2. ★ 현재 프로덕션 판정값 — 코드에 보이는 값이 아니다

`USE_GOVERNANCE_BENCHMARKS = False` 이므로 `_common.resolve()` 는
`rule_configs(0행) → default_metric_values → 인라인 상수` 를 탄다.

### 2-1. `default_metric_values` 실측 (프로덕션)

| scope | code | warning | critical | dir | threshold_basis | source_ref |
|---|---|---|---|---|---|---|
| region | **BR** | **8.20** | 12.00 | above | — | `Agriness2024` |
| region | KR | 8.00 | 12.00 | above | — | `PigPlan:PIGLET_DEATH_KPI_V1` |
| region | US | 8.00 | 12.00 | above | — | `PigCHAMP2023` |
| system | SYSTEM | 8.00 | 12.00 | above | `investigate_gt7_normal_5_10` | `PigCHAMP2023/NADIS/Le2022` |

### 2-2. resolver 최종값 실측 (로컬 재현, 배포·설정변경 없음)

```
stillborn.rate_high  최종 (warning / critical)

country   flag OFF (현재 prod)      flag ON (가상)
BR        8.20 / 12.00             8.00 / 12.00     ← 유일하게 달라진다
KR        8.00 / 12.00             8.00 / 12.00
US        8.00 / 12.00             8.00 / 12.00
SYSTEM    8.00 / 12.00             8.00 / 12.00
```

★ **BR 은 8.20 으로 판정되고 있다.** 코드 인라인 상수(8.0)도, `operational_defaults`(8.0)도
아니다. **"코드에 8/12 가 있다"로 결재안을 만들면 실제 판정값과 어긋난다.**

★ flag 를 켜면 BR 의 warning 이 8.20 → 8.00 으로 **조여진다.** 유일한 파일럿 국가다.
→ **승격·검증 전에 `USE_GOVERNANCE_BENCHMARKS` 를 켜지 않는다.**

### 2-3. ★ 승인 상태 — "현재 프로덕션값" ≠ "승인된 정책값"

| 소스 | 상태 |
|---|---|
| `rule_configs` | 0행 |
| `operational_defaults` | 29행, `origin` 29/29 = `code_default`. **flag OFF 라 읽히지도 않음** |
| `default_metric_values` | **실제 판정 소스.** `threshold_basis` 4행 중 1행만 존재 |

**결재를 거친 임계값은 시스템 전체에 0건이다.** 위 8.00/8.20/12.00 은 전부
"현재 프로덕션값"이지 "승인된 정책값"이 아니다.

### 2-4. ★ 임계값 출처가 서로 다른 정의에서 왔다 — 결정적

| row | source_ref | 그 출처의 사산 정의 |
|---|---|---|
| KR | `PigPlan:PIGLET_DEATH_KPI_V1` | 내부 문서상 **사산 + 미라** (= 경로 ②) |
| US | `PigCHAMP2023` | 사산과 미라를 **별도 행**으로 발표 (stillborn 1.18 / mummies 0.50, COUNT) → **사산만** (= 경로 ①) |

**같은 숫자 8.00 이 서로 다른 분자 정의에서 유도됐다.** 어느 산식을 고르든 최소한
한쪽 국가의 임계는 근거가 어긋난 상태로 남는다.
→ **①을 정하면 ②는 반드시 재산정 대상이다.** 재사용 가능 여부를 "검토"로 둘 수 없다.

> 참고: PigCHAMP2023 구성요소로 역산하면
> 사산만 `1.18 ÷ 15.84 = 7.45%` · 사산+미라 `1.68 ÷ 15.84 = 10.61%`.
> `default_metric_values` 의 US 값 8.00 은 **둘 중 어느 쪽과도 정확히 일치하지 않는다.**
> `threshold_basis` 가 비어 있어 유도 과정을 확인할 수 없다. **[UNVERIFIED]**

---

## 3. 선택에 따른 영향 (INTERNAL_REFERENCE 모집단)

> ★ 아래 수치는 `data_origin = pigplan_migration`(하베스트 참조) 42농장 기준이다.
> `native_signup`(실고객)은 최근 365일 분만 3건으로 **산출 불가**다.
> 실고객 예측치가 아니다 — 아키텍처 §2-1-A.

임계 8/12 적용 시 (44농장, 하베스트 참조):

| | 값 | severity 분포 |
|---|---|---|
| 경로 ① (사산만) | 평균 6.08% | none 33 · WARNING 10 · CRITICAL 1 |
| 경로 ② (사산+미라) | 평균 8.16% | none 20 · WARNING 16 · CRITICAL 8 |
| 등급이 달라지는 농장 | **17 / 44 (38.6%)** | 평균 격차 2.52%p · 최대 9.50%p |

★ 경로 ① ≤ 경로 ② 는 **산술적 필연**이다(분자가 부분집합, 분모 동일).
"경로 ①이 항상 관대하다"는 발견이 아니라 정의상 그렇다. 데이터인 것은 **격차 크기와
등급 변경 비율뿐**이다.

---

## 4. 결정표

| 결정항목 | **선택지 A — 사산만** | **선택지 B — 사산 + 미라** |
|---|---|---|
| 산식 | `stillborn ÷ total_born` | `(stillborn + mummified) ÷ total_born` |
| 현재 코드 대응 | 경로 ① (대시보드) | 경로 ② (이벤트 인사이트) |
| 현재 prod threshold | BR 8.20 / 그 외 8.00 · crit 12.00 | 동일 (같은 행을 공유) |
| legacy/code threshold | 8.0 / 12.0 (인라인 + `operational_defaults`) | 동일 |
| 승인 이력 | **없음** (`threshold_basis` 1/4, `origin=code_default`) | **없음** |
| 동일 threshold 재사용 | **부분 가능** — US 행이 PigCHAMP(사산만)에서 왔으므로 정합. KR 행은 PigPlan(사산+미라) 유도라 재검증 필요 | **불가** — 값이 구조적으로 상승하므로 8.00 은 과민. 전 국가 재산정 필수 |
| 외부 벤치마크 대조 | **직접 가능.** PigCHAMP·MetaFarms 가 사산/미라를 분리 발표 | 불가. 합산 지표를 내는 공개 출처가 드묾 |
| `MUMMIFIED_RATE` 중복 | 없음 (별도 지표로 병존) | **중복 발생** — 미라가 두 지표에 이중 계상 |
| 질병 신호 민감도 | 낮음 (미라 급증을 사산율이 못 잡음) | 높음 (PRRS 등 미라 급증을 조기 포착) |
| 하베스트 42농장 영향 | WARNING↑ 10 · CRITICAL 1 | WARNING↑ 16 · CRITICAL 8 |
| 필요한 조치 | 경로 ② 를 ① 로 정렬 + 회귀테스트 + KR 임계 재검증 + D-13 재실사 | 경로 ① 을 ② 로 정렬 + **전 국가 임계 재산정** + `MUMMIFIED_RATE` 처리 결정 + D-13 재실사 |

### 4-1. 실무 권고 — A

근거 셋.
1. **외부 대조 가능성.** D-8 mapping 이 목전이고, PigCHAMP·MetaFarms 가 사산과 미라를
   분리 발표한다. A 는 1:1 mapping 이 서지만 B 는 `APPROVED_TRANSFORM` 이 필요하고
   그 변환의 구성요소 유일성은 증명되지 않았다(아키텍처 §3-4).
2. **`MUMMIFIED_RATE` 중복 회피.** 별도 지표가 이미 있고 임계(2/4)도 있다.
3. **사용자가 보는 값이 이미 A 다.** 대시보드가 경로 ①이므로 변경 폭이 작다.

**단, B 의 장점(미라 급증 조기 포착)은 실재한다.** A 를 택하면
`MUMMIFIED_RATE` 룰(`mummified.rate_high`, 2/4)이 그 역할을 대신하는지
별도 확인이 필요하다 — 현재 그 룰이 어느 화면에 노출되는지 미확인.

### 4-2. ②(임계값) 결재 방식 — 두 갈래

| | 내용 |
|---|---|
| **B-1. 현재값 승격** | `default_metric_values` 의 현재값을 그대로 `approved_policy` 로 승격. BR 8.20 유지 · 나머지 8.00. **KR 행은 PigPlan(사산+미라) 유도라 A 선택 시 근거 불일치가 남는다** |
| **B-2. 재산정** | 국가별로 출처를 명시해 재유도. US 는 PigCHAMP 구성요소로 역산(7.45%) 가능. KR·BR 은 원출처 재확인 필요 |

**권고 B-2.** B-1 은 근거 없는 값을 결재로 세탁하는 것이 된다.
다만 B-2 는 D-15(MetaFarms 원문 실사) 결과를 기다려야 하므로,
**잠정적으로 현재값을 `provisional` 로 두고 D-15 후 확정**하는 3안도 가능하다.

---

## 5. 결재 후 반드시 남는 것 — `APPROVED ≠ CONFIRMED`

```
①·② 결재 (APPROVED)
   ↓  경로 정렬 (code alignment) — 두 산식 중 하나를 제거
   ↓  회귀 테스트 (두 경로가 같은 값을 내는지 잠금)
   ↓  D-13 재실사
CONFIRMED  →  비로소 D-8 mapping 대상
```

★ 결재만으로 실행 코드가 하나가 되지 않는다. 두 경로가 모두 live 인 상태에서
문서만 하나가 되면 그것도 위조 우회로다.

★ 그리고 **`USE_GOVERNANCE_BENCHMARKS` 토글은 별도 배포 스텝**이다.
켜는 순간 32룰의 임계 소스가 통째로 바뀌고 BR 이 8.20 → 8.00 으로 조여진다.
결재·정렬과 같은 배포에 넣지 않는다.

---

## 6. 미확인으로 남긴 것

| # | 항목 |
|---|---|
| 1 | `default_metric_values` US 8.00 의 유도 근거 — PigCHAMP 역산과 불일치, `threshold_basis` 없음 **[UNVERIFIED]** |
| 2 | KR 8.00 이 PigPlan 의 어느 정의에서 왔는지 원문 미확인 |
| 3 | BR 8.20(Agriness2024)의 분자 정의 미확인 |
| 4 | `mummified.rate_high`(2/4) 룰이 실제로 어느 화면에 노출되는지 |
| 5 | 실고객 모집단 영향 — 표본 3건으로 산출 불가. 고객 증가 후 재측정 |
