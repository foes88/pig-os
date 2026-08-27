# CODEX 검증 결과 2026-08-27 (대상 `a2e813c`)

## 결론

D-13·D-19·D-20의 핵심 문제 제기는 유효하지만, 감사 결과를 완전한 사실 목록으로 사용하기에는 누락과 과장이 있다. 가장 중요한 반증은 다음 세 가지다.

1. 운영 severity 32개가 모두 `default_metric_values`에서 나온다는 주장은 거짓이다. 현재 운영에서 B-resolve 29개 중 14개가 전부 또는 일부 임계값을 코드 상수에 의존한다.
2. 사산율 divergence의 “실고객 노출 사실상 0” 주장은 거짓이다. 최근 365일 분만이 있는 `live_customer` 농장 2개가 모두 고정 8/12 기준에서 등급이 바뀐다.
3. D-13의 “단일 경로 7개”와 “divergence 2개” 목록은 계산 경로 전체를 포괄하지 못한다. `report_service.py`와 실행 중인 snapshot job에 별도 산식이 있다.

검증 대상 PigOS 커밋 이후 현재 HEAD까지 애플리케이션 코드 변경은 없었다. 모바일은 별도 저장소의 현재 HEAD를 읽었다. 운영 환경은 SELECT만 수행했으며 코드·마이그레이션·seed·설정·운영 데이터는 변경하지 않았다.

## 검증 기준점

| 구분 | 검증 기준 |
|---|---|
| PigOS 문서 대상 | `a2e813c` (`main`) |
| 검증 시 PigOS HEAD | `d99a8c9`; `a2e813c..HEAD`의 변경은 문서 3개뿐, 애플리케이션 코드 변경 없음 |
| Android | `75458412b99e726424a580a784d51cd677c0ad7c`, clean |
| iOS | `321d4e8f140f47c8915bc0de619164e040d730c4`, clean |
| 운영 확인 | 2026-08-27 KST, `pigos-api`/`pigos-worker` 및 PostgreSQL 17.11, SELECT-only |
| 테스트 | 로컬 PostgreSQL, `test_us_template_lock.py`: 10 passed |

검증 전부터 있던 아래 작업 트리 변경은 건드리지 않았다.

- `docs/adr/ADR-KPI-08-backend-owned-kpi-status.md`
- `handoff/CODEX_RESULT_2026-08-25.md`
- `api/scripts/pigplan_rules_diff.py`

## 판정 요약

| 항목 | 주장 | 판정 | 핵심 근거 |
|---|---|---|---|
| C-1 | LIVE_DIVERGENCE는 사산·PWM 2건이며 양쪽 경로가 LIVE | **OVERSTATED** | 지목한 두 산식과 REST 이벤트/대시보드 reachability는 맞다. 그러나 live report 경로에 별도 사산·PWM·분만율 산식이 있고 sync에는 insight 부착이 없다. |
| C-2 | PSY·NPD·SOW_TURNOVER·FARROWING_RATE·WSI·MSY·WEANED_PER_LITTER는 단일 경로 | **REFUTED** | FARROWING_RATE, WSI, WEANED 계열은 복수 live 계산 경로다. PSY도 실행 중인 snapshot job에 별도 산식이 있다. |
| C-3 | `_avg_active_inventory`가 후보돈과 퇴출돈을 잘못 포함 | **CONFIRMED** | SQL 조건상 `deleted_at IS NULL`이면 과거 퇴출일과 무관하게 포함되고 산차 필터가 없다. 운영 internal-reference 데이터에 해당 행 110,010개 존재. |
| C-4 | 모바일은 KPI 목록을 하드코딩하고 `/kpi/presentation`을 소비하지 않음; iOS에는 benchmark 필드도 없음 | **OVERSTATED** | 하드코딩과 presentation 미소비는 양쪽 모두 확인. 현재 iOS에는 `benchmarks` 모델과 표시 코드가 이미 있다. |
| C-5 | 룰 40개는 B 29 + A 3 + no-threshold 8이고 B 29와 operational default가 정확히 1:1 | **OVERSTATED** | 40/29/3/8과 운영 default 29행은 재현. 다만 B 6개는 별도 resolver이며 “no-threshold” 8개에도 고정 cut-off·상태 gate가 있다. |
| C-6 | flag OFF 운영 severity 32개 전부를 `default_metric_values`가 만듦 | **REFUTED** | flag=False, RuleConfig=0은 맞다. 하지만 B 29개 중 14개는 active farm에서 전부/일부 code default fallback을 사용한다. |
| C-7 | 승인 이력이 있는 threshold는 0개 | **OVERSTATED** | DB 안에는 threshold Decision Register/audit 이력이 없다. 그러나 `threshold_basis IS NULL`은 승인 부재와 동의어가 아니며 DB 밖 승인까지 0이라고 증명할 수 없다. |
| C-8 | divergence 통계는 대부분 internal reference이고 실고객 노출은 사실상 0 | **REFUTED** | 42 internal + 2 live 분리는 맞다. 그러나 live 농장 2/2가 사산율 severity flip이며 internal 42개 농장에도 최근 로그인한 활성 직접 멤버가 있다. |
| C-9 | 사산 경로 ①≤②라서 반대 방향/역전은 산술적으로 불가능 | **CONFIRMED** | 같은 분모이고 mummified≥0이면 항상 성립한다. PWM에는 같은 불변식이 없고 운영 집계에서도 A>B 사례가 있다. |
| C-10 | §3-4를 AMBIGUOUS로 정정했고 영향 문서 7개를 식별 | **OVERSTATED** | 정정 방향은 맞지만 동일 단정이 남은 문서가 목록 밖에서도 다수 발견된다. |
| C-11 | benchmark-derived를 차단하면 BR Pilot 화면이 무채색 | **OVERSTATED** | BR 표시 KPI 3개는 모두 A-bench라 해당 카드 색은 사라진다. 하지만 숨김 KPI와 categorical/composite 룰까지 시스템 전체가 무채색이 되는 것은 아니다. |
| C-12 | L1~L6 통과로 “US 활성화에는 INSERT만 필요”가 증명됨 | **OVERSTATED** | resolver 계약 10개 테스트는 모두 통과하고 L4도 실질적인 타국 누출을 잡는다. HTTP·모바일·threshold·권한을 포함한 제품 전체 활성화는 이 테스트 범위 밖이다. |

## 반증된 것

### 1. “운영 32룰의 severity source는 전부 default_metric_values”

운영 확인값은 다음과 같다.

| 확인 항목 | 결과 |
|---|---:|
| `USE_GOVERNANCE_BENCHMARKS` | `False` |
| `rule_configs` | 0행 |
| `operational_defaults` | 29행, 전부 `origin='code_default'` |
| `default_metric_values` | 87행 |
| warning 보유 | 68행 |
| critical 보유 | 65행 |
| warning 보유 행 중 `threshold_basis IS NULL` | 61행 |
| active farm | 71개 |

DB 컬럼은 실제로 `kpi_service.py:325-330`에서 `warning_threshold → benchmarks[kpi]["warning"]`, `critical_threshold → ["critical"]`로 매핑된다. `PRE_WEANING_MORTALITY → PWMR` alias도 `kpi_service.py:334-336`에 있으므로 PWMR은 누락으로 세지 않았다.

`governance_enabled()` 자체는 threshold 해소 때마다 호출되지만(`threshold_resolver.py:21-22`), 읽는 값은 import 시 생성된 singleton `settings`다(`api/app/core/config.py:114`). 따라서 환경변수를 요청마다 다시 읽는 hot toggle은 아니며 프로세스 재시작 전에는 바뀌지 않는다.

그 매핑을 적용해도 source coverage는 다음과 같다.

| 룰군 | 개수 | 현재 운영 source |
|---|---:|---|
| A-bench | 3 | 3개 모두 DMV 임계값 존재 |
| B-resolve, DMV 완전 충족 | 15 | DMV |
| B-resolve, 전부 또는 일부 DMV 누락 | 14 | code default 전부/일부 fallback |

전부 빠진 metric/rule에는 `ACCIDENT_P1_RATIO`, `BATCH_DOW_CONCENTRATION`, `BOAR_FARROW_RATE`, `CONCEPTION_RATE`, `CRUSHING_RATE`, `DEATH_AGE_0_3_RATIO`, `MSY`, `REPLACEMENT_RATE`, `SECOND_LITTER_DROP`, `SUMMER_FARROW_DROP`가 포함된다. `CULLING_RATE`, `WEANING_AGE_LOW`, `RTS_RATE`, `SOW_MORTALITY`는 적용 farm에서 임계 한쪽 또는 양쪽이 빠져 상수 fallback이 개입한다.

따라서 D-19의 “DMV가 32룰 severity 전부를 만든다”는 결론은 반증됐다. 현재 운영은 **DMV + inline code default의 혼합 source**다.

### 2. “사산 divergence의 실고객 노출은 사실상 0”

최근 365일 분만 모집단은 문서와 같이 44개 농장이지만 분리 결과는 아래와 같다.

| origin / classification | 농장 | 분만 | total born | stillborn | mummified |
|---|---:|---:|---:|---:|---:|
| `pigplan_migration / internal_reference` | 42 | 54,031 | 798,324 | 43,373 | 17,615 |
| `native_signup / live_customer` | 2 | 3 | 40 | 3 | 2 |

고정 warning=8%, critical=12%로 농장별 365일 집계를 다시 계산하면:

| 모집단 | 농장 | A 평균: stillborn/TB | B 평균: (stillborn+mummified)/TB | 평균 gap | severity 변화 |
|---|---:|---:|---:|---:|---:|
| internal reference | 42 | 6.0270% | 8.4012% | 2.3742%p | 15 |
| live customer | 2 | 7.4176% | 12.9121% | 5.4945%p | **2** |
| 전체 | 44 | 약 6.09% | 약 8.61% | 약 2.52%p | 17 |

live 2개 농장은 각각 `NONE→WARNING`, `NONE→CRITICAL`로 바뀐다. 표본이 2개라 시장 전체로 일반화할 수는 없지만, **관측된 live 모집단의 노출이 0이라는 결론은 낼 수 없다.**

전체 severity matrix도 재현됐다.

| A \ B | NONE | WARNING | CRITICAL |
|---|---:|---:|---:|
| NONE | 20 | 10 | 3 |
| WARNING | 0 | 6 | 4 |
| CRITICAL | 0 | 0 | 1 |

`13`은 NONE에서 경고/치명으로 새로 켜지는 건수이고, severity tier가 달라지는 전체 건수는 `17`이다. 새로 켜지는 13개에도 live 2개가 포함된다. D-20 본문의 “13개 전부 reference” 취지 문구는 틀렸다.

후속 결정문 `handoff/P0-2_STILLBORN_DECISION_2026-08-27.md:105`도 44개 전체를 “하베스트 참조”라고 표기한다. 실제 분리는 42 internal + 2 live이므로 이 결정 근거 표 역시 정정이 필요하다.

또한 internal-reference 42개 농장 모두에 직접 farm membership이 있었고, 42명의 활성 계정이 최근 90일 안에 로그인했다. 이는 그들이 KPI 화면을 실제로 봤다는 증명은 아니지만, “대시보드를 보는 사용자가 아니다” 또는 “노출이 불가능하다”는 단정을 반증한다. 개인 식별자는 결과에 기록하지 않았다.

D-20의 전체 평균 B=`8.16%`도 재계산되지 않았다. 위 population별 결과와 44개 농장 비가중 평균을 합치면 약 `8.61%`다. 문서의 gap `2.52%p` 및 severity matrix와도 `8.61%`가 일관된다.

### 3. “단일 경로 7개”

| KPI | 직접 추적 결과 |
|---|---|
| PSY | canonical service 외에 `jobs/kpi.py:132-135`가 `(period weaned/current active)×annualization`으로 snapshot을 계산한다. worker는 실행 중이지만 현재 앱에는 `KpiSnapshot` reader가 없어 latent writer다. |
| NPD | 현재 서비스 계산 경로만 live. `v_sow_npd`는 앱에서 소비되지 않는다. |
| SOW_TURNOVER | 현재 `calculate_npd` 반환 경로 외 별도 live 산식은 찾지 못했다. |
| FARROWING_RATE | 대시보드는 cohort 산식(`kpi_service.py:520`), 보고서는 동일 기간 `farrowings/matings`(`report_service.py:182`), snapshot job도 동일 기간 방식(`jobs/kpi.py:138-144`)이다. |
| WSI | 대시보드는 365일 평균(`kpi_service.py:527`), REST mating insight는 단일 이벤트 간격(`insight_service.py:244-257`)이다. |
| MSY | 현재 herd KPI 경로 외 별도 live consumer는 찾지 못했다. 다만 별도 rule threshold source는 존재한다. |
| WEANED_PER_LITTER | 대시보드는 365일 평균 `WEANED_COUNT`(`kpi_service.py:530`), REST weaning insight는 단일 이벤트 값(`insight_service.py:219-230`), 보고서는 복별 평균(`report_service.py:175-179`)이다. |

따라서 7개 모두를 하나의 계산 경로라고 확정한 C-2는 반증됐다.

## 과장·축소된 것

### C-1 — 두 divergence 자체는 맞지만 목록은 완전하지 않다

문서가 지목한 산식은 코드와 일치한다.

- 사산 A: `stillborn / total_born` — `api/app/services/kpi_service.py:523`
- 사산 B: `(stillborn + mummified) / total_born` — `api/app/services/insight_service.py:205-215`
- PWM A: `deaths / (weaned + deaths)` — `api/app/services/kpi_service.py:512`
- PWM B: `(born_alive - weaned) / born_alive` — `api/app/services/insight_service.py:219-230`

대시보드 A와 REST 이벤트 생성 B는 live다. REST event router는 mating/farrowing/weaning 저장 후 `_attach_insights`를 호출한다(`api/app/routers/base/events.py:55-64, 123, 155, 250`). 반면 sync service에는 insight 분석/저장 호출이 없다. 따라서 동일 이벤트라도 진입점에 따라 즉시 insight 생성 여부가 다르다.

추가 live user-facing 경로인 보고서는 다음 값을 별도로 계산해 웹 화면에 표시한다.

- 같은 기간 `farrowings/matings` — `report_service.py:182`
- PWM A — `report_service.py:193-194`
- PWM B: total-born 기반 복별 값 — `report_service.py:185-191`
- stillborn-only, mummified-only, combined birth loss — `report_service.py:195-197`
- 실제 웹 표시 — `src/app/(app)/reports/reproduction/page.tsx:40-44`

이벤트 insight는 항상 DMV를 직접 읽지만 RuleEngine 경로는 RuleConfig/flag 분기를 가진다. 현재 운영은 RuleConfig=0이라 일부 동일 metric의 실효 임계가 우연히 같을 수 있어도, 두 경로가 동일 threshold source contract로 고정된 것은 아니다.

### C-3 — 버그는 실재하지만 현재 live_customer 영향은 관측되지 않았다

`api/app/services/kpi_service.py:348-367`의 조건은 다음 논리다.

```sql
(s.deleted_at IS NULL OR (s.exit_date IS NOT NULL AND s.exit_date >= mo))
```

`deleted_at IS NULL`인 일반 행은 `exit_date < mo`여도 OR 전체가 참이다. parity 조건도 없으므로 후보돈을 제외하지 않는다.

운영 현황:

| 모집단 | 퇴출됐지만 미삭제 | 그중 후보돈 | 그중 산차돈 |
|---|---:|---:|---:|
| native/live | 0 | 0 | 0 |
| migration/internal | 110,010 | 13,779 | 96,231 |

즉 구현 결함은 확정이며 이론적 결함도 아니다. 다만 현재 native/live 표본에서 해당 행은 0개라 관측 영향은 internal-reference에 집중돼 있다.

### C-4 — 모바일 핵심 문제는 남았지만 iOS 설명은 오래됐다

Android:

- Dashboard 카드가 PSY/NPD를 직접 작성: `DashboardScreen.kt:100-101`
- benchmark 행도 PSY/NPD/FR 및 방향을 직접 작성: `DashboardScreen.kt:218-219`
- DTO key가 3개로 고정: `KpiDto.kt:31-33`
- 상세 화면도 PSY/NPD label과 방향을 직접 작성: `KpiDetailScreen.kt:68, 76, 96`

iOS:

- Dashboard 표시 집합/방향이 PSY/NPD/FR로 고정: `DashboardScreen.swift:81-84, 189-191`
- repository는 `/kpi/dashboard`를 호출하고 `/kpi/presentation` 소비 경로가 없다: `KpiRepository.swift:8-11`
- 그러나 현재 모델에는 `benchmarks: [String: KpiBenchmark]?`가 존재한다: `Domain/Model/KPI.swift:19`

따라서 “두 앱 모두 backend-owned presentation이 아니다”는 확인됐지만 “iOS benchmark 필드 자체가 없다”는 현재 HEAD에서 반증됐다.

### C-5 — 분류 숫자는 맞아도 source 의미가 단순하지 않다

`RuleRegistry.register` 호출은 정확히 40개다. 문서의 구조적 분할 29+3+8과 `operational_defaults` 29행도 재현된다. 그러나:

- 29개 B 중 23개만 `_common.resolve()`를 사용한다.
- reproduction 6개(`wsi`, `rts`, `pwmr`, `abortion`, `summer`, `conception`)는 `reproduction.py:47-54`의 로컬 `_resolve()`를 사용한다.
- flag OFF 우선순위는 공통 resolver가 `RuleConfig → benchmark → code`(`_common.py:34-54`)인 반면 reproduction은 `benchmark → RuleConfig → code`다.
- `no-threshold` 8은 “설정 가능한 warning/critical pair가 없다”는 좁은 뜻으로만 맞다. 예를 들어 `farm.health_class`는 critical 1건 또는 warning 3건이라는 고정 cutoff를 쓴다(`composite.py:24-31`), `inventory.zero`는 active=0 gate를 쓴다.
- `replacement.rate_abnormal`은 B군이지만 resolver 밖에 고정 하한 `30.0`이 있다(`sow_herd.py:88-98`).

따라서 40개 inventory는 유용하지만 “29개 모두 동일 source chain”, “8개는 threshold가 없음”으로 읽으면 과장이다.

### C-7 — DB 감사 이력 0과 전 세계 승인 0은 다르다

운영 schema에서 관련 테이블은 `audit_log`, `country_kpi_policy`, `rule_configs`였고 threshold 결정 전용 Decision Register는 찾지 못했다. `audit_log`에도 threshold 관련 기록이 없었다. `country_kpi_policy` 28행 및 presentation 7행은 표시 정책 승인이지 threshold 승인 이력이 아니다.

따라서 “운영 DB에서 감사 가능한 threshold 승인 이력은 발견되지 않음”은 확인됐다. 다만 `threshold_basis`는 산출 근거 metadata이지 승인 ledger가 아니고, 외부 문서/회의/시스템의 승인을 DB 조회로 부정할 수 없다. 결론의 안전한 범위는 **DB-auditable approval history 0**이다.

### C-10 — AMBIGUOUS 정정은 맞지만 영향 목록은 불완전하다

아키텍처 §3-4가 단일 공식을 선택하지 않고 두 live 경로를 AMBIGUOUS로 남긴 정정은 적절하다. 그러나 repo-wide 검색에서는 정정 대상 7개 밖에도 combined 공식을 PigOS 정의로 단정하거나 전제로 삼는 문서가 발견됐다.

- `docs/specs/COUNTRY_KPI_RULE_SPEC_v0.3.1.md:164`
- `handoff/pigplan-rules/PROMPT_kpi_benchmark_structure.md:70`
- `handoff/WORK_A_OUTPUT_schema_migration.md:50`
- `handoff/WORK_B_OUTPUT_kr27_reverification.md:64`
- `handoff/WORK_C_OUTPUT_kr_verified.md:26`
- `handoff/PROMPT_C_kr_verified_promotion.md:88`
- `docs/qa/overnight-market-qa/2026-06-24/market-BR.md:142`

또한 `docs/KPI_DEFINITIONS.md:30,50`, `docs/PIGOS_WEB_FULLSPEC_QA_PROMPT.md:75`, `handoff/pigos-overnight-qa-prompt.md:31` 등 문서가 아직 단정형 표현을 유지한다. 일부는 D-13이 이미 열거한 문서지만, 전체 검색 결과를 기준으로 정정 범위가 닫혔다고 볼 수 없다.

### C-11 — BR의 보이는 3개 카드는 막히지만 엔진 전체가 무채색은 아니다

BR Pilot 표시 KPI는 정확히 PSY, FARROWING_RATE, NPD다(`api/app/db/br_pilot_seed.py:22-24`). Global 표시 기본도 같은 3개다(`global_policy_defaults.py:28`). 이 세 KPI의 색은 A-bench 경로에 있으므로, 승인되지 않은 benchmark-derived severity를 fail-closed로 차단하면 BR의 **현재 보이는 세 카드**는 무채색이 된다.

그러나 BR hidden KPI는 계속 계산될 수 있고, disease/inventory/composite 같은 categorical 또는 고정 gate 룰은 별도 차단 정책이 없으면 finding을 낼 수 있다. D-19의 “32개 모두 DMV” 전제도 거짓이다. 따라서 카드 단위 결론은 맞지만 PigOS severity 시스템 전체에 대한 결론으로 넓히면 과장이다.

### C-12 — L1~L6는 유효한 resolver gate이지 제품 전체 gate가 아니다

실행 명령:

```text
cd api
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/integration/test_us_template_lock.py -q -p no:cacheprovider
```

결과: **10 passed in 2.68s**.

L4는 KR/BR의 ADG/FCR/MSY와 현지 label을 실제로 삽입한 뒤 US 결과 집합과 label 누출을 검사한다(`test_us_template_lock.py:165-185`). unknown country가 US를 빌리지 않는지도 별도로 검사한다(`:188-198`). 따라서 이 좁은 계약은 자기충족형 테스트가 아니다.

다만 테스트 호출 대상은 `resolve_display_kpis`다. 다음은 검증하지 않는다.

- HTTP router/response가 resolver 결과를 빠짐없이 전달하는지
- Android/iOS가 동적 표시 집합을 소비하는지
- threshold·terminology·entitlement·farm type 축
- 제품의 다른 위치에 country-specific 분기가 없는지

따라서 “L1~L6 resolver 계약 통과”는 확인됐지만, 파일 헤더의 “US 활성화에 필요한 것은 INSERT뿐임이 증명된다”는 범위가 더 크다.

## 문서에 없던 신규 발견

### 보고서에는 세 번째 의미 경로가 있다

`report_service.py`는 dashboard/insight 중 하나를 재사용하지 않고 raw event를 다시 집계한다. 특히 PWM B는 event insight의 `born_alive` 분모가 아니라 total-born 기반 복별 계산이고, 사산·미라·combined loss를 별도 필드로 동시에 노출한다. D-13 formula inventory에 반드시 별도 consumer로 들어가야 한다.

### scheduled snapshot 산식은 실행 중이지만 현재는 읽히지 않는다

`api/app/jobs/kpi.py:74-172`는 PSY와 분만율을 별도 산식으로 계산해 `KpiSnapshot`에 쓴다. 운영 worker도 실행 중이다. repo-wide app 검색에서는 jobs 외 `KpiSnapshot` reader가 없었다. 즉 현재 API 결과를 바꾸는 live read path는 아니지만, **실행되는 latent calculation path**다.

### PWM impact 문서는 실제 이벤트 verdict를 비교하지 않았다

D-20의 PWM B 약 7.54%, gap 약 7.24%p, flip 4건은 weaning event별 `insight_service.py:227-230` 결과가 아니라, 농장별로 `SUM(born_alive)`와 `SUM(weaned)`를 합친 합성 집계에서 재현된다. 실제 이벤트 단위 B를 평균하면 migration 데이터의 부분 이유/연결 특성 때문에 값과 방향이 크게 달라진다.

수학적으로도 PWM은 방향이 고정되지 않는다. `w=weaned`, `d=recorded deaths`, `b=born_alive`라 하면:

```text
A = d / (w + d)
B = (b - w) / b
A <= B  iff  d <= b - w   (w > 0)
```

`d`와 `b-w` 사이에 데이터 제약이 없으므로 A≤B는 보장되지 않는다. 운영 농장 집계에도 A>B가 적어도 1건 있었다. 사산의 `stillborn/TB ≤ (stillborn+mummified)/TB`와 달리 PWM에는 산술적 불변식이 없다.

### internal-reference는 “접근 사용자 없음”과 동의어가 아니다

provenance 분리는 분석 품질상 필요하지만, classification만으로 exposure를 0으로 둘 수 없다. 이번 운영 조회에서 42개 internal-reference 농장 모두 활성·최근 로그인 직접 멤버를 가졌다. 앞으로 impact 보고서는 최소한 `data_origin`, `data_classification`, active membership, 최근 로그인, 실제 KPI endpoint access를 서로 다른 축으로 다뤄야 한다.

## 미검증으로 남긴 것

- DB 밖 문서·회의·티켓에 threshold 승인이 존재하는지는 확인하지 못했다. 따라서 “전사 승인 0”은 `UNVERIFIED`다.
- internal-reference 멤버가 실제 KPI 화면/endpoint를 열었는지는 application access log를 조회하지 않았으므로 `UNVERIFIED`다. 이번 결과는 접근 가능성과 최근 로그인까지만 증명한다.
- `KpiSnapshot`을 repo 밖 BI/SQL 사용자가 소비하는지는 확인하지 못했다. 앱 코드에서 reader가 없다는 범위까지만 확인했다.
- live customer 2개 농장 결과는 관측 표본 설명에는 충분하지만 시장 전체 영향률 추정에는 부족하다.
- 이벤트 insight가 운영 DB에 실제 얼마나 저장·노출됐는지는 정적 호출 경로만 확인했고 insight row population은 조회하지 않았다.

## 이 검증에서도 확인하지 못한 사각지대

1. 운영 데이터는 2026-08-27 조회 시점 snapshot이다. 이후 이벤트 입력에 따라 수치는 달라질 수 있다.
2. 생산 API에 쓰기 요청을 보내지 않았으므로 동일 payload를 REST와 sync로 end-to-end replay해 응답/저장 결과를 비교하지 않았다.
3. 모바일은 현재 source를 정적으로 추적했으며 실제 기기 UI 자동화나 네트워크 capture는 수행하지 않았다.
4. Template LOCK 테스트는 로컬 PostgreSQL의 integration test다. production schema drift와 모바일 소비를 함께 검증하는 E2E gate는 아니다.
5. D-20의 PWM event 단위 재계산은 migration 연결 데이터의 의미 품질을 별도로 정제하지 않았다. 따라서 합성 집계가 실제 사용자에게 더 유용한 지표인지 여부는 제품 결정으로 남는다.
6. 이번 검증 대상은 `a2e813c`지만 iOS 참조 저장소는 별도 HEAD가 계속 전진한다. 모바일 관련 문서에는 앞으로 반드시 검증한 repo commit을 고정해야 한다.

## 최종 권고 우선순위

1. D-19 source 표를 실제 운영 기준 `DMV 18개(A 3+B 15) / code fallback 개입 B 14개`로 정정하고, reproduction 6개의 flag-OFF 우선순위 차이를 별도 표시한다.
2. D-20에서 “reference=미노출” 가정을 제거하고 live 2/2 flip, active membership, 실제 access log를 분리해 보고한다. 전체 B 평균 `8.16%`도 재계산한다.
3. D-13 inventory에 `report_service.py`, `jobs/kpi.py`, REST-vs-sync reachability를 추가하고 “단일 경로 7개” 상태를 KPI별로 다시 판정한다.
4. C-3의 inventory SQL은 `entry_date <= mo AND (exit_date IS NULL OR exit_date >= mo)` 및 명시적 번식돈/parity 조건으로 설계를 결정한 뒤 별도 변경 작업에서 수정한다.
5. Template LOCK은 resolver gate라는 이름으로 범위를 축소하거나, HTTP→web/mobile 렌더링까지 포함한 E2E gate를 추가한다.
