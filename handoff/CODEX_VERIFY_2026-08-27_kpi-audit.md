# CODEX 독립검증 — KPI 감사 3건 (D-13 / D-19 / D-20)

```
대상 커밋   a2e813c  (main)
저장소      C:\dev\PigOS  ·  참조: C:\dev\pigos-android, C:\dev\pigos-ios
모드        READ-ONLY. 코드 수정·커밋·푸시·마이그레이션 전면 금지
프로덕션    조회 필요 시 SELECT 만. ssh -i <key> ubuntu@52.78.65.6
            sudo -u postgres psql -p 5434 -d pigos
산출물      이 파일 옆에 CODEX_RESULT_2026-08-27.md 1개
```

## 검증 대상 문서

```
docs/kpi/CANONICAL_FORMULA_SPEC.md      D-13 canonical formula 실사
docs/kpi/D19_THRESHOLD_SOURCE_AUDIT.md  D-19 threshold source 감사 (본실사)
docs/kpi/D20_DIVERGENCE_IMPACT.md       D-20 divergence 영향 정량화 (+ 정정 섹션)
docs/specs/COUNTRY_KPI_EVIDENCE_ARCHITECTURE_v1.1.md   §3-4 정정 · G3 ③ · §2-1-A
api/tests/integration/test_us_template_lock.py         P1 Template LOCK 게이트
```

---

## 0. 이 검증에서 가장 중요한 것

작성자(Claude)는 **오늘 같은 종류의 실수를 세 번 했다.** 세 번 다 스스로 잡았지만,
세 번 다 **처음 보고할 때는 확신에 차 있었다.** 그러니 확신의 어조를 근거로 취급하지 마라.

| # | 오류 | 원인 |
|---|---|---|
| 1 | "11룰이 하드코딩 상수로 색을 낸다" | resolver 체인을 보고 **모든 룰이 그 체인을 탄다고 추론**. 호출자 미확인 |
| 2 | "37룰은 임계값이 없다" | **핸들러 본문만 grep.** 29룰이 `_common.resolve()` 헬퍼를 거쳐 안 보였을 뿐 |
| 3 | "사산 flip 38.6% → 인시던트" | **`farms.data_origin` 으로 모집단을 나누지 않음.** 42/44 가 하베스트 참조 농장 |

**공통 실패 모드 두 가지다. 이 검증은 이 둘을 겨냥한다.**

```
① 호출 그래프를 한 단계만 보고 판정한다 (헬퍼·간접호출·flag 분기를 관통하지 않는다)
② 집계 전에 모집단을 나누지 않는다
```

★ 아래 어떤 주장이든, **당신이 직접 코드/DB 에서 재도출하지 못하면 `UNVERIFIED`** 다.
문서가 인용한 file:line 을 그대로 믿지 말고 열어라. 라인이 어긋나 있을 수도 있다.

★ **반증 우선.** "맞다"를 확인하려 하지 말고 **틀릴 수 있는 지점을 먼저 치라.**
각 항목에 "여기를 의심하라"를 달아뒀다.

---

## 1. D-13 — canonical formula

### C-1. LIVE_DIVERGENCE 2건이 실재하는가 (최우선)

주장:

```
사산    ①  stillborn / total_born                services/kpi_service.py:523
        ②  (stillborn + mummified) / total_born  services/insight_service.py:211
PWM     ①  deaths / (weaned + deaths)            services/kpi_service.py:512
        ②  (born_alive - weaned) / born_alive    services/insight_service.py:229
양쪽 모두 path_reachability = LIVE
```

**검증할 것**
1. 네 지점의 산식이 문서 서술과 실제로 같은가.
2. reachability 를 **당신이 독립적으로** 추적하라. 문서가 적은 경로를 확인만 하지 말고,
   **다른 진입점이 더 있는지** 찾아라. 특히 `sync` 경로(오프라인 동기화)와
   배치 잡(`app/jobs/`)에서 같은 KPI 를 또 계산하는 곳이 있는지.
3. 두 경로가 **같은 metric_code 로 같은 임계/벤치마크에 대조되는가.**

**여기를 의심하라**
- 문서는 진입점을 2개만 찾았다. `app/jobs/kpi.py` 는 확인했는가? 스냅샷 재계산 경로
  (`recalculate_snapshot_on_event_change`)가 세 번째 산식을 쓰고 있을 수 있다.
- `report_service.py` 에도 사산/PWM 계산이 있는가? (grep 매치 45건이 있었다)

### C-2. CONFIRMED 7건이 정말 단일 경로인가

`PSY · NPD · SOW_TURNOVER · FARROWING_RATE · WSI · MSY · WEANED_PER_LITTER`

**검증할 것**: 각 KPI 에 대해 **계산 경로가 하나뿐임을 증명**하라.
C-1 의 두 건은 "두 경로"라서 AMBIGUOUS 가 됐다. 나머지 7건은 **경로가 하나임을
확인한 것인가, 아니면 하나만 찾은 것인가?**

**여기를 의심하라**
- 문서는 `api/app` 만 스캔했다. `app/repositories/npd_repo.py` 는 별도 산식을 갖는가?
- `v_sow_npd` view 가 "미사용"이라는 주장을 확인하라. 진짜 아무도 안 쓰는가?

### C-3. §7-3 재고 분모 2구현

주장: `_avg_active_inventory`(`kpi_service.py:348-367`)가 PSY docstring 이 결함으로
명시한 두 가지(후보돈 포함 · `deleted_at` 게이팅)를 그대로 갖고 있다.

**검증할 것**: 논리를 직접 따져라 —
`(s.deleted_at IS NULL OR (s.exit_date IS NOT NULL AND s.exit_date >= mo))` 가
정말 "퇴출됐는데 soft-delete 안 된 모돈을 계속 포함"시키는가?

**여기를 의심하라**: 프로덕션에 그런 행이 실제로 있는가?
`SELECT count(*) FROM sows WHERE deleted_at IS NULL AND exit_date < CURRENT_DATE;`
0이면 이 결함은 이론적이다. 문서는 그 확인을 하지 않았다.

### C-4. 모바일 감사

주장: Android·iOS 둘 다 KPI 목록 하드코딩, `/kpi/presentation` 미소비,
iOS 는 benchmark 필드 자체가 없음.

**여기를 의심하라**
- 문서는 `DashboardScreen` 만 봤다. 다른 화면(리포트·KPI 상세)이 API 를 소비하는가?
- Android `KpiDetailScreen.kt` 는 확인되지 않았다.

---

## 2. D-19 — threshold source (오류 이력 2회)

### C-5. 룰 40 분류가 맞는가

주장: `B-resolve 29 + A-bench 3 + no-threshold 8 = 40`, 그리고
B-resolve 29 가 `operational_defaults` 29 와 **정확히 1:1**.

**검증할 것**: 당신 방식으로 다시 세라. 특히 **`no-threshold 8`** 이 정말 임계값을
안 쓰는지 — 오진 2가 정확히 이 분류에서 났다.

**여기를 의심하라**
- `loss.*` 4건은 손실액 산출이라 임계가 없다고 했다. 그런데 `loss.npd` 는 내부에서
  `_residual` / benchmark 를 읽는다. **금액 임계**가 숨어 있지 않은가?
- `farm.health_class` / `farm.weakest_kpi` 는 다른 룰 결과를 합성한다고 했다.
  합성 과정에 **자체 컷오프**가 있지 않은가?
- 정적 추출에 실패한 6건(`abortion.rate_high` · `conception.rate_low` · `pwmr.high` ·
  `rts.rate_high` · `seasonal.summer_infertility` · `wsi.overdue`)의 실제 상수를 읽어라.

### C-6. ★ 프로덕션 severity 소스 (가장 중요)

주장:

```
USE_GOVERNANCE_BENCHMARKS = False   (프로덕션)
→ _common.resolve() 가 flag OFF 갈래를 탄다
→ rule_configs(0행) → default_metric_values → 인라인 상수
→ 즉 default_metric_values 가 32룰 전부의 severity 를 만든다
```

**검증할 것**
1. flag 값을 직접 확인하라 (`sudo docker exec pigos-api python -c "..."`).
2. `_common.resolve()` 의 두 갈래를 읽고, **flag OFF 에서 어느 소스가 이기는지** 따져라.
3. `rule_configs` 가 정말 0행인가.
4. `default_metric_values` 의 `warning_threshold` 가 `ctx.benchmarks[kpi]["warning"]` 로
   **실제로 전달되는지** 로딩 경로를 추적하라 (`_all_benchmarks` / `_get_benchmark`).

**여기를 의심하라**
- 컬럼명이 `warning_threshold` 인데 코드는 `bench.get("warning")` 을 읽는다.
  **어디서 키 이름이 바뀌는가?** 매핑이 없으면 이 주장 전체가 무너지고,
  실제로는 인라인 상수가 이기는 것이 된다. **이 지점을 반드시 확인하라.**
- `governance_enabled()` 가 요청마다 읽히는가, import 시점에 고정되는가?

### C-7. "승인 이력 있는 threshold = 0"

주장: `rule_configs` 0행 · `operational_defaults.origin` 29/29 `code_default` ·
`default_metric_values.threshold_basis` 61/68 NULL.

**검증할 것**: 세 쿼리를 직접 돌려라.

**여기를 의심하라**: `threshold_basis` 가 NULL 인 것과 "승인 이력이 없다"는 같은 말인가?
승인 기록이 **다른 테이블**(decision register 류)에 있지 않은가? 있으면 이 결론은 과장이다.

---

## 3. D-20 — divergence 영향 (오류 이력 1회)

### C-8. 모집단 분리 후 수치

주장:

```
최근 365일 분만 실적 44농장
  pigplan_migration / internal_reference   42농장 · 54,031분만
  native_signup     / live_customer         2농장 ·      3분만
사산 flip 17/44(38.6%) · PWM 격차 7.24%p — 전부 하베스트 참조 데이터 통계
```

**검증할 것**: 쿼리를 재현하라. 그리고 **`live_customer` 만으로 같은 통계를 내라.**
표본이 3건이면 "산출 불가"로 보고되어야 한다 — 문서가 그렇게 적었는가?

**여기를 의심하라**
- `data_classification` 이 `internal_reference` 인데 **실제로 로그인해서 대시보드를 보는
  계정이 붙어 있는지** 확인하라. 붙어 있으면 "실고객 노출 0" 은 틀린다.
  `SELECT ... FROM users u JOIN farm_members ... WHERE farm.data_origin='pigplan_migration'`
  최근 로그인 이력이 있는가?
- 정정 전 커밋(`3101e56`)이 "인시던트"라고 단언했다. 정정(`da7f1a5`)이 충분한가,
  아니면 여전히 과장/축소가 남았는가?

### C-9. 역방향 flip 0건

문서는 이것을 "발견"이 아니라 **산술적 필연**으로 정정했다
(`stillborn ⊆ stillborn+mummified`, 분모 동일 → ① ≤ ② 항상).

**검증할 것**: 이 정정이 맞는가. 그리고 **PWM 에도 같은 종류의 산술 필연이 숨어 있지
않은가?** `deaths/(weaned+deaths)` 와 `(born_alive−weaned)/born_alive` 사이에
대소 관계가 구조적으로 정해지는가? 문서는 PWM 에 대해 이 검토를 하지 않았다.

---

## 4. 문서 정정의 적정성

### C-10. §3-4 정정

아키텍처가 "PigOS 사산공식 = `(stillborn+mummified) ÷ total born`" 이라고 단정했던 것을
정정했다. **단, 경로 ①로 뒤집어 쓰지 않고 `AMBIGUOUS` 로 남겼다.**

**검증할 것**: 정정문이 새로운 단정을 만들지 않았는가? DISPUTED 로 표시한 7개 문서
목록이 **누락 없이 전수인가** (전 저장소 grep).

### C-11. G3 ③ 재작성안

**검증할 것**: `benchmark_derived → DENY` 를 지금 적용하면 무엇이 죽는가?
문서는 "BR 전면 무채색"이라고 했다. **BR 파일럿 3개 KPI(PSY·FARROWING_RATE·NPD)가
A-bench 경로라는 것과, 그것이 곧 전면이라는 것**이 맞는지 확인하라.

### C-12. P1 Template LOCK 게이트

`api/tests/integration/test_us_template_lock.py` L1~L6.

**검증할 것**: 테스트가 **자기 자신을 통과시키도록 쓰이지 않았는가.**
특히 L4(폴백 금지)가 실제로 폴백을 잡는가 — 리졸버에 일부러 폴백을 넣으면 red 가 되는가?
(코드 수정 금지이므로 **논증으로** 판단하라.)

---

## 5. 산출 형식

`handoff/CODEX_RESULT_2026-08-27.md`

```markdown
# CODEX 검증 결과 2026-08-27 (대상 a2e813c)

## 판정 요약
| 항목 | 주장 | 판정 | 근거 |
|---|---|---|---|
| C-1 | ... | CONFIRMED / REFUTED / UNVERIFIED / OVERSTATED | file:line 또는 쿼리+결과 |

## 반증된 것        ← 있으면 최상단. 없으면 "없음" 명시
## 과장·축소된 것    ← REFUTED 는 아니나 문서 표현이 근거보다 센 것
## 미검증으로 남긴 것 ← 왜 확인 못 했는지
## 문서에 없던 신규 발견
## 이 검증에서 내가 확인하지 못한 사각지대   ← 반드시 채울 것
```

**판정 기준**
- `CONFIRMED` = 당신이 직접 재도출했다. "문서와 일치" 는 근거가 아니다.
- `OVERSTATED` 를 적극적으로 쓰라. 오늘 오류 3건 중 2건이 "틀림"이 아니라
  **"근거보다 센 주장"** 이었다.
- 확신이 안 서면 `UNVERIFIED`. **빈칸이 틀린 값보다 낫다.**

## 6. 금지

코드·테스트·마이그레이션·seed 수정, `git add/commit/push`, 프로덕션 쓰기(INSERT/UPDATE/
DELETE/DDL), 설정 변경(특히 `USE_GOVERNANCE_BENCHMARKS` 토글 — 켜면 32룰의 임계 소스가
통째로 바뀐다), 모바일 저장소 수정.
