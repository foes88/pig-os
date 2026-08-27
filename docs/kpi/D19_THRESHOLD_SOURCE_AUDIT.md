# D-19 — Threshold Source 감사

```
Mode     : READ-ONLY (계산·조회만, 수정 0)
Machine  : bjh
Date     : 2026-08-27
Commit   : 70a56a9  (D-13 과 동일 baseline)
목적     : 등록 룰 40개 각각이 severity 를 어디서 얻는가 + 각 룰이 붙는 KPI
입력처   : G3 불변조건 ③ · 아키텍처 v1.1 §6-1 "APPROVED threshold"
```

---

## 0. 결론부터 — 사전 진단이 틀렸다

D-13 보고 시점의 내 진단은 이랬다.

> "`threshold_resolver` 의 해소 순서는 `rule_configs → operational_defaults → code_default`
> 이고 등록 룰 40개 대비 시드는 29키다. 나머지 11룰은 하드코딩 상수로 색을 낸다."

**틀렸다.** resolver 체인을 보고 "룰 전체가 그 체인을 탄다"고 **추론**했는데,
실제로 그 체인을 호출하는 룰이 누구인지 확인하지 않았다.

확인 결과 **severity 메커니즘이 둘**이고, US 가 표시할 3개 KPI 는
내가 지목한 경로를 **아예 타지 않는다.**

---

## 1. 두 메커니즘

### A. `_severity_from_bench` — 벤치마크 유도

```
loc     app/engine/rules/base.py:17
사용    base.py:69  npd.overdue
        base.py:118 psy.below_target
        base.py:162 farrowing.low_rate
입력    ctx.benchmarks[code]["warning"] / ["critical"]
        = default_metric_values (벤치마크 테이블)
동작    warning is None  →  return None  (경보 없음)
```

**fail-closed 다.** 벤치마크가 없으면 severity 를 만들지 않는다.

### B. `gov_resolve_thresholds` — 임계 리졸버

```
loc     app/engine/threshold_resolver.py:25
사용    rules/_common.py:44   (다수 룰이 공용)
        rules/reproduction.py:52
체인    rule_configs → operational_defaults → code_default
동작    앞의 둘이 없으면 호출부가 넘긴 default_w / default_c 사용
```

**fail-open 이다.** 결재 기록 없는 하드코딩 상수로 색이 나간다.

---

## 2. 커버리지 실측

```
등록 룰                 40
operational_defaults    29   (seed orphan 0)
── covered              29
── UNCOVERED            11
```

**UNCOVERED 11건**

| rule_id | 파일 | severity 메커니즘 |
|---|---|---|
| `psy.below_target` | `rules/base.py` | **A (벤치마크 유도)** |
| `npd.overdue` | `rules/base.py` | **A** |
| `farrowing.low_rate` | `rules/base.py` | **A** |
| `loss.npd` | `rules/loss.py` | 손실액 산출 — 임계 판정 아님 |
| `loss.preweaning_mortality` | `rules/loss.py` | 손실액 산출 |
| `loss.pregnancy_accident` | `rules/loss.py` | 손실액 산출 |
| `loss.sow_culling` | `rules/loss.py` | 손실액 산출 · **KR 게이트**(비-KR 미발화) |
| `farm.weakest_kpi` | `rules/composite.py` | 다른 룰 결과의 합성 |
| `farm.health_class` | `rules/composite.py` | 합성 |
| `inventory.zero` | `rules/base.py` | 존재 판정(임계 없음) |
| `disease.endemic_risk` | `rules/disease.py` | 질병코드 기반 |

★ **11건 중 임계값으로 색을 내는 것은 상단 3건뿐이고, 그 3건은 메커니즘 A 다.**
나머지 8건은 손실액·합성·존재판정이라 애초에 warning/critical 이 없다.
즉 "결재 없는 하드코딩 상수로 색이 나가는 룰"은 이 11건 안에 **없다.**

---

## 3. ★ 진짜 발견 — 두 리졸버 분리 원칙이 깨져 있다

아키텍처 v1.1 §G3 가 선언한 불변조건:

```
Threshold Resolver          → severity/색상의 유일한 권한 (rule_configs / operational_default)
Benchmark Context Resolver  → 비교 맥락만. 색상·판정 없음
```

그리고 G3 불변조건 ①:

```
① … benchmark 기반 severity 없음
```

**이 둘이 이미 위반돼 있다.** `_severity_from_bench` 는 `default_metric_values` 의
`warning`/`critical` 을 읽어 **직접 Severity 를 만든다.** 그리고 그 대상이 하필
`PSY` · `NPD` · `FARROWING_RATE` — **`GLOBAL_VISIBLE` 3개 전부**다.

```python
GLOBAL_VISIBLE = ['FARROWING_RATE', 'NPD', 'PSY']
```

---

## 4. US 교집합 — 사용자가 물은 질문의 답

> "커버 안 된 11룰 중 US 에서 visible 한 KPI 를 건드리는 게 몇 개인가?
>  0개 → US 는 Track 4 와 무관 / N개 → 그 룰만 추출"

**답: 3 of 3.** US 는 COUNTRY 행이 없어 `GLOBAL_VISIBLE` 을 상속하고,
그 3개 전부가 UNCOVERED 이며 전부 메커니즘 A 다.

**다만 처방이 다르다.** "그 룰만 `operational_defaults` 로 추출"은 **효과가 없다** —
이 3개는 `gov_resolve_thresholds` 를 호출하지 않으므로 `operational_defaults` 에
행을 넣어도 읽지 않는다.

```
필요한 것 = 임계값 추출  ✗
필요한 것 = 메커니즘 이관 (A → B) + 그 임계값 결재   ✓
```

### 4-1. 지금 US 를 켜면 실제로 무슨 일이 일어나는가

US 는 승인된 벤치마크가 없다 → `ctx.benchmarks["PSY"]` 등이 비어 있다
→ `warning is None` → `_severity_from_bench` 가 `None` 반환
→ **3개 KPI 전부 severity 없음. 값은 보이고 색은 안 난다.**

이는 G3 가 요구하는 동작과 **우연히 일치한다.** 카드는 살아 있고 비교만 없다.

### 4-2. 그러나 §6-1 의 전제는 깨진다

§6-1 은 `threshold (rule_configs 또는 operational_default)` 를 **런치 필수**로 두고
"severity 권한"이라고 적었다. **이 3개 KPI 에 대해서는 사실이 아니다.**
`operational_defaults` 에 APPROVED 행을 넣어도 severity 가 생기지 않는다.

→ §6-1 과 G3 ③ 의 문안이 **메커니즘 A 를 전제하지 않고 쓰였다.** 정정 필요.

---

## 5. G3 ③ 문안 수정 제안

현재 문안은 `threshold_source ∈ {rule_configs, operational_default}` 만 인정한다.
이대로 강제하면 메커니즘 A 로 색을 내는 3개 KPI 가 **기존 활성 국가에서도** 죽는다
(BR 은 벤치마크가 들어가 있어 현재 색이 난다).

```
③ severity 발화 조건 — severity_source 로 판정한다

   ALLOW   rule_configs
   ALLOW   operational_default
   DENY    code_default                      (결재 기록 없음)
   REVIEW  benchmark_derived (_severity_from_bench)
             → 메커니즘 A. 두 리졸버 분리 원칙 위반이나 현재 PSY·NPD·
               FARROWING_RATE 가 여기 의존한다. 즉시 DENY 하면 BR 이 색을 잃는다.
             → 기존 활성 국가: FLAGGED_FOR_REVIEW (G0 와 동일, 자동 revoke 금지)
             → 신규 국가: 벤치마크 미승인 상태에서는 자연히 None 이므로 추가 차단 불요
             → 해소: 메커니즘 B 로 이관 + 임계 결재 후 ALLOW 로 전환
```

---

## 6. 후속

| # | 항목 | 성격 |
|---|---|---|
| 1 | `psy.below_target` · `npd.overdue` · `farrowing.low_rate` 를 메커니즘 B 로 이관 | **코드 변경.** US 런치 전 필요 여부는 아래 2 에 달림 |
| 2 | US 런치 시 3개 KPI 를 severity 없이 출발시킬 것인가 | **제품 결정.** 없이 가면 1은 런치 후로 미룰 수 있다 |
| 3 | G3 ③ · §6-1 문안 정정 (§5) | 문서 |
| 4 | 메커니즘 A 를 남길 것인가 폐지할 것인가 | 아키텍처 결정. 남기면 "벤치마크는 판정 안 한다"는 선언을 고쳐야 한다 |

**Track 4 전체는 여전히 불필요하다.** 대상은 3개 룰이고, 작업 성격이 추출이 아니라
이관이라는 점만 다르다.

---

## 7. Explicit Non-Changes

소스 수정 0 · migration 0 · seed 0 · git add/commit/push 0.
본 문서 1건만 신규 생성.
