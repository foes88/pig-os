# D-19 — Threshold Source 감사 (본실사)

```
Mode     : READ-ONLY (코드 정적분석 + 프로덕션 SELECT) — 대표 승인 2026-08-27
Machine  : bjh · PigOS 70a56a9 · api.pigos.io PostgreSQL 17 :5434 / db=pigos
목적     : 등록 룰 40개가 severity 를 **실제로** 어디서 얻는가 + 승격 가능 여부
입력처   : G3 불변조건 ③ · 아키텍처 §6-1 "APPROVED threshold" · 사산 P0-2
population_scope : 코드 = 전수 · 프로덕션 설정 = LIVE (모집단 무관, 스키마·설정 사실)
```

> 본 문서는 1차 약식 감사를 **전면 대체**한다. 1차는 두 차례 틀렸고 그 경위를 §0 에 남긴다.

---

## 0. 두 번의 오진 — 경위를 남긴다

### 오진 1 (D-13 보고 시점)

> "`threshold_resolver` 체인이 `rule_configs → operational_defaults → code_default` 이고
> 등록 룰 40 대비 시드 29키다. **나머지 11룰이 하드코딩 상수로 색을 낸다.**"

resolver 체인을 보고 **모든 룰이 그 체인을 탄다고 추론**했다. 호출자를 확인하지 않았다.

### 오진 2 (1차 D-19)

> "severity 메커니즘은 둘이다. UNCOVERED 11 중 색을 내는 건 3건뿐이고 그 3건은
> 메커니즘 A 다."

핸들러 본문만 grep 했다. 나머지 29룰은 `_common.resolve()` 헬퍼를 거치므로
본문에 `gov_resolve_thresholds` 가 **보이지 않았을 뿐** 임계값을 쓰고 있었다.
그래서 37건을 "임계 없음"으로 오분류했다.

### 공통 원인

두 번 다 **호출 그래프를 한 단계만 보고 판정**했다. 이 문서는 헬퍼를 관통해
호출부의 리터럴까지 추출했고, **프로덕션 설정과 테이블 실적재까지** 확인했다.

---

## 1. 룰 40개 분류 (코드 전수)

```
B-resolve      29   _common.resolve(ctx, rule_id, kpi, default_w, default_c)
A-bench         3   _severity_from_bench(value, ctx.benchmarks[kpi], direction)
no-threshold    8   손실액·합성·존재판정 — warning/critical 개념이 없다
                ──
                40
```

**임계값을 쓰는 룰 = 32.** `B-resolve` 29 는 `operational_defaults` 시드 29 와 **정확히 1:1** 이다.

### 1-1. A-bench 3 — `GLOBAL_VISIBLE` 전부다

| rule_id | KPI | loc |
|---|---|---|
| `psy.below_target` | PSY | `base.py:118` |
| `npd.overdue` | NPD | `base.py:69` |
| `farrowing.low_rate` | FARROWING_RATE | `base.py:162` |

```python
GLOBAL_VISIBLE = ['FARROWING_RATE', 'NPD', 'PSY']
```

### 1-2. B-resolve 29 — 호출부 인라인 상수

| rule_id | code_default (w/c) | rule_id | code_default (w/c) |
|---|---|---|---|
| `accident.parity_skew` | 40.0 / 55.0 | `msy.below_bep` | 17.0 / 15.0 |
| `adg.low` | 650.0 / 550.0 | `mummified.rate_high` | 2.0 / 4.0 |
| `batch.aiao_detect` | 50.0 / 70.0 | `parity.high_ratio` | 20.0 / 30.0 |
| `birth_weight.low` | 1.3 / 1.1 | `parity.second_litter_slump` | 1.5 / 2.5 |
| `boar.farrow_rate_low` | 65.0 / 55.0 | `piglet.crushing_rate_high` | 6.0 / 10.0 |
| `born_alive.low` | 11.0 / 10.0 | `piglet.death_age_skew` | 70.0 / 80.0 |
| `culling.rate_high` | 45.0 / 55.0 | `replacement.rate_abnormal` | 50.0 / 60.0 |
| `fcr.high` | 3.0 / 3.3 | `sow_mortality.high` | 8.0 / 12.0 |
| `finish_mortality.high` | 5.0 / 8.0 | `stillborn.rate_high` | 8.0 / 12.0 |
| `lactation.too_long` | 28.0 / 35.0 | `total_born.low` | 12.0 / 11.0 |
| `lactation.too_short` | 19.0 / 16.0 | `weaned.low` | 10.0 / 9.0 |
| | | `weaning_weight.low` | 5.5 / 5.0 |

(리터럴이 변수/조건으로 들어가 정적 추출이 안 된 6건: `abortion.rate_high` ·
`conception.rate_low` · `pwmr.high` · `rts.rate_high` · `seasonal.summer_infertility` ·
`wsi.overdue` — 상수 존재는 확인, 값은 개별 판독 필요)

### 1-3. no-threshold 8

`disease.endemic_risk` · `farm.health_class` · `farm.weakest_kpi` · `inventory.zero` ·
`loss.npd` · `loss.preweaning_mortality` · `loss.pregnancy_accident` · `loss.sow_culling`

→ G3 ③ 적용 대상이 아니다.

---

## 2. ★ 프로덕션에서 실제로 색을 내는 것

```
USE_GOVERNANCE_BENCHMARKS = False        ← 프로덕션 실측
```

`_common.resolve()` 는 이 flag 로 갈린다.

```python
if governance_enabled():                        # ← 프로덕션에서 False
    return gov_resolve_thresholds(...)          # rule_configs → operational_defaults → code
# flag OFF 경로 (= 현재 프로덕션)
cfg = ctx.extra["rule_configs"].get(rule_id)
w, c = cfg.get("warning"), cfg.get("critical")
if w is None: w = ctx.benchmarks[kpi].get("warning")      # ← default_metric_values
if c is None: c = ctx.benchmarks[kpi].get("critical")
return (w or default_w, c or default_c)                   # ← 인라인 상수
```

### 실적재 확인 (프로덕션)

| 소스 | 행 | 상태 |
|---|---|---|
| `rule_configs` | **0** | 비어 있음 — 기여 없음 |
| `operational_defaults` | 29 | **flag OFF 라 읽히지 않는다.** origin 29/29 = `code_default` |
| `default_metric_values` | 87 (warning 68 / critical 65) | **← 실제로 색을 내는 것** |

`default_metric_values` 의 임계 근거:

```
warning_threshold 보유 68행 중
  threshold_basis 있음   7행  (us_avg_pic_intervention 등)
  threshold_basis NULL  61행
is_proxy = true         20행
```

### 2-1. 결론 — 두 리졸버 분리 원칙은 3룰이 아니라 **32룰 전부**에서 깨져 있다

아키텍처 §G3 선언:

```
Threshold Resolver          → severity/색상의 유일한 권한 (rule_configs / operational_default)
Benchmark Context Resolver  → 비교 맥락만. 색상·판정 없음
```

프로덕션 실태:

```
rule_configs        0행       → 권한 행사 없음
operational_default 미조회    → flag OFF
default_metric_values        → 32룰 전부의 severity 를 사실상 여기서 만든다
```

**벤치마크 테이블이 곧 임계값 테이블이다.** 메커니즘 A(3룰)만의 문제가 아니었다.

---

## 3. 승인 이력이 있는 threshold = **0**

```
rule_configs           0행
operational_defaults   origin 29/29 = 'code_default'   (스스로 그렇게 기록)
default_metric_values  threshold_basis 61/68 NULL, is_proxy 20
```

**시스템 전체에 결재를 거친 임계값이 하나도 없다. BR 도 포함이다.**

→ G3 ③ 을 원안대로 강제하면 **BR 이 즉시 전면 무채색이 된다.** 일부 KPI 가 아니라 전부다.
G0(소급 자동 revoke 금지)가 필요했던 이유이고, 그 적용 범위가 전체라는 뜻이다.

---

## 4. G3 불변조건 ③ — 재작성안

원안(`threshold_source ∈ {rule_configs, operational_default}`)은 **실제 소스를 enum 에
넣지도 않았다.** 프로덕션이 쓰는 `default_metric_values` 가 목록에 없다.

```
③ severity 발화 조건 — threshold row 의 origin 으로 판정한다

  ALLOW   origin ∈ {approved_policy, tenant_config}
  DENY    origin = code_default
  DENY    benchmark_derived (default_metric_values / _severity_from_bench)
            ★ 벤치마크는 비교 맥락이지 판정 권한이 아니다 — ① 과 같은 원칙

  적용
    신규 국가 활성화  → 강제
    기존 활성 국가    → FLAGGED_FOR_REVIEW (자동 revoke 금지, G0 동일)
                        현재 승인 threshold 0 이므로 사실상 전건 FLAGGED
```

---

## 5. 범위 재정의 — 테이블 채우기가 아니라 origin 승격

1차 결론("11룰을 operational_default 로 추출")은 폐기한다. 테이블은 이미 29행이 있고
**읽히지도 않는다.** 실제 작업은:

| 대상 | 건수 | 작업 |
|---|---|---|
| B-resolve 29 | 29 | 값은 이미 시드돼 있다 → **`origin` 을 `approved_policy` 로 승격**. 값 자체의 타당성 재검토 동반 |
| A-bench 3 | 3 | **메커니즘 이관(A → B)** 후 승격. 코드 변경 필요 |
| 리터럴 미추출 6 | 6 | 개별 판독 후 위 두 갈래로 편입 |
| no-threshold 8 | 8 | 대상 아님 |
| `USE_GOVERNANCE_BENCHMARKS` | — | 승격 완료 전에는 켜면 안 된다 — 켜는 순간 소스가 바뀐다 |
| `default_metric_values` 68행 | 68 | 임계 컬럼을 **벤치마크에서 분리**하거나, 판정 사용을 차단 |

★ **`USE_GOVERNANCE_BENCHMARKS` 를 켜는 것 자체가 배포 변수다.** 켜면 32룰의 임계 소스가
`default_metric_values` → `operational_defaults` 로 통째로 바뀐다. 값이 다르면 색이 바뀐다.
승격·검증 전에 켜지 않는다. **DB 제약 변경과 같은 배포에 넣지 않는다.**

---

## 6. 사산 P0-2 로 넘기는 것

사산 결정표는 **산식 + 임계값 묶음**이어야 한다. 근거:

- `stillborn.rate_high` 의 8.0/12.0 은 인라인 상수이며 `operational_defaults` 사본도
  `origin=code_default` 다. **승인 이력이 없다.**
- 두 산식은 분자가 다르다(미라 포함/제외). 미라를 포함하면 값이 **구조적으로 올라가므로**
  같은 8/12 가 두 산식에 동시에 타당할 수 없다.
- 즉 산식만 고르면 **승인 안 된 기준에 승인된 산식을 붙이는** 반쪽 결재가 된다.

---

## 7. Explicit Non-Changes

코드 수정 0 · migration 0 · seed 0 · 설정 변경 0 · git add/commit/push 0(실사 중).
프로덕션은 `SELECT` 와 설정 조회만. 본 문서 1건 갱신.
