# D-20 — LIVE_DIVERGENCE 영향 정량화

```
Mode     : PRODUCTION READ-ONLY (SELECT only) — 대표 승인 2026-08-27
Machine  : bjh → api.pigos.io (52.78.65.6) PostgreSQL 17 :5434 / db=pigos
Date     : 2026-08-27
목적     : D-13 이 찾은 LIVE_DIVERGENCE 2건이 **판정을 뒤집는가**
제약     : 수정·마이그레이션·seed 0. 합성 데이터 대체 없음
```

> **핵심 질문은 값 차이가 아니라 verdict flip rate 다.**
> 뒤집히지 않음 → 정합성 버그(여유 있게 수정). 뒤집힘 → 인시던트(BR 운영 중).

---

## 0. 결론

| | 사산 계열 | PRE_WEANING_MORTALITY |
|---|---|---|
| flip rate | **17 / 44 = 38.6%** | 4 / 44 = 9.1% |
| 평균 격차 | 2.52 %p | **7.24 %p** |
| 최대 격차 | 9.50 %p | **19.67 %p** |
| 판정 | **인시던트** | **경로 ① 결함 — 정책 선택 아님** |
| 라우팅 | **P0-2 (숫자 포함)** | **버그 수정 트랙** |

---

## 1. 데이터 규모

```
farms          72        farrowings   531,760      weanings  527,019 (전건 farrowing 연결)
total_born  7,325,838    stillborn    445,375      mummified 152,579
```

분석 대상: 최근 365일 분만 실적이 있는 **44 농장**.

---

## 2. ③ 유모돈(fostering) — PWM 갈림길

```sql
SELECT event_type, count(*), count(DISTINCT farm_id), sum(piglet_count)
FROM piglet_events WHERE deleted_at IS NULL GROUP BY event_type;
```

```
 event_type | n | farms | piglets
 DEATH      | 2 |     1 |       3
```

**`FOSTER_IN` / `FOSTER_OUT` 0건.**

→ 경로 ②의 구조적 약점("유모돈이 있으면 전출 자돈이 폐사로 잡힌다")은 **현재 데이터에서
발현되지 않는다.** 사전 가설은 이 지점에서 기각된다.

→ **그러나 같은 쿼리가 더 큰 문제를 드러냈다.** `DEATH` 이벤트가 전체 2건(3두)뿐이다.
경로 ①의 분자가 바로 이 `DEATH` 이벤트다.

---

## 3. 사산 계열 — 인시던트

임계값(운영 DB `operational_defaults`): `stillborn.rate_high`
`warning_max = 8` · `critical_max = 12` · `lower_better`

```
경로 ①  stillborn / total_born              (대시보드, kpi_service.py:523)
경로 ②  (stillborn + mummified) / total_born (이벤트 인사이트, insight_service.py:211)
```

| farms | avg_gap | max_gap | severity 동일 | **severity FLIP** |
|---|---|---|---|---|
| 44 | 2.52 %p | 9.50 %p | 27 | **17 (38.6%)** |

### 3-1. flip 방향 — 전부 한 방향이다

| 대시보드 | 이벤트 인사이트 | 농장 수 |
|---|---|---|
| none | none | 20 |
| **none** | **WARNING** | **10** |
| WARNING | WARNING | 6 |
| **WARNING** | **CRITICAL** | **4** |
| **none** | **CRITICAL** | **3** |
| CRITICAL | CRITICAL | 1 |

★ **대시보드가 예외 없이 더 관대하다.** 역방향 flip 은 0건이다.

★ **13개 농장이 대시보드에서 "정상"인데 분만 입력 시점에는 경고를 받는다.**
그중 **3곳은 CRITICAL** 이다 — 대시보드에는 아무 표시가 없다.

> 집계 기준으로도 뒤집힌다: 전체 ① 6.08% (임계 8 미만, 무경보) vs ② 8.16% (WARNING).
> 아키텍처 §3-4 가 말한 "~3%p" 는 농장 평균 2.52%p 로 **크기 자체는 대체로 맞았다.**
> 틀린 것은 그 값이 **대시보드 값이라는 전제**였다.

### 3-2. 판정

**정책 선택이 맞다.** 미라 포함/제외 둘 다 방어 가능하고, `MUMMIFIED_RATE` 가 이미
별도 지표로 있어 포함을 택하면 중복이 생긴다. 외부 대조에서도 PigCHAMP 는 stillborn 과
mummies 를 별도 행으로 내므로 **경로 ① 이 외부 벤치마크와 직접 대조 가능한 쪽**이다.

→ **P0-2 결정.** 단 이제 숫자가 있다 — "미라를 포함할까요"가 아니라
**"38.6% 농장의 경고 등급이 달라지는데 어느 쪽을 기준으로 삼을 것인가"** 로 묻는다.

---

## 4. PRE_WEANING_MORTALITY — 정책 선택이 아니다

임계값: `pwmr.high` `warning_max = 15` · `critical_max = 20` · `lower_better`

```
경로 ①  deaths / (weaned + deaths)          deaths = piglet_events[event_type='DEATH']
경로 ②  (born_alive − weaned) / born_alive
```

| 지표 | 값 |
|---|---|
| 경로 ① 평균 | **0.30 %** |
| 경로 ② 평균 | **7.54 %** |
| 평균 격차 | 7.24 %p (**25배**) |
| 최대 격차 | 19.67 %p |
| severity flip | 4 / 44 (9.1%) — 전부 `none → WARNING` |
| **DEATH 이벤트가 0건인 농장** | **43 / 44** |

### 4-1. 판정 — 경로 ①이 실질적으로 작동하지 않는다

경로 ①의 분자는 `piglet_events` 의 `DEATH` 기록인데 **44농장 중 43농장이 이를 입력하지
않는다.** 그래서 대시보드 포유폐사율은 사실상 **항상 0%** 로 표시된다.

flip rate 가 9.1% 로 낮은 것은 두 값이 비슷해서가 아니라, **경로 ①이 0에 붙어 있어
임계 15 를 넘을 방법이 없기** 때문이다. 격차는 사산(2.52%p)의 **3배**다.

→ **CEO 결재 대상이 아니다.** "어느 정의를 채택할까"의 문제가 아니라, 한쪽이 필요한
입력을 받지 못해 동작하지 않는 상태다. **버그 수정 트랙.**

→ 사전 가설(유모돈 때문에 경로 ②가 깨진다)은 §2 로 기각됐다. 유모돈이 0건이므로
**현재 데이터에서는 경로 ②가 더 정확하다.**

> 단 유모돈이 0건인 것이 "유모돈을 안 한다"인지 "이벤트로 기록하지 않는다"인지는
> 이 쿼리로 구분되지 않는다. 후자라면 경로 ②의 구조적 약점은 여전히 잠복해 있다.
> **미확인으로 남긴다.** → §6

---

## 5. 부수 발견 — `operational_defaults` 전건이 `code_default` 다

```sql
SELECT origin, count(*) FROM operational_defaults GROUP BY origin;
--  code_default | 29
```

`operational_defaults` 테이블에는 `origin` 컬럼이 있고, **29행 전부가 `code_default`** 다.
즉 이 표는 결재 결과가 아니라 **코드 상수를 옮겨 담은 것**이며, 스스로 그렇게 기록하고 있다.

★ **G3 불변조건 ③ 의 `operational_default = ALLOW` 전제가 틀렸다.**
"결재 기록이 있으므로 severity 를 낼 수 있다"고 썼는데, 실제로는 origin 이
`code_default` 라 결재 기록이 없다. D-19 에서 메커니즘 A 를 놓친 데 이어
**같은 조항의 두 번째 오류**다.

→ G3 ③ 은 `severity_source` 가 아니라 **`origin`** 으로 판정해야 한다:

```
ALLOW   rule_configs                          (운영자가 명시 설정)
ALLOW   operational_default WHERE origin ∈ {decision, approved}
REVIEW  operational_default WHERE origin = 'code_default'    ← 현재 29/29
REVIEW  benchmark_derived (_severity_from_bench)             ← D-19
DENY    code_default (테이블에도 없음)
```

---

## 6. 미확인 / 후속

| # | 항목 | 성격 |
|---|---|---|
| 1 | 유모돈 0건이 "안 함"인가 "기록 안 함"인가 | 현장 확인. 후자면 경로 ② 약점 잠복 |
| 2 | `DEATH` 이벤트 미입력이 UX 문제인가 기능 부재인가 | 입력 동선 확인 → PWM 수정 방향 결정 |
| 3 | `operational_defaults` 29건의 결재 승격 | G3 ③ 전제 복구에 필요 |
| 4 | 사산 P0-2 결정표 (본 문서 §3 숫자 첨부) | 대표 결재 |

---

## 7. Explicit Non-Changes

프로덕션 **SELECT 만** 실행했다. INSERT/UPDATE/DELETE/DDL 0.
소스 수정 0 · migration 0 · seed 0.
본 문서 1건만 신규 생성.
