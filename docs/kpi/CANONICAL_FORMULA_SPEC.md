# CANONICAL_FORMULA_SPEC

> # ⚠ 반증됨 — 재실사 필요 (2026-08-27, Codex 독립검증 + 자체 추가 발견)
>
> **§3 의 `CONFIRMED 7` 과 §6 의 `NPD/WEI verdict: CLEAN` 은 무효다.**
> "경로가 하나임을 확인" 한 것이 아니라 **하나만 찾은 것**이었다.
>
> ### ① 단일 경로 판정 무효 (Codex C-2 REFUTED)
>
> | KPI | 추가로 발견된 live 경로 |
> |---|---|
> | FARROWING_RATE | 보고서 동기간 `farrowings/matings` `report_service.py:182` · snapshot job `jobs/kpi.py:138-144` |
> | WSI | REST mating insight 단일 이벤트 간격 `insight_service.py:244-257` |
> | WEANED_PER_LITTER | REST weaning insight 단건 `insight_service.py:219-230` · 보고서 복별 평균 `report_service.py:175-179` |
> | PSY | snapshot job 별도 산식 `jobs/kpi.py:132-135` (latent writer — 현재 reader 없음) |
>
> 보고서 경로에는 사산·PWM 산식도 따로 있다(`report_service.py:185-197`) — 웹에 실제
> 표시된다(`src/app/(app)/reports/reproduction/page.tsx:40-44`). C-1 의 divergence 목록도
> 완전하지 않았다.
>
> ### ② ★ `NPD/WEI CLEAN` 은 틀렸다 — 오염이 재발해 있다 (자체 발견, Codex 도 놓침)
>
> ```sql
> -- kpi_service.py get_trend()  →  GET /kpi/trend (kpi.py:112, 프론트 소비 kpi.ts:10-12)
> npd_by_month AS (
>     SELECT date_trunc('month', weaning_date)::date AS m,
>            AVG(wei_days) AS avg_npd        ← WEI 다. 여집합 NPD 가 아니다
>     FROM wei_rows )
> ...
> KpiTrend(npd=row.npd)                      ← npd 필드에 WEI 가 담긴다
> ```
>
> **M1 STEP 1 이 고친 그 오염이 트렌드 경로에 그대로 남아 있다.**
> 실행 스펙 §4 가 "변수명·필드명만으로 NPD/WEI 를 판정하지 마라" 고 이름까지 붙여
> 경고한 지점에서, `calculate_npd` 하나만 읽고 CLEAN 을 찍었다.
> 같은 함수의 `farrowing_rate` 도 동월 나눗셈이라 코호트 산식이 아니다.
>
> → **verdict 를 `CONTAMINATED` 로 정정한다.**
>
> ### ③ 그 밖의 판정 조정
>
> - §9 모바일 — iOS 에 **현재 `benchmarks` 모델과 표시 코드가 있다.** "benchmark 필드
>   자체가 없다" 는 서술은 낡았다(Codex C-4 OVERSTATED). 하드코딩·presentation
>   미소비는 양쪽 다 유효.
> - §7-3 `_avg_active_inventory` 결함은 **CONFIRMED** — 운영 internal-reference 에
>   해당 행 110,010개(후보돈 13,779 / 산차돈 96,231). live 표본에는 0개.
> - Template LOCK 은 **resolver 계약 10건에 한해** 통과. "제품 전체가 INSERT 만으로
>   활성화된다" 는 결론은 과장이다(HTTP·모바일·threshold·권한 범위 밖).
>
> ### ④ 결론
>
> **현 상태로 D-8 mapping 에 넘길 수 없다.** `CONFIRMED` 7건 중 최소 4건이 재판정
> 대상이고, 전 경로(서비스·보고서·인사이트·job·trend)를 관통한 D-13 재실사가 필요하다.
> 상세 근거: `handoff/CODEX_RESULT_2026-08-27.md`

```
CANONICAL_FORMULA_SPEC : PigOS 내부 계산 의미
COUNTRY_KPI_RULE_SPEC  : 국가 정책·표시·룰 적용

관계: CANONICAL_FORMULA_SPEC 이 COUNTRY_KPI_RULE_SPEC 의 입력이다.
      산식 변경은 CANONICAL_FORMULA_SPEC 에서만 정의한다.
      국가 표시 정책이 canonical formula 를 재정의해서는 안 된다.
```

---

## 0. Status

| 항목 | 값 |
|---|---|
| audit_date | 2026-08-27 |
| run_spec | `docs/runs/RUN_PROMPT_D13_canonical_formula_audit.md` v1.4 |
| machine | `bjh` |
| pigos_commit | `70a56a9cb825d07e69a4049a71cdccd8460e6bfa` |
| android_commit | `75458412b99e726424a580a784d51cd677c0ad7c` |
| ios_commit | `14bf8b01ef38b3a5889c29abb73a722f5aeb05bc` |
| alembic_heads | `f3c6a8d0b2e4` — **단일 head** |
| test_collection_cmd | `uv run python -m pytest --collect-only -q -p no:cacheprovider` (`PYTHONDONTWRITEBYTECODE=1`) |
| collected_tests | 1292 |
| audit_scope | IN_SCOPE 9 · DEFERRED 다수 (§2) |
| source_of_truth | **실행 코드 본문.** 문서·필드명·설계의도·도메인 상식 불채택 |

> **D-13 RUN PASS ≠ 모든 KPI CONFIRMED.** AMBIGUOUS·UNKNOWN 은 실패가 아니다.
> 근거 없이 CONFIRMED 를 만드는 것이 실패다.

---

## 1. Scope / Non-Scope

**Scope** — raw data → KPI 값 (분자/분모/기간/as_of/단위/scope)

**Non-Scope**
- KPI 값 → Threshold Resolver → severity → 색상 (**D-19**)
- Benchmark Context Resolver
- 외부 benchmark 조사(D-15) / 외부 정의 대조(D-8)
- 국가별 KPI 정책 수정 · Rule Engine 리팩터링

**이 문서에 외부 benchmark 수치·출처가 없다.** 관련 관찰은 전부 D-8 입력으로 보낸다.

---

## 2. KPI Identifier Discovery (STEP 1)

`api/app` + `api/tests` 스캔, 51개 파일 486건 매치.

| discovered_name | location | role | canonical_candidate | audit_scope | notes |
|---|---|---|---|---|---|
| `calculate_psy` | `services/kpi_service.py:60` | A | PSY | IN_SCOPE | |
| `calculate_npd` / `_NPD_SQL` | `services/kpi_service.py:127,216` | A | NPD | IN_SCOPE | 여집합 방식 |
| `sow_turnover` | `services/kpi_service.py:234` | A | SOW_TURNOVER | IN_SCOPE | NPD 산출물에 동거 |
| `_cohort_farrowing_rate` | `services/kpi_service.py:370` | A | FARROWING_RATE | IN_SCOPE | |
| `STILLBORN_RATE` | `services/kpi_service.py:523` | A | 사산 계열 | IN_SCOPE | **경로 ①** |
| `STILLBORN_RATE` | `services/insight_service.py:211` | A | 사산 계열 | IN_SCOPE | **경로 ② — 산식 다름** |
| `MUMMIFIED_RATE` | `services/kpi_service.py:524` | A | 사산 계열 | IN_SCOPE | 별도 지표 |
| `pwmr` / `PRE_WEANING_MORTALITY` | `services/kpi_service.py:512` | A | PRE_WEANING_MORTALITY | IN_SCOPE | **경로 ①** |
| `PRE_WEANING_MORTALITY` | `services/insight_service.py:229` | A | PRE_WEANING_MORTALITY | IN_SCOPE | **경로 ② — 산식 다름** |
| `MSY` | `services/kpi_service.py:559` | A | MSY | IN_SCOPE | |
| `WSI` | `services/kpi_service.py:425` | A | WSI | IN_SCOPE | |
| `WEANED_COUNT` | `services/kpi_service.py:530` | A | WEANED_PER_LITTER | IN_SCOPE | 실질 per-litter |
| `weaning_to_mating_days` | `services/kpi_service.py:238` | B | (WEI alias) | IN_SCOPE | §6 |
| `STILLBORN_RATE` 등 | `db/global_policy_defaults.py`, `db/br_pilot_seed.py` | D | — | — | presentation identifier |
| `stillborn` / `mummified` | `db/models/events.py:85-86` | C | — | — | DB 컬럼 |
| `stillborn.rate_high` | `db/operational_defaults_seed.py:23` | D | — | — | threshold 레지스트리 → D-19 |
| `MAX_STILLBORN` | `validators/farrowing.py:17` | — | — | — | 입력 검증 상수 |
| `postweaning_survival` | — | — | — | — | **PigOS 실물에 없음.** `FINISH_MORTALITY` 가 인접하나 동일 지표 아님 |
| `PWM` | — | — | — | — | 외부 용어. PigOS 실물 없음 |

**DEFERRED** (우선범주 밖, 목록만): `ADG` `FCR` `RTS_RATE` `ABORTION_RATE` `BORN_ALIVE` `TOTAL_BORN` `BIRTH_WEIGHT` `WEANING_WEIGHT` `WEANING_AGE` `FINISH_MORTALITY` `CULLING_RATE` `SOW_MORTALITY` `HIGH_PARITY_RATIO` `REPLACEMENT_RATE` `SECOND_LITTER_DROP` `ACCIDENT_P1_RATIO` `SUMMER_FARROW_DROP` `CONCEPTION_RATE` `CRUSHING_RATE` `DEATH_AGE_0_3_RATIO` `BATCH_DOW_CONCENTRATION`

> `DEFERRED` 는 audit 범위 상태이지 implementation status 가 아니다.

---

## 3. Canonical KPI Summary

| code | formula_id | v | measure_kind | output_unit | direction | status |
|---|---|---|---|---|---|---|
| PSY | `PSY_ROLLING12M` | 1 | RATIO | pigs/sow/year | UNKNOWN | **REVOKED → UNVERIFIED** |
| NPD | `NPD_COMPLEMENT_SOWYEAR` | 1 | DURATION | days/sow-year | UNKNOWN | **REVOKED → UNVERIFIED** (trend 오염) |
| SOW_TURNOVER | `SOW_TURNOVER_FARROWINGS_PER_INV` | 1 | RATIO | litters/sow/year | UNKNOWN | **PENDING_RECHECK** (기준 ②③ 미충족) |
| FARROWING_RATE | `FARROWING_RATE_COHORT_110_150` | 1 | RATE | percent_0_100 | UNKNOWN | **REVOKED → UNVERIFIED** |
| WSI | `WSI_WEAN_TO_SERVICE` | 1 | DURATION | days | UNKNOWN | **REVOKED → UNVERIFIED** |
| MSY | `MSY_HEADOUT_PER_INV` | 1 | RATIO | pigs/sow/year | UNKNOWN | **PENDING_RECHECK** ⚠ §7-3 |
| WEANED_PER_LITTER | `WEANED_AVG_PER_WEANING` | 1 | COUNT | pigs/litter | UNKNOWN | **REVOKED → UNVERIFIED** |
| 사산 계열 | — | — | RATE | percent_0_100 | UNKNOWN | **AMBIGUOUS · LIVE_DIVERGENCE** |
| PRE_WEANING_MORTALITY | — | — | RATE | percent_0_100 | UNKNOWN | **AMBIGUOUS · LIVE_DIVERGENCE** |

> `performance_direction` 전건 `UNKNOWN` / `NONE_IN_FORMULA_LAYER`.
> 방향은 계산 계층이 아니라 `operational_defaults.direction` 에 있고, 그 계층은 §0-5 로 감사 제외했다.
> **"사산율이니까 LOWER_IS_BETTER" 는 코드-only 원칙 위반이라 쓰지 않았다.**
>
> AMBIGUOUS 2건에는 §3 규율대로 확정 `formula_id` 를 부여하지 않았다.

### ★ CONFIRMED 판정 기준 (2026-08-27 신설 — 재실사부터 적용)

`CONFIRMED 7` 중 4건이 무효였다는 것은 **검증 절차 자체에 결함이 있었다**는 뜻이다.
같은 절차로 재실사하면 재실사 결과도 뒤집힌다. 그래서 기준을 먼저 고정한다.

```
셋을 동시에 충족해야만 CONFIRMED
  ① 실제 코드 라인 인용 (파일:행)
  ② 해당 산식의 테스트 통과
  ③ 실데이터 1건 수기 검산 일치

하나라도 빠지면 UNVERIFIED. 문서 대조만으로 CONFIRMED 금지.

★ 이 기준을 소급 적용하면 **기존 7건 전부가 미충족**이다(②③ 을 한 건도 하지 않았다).
  반증된 5건은 REVOKED, 반증되지 않은 2건은 PENDING_RECHECK 다.
  "반증 안 됐으니 유효" 는 이 기준의 정반대다 — 입증 책임은 CONFIRMED 쪽에 있다.
```

### 재실사 완료 기준 — 탐색이 아니라 열거

"전 경로를 안 훑었으므로 더 있을 수 있다" 가 끝나고도 남으면 그건 재실사가 아니라
**부분 탐색 3회차**다. `/kpi/trend` 사례가 방향을 알려준다 — **필드명은 `npd` 인데
값은 WEI 였다.** 산식 함수에서 호출자로 내려가는 추적만으로는 이걸 못 잡는다.

```
A. 산식 함수 → 호출자 역추적 (call graph 전수)
B. 응답 스키마 필드명 → 실제 담기는 산식 대조표
   서비스 · 보고서 · 인사이트 · job · trend 전 경로

완료 기준 = A ∩ B 교차 대조.  A 만 하면 오늘과 같은 결과가 나온다.
```

---

## 4. KPI Detail

### 4-1. PSY — CONFIRMED

```
formula_id            PSY_ROLLING12M  v1
numerator             SUM(weanings.weaned_count)
                        WHERE deleted_at IS NULL
                          AND weaning_date ∈ (ref − 12 months, ref]
denominator           AVG over 12 month-starts of
                        COUNT(sows) WHERE parity >= 1
                          AND entry_date <= m
                          AND (exit_date IS NULL OR exit_date >= m)
population_basis      경산돈(parity>=1). 후보돈 제외 — 코드 주석이 PigPlan 035001 정합 명시
excluded_components   후보돈(parity=0) · exit_date 지난 모돈
aggregation_scope     FARM
time_window           rolling 12 months, month-start 표본
as_of_semantics       PARAMETERIZED (ref_date 인자)
zero_denominator      avg_inv < 1  →  psy = None (폭발값 방지)
null_handling         이유 0건 → psy = 0.0 (None 아님)
rounding              round(x, 2)
country_override_path 없음
implementation        services/kpi_service.py:60-121
threshold_boundary    반환 후 rule engine / assemble_kpi_status
```

★ **`deleted_at` 을 재고 판정에 쓰지 않는다.** docstring 이 그 이유를 남겨놨다 —
soft-delete 되지 않은 하베스트 데이터에서 도폐사 모돈이 재고를 영구 부풀려 PSY 를
급락시켰다. **exit_date 로만 판정한다.** (§7-3 과 대조할 것)

### 4-2. NPD — CONFIRMED

```
formula_id            NPD_COMPLEMENT_SOWYEAR  v1
formula               365 × (사육일 − 임신일 − 포유일) / 사육일
                      npd_days = max(0, sow_days − (preg_days + lact_days))
sow_days              Σ clip(exit|ref) − clip(entry|ref−365), parity>=1
preg_days             완결분: Σ LEAST(farrowing_date, ref, mating_date+130)
                                − GREATEST(mating_date, w0, entry_date)
                      진행중(preg_open): 최근 교배 ≤130일 & 후속 분만 없음 & ref 시점 재고
lact_days             완결분: Σ LEAST(weaning_date, ref, farrowing_date+70)
                                − GREATEST(farrowing_date, w0, entry_date)
                      진행중(lact_open): 최근 분만 ≤70일 & 후속 이유 없음 & ref 시점 재고
population_basis      경산돈(parity>=1) — PSY 분모와 동일 정의
aggregation_scope     FARM
time_window           [ref − 365, ref]
as_of_semantics       PARAMETERIZED
zero_denominator      sow_days <= 0 → None
rounding              round(x, 1)
implementation        services/kpi_service.py:127-256
```

★ 완결 이벤트에 **sanity 상한 클립**(임신 130 / 포유 70)을 적용하되 **행을 drop 하지 않는다**
— 유모돈(fostering) 보존이 이유라고 코드가 명시한다.
★ 진행중 꼬리는 `status` 컬럼이 아니라 **이벤트 기반**으로 판정한다(status 비의존).

### 4-3. SOW_TURNOVER — CONFIRMED

```
formula_id   SOW_TURNOVER_FARROWINGS_PER_INV  v1
numerator    COUNT(farrowings) WHERE parity>=1 모돈 AND farrowing_date ∈ [ref−365, ref]
denominator  AVG(월초 경산 재고)   ← PSY/NPD 와 동일 inv CTE
as_of        PARAMETERIZED     zero_den → None     rounding round(x,2)
implementation  services/kpi_service.py:202-234
```

### 4-4. FARROWING_RATE — CONFIRMED

```
formula_id   FARROWING_RATE_COHORT_110_150  v1
분모         COUNT(DISTINCT matings) WHERE mating_number = 1
               AND mating_date ∈ [ref−150, ref−110]
               AND NOT EXISTS(removals: type='DEAD',
                              removal_date ∈ [mating_date, mating_date+115])
분자         COUNT(DISTINCT farrowings) — 위 교배에 mating_id 로 연결된 것
measure_kind RATE   output_unit percent_0_100   rounding round(x,1)
zero_den     mated = 0 → None (날조 금지)
as_of        PARAMETERIZED (ref 인자) — 단 호출부는 §7-1 참조
implementation  services/kpi_service.py:370-386
```

★ **코호트 방식이다.** 같은 기간의 farrowings/matings 를 나누는 비코호트 방식은
서로 다른 개체를 비교해 두수 변동에 왜곡된다고 코드가 명시한다.
★ 교배 후 115일 내 폐사 모돈을 분모에서 제외한다 — 분만 기회가 없던 개체다.

### 4-5. WSI — CONFIRMED

```
formula_id  WSI_WEAN_TO_SERVICE  v1
value       AVG(mating_date − (직전 weaning_date ≤ mating_date))
            대상: mating_date ∈ [today−365, today], wsi >= 0 인 것만
measure_kind DURATION   output_unit days   rounding round(x,1)
implementation  services/kpi_service.py:425-429
```

⚠ `wsi >= 0` 필터가 있어 음수(데이터 오류)는 조용히 제외된다 — 건수는 남지 않는다.

### 4-6. MSY — CONFIRMED (분모 주의)

```
formula_id   MSY_HEADOUT_PER_INV  v1
numerator    SUM(finisher_groups.head_count_out)
               WHERE end_date ∈ [today−365, today] AND 완결 그룹
denominator  _avg_active_inventory(farm, today−365, today)   ← ★ PSY 분모와 다르다
zero_den     avg_inv < 1 → 0.0 처리 → None
null         출하 데이터 없으면 None (오발화 방지)
rounding     round(x,1)
implementation  services/kpi_service.py:559-560, 348-367
```

⚠ **§7-3 을 반드시 함께 읽을 것.** 분모가 PSY/NPD 의 재고 정의와 다르다.

### 4-7. WEANED_PER_LITTER — CONFIRMED

```
formula_id  WEANED_AVG_PER_WEANING  v1
value       AVG(weanings.weaned_count) WHERE weaning_date ∈ [today−365, today]
measure_kind COUNT   output_unit pigs/litter   rounding round(x,1)
```

★ 코드의 identifier 는 `WEANED_COUNT` 지만 계산은 **이유 이벤트당 평균**이므로
의미상 per-litter 다. 이름이 COUNT 라고 총합이 아니다.

### 4-8. 사산 계열 — **AMBIGUOUS · LIVE_DIVERGENCE**

같은 metric_code `STILLBORN_RATE` 를 **두 live 경로가 다른 분자로** 계산한다.

```
경로 ①   STILLBORN_RATE = stillborn / total_born × 100     (미라 제외)
         MUMMIFIED_RATE = mummified / total_born × 100     (별도 지표)
  loc    services/kpi_service.py:523-524
  reach  LIVE — GET 대시보드/KPI
         → kpi_service.get_dashboard:846 · build_rule_context:650
         → build_herd_kpis:389 → :523
  window rolling 365d, 농장 전체 집계

경로 ②   STILLBORN_RATE = (stillborn + mummified) / total_born × 100   (미라 포함)
  loc    services/insight_service.py:208-211
  reach  LIVE — POST /events/farrowings
         → routers/base/events.py:141 → :155 _attach_insights
         → insight_service.analyze_event:263 → analyze_farrowing:205 → :211
  window 단일 분만 이벤트

divergence_severity : LIVE_DIVERGENCE   (양 경로 모두 path_reachability = LIVE)
```

★ 두 경로가 **같은 metric_code 로 같은 임계·벤치마크에 대조된다.** 즉 하나의
`STILLBORN_RATE` 기준값이 서로 다른 두 측정치를 채점하고 있다.

★ **아키텍처 v1.1 §3-4 의 서술과 코드가 어긋난다.** 문서는 PigOS 사산공식을
`(stillborn + mummified) ÷ total born` 으로 단정하는데, 이는 **경로 ② 만 맞고
경로 ① 은 틀리다.** "관행 대비 ~3%p 높다"는 진단도 경로 ② 에만 성립한다.
→ §8 · §10 참조. **D-8 mapping 금지 대상이다.**

### 4-9. PRE_WEANING_MORTALITY — **AMBIGUOUS · LIVE_DIVERGENCE**

```
경로 ①   pwmr = deaths / (weaned + deaths) × 100
         deaths = Σ piglet_events.piglet_count WHERE event_type='DEATH'
  loc    services/kpi_service.py:512  (별칭 PWMR 도 동일값, :525-526)
  reach  LIVE — build_herd_kpis (경로 ①과 동일 진입)
  성격   이벤트 기록 기반. DEATH 로 기록되지 않은 감모는 분자에 안 잡힌다

경로 ②   pwm = (born_alive − weaned_count) / born_alive × 100
  loc    services/insight_service.py:227-230
  reach  LIVE — POST /events/weanings
         → routers/base/events.py:236 → :250 _attach_insights
         → analyze_event:263 → analyze_weaning:219 → :230
  성격   차감 추정. 폐사·전출·미기록 감모가 전부 분자에 들어간다

divergence_severity : LIVE_DIVERGENCE
```

★ 분모도 다르다 — ① 은 `weaned + deaths`, ② 는 `born_alive`. 유모돈(fostering)이
있으면 두 값은 구조적으로 벌어진다.

---

## 5. Alias / Legacy / Field-name Risks

| 항목 | 내용 |
|---|---|
| `PWMR` ↔ `PRE_WEANING_MORTALITY` | `kpi_service.py:525-526` 에서 **같은 값을 두 키로** 반환. 룰 호환용 별칭 |
| `PRE_WEANING_MORTALITY` → `PWMR` | `kpi_service.py:335-336` 벤치마크 키 별칭 매핑 (시드는 `PRE_WEANING_MORTALITY`, 룰은 `PWMR`) |
| `WEANED_COUNT` | 이름은 COUNT 지만 **이유당 평균**(§4-7) |
| `STILLBORN_RATE` (role D) | `global_policy_defaults` / `br_pilot_seed` 의 것은 presentation identifier — 계산 코드명과 별개 |
| `benchmark_service.py:227` | `STILLBORN_RATE → "stillbirth_rate"`, `MUMMIFIED_RATE → "mummy_rate"` 외부 키 매핑 |
| `v_sow_npd` | DB view, `CURRENT_DATE` 의존. **현재 계산 경로에서 미사용** — repository 로 대체됨(`kpi_service.py:236-240`) |

---

## 6. NPD / WEI Contamination Audit

```
npd identifier      services/kpi_service.py:216 calculate_npd / _NPD_SQL:127
npd 실제 계산 의미   365 × (사육일 − 임신일 − 포유일) / 사육일  — 여집합
                    ★ weaning→mating 간격이 아니다

wei identifier      services/kpi_service.py:238 npd_repo.avg_wei_days
                    → NpdBreakdown.weaning_to_mating_days (별도 필드)
wei 실제 계산 의미   이유 → 차기 교배 간격 평균, as_of=ref_date 로 재현 가능

계층별 일관성
  backend        분리 확인 (다른 함수·다른 필드)
  API response   NpdBreakdown.avg_npd  vs  .weaning_to_mating_days — 분리
  android        DashboardScreen.kt:101 KpiCard("NPD", data.npd) — NPD 단독 표시
  ios            DashboardScreen.swift:163 kpiCell("NPD", kpi.npd) — NPD 단독 표시

test evidence     1292 tests 수집. NPD 계산 경로 테스트 존재(회귀 스위트 내)

verdict : CLEAN
```

★ M1 STEP 1 에서 수정된 오염이 **재발하지 않았다.** WSI 도 별도 KPI 로 독립 계산되며
(§4-5) NPD 와 섞이지 않는다.

---

## 7. as_of / Wall-clock Dependency Findings

### 7-1. `build_herd_kpis` 전체가 WALL_CLOCK_DEPENDENT ⚠

```
kpi_service.py:396   today = farm_today(farm)
```

`build_herd_kpis` 에는 **`as_of` 인자가 없다.** 농장 현지 오늘을 함수 안에서 읽는다.

영향받는 IN_SCOPE KPI: `FARROWING_RATE` · `STILLBORN_RATE` · `PRE_WEANING_MORTALITY`
· `MSY` · `WSI` · `WEANED_PER_LITTER` (그리고 DEFERRED 전건)

→ **과거 시점 스냅샷을 재현할 수 없다.** 월마감 후 같은 기간을 다시 계산하면 창이
움직인다. `calculate_psy` / `calculate_npd` 는 `ref_date` 를 받으므로 재현 가능하다 —
**같은 대시보드 안에서 두 부류가 섞여 있다.**

> `farm_today(farm)` 자체는 옳다(농장 현지 기준). 문제는 **파라미터화 부재**다.
> 이번 run 에서 고치지 않는다 — 발견으로만 기록한다.

### 7-2. `_cohort_farrowing_rate` 는 파라미터화돼 있으나 호출부가 wall-clock

함수는 `ref` 를 받는다(재현 가능). 그러나 호출부 `:520` 이 `today` 를 넘기므로
실효는 §7-1 과 같다. `:817` (get_dashboard) 도 동일.

### 7-3. ⚠ 재고 분모가 두 구현 — 문서화된 결함이 한쪽에만 잔존

```
PSY / NPD / SOW_TURNOVER  (kpi_service.py:86-88, 137-138)
    s.parity >= 1
    AND s.entry_date <= mo
    AND (s.exit_date IS NULL OR s.exit_date >= mo)          ← deleted_at 무관

_avg_active_inventory     (kpi_service.py:363-364)
    s.entry_date <= mo
    AND (s.deleted_at IS NULL
         OR (s.exit_date IS NOT NULL AND s.exit_date >= mo))  ← deleted_at 게이팅
    (parity 필터 없음)
```

`_avg_active_inventory` 를 분모로 쓰는 KPI: **`MSY`**(IN_SCOPE) · `CULLING_RATE` ·
`SOW_MORTALITY` · `REPLACEMENT_RATE`(DEFERRED).

★ `calculate_psy` 의 docstring 이 **바로 이 두 가지를 결함으로 명시하고 고쳤다** —
(a) 후보돈 포함, (b) `deleted_at` 게이팅. 특히 (b)는 soft-delete 되지 않은
하베스트 데이터에서 **도폐사 모돈이 재고를 영구 부풀린다.** 그 수정이
`_avg_active_inventory` 에는 반영되지 않았다.

논리 확인: `deleted_at IS NULL` 이면 `exit_date` 와 무관하게 포함된다 — 이미 퇴출됐지만
soft-delete 되지 않은 모돈이 계속 재고로 잡힌다. PSY 는 이 경로를 쓰지 않으므로
**같은 농장에서 PSY 분모와 MSY 분모가 다른 값이 된다.**

→ AMBIGUOUS 판정은 하지 않았다. MSY 자체의 계산 경로는 하나뿐이라 `CONFIRMED` 이고,
이것은 **"활성 모돈 재고"라는 개념이 두 정의를 갖는다**는 별개 findings 다.
`formula_id` 를 부여할 때 두 재고 정의를 구분해야 한다. → §10 P0-2 안건

---

## 8. Test / Code Mismatch Findings

| 항목 | 내용 |
|---|---|
| `kpi_service.py:4` docstring | `"PSY, MSY, NPD from DB views"` — **현재 코드는 DB view 를 쓰지 않는다.** PSY/NPD 는 인라인 SQL, MSY 는 `build_herd_kpis` 집계. `v_sow_npd` 는 미사용(§5). `doc_code_mismatch` |
| 아키텍처 v1.1 §3-4 | PigOS 사산공식을 `(stillborn+mummified) ÷ total born` 으로 단정 — **경로 ① 과 불일치**(§4-8). `doc_code_mismatch` |

> `test_code_mismatch` : IN_SCOPE 9건에서 **발견되지 않았다.** 다만 이는
> "테스트가 두 경로의 차이를 단언하지 않는다"는 뜻이기도 하다 — §4-8 · §4-9 의
> LIVE_DIVERGENCE 를 잡는 테스트가 **없다.** 그래서 지금까지 드러나지 않았다.

---

## 9. Mobile Presentation Audit

```
Android (C:\dev\pigos-android)
- repo_status          : FOUND
- commit               : 75458412b99e726424a580a784d51cd677c0ad7c
- endpoint consumer    : /kpi/presentation 소비 안 함
- hardcoded KPI list   : DashboardScreen.kt:100-101  KpiCard("PSY") / KpiCard("NPD")
                         KpiDto.kt:31-33 @SerializedName("PSY"/"NPD"/"FARROWING_RATE")
                         BenchmarkRow("PSY"/"NPD")  :218-219  — higherIsBetter 도 코드 상수
- hardcoded visibility : 예 — 카드 목록·순서가 Compose 코드에 고정
- null benchmark 처리   : 처리함. benchmarks: DashboardBenchmarks? = null,
                         KpiBenchmark? = null, benchmarkAvg: Double?
                         DashboardScreen.kt:131  data.benchmarks?.let { }
- verdict              : HARDCODED

iOS (C:\dev\pigos-ios)
- repo_status          : FOUND
- commit               : 14bf8b01ef38b3a5889c29abb73a722f5aeb05bc
- endpoint consumer    : /kpi/presentation 소비 안 함
                         ※ MainTabView.swift:24-25 의 "presentation" 매치는
                           SwiftUI .presentationDetents / .presentationDragIndicator —
                           API 아님(오탐 확인)
- hardcoded KPI list   : DashboardScreen.swift:162-165
                         kpiCell("PSY") / ("NPD") / ("FARROWING_RATE")
- hardcoded visibility : 예
- null benchmark 처리   : **benchmark 필드 자체가 없음** — 전 소스 grep 0건.
                         null 수신 이전에 benchmark 를 소비하지 않는다
- verdict              : HARDCODED

MOBILE_AUDIT : COMPLETE
```

### ★ 이 결과의 의미 — Template LOCK 결론의 한정

`api/tests/integration/test_us_template_lock.py` L1~L6 은 **백엔드 리졸버 축**에서
"국가 추가 = 코드 변경 0" 을 증명했다. 그 증명은 유효하지만 **모바일에는 미치지 않는다.**

```
국가 KPI 정책 데이터 INSERT
   → /kpi/presentation 응답 변화          ✅ (L1~L6 로 증명)
   → 웹 대시보드 반영                      ✅ (registry-map 렌더링)
   → Android / iOS 반영                   ❌ (카드 목록이 코드 상수)
```

즉 신규 국가에 맞는 KPI 집합을 데이터로 켜도 **모바일 화면은 PSY/NPD/FARROWING_RATE
에 고정된 채로 남는다.** G3(D-17)의 "모바일까지 적용된다" 조항이 가리키는 실물 상태가
이것이다. iOS 는 benchmark 를 아예 소비하지 않으므로 `benchmark_value: null` 계약
자체는 깨지지 않지만, 표시 통제가 백엔드에 없다는 점은 동일하다.

---

## 10. AMBIGUOUS Items → P0-2 Decision

| # | 항목 | 결정할 것 | 비고 |
|---|---|---|---|
| 1 | **사산 계열** | `STILLBORN_RATE` 의 분자에 미라를 포함하는가. 포함한다면 `MUMMIFIED_RATE` 와의 중복을 어떻게 하는가 | **LIVE_DIVERGENCE** — 정의 선택 후에도 `code alignment + 회귀 테스트 → D-13 재실사` 를 거쳐야 CONFIRMED |
| 2 | **PRE_WEANING_MORTALITY** | 이벤트 기록 기반(①)인가 차감 추정(②)인가. 분모는 `weaned+deaths` 인가 `born_alive` 인가 | **LIVE_DIVERGENCE** — 동일 |
| 3 | **"활성 모돈 재고" 정의** | 경산돈만인가 후보돈 포함인가 · `deleted_at` 게이팅을 둘 것인가 | §7-3. MSY 분모가 PSY 분모와 다르다 |

> **`Decision APPROVED ≠ formula CONFIRMED`.** 1·2 는 두 경로가 모두 live 이므로
> 사람이 정의를 골라도 실행 코드는 여전히 둘이다. 문서만 하나가 되는 것은
> 또 하나의 위조 우회로다.

### LIVE_DIVERGENCE — 데이터 정합성 findings (D-8 이전 별도 대응)

현재 **사용자가 보는 화면에 따라 다른 값을 받고 있다.** 대시보드의 사산율/포유폐사율과
분만·이유 입력 직후 인사이트의 같은 이름 지표가 서로 다른 산식이다. 값이 다를 뿐 아니라
**같은 임계값으로 채점된다.**

---

## 11. UNRESOLVED_OUTSIDE_SCOPE → P0-1B Technical Trace

**해당 없음.** IN_SCOPE 9건 전부 `api/app` 내 Python 본문에서 계산이 완결됐다.
raw SQL 은 있으나 전부 인라인 `text()` 라 본문을 읽었다. DB view / stored procedure /
외부 서비스로 넘어간 경로는 없다.

> `v_sow_npd` view 는 존재하나 현재 계산 경로에서 미사용이다(§5).
> 사용처가 되살아나면 그때 `UNRESOLVED_OUTSIDE_SCOPE` 로 재분류한다.

---

## 12. Follow-up Governance Requirements (기록만)

- **D-19 threshold source 감사** — 등록 룰 40 vs `operational_defaults` 29키.
  `threshold_resolver` 의 `code_default` 폴백이 결재 없이 severity 를 낸다.
  G3 불변조건 ③ 의 입력.
- **D-17 G3 표시 안전 계약** — §9 결과가 입력. 모바일이 KPI 목록을 하드코딩하므로
  백엔드 표시 통제가 모바일에서 뚫린다.
- **D-8 mapping 자격** — 사산 계열·PRE_WEANING_MORTALITY 는 `AMBIGUOUS` 이므로
  **mapping 금지.** CONFIRMED 7건만 대상.
- **as_of 파라미터화** — `build_herd_kpis` 에 `as_of` 인자 도입 여부(§7-1).
  월마감·과거 스냅샷 재현에 필요하다.
- `PIGOS_SPEC_INDEX` 에 본 문서 등록 (이번 run 에서 인덱스 미수정).

---

## 13. Explicit Non-Changes

이번 run 에서 **아무 소스도 수정하지 않았다.**

- `.py` 수정 0 · 테스트 수정 0 · migration 0 · seed 0 · 모바일 코드 수정 0
- `git add` / `commit` / `push` 0 (3개 repo 전부)
- formatter · 자동 fix · refactor 0
- `PYTHONDONTWRITEBYTECODE=1` 로 `__pycache__` 생성 차단, `-p no:cacheprovider` 로
  `.pytest_cache` 차단
- 발견했으나 고치지 않은 것: §7-1 wall-clock · §7-3 재고 분모 · §4-8 · §4-9
  LIVE_DIVERGENCE · §8 docstring 불일치
