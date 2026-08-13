# ADR-KPI-08 — KPI Status Contract: Rule Engine → API → Frontend

> (구 제목: Backend-Owned KPI Status Contract — 판독 결과 "새 판정엔진 구축"이 아니라
> "이미 있는 판정의 끊어진 contract 복구"임이 확인되어 v0.2에서 범위를 축소·개명)

status: ACCEPTED (v0.3 — P1·P2·P3 패치 반영)
date: 2026-08-13
supersedes: (없음) · depends_on: ADR-KPI-00 P7 · blocks: M3 Country Policy

## 0. Decision (한 문장)

> **PigOS는 새로운 KPI 판정 로직을 만들지 않는다. 기존 국가별 Rule Engine 판정을 canonical status로
> API에 전달하고, Frontend의 모든 KPI threshold/tier 판정을 제거한다.**

---

## 1. Context

PigOS는 국가별 KPI 임계값을 DB(`effective_metric_values`)에 두고 Rule Engine이 이를 적용해 판정한다.
그러나 **대시보드 KPI 카드의 색/등급은 프론트엔드 상수**(`src/lib/kpi/status.ts`)에서 나온다.
결과적으로 국가별 임계값을 바꿔도 화면 상태가 변하지 않는다. 본 ADR은 KPI 상태 판정의 authority를
백엔드로 단일화하는 계약을 정의한다. **본 문서는 설계이며 구현을 포함하지 않는다.**

---

## 2. Verified Current State

### 2.0 Provenance (판독 기준)

```yaml
provenance:
  machine: bjh
  repo: C:/dev/PigOS
  branch: feat/consent-infra
  commit: 7cd764c
  refs:
    main / origin/main: 898d3bf
    fix/kpi-npd-wei-m1 / origin/…: bc66c61   # origin/main 조상 YES
    feat/consent-infra(origin): 088edae      # origin/main 조상 YES, merge-base 898d3bf
merge_plan: NOT_FOUND        # feat/consent-infra의 main 머지 예정 여부는 repo에서 확인 불가
note: 두 브랜치 모두 origin/main을 조상으로 하며, 아래 프론트 tier FACT는 세 ref에서 동일(3건).
```

### 2.1 Frontend tier — 존재 확인 (P7 위반 실재)

`src/lib/kpi/status.ts`
```ts
export type KpiTier = "normal" | "warning" | "critical" | "insufficient";   // L5
psyTier:           invalid(v,0,45)  → insufficient; n>=28 normal : n>=22 warning : critical   // L12-15
npdTier:           invalid(v,0,365) → insufficient; n<=35 normal : n<=50 warning : critical   // L19-22
farrowingRateTier: invalid(v,0,100) → insufficient; n>=90 normal : n>=80 warning : critical   // L26-29
TIER_STYLE: Record<KpiTier, {text,dot,chip}>                                                   // L33
```

**호출처 전수 (G2)** — 사용 화면은 2개뿐:
```
src/app/(app)/kpi/page.tsx   L10 import · L78 psyTier · L83 npdTier · L89 farrowingRateTier · L149/151 KpiTier·TIER_STYLE
src/app/(app)/page.tsx       L16 import · L131 psyT · L132 npdT · L133 frT · L337/339 KpiTier·TIER_STYLE
src/tests/lib/kpiStatus.test.ts  (임계값 회귀 테스트 — 마이그레이션 시 교체 대상)
```
report/export/mobile 경로에서의 tier 사용: **NOT_FOUND**(위 2파일 외 호출처 없음).

### 2.2 Backend severity — 존재하나 KPI 카드용으로 노출되지 않음

```python
# api/app/engine/rule_engine.py
class Severity(str, Enum): OK="OK"; INFO="INFO"; WARNING="WARNING"; CRITICAL="CRITICAL"
_SEVERITY_RANK = {OK:0, INFO:1, WARNING:2, CRITICAL:3}
```

세 번째 vocabulary도 존재:
```python
# api/app/schemas/kpi.py L53-60
class _KpiValueInternal(BaseModel):
    """Internal — rich KPI value with benchmarks. Not exposed in API responses."""
    status: str  # OK / WARNING / CRITICAL / NO_DATA      ← 내부 전용, API 미노출
```

즉 시스템에 상태 어휘가 **3개** 병존한다:
| 계층 | 어휘 | 값 |
|---|---|---|
| 백엔드 룰 | `Severity` | OK · INFO · WARNING · CRITICAL |
| 백엔드 내부 KPI | `_KpiValueInternal.status` | OK · WARNING · CRITICAL · **NO_DATA** |
| 프론트 | `KpiTier` | normal · warning · critical · **insufficient** |

### 2.3 API status — KPI별 status 필드 부재 (핵심 갭)

```python
# api/app/schemas/kpi.py — DashboardKpi (L25-50)
psy: float | None
npd: float | None
sow_turnover: float | None
farrowing_rate: float | None
country: str | None
benchmarks: dict[str, KpiBenchmark]      # "PSY" | "NPD" | "FARROWING_RATE"
alerts: list[Alert]                       # Alert.severity: str (OK/INFO/WARNING/CRITICAL) — L10
```
**KPI별 `status`/`severity` 필드 없음.** severity는 `alerts[]`(룰 finding)에만 존재하며
카드 단위 판정으로 매핑되지 않는다 → 프론트가 tier 함수로 이 공백을 메우고 있다.

### 2.4 Benchmark path — 국가별 임계는 이미 백엔드에 있다

```python
# api/app/services/kpi_service.py
L5   "Benchmarks resolved via effective_metric_values() DB function"
L34/314 SELECT * FROM effective_metric_values
L45-47 / L325-327:
    "warning":   row.warning_threshold
    "critical":  row.critical_threshold
    "direction": row.alert_direction (기본 "below")
L644/835 benchmarks = await _all_benchmarks(db, farm) → DashboardKpi(benchmarks=…)
```
```python
# api/app/schemas/kpi.py — KpiBenchmark
avg: float|None ; top25: float|None ; target: float|None      # ← warning/critical/direction 없음
```

**판정**: `effective_metric_values`는 국가별 `warning_threshold`·`critical_threshold`·`alert_direction`을
이미 보유하고 Rule Engine이 사용 중이다(`_severity_from_bench`, `base.py`). 그러나 **API 직렬화 단계에서
임계·방향이 탈락**하고 avg/top25/target만 나간다. 프론트는 판정에 필요한 정보를 받지 못한 채 상수를 쓴다.

benchmark 값 출처 분류: **COUNTRY_POLICY** (`effective_metric_values`, 농장 country 기준) —
단 프론트 fallback 상수(`?? 28`, `?? 35`, `?? 90` — kpi/page.tsx L77·82·88)는 **STATIC_FRONTEND**.

---

## 3. Problem

§3 명제는 **현재 코드에서 성립한다**:

> 동일 KPI에 대해 백엔드는 국가별 규칙으로 판정하고(alerts), 프론트는 별도 하드코딩 임계로 다시 판정한다(카드 색).

파생 위험(모두 현재 코드에서 가능):
- `backend verdict != frontend color` — 룰은 WARNING인데 카드는 normal(또는 그 반대)
- **국가별 benchmark 변경이 UI 상태에 반영되지 않음** → M3 산출물 무효화
- 새 국가 추가 시 프론트 코드 수정 필요
- Rule Engine과 UI 의미가 독립적으로 drift
- 어휘 3종 병존으로 채널 간 status 불일치
- 실증 사례: `npdTier(<=35 normal)`에 WEI(5~8일)가 들어가 **항상 normal** (M1에서 tier=null로 우회)

---

## 4. Decision

1. **KPI 상태 판정 authority = 백엔드**(기존 Rule Engine). 프론트는 렌더링만 한다.
2. **판정 로직을 새로 만들지 않는다.** 기존 `effective_metric_values`(국가별 warning/critical/direction)
   + Rule Engine 판정을 **canonical status로 승격**해 API에 싣는다.
3. 프론트의 KPI 임계·국가 분기·방향성 판정 코드는 **전량 제거**한다.
4. 상태 어휘는 **하나**로 통일하고, 나머지는 백엔드 내부에서 매핑한다.

### 4.1 판독: 대시보드 KPI ↔ Rule 판정 1:1 재사용 가능성 (핵심 질문)

`RuleRegistry.register` (api/app/engine/rules/base.py) 기준:

| 대시보드 KPI (DashboardKpi) | Rule | rule의 kpi= | 1:1 재사용 |
|---|---|---|---|
| `psy` | `psy.below_target` (L150) | `PSY` | ✅ 가능 |
| `farrowing_rate` | `farrowing.low_rate` (L185) | `FARROWING_RATE` | ✅ 가능 |
| `npd` | `npd.overdue` (L97) | `NPD` | ⚠️ 매핑은 1:1이나 **M1에서 비활성**(ADR-KPI-03 대기) → 당분간 `insufficient` |
| **`sow_turnover`** | **없음** | — | ❌ **rule 미존재 → adapter 필요** |
| `active_sows` 등 카운트 | `inventory.zero`(SOW_COUNT) | 상태카드 아님 | N/A |

**결론: 부분 YES(3/4).** 따라서 serializer는 "severity를 그냥 가져오기"만으로 충분하지 않고,
**KPI Status Contract Assembler**(§4.2)가 필요하다.

### 4.1.1 status 결정 규칙 (P1 — `normal`은 적극적으로 증명된 상태)

> "발화 없음 = normal"로 뭉뚱그리지 않는다. rule 미실행·컨텍스트 부족·매핑 실패가
> normal(초록)로 표시되면 침묵 실패(silent pass)가 된다.

```
rule exists + evaluation completed + sufficient data + no violation
    → normal                       # 적극 증명됨

rule exists + evaluation completed + violation
    → warning / critical           # severity 매핑

rule exists but evaluation unavailable / skipped / disabled / context missing
    → insufficient(reason= evaluation_skipped | rule_disabled | context_missing | policy_pending)

rule does not exist for this metric_key
    → insufficient(reason="no_policy")

value 없음 / 표본 부족 / 유효범위 밖
    → insufficient(reason= no_data | insufficient_sample | out_of_valid_range)
```

- `npd`는 현재 rule이 **비활성**(M1) → `insufficient(reason="policy_pending")`.
  **절대 `npdTier()`로 폴백하지 않는다.** 정책 미확정이면 UI는 판단하지 않고 insufficient를 표시한다
  — 이 케이스가 본 ADR 원칙의 실증이다.

### 4.2 KPI Status Contract Assembler (P2 — 판정기가 아님)

이름을 **Assembler**로 고정한다(“adapter”는 판정 로직이 스며들 여지를 준다).
책임은 **연결·정규화**뿐이다.

```
허용:
  - metric_key ↔ rule evaluation 결과 연결
  - rule evaluation 결과(Severity) → canonical status 변환
  - missing / unavailable / no_policy / disabled → insufficient(+reason) 정규화

금지:
  - threshold 비교          (warning/critical 값을 직접 다루지 않음)
  - country 조건 분기
  - KPI별 자체 판정
  - benchmark(avg/top25/target) 기반 재판정
```
Assembler가 threshold를 읽어야 한다면 그것은 설계 위반이다 — 판정은 Rule Engine에서 이미 끝나 있어야 한다.

---

## 5. Canonical Status Contract

```yaml
canonical_status:
  owner: backend
  values: [normal, warning, critical, insufficient]
  unknown_behavior: 프론트는 미지 값을 insufficient와 동일한 중립 표현으로 렌더 + 로깅. 자체 임계 계산 금지.
```

**선택 근거**: 카드 상태는 "경보 발생 여부(Severity)"가 아니라 "지표가 좋은가/데이터가 있는가"다.
`normal|warning|critical|insufficient`는 (a) 이미 프론트·`_KpiValueInternal`(NO_DATA≈insufficient)에서
쓰는 4분류와 정합하고, (b) `Severity.INFO`처럼 카드에 의미 없는 값이 없다.
`Severity`는 **알림(alerts) 도메인 어휘로 존속**하며 폐기하지 않는다.

**매핑(백엔드 내부, 단방향)**
```
Severity.OK        → normal
Severity.WARNING   → warning
Severity.CRITICAL  → critical
Severity.INFO      → (카드 상태 아님 — alerts에만 유지)
_KpiValueInternal.NO_DATA / value=None / 근거부족 → insufficient
```

---

## 6. Backend Responsibilities

```
farm.country → effective_metric_values(warning/critical/direction) → KPI value
            → status 계산(_severity_from_bench 동일 로직) → canonical status → serializer
```
- 값 부재·표본 부족·정의 미확정(예: 현재 NPD/WEI 혼선)은 **insufficient**로 산출한다.
- KPI별 status 계산은 룰 발화와 **동일한 임계·방향 소스**를 사용해야 한다(이중 진실 금지).

---

## 7. API Contract

`DashboardKpi`에 KPI별 status를 추가한다(필드 추가 = 하위호환). **D1 확정:**

```json
{
  "psy": 24.3,
  "kpi_status": {
    "PSY":            { "status": "normal",       "reason": null },
    "FARROWING_RATE": { "status": "warning",      "reason": null },
    "NPD":            { "status": "insufficient", "reason": "policy_pending" },
    "SOW_TURNOVER":   { "status": "insufficient", "reason": "no_policy" }
  }
}
```

**D1-1. `reason`은 항상 존재하고, 없으면 `null`** (optional 금지)
> optional로 두면 프론트가 `reason` 유무로 분기하게 되고, **그것이 프론트 판단 로직의 입구**가 된다.
> 본 ADR이 막으려는 바로 그 패턴이므로 키를 항상 내려보낸다.

**D1-2. 키는 `metric_code`로 통일** (`PSY`·`NPD`·`FARROWING_RATE`·`SOW_TURNOVER`)
> 이미 `effective_metric_values`와 `benchmarks` dict가 쓰는 키다. 동일 키를 쓰면
> 후속 Registry(canonical_variant_id) 연결 시 **매핑 테이블이 불필요**하다.
- **UI가 판정을 재현하기 위해 threshold 전체를 받을 필요는 없다.**
- 기존 `benchmarks`(avg/top25/target)는 "비교 표시" 목적이며 **status 계산과 분리**된다.

---

## 8. Frontend Responsibilities

허용: ① status 수신 ② status→UI 토큰 매핑 ③ 렌더 ④ unknown 안전 폴백
금지: KPI 임계값, 국가 조건 분기, benchmark 비교로 good/bad 판정, 방향성 판정,
그리고 `?? 28`·`?? 35`·`?? 90` 형태의 **정적 임계 폴백**.

---

## 9. Benchmark Exposure Policy

### 9.1 benchmark ≠ threshold ≠ status (세 데이터는 별개)

| 데이터 | 소스 | 성격 | 프론트 노출 |
|---|---|---|---|
| **benchmark** `avg/top25/target` | `effective_metric_values` → `KpiBenchmark` | **설명·비교용** ("국가평균 22.0") | ✅ 현행 유지 |
| **threshold** `warning/critical/direction` | `effective_metric_values` → Rule Engine | **판정 정책** | ❌ **내려보내지 않음** |
| **status** | 백엔드가 threshold 적용한 결과 | **판정 결과** | ✅ 신규(본 ADR) |

**threshold를 API로 내려 프론트가 재계산하게 만들면 본 ADR을 한 의미가 사라진다.**
프론트는 threshold를 알 필요가 없다. benchmark는 "비교 표시"로만 계속 쓴다.

### 9.2 채널별 노출

> **Status semantic consistency ≠ identical field exposure**

- status 의미는 dashboard/report/export/mobile에서 동일해야 한다.
- 그러나 `benchmark_value`·`benchmark_source`·`threshold`·`rule config`는 채널별 노출 정책을 따른다
  (외부 API·export에서는 숨길 수 있음). serializer는 status 통일을 이유로 임계·내부 config를 자동 노출하지 않는다.

---

## 10. Insufficient / Unknown Handling

- `insufficient`는 normal/warning으로 강등·승격하지 않는다.
- 현재 백엔드에 `NO_DATA`가 존재(내부)하나 **API로 나가지 않음** → 계약에 포함시킨다.
- reason 후보: `no_data` · `insufficient_sample` · `definition_pending` · `out_of_valid_range`.
- 프론트 unknown enum: 중립 렌더 + telemetry. **임계 계산으로 폴백 금지.**

---

## 11. Migration Plan

| Phase | 내용 | 되돌리기 |
|---|---|---|
| **1. Contract** | 백엔드 status 계산 + `kpi_status` 응답 필드 추가(가산적) | 필드 무시 |
| **2. Dual observation** | 프론트가 backend status와 legacy tier를 비교해 **불일치만 로깅**(사용자 판정은 legacy 유지) | 로깅 제거 |
| **3. Renderer 전환** | 카드가 backend status만 사용 (kpi/page.tsx, page.tsx) | Phase2로 롤백 |
| **4. Legacy 제거** | `psyTier`/`npdTier`/`farrowingRateTier`·정적 폴백 상수 삭제, `kpiStatus.test.ts` 교체 | revert |
| **5. Guard** | lint/test gate로 KPI 하드코딩 임계 재도입 차단 | — |

M1 연계: M1의 `tier={null}`·`bench={null}`(NPD 카드)은 Phase 3에서 backend status로 대체되며,
M1 INTERIM 트리거(여집합 NPD가 main에 이관되면 revert)와 **충돌하지 않는다**.

---

## 12. Test / Acceptance Gates (목록만 — 작성은 구현 시)

1. **Backend contract**: country → rule/benchmark → status
2. **국가 차등**: 동일 KPI value가 국가별로 다른 status
3. **Insufficient 보존**: 데이터 부족이 normal/warning으로 변질되지 않음
4. **Frontend renderer**: 4개 canonical status 각각의 렌더
5. **Unknown enum**: 미지 status가 임계 계산으로 폴백하지 않음
6. **Regression**: 프론트 tier 함수 호출 0 (grep gate)
7. **Cross-channel**: dashboard/report의 동일 KPI status 의미 일치
   — 단 **benchmark 필드 노출 차이는 불일치로 보지 않는다**
8. **normal 적극증명 (P1)**: rule 미실행·skipped·disabled·context 결손이 **normal로 새지 않음**
   (각각 insufficient + 해당 reason)
9. **no_policy**: rule 없는 KPI(`sow_turnover`)가 `insufficient(no_policy)`로 나오고 프론트가 대체판정하지 않음
10. **policy_pending**: NPD가 `insufficient(policy_pending)`이며 `npdTier` 폴백이 호출되지 않음
11. **Assembler 순수성 (P2)**: Assembler 코드에 threshold 비교·country 분기·benchmark 재판정 부재
    (구현 시 grep/리뷰 게이트)

---

## 13. Rollback

- Phase 1~2는 가산적이므로 무해(필드 무시).
- Phase 3 이후 문제 시: 해당 커밋 revert → legacy tier 복원(Phase 4 이전이면 함수가 남아 있음).
- Phase 4 이후 롤백은 tier 함수 복원이 필요하므로, **Phase 3에서 1개 릴리스 관찰 후 4로 진행**한다.

---

## 14. Risks

- 백엔드 status와 기존 화면 색이 달라져 **사용자가 "성적이 나빠졌다"고 오인** (Phase 2 관찰로 사전 파악)
- **[실측] 임계 시드 커버리지** (2026-08-13, bjh 로컬 판독):
  | 대상 | 시드 행 | 판정 |
  |---|---|---|
  | PSY | 20 | ✅ 임계 적용 가능 |
  | NPD | 20 | ✅ (단 rule 비활성 → policy_pending) |
  | FARROWING_RATE | 12 | ✅ |
  | **SOW_TURNOVER** | **0** | ❌ no_policy 확정 |
  | 로컬 DB `default_metric_values` | **0 rows** (마이그레이션 미적용) | ⚠️ **이 상태로 Phase 3 → 화면 전체 회색** |

  → **착수 전 필수**: ① 개발 DB에 시드 마이그레이션 적용 ② **프로드 실제 커버리지 read-only 확인**.
  프로드에 임계가 비어 있으면 Phase 3 전에 시드 보완이 선행되어야 한다.
- NPD 정의 혼선(브랜치 발산)이 남은 상태에서 status를 붙이면 잘못된 판정 고착 → **NPD는 ADR-KPI-03 확정 후**
- 어휘 3종 매핑 누락 시 채널 간 불일치

---

## 15. Non-Goals (명시적 금지 — 범위 팽창 방지)

- ❌ **새로운 국가별 판정 엔진 구축** — 이미 `effective_metric_values` + Rule Engine이 있다. 복제 금지.
- ❌ **`effective_metric_values` 재설계**
- ❌ **threshold를 frontend로 이전** — warning/critical을 API로 내려 프론트가 재계산하면 본 ADR이 무의미해진다.
- ❌ **benchmark(avg/top25/target)와 alert threshold(warning/critical/direction) 통합** — §9 참조. 둘은 다른 데이터다.
- ❌ **Rule Engine 계산식 변경**
- ❌ **`sow_turnover` 등 rule 없는 KPI를 위한 신규 정책/rule 신설** (D7-B — 후속 작업. 본 ADR은 `no_policy → insufficient` contract만 확정)
- ❌ **ADR-KPI-03(NPD 정의) 완료 대기** — NPD는 `insufficient(policy_pending)`으로 두고 선행 구현한다
- KPI 계산식 변경 · DB 스키마 변경 · 알림(alerts) 도메인의 `Severity` 폐기
- benchmark 값 자체의 정확성 검증(ADR-KPI-01/02 소관)
- NPD 정의 확정(ADR-KPI-03 소관)

---

## 16. Open Decisions

| # | 질문 | 상태 |
|---|---|---|
| D1 | `kpi_status` 필드명·중첩 구조 | **DECIDED** — §7 (reason 항상 존재·null 허용, 키=metric_code) |
| D2 | insufficient reason 어휘 | **DECIDED** — `no_data`·`insufficient_sample`·`out_of_valid_range`·`no_policy`·`policy_pending`·`evaluation_skipped`·`rule_disabled`·`context_missing` (§4.1.1) |
| D3 | Phase 2(dual observation) 수행 여부 | **DECIDED — 수행함.** 사용자 수가 적은 지금이 가장 저렴하고, 백엔드 판정 ↔ 기존 화면색 불일치 로그가 **D-2(재고 결함)의 간접 증거**가 된다(백엔드 WARNING인데 화면 normal = 미발화 사례) |
| D4 | `feat/consent-infra` 머지 계획 | **NOT_FOUND** (조직 결정) |
| D5 | 임계 미설정 KPI 시드 보완 범위 | OPEN |
| D6 | 모바일(Android) 클라이언트 동일 계약 적용 시점 | OPEN |
| **D7-A** | rule 없는 KPI(`sow_turnover` 등)의 contract 처리 | **DECIDED — `insufficient(reason="no_policy")`** (ADR-08 내에서 확정) |
| **D7-B** | `sow_turnover`용 정책/rule을 신설할 것인가 | **분리 — 후속 작업/별도 ADR. ADR-08 Non-Goal, blocker 아님** |

### 16.1 Blocking items (ADR-08 구현 착수 기준 — P3로 축소)

```
1. canonical status enum 확정                      → §5 (결정됨)
2. rule-result → KPI mapping 확정                  → §4.1 (판독 완료)
3. normal / insufficient 판정 조건 확정            → §4.1.1 (결정됨)
4. API additive contract 확정                      → D1 (필드명·구조)
5. frontend legacy tier 호출처 전수 확인           → §2.1 (완료: 2화면+테스트1)
6. NPD 임시 insufficient 정책 확정                 → policy_pending (결정됨)
```
**ADR-08 blocker에서 제외**(과결합 해소): `sow_turnover` rule 신설(D7-B), **ADR-KPI-03 본 구현**.
ADR-03 완료 전에도 다음까지 구현 가능하다 —
`PSY→status` · `farrowing_rate→status` · `NPD→insufficient(policy_pending)` · `sow_turnover→insufficient(no_policy)`.
이것이 오히려 안전한 단계적 이행이다.

---

## §15 질문에 대한 답 (요약)

1. authority = **백엔드** · 2. canonical = `normal|warning|critical|insufficient`
3. 프론트 tier 전부 제거 = **YES**(Phase 4) · 4. 프론트 threshold 예외 = **없음**
5. 프론트가 국가별 threshold를 알 필요 = **NO** · 6. API에 KPI별 status 제공 = **YES**(신규)
7. insufficient 별도 유지 = **YES** · 8. unknown = 중립 렌더+로깅, 계산 폴백 금지
9. benchmark 항상 노출 = **NO**(채널별 정책) · 10. 채널 간 status contract 동일 = **YES**(필드 노출은 별개)
11. 제거 순서 = Contract→Dual→Renderer→Legacy→Guard · 12. rollback = §13
13. M3가 UI까지 도달하는가 = **현재 NO → 본 ADR 시행 시 YES**
