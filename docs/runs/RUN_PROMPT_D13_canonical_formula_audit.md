# [D-13 P0] PigOS Canonical KPI Formula Audit — Gate Run Spec v1.4

```
Mode      : SOURCE READ-ONLY / SPEC OUTPUT ONLY
Machine   : bjh only
Shell     : PowerShell 7 (bash 구문 사용 금지)
Output    : docs/kpi/CANONICAL_FORMULA_SPEC.md (1개 파일) + stdout run log
Git       : add / commit / push 전면 금지 (PigOS·android·ios 3개 repo 모두)
```

**v1.4 변경 (2026-08-27):** STEP 1 우선범주에 **사산 계열** 추가 (8 → 9, 상한 12 이내).

> 근거는 하나가 아니라 둘이다.
>
> ① 아키텍처 §3-4 `APPROVED_TRANSFORM` 후보 3건 중 **2건이 사산 KPI 에 걸려 있다.**
>    빼면 3건 중 2건이 판정 불가로 남는다.
>
> | 후보 | 필요 KPI | 사산 제외 시 |
> |---|---|---|
> | `survival = 1 − mortality` | preweaning_survival | ✅ 가능 |
> | PigOS 사산공식 ↔ PigCHAMP 구성요소 | 사산 계열 | ❌ 불가 |
> | MetaFarms Piglet Survival `NOT_EQUIVALENT` 판정 | preweaning_survival + 사산 | ❌ 부분 |
>
> ② **비표준 정의가 이미 확인된 유일한 KPI 다** — 미라(mummified)를 분자에 포함해
>    관행 대비 ~3%p 높게 나온다. `sow_turnover` 보다 우선순위가 높다.
>
> ★ **식별자를 고정하지 않는다.** `STILLBORN_RATE` 는 GLOBAL 레지스트리의 이름이지
>   실물 계산 코드명이 아니다. 실물이 `stillborn_rate` / `stillborn_per_litter` /
>   `stillbirth_rate` 중 무엇인지는 **STEP 1 이 정한다.** 미리 박으면 없는 코드를
>   찾다가 AMBIGUOUS 가 뜬다 — §2 의 "목록을 미리 canonical 로 확정하지 않는다"를
>   이 패치가 스스로 위반하게 된다.

**v1.3 변경:** `measure_kind` / `output_unit` UNKNOWN 허용 · `LIVE_DIVERGENCE` reachability 근거 필수.

**v1.2 변경:** pytest/alembic no-write 환경 고정 · `Decision APPROVED ≠ CONFIRMED` 명문화 · D-8 mapping 자격에 valid NOT_APPLICABLE 포함.

**v1.1 변경:** PowerShell 명령 정정 · `api/tests` 범위 추가 · status enum 통일 · `formula_id`에서 version 분리 · `UNRESOLVED_OUTSIDE_SCOPE`를 결정이 아닌 기술추적으로 분리 · 모바일 repo baseline 추가 · 외부 evidence note 제거 · `performance_direction` UNKNOWN 허용.

---

## 목적

PigOS가 **현재 실행 코드에서 실제로 무엇을 계산하는가**를 재도출하여 `CANONICAL_FORMULA_SPEC`을 신규 SSOT로 만든다.

이 작업은 다음이 **아니다.**
- 외부 benchmark 조사 (→ D-15, 별도 병렬 실행)
- 외부 정의와의 대조 (→ D-8)
- 국가별 KPI 정책 수정
- Rule Engine 리팩터링
- threshold / verdict 로직 감사 (→ **D-19**, D-13 직후 별도 run)

핵심 질문은 하나다.

> **PigOS 현재 실행 코드가 각 KPI를 정확히 어떻게 계산하는가?**

문서·필드명·설계 의도·도메인 상식을 믿지 않는다. **계산 코드 본문으로만 판정한다.**

> **D-13 RUN PASS ≠ 모든 KPI formula CONFIRMED.**
>
> D-8 mapping 대상은 canonical `implementation_status = CONFIRMED` **또는 valid `NOT_APPLICABLE`** 인 항목으로 제한한다.
> `AMBIGUOUS` / `UNRESOLVED_OUTSIDE_SCOPE` 는 mapping 금지.
>
> (valid `NOT_APPLICABLE`은 구조적으로 산식이 존재하지 않는 지표이며, mapping은 `EXACT`가 아니라 `STRUCTURAL_EQUIVALENCE` 경로로 간다. §6 참조.)

---

## 0. 절대 규칙

### 0-1. 머신 게이트 (최우선)

다른 어떤 작업보다 먼저 실행한다.

```powershell
hostname
```

- 결과가 정확히 `bjh` 가 아니면 **즉시 STOP.**
- 특히 `brian` 이면 무조건 중단. `brian`은 pull-only 미러이며 이 작업 대상이 아니다.
- STOP 시 `STOP_REASON: MACHINE_GATE_FAIL / hostname=<값>` 만 출력하고 **어떤 후속 명령도 실행하지 않는다.** 부분 수행 금지.

### 0-2. 작업 범위

| 구분 | 경로 | 접근 |
|---|---|---|
| **Primary calculation scan** | `C:\dev\PigOS\api\app` | read-only |
| **Existing test evidence scan** | `C:\dev\PigOS\api\tests` | read-only, 수정 절대 금지 |
| 모바일 확인 (별도 저장소) | `C:\dev\pigos-android`, `C:\dev\pigos-ios` | read-only |
| 유일한 write | `C:\dev\PigOS\docs\kpi\CANONICAL_FORMULA_SPEC.md` | 신규 생성 1건 |

**제외:** `.venv`, `node_modules`, build/dist/cache/generated 산출물, git history 전수 검색, 외부 서비스, production server.

> 모바일은 PigOS 저장소 하위 디렉터리가 **아니다.** 독립 저장소 2개이며 read-only 스캔만 한다.

**테스트의 지위:** 테스트는 formula의 **근거(authority)가 아니라 구현 방증(corroboration)** 이다. 테스트가 코드보다 우선하지 않는다. 테스트가 코드와 다른 산식을 단언하고 있으면 그것은 모순이 아니라 **기록 대상 findings**다 → `test_code_mismatch` 필드에 양쪽 위치를 기록하고, **판정은 코드를 따른다.**

### 0-3. Source read-only

**금지:** `.py` 수정, 테스트 코드 수정, migration 생성, Alembic 수정, DB 변경, seed 변경, `git add/commit/push`(3개 repo 전부), formatter 실행, 자동 fix, refactor, 모바일 코드 수정.

**허용되는 write는 SPEC 파일 1개뿐이다.** 이 파일도 git에 add 하지 않는다.

파일 쓰기는 UTF-8 (BOM 없음) 고정:
```powershell
[System.IO.File]::WriteAllText($path, $content, [System.Text.UTF8Encoding]::new($false))
```

**선행 확인:** `docs/kpi/CANONICAL_FORMULA_SPEC.md` 가 이미 존재하면 덮어쓰지 말고 STOP (`STOP_REASON: SPEC_ALREADY_EXISTS`). 기존 파일 존재는 이전 run이 있었다는 뜻이므로 사람이 판단한다.

### 0-4. 이번 run에서 절대 건드리지 않을 것

발견되더라도 **NOTE만 남기고 수정하지 않는다.**

- Track 4 / D-7 KRW leak gate
- `operational_default` 추출 / Rule Engine inline default 40개 → **D-19 소관**
- 국가별 threshold 정비
- WiseLake Console `product_context` governance
- PigSignal 노출 경로
- 외부 evidence 수집·대조 (D-15 / D-8 소관)
- benchmark 값 승인
- presentation 정책 수정
- entitlement / FCR 변경
- ADR-KPI-00 DB constraint 변경

### 0-5. 값 계산 vs 판정 로직 경계 (중요)

D-13이 감사하는 것은 **KPI 값 계산**이다. **verdict/색상 판정은 감사 대상이 아니다.**

```
[감사 대상]  raw data → KPI 값 (numerator/denominator/period/as_of)
[감사 제외]  KPI 값 → Threshold Resolver → Severity → 색상   ← D-19
[감사 제외]  Benchmark Context Resolver
```

계산 경로 추적 중 Threshold Resolver 영역에 진입하면 **거기서 추적을 멈추고 경계 지점만 기록**한다. 두 계층을 한 KPI 항목에 섞어 적으면 후속 mapping 판정이 오염된다.

---

## 1. Baseline Gate

코드 분석 전에 반드시 기록한다. **3개 저장소 전부.**

```
BASELINE
- machine                     : (hostname)
- pigos_commit                : (git rev-parse HEAD)
- pigos_working_tree_before   : (git status --short 전체 출력)
- android_commit              : (또는 REPO_NOT_FOUND)
- android_working_tree_before :
- ios_commit                  : (또는 REPO_NOT_FOUND)
- ios_working_tree_before     :
- alembic_heads               : (아래 참조)
- test_collection_cmd         : (사용한 명령)
- collected_tests             : (숫자)
```

모바일 저장소 commit hash를 남기지 않으면 3개월 뒤 "그때 iOS가 하드코딩이었나"를 재현할 수 없다.

**Alembic head 확인.** 과거 revision parent 중복 클레임으로 `KeyError`가 발생한 이력이 있다. migration을 만들지 않더라도 현재 head 단일성 여부를 기록한다.
- 우선 `alembic heads` 시도. 환경 문제로 실패하면 `versions/` 디렉터리의 `revision` / `down_revision` 관계를 read-only로 파싱해 head 개수만 기록한다.
- head가 2개 이상이면 STOP 하지 않고 **`ALEMBIC_MULTIPLE_HEADS` 경고로 기록**한다 (D-13은 migration을 만들지 않으므로 blocker가 아니다).

**테스트 수.** 프로젝트에 표준 collection 명령이 있으면 그것을 우선 사용한다. 없으면 pytest 설정을 확인한 뒤 read-only collection(`--collect-only`)을 사용한다. **임의로 테스트 체계를 새로 만들지 않는다.**

**⚠ collection도 파일을 쓴다.** pytest는 import 과정에서 `__pycache__`, `.pytest_cache`를 생성한다. §0-3의 "write는 SPEC 1개뿐" 규칙과 실행을 일치시키려면 환경을 먼저 고정한다.

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'

python -m pytest <기존옵션> --collect-only -p no:cacheprovider
```

**Alembic 실행 시에도 동일한 환경변수 상태를 유지한다.** 이 세션 동안 해제하지 않는다.

> 이 패치가 없으면 위험이 두 겹이다. `__pycache__` / `.pytest_cache`는 대개 gitignore 대상이라 §11의 `git status --short` 대조를 **그대로 통과한다.** 즉 규칙은 위반됐는데 검증은 PASS로 나온다. 환경변수로 애초에 막는 것이 유일한 확실한 방법이다.

> 테스트 수를 확보하지 못하면 본 분석에 들어가지 말고 `STOP_REASON` 기록 후 중단.

---

## 2. STEP 1 — KPI 실재 코드명 Discovery

**KPI 목록을 미리 canonical로 확정하지 않는다.** 아래는 탐색 seed일 뿐이다.

```
seed (현재 코드 추정)  : psy  msy  farrowing_rate  preweaning_survival
                        postweaning_survival  weaned_per_litter  sow_turnover
alias 후보 (과거/외부) : npd  wei  pwm  preweaning_mortality  stillborn
                        stillborn_rate  born_alive  total_born  mummified
                        litters_per_sow  fcr  adg
```

### 검색 명령 (PowerShell 7)

`Select-String`에는 `-Recurse` / `-File` 파라미터가 **없다.** 파일 열거는 `Get-ChildItem`이 한다.

```powershell
# Primary calculation scan
Get-ChildItem -LiteralPath 'C:\dev\PigOS\api\app' -Recurse -File -Filter '*.py' |
  Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
  Select-String -Pattern '<term>'

# Existing test evidence scan
Get-ChildItem -LiteralPath 'C:\dev\PigOS\api\tests' -Recurse -File -Filter '*.py' |
  Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
  Select-String -Pattern '<term>'
```

### 결과 분류

| 코드 | 분류 |
|---|---|
| A | 실제 canonical 계산 코드 |
| B | API response / output alias |
| C | DB model field |
| D | registry / presentation identifier |
| E | legacy / dead code |
| F | test fixture / assertion |
| G | comment / docstring only |

> **"문자열이 존재한다" ≠ "canonical KPI code다."**

### STEP 1 산출표

| discovered_name | location | role(A~G) | canonical_candidate | audit_scope_status | notes |
|---|---|---|---|---|---|

이 표가 나온 뒤에야 audit 대상 KPI를 확정한다.

**스코프 폭주 방지.** canonical_candidate가 12개를 넘으면 아래 우선 범주만 `audit_scope_status = IN_SCOPE`로 두고, 나머지는 `DEFERRED`로 목록만 남긴다.

우선 범주 (9):
```
PSY 계열 · MSY 계열 · FARROWING RATE
PRE-WEANING SURVIVAL 계열 · POST-WEANING SURVIVAL 계열
WEANED PER LITTER · SOW TURNOVER · NPD/WEI 계열
사산 계열 (stillborn / mummified 포함)          ← v1.4 추가
```

> `DEFERRED`는 **audit 범위 상태**이지 implementation status가 아니다. 두 축을 섞지 않는다.

**없는 identifier를 억지로 만들지 않는다.** 외부 문헌 용어(`PWM` 등)가 PigOS 실물에 없다면 그것 자체가 유효한 발견이다.

### 사산 계열 주의 (v1.4)

우선범주에 들어갔지만 **코드명을 모른다.** GLOBAL 레지스트리에는 `STILLBORN_RATE` 로 있으나 그것은 presentation identifier(role D)일 수 있고 실제 계산 코드명과 다를 수 있다.

- STEP 1 이 실물 identifier 를 정한다. seed 는 `stillborn` / `stillborn_rate` / `mummified` / `total_born` 이다.
- 분자에 **미라(mummified)가 포함되는지**를 반드시 본문에서 확인한다. 포함이 확인되면 그 자체가 §5 의 `doc_code_mismatch` 가 아니라 **canonical 사실**이며, 외부 관행과의 차이 판정은 D-8 소관이다.
- 계산 코드가 없고 presentation identifier 만 있으면 `implementation_status` 는
  `NOT_APPLICABLE` 이 아니라 **`UNRESOLVED_OUTSIDE_SCOPE` 또는 `AMBIGUOUS`** 다 (§6 참조).

### Survival vs Mortality 명칭 주의

PigOS 코드에 `preweaning_survival`처럼 survival 계열 identifier가 있고, 외부 문헌에는 mortality 계열 지표가 존재한다. 이 둘은 이름만 다른 동일 KPI가 **아닐 수 있다.**

**D-13에서는 외부 mapping을 판정하지 않는다.** 내부 canonical 정의(분자·분모·단위)만 정확히 고정하고, 방향(`performance_direction`)은 **§3의 규칙대로 코드 근거가 있을 때만** 기록한다. 도메인 상식으로 채우지 않는다.

---

## 3. STEP 2 — 계산 본문 추출

각 canonical KPI마다 실제 calculation path를 **끝까지** 따라간다. 함수명·필드명만 보고 의미를 결정하지 않는다.

### KPI별 필수 추출 항목

```yaml
canonical_kpi_code:
formula_id:                 # version 을 포함하지 않는다. 예: PSY_ROLLING12M
formula_version:            # 정수. 예: 1

audit_scope_status:         # IN_SCOPE | DEFERRED
implementation_status:      # CONFIRMED | AMBIGUOUS | NOT_APPLICABLE | UNRESOLVED_OUTSIDE_SCOPE

measure_kind:               # COUNT | RATE | RATIO | DURATION | INDEX | COST
                            # | OBSERVED_COUNT | OTHER | UNKNOWN
output_unit:                # 또는 UNKNOWN
performance_direction:      # HIGHER_IS_BETTER | LOWER_IS_BETTER | NEUTRAL | UNKNOWN
performance_direction_evidence:   # file/function/field  또는  NONE_IN_FORMULA_LAYER

path_reachability:          # LIVE | DEAD | TEST_ONLY | UNKNOWN
reachability_evidence:      # route → service → function 호출경로
divergence_severity:        # AUDIT_ONLY | LIVE_DIVERGENCE  (AMBIGUOUS 일 때만)

numerator:
denominator:
included_components:
excluded_components:

population_basis:           # 상시모돈 / 교배모돈 / 기말재고 등 — 코드에서 재도출
aggregation_scope:          # FARM | SITE | MULTI_FARM | TENANT | UNKNOWN
time_window:
as_of_semantics:            # PARAMETERIZED | WALL_CLOCK_DEPENDENT | UNKNOWN + 근거

null_handling:
zero_denominator_handling:
rounding:
unit_conversion:            # kg↔lb 변환이 계산단계인지 표시단계인지

source_data_fields:
implementation_path:
implementation_function:
calculation_dependencies:   # 번식 사이클 상태 등 선행 조건
country_override_path:      # 국가별 분기 존재 여부 (원칙상 0이어야 함)
threshold_boundary:         # 값 계산이 끝나고 판정 로직으로 넘어가는 지점
known_tests:                # api/tests 근거 (corroboration)
test_code_mismatch:         # 테스트가 코드와 다른 산식을 단언하면 양쪽 위치 기록
doc_code_mismatch:
```

### formula_id / formula_version 원칙

- `formula_id`는 **계산 의미를 표현하는 안정 ID**. **version 문자열을 ID에 넣지 않는다.**

```
✅  formula_id: PSY_ROLLING12M   formula_version: 1
❌  formula_id: PSY-ROLLING12M-v1  formula_version: 1     ← 이중 관리
```

- **version 증가 대상:** numerator / denominator / inclusion·exclusion / population basis / period semantics / as_of 의미 변경
- **version 유지:** 함수 이동, rename, refactor, 동일 의미 재작성
- denominator가 바뀌어 사실상 완전히 다른 공식이 된 경우, `formula_id` 자체를 새로 만들지 여부는 **Decision 안건**이지 auditor 판단이 아니다.
- 이번 최초 audit에서는 **historical version을 상상해서 만들지 않는다.** 현재 실물 정의를 baseline `1`로 선언한다.
- **`AMBIGUOUS` / `UNRESOLVED_OUTSIDE_SCOPE` KPI에는 확정 `formula_id`를 부여하지 않는다.**

### performance_direction 은 코드 근거가 있을 때만

방향 정보는 raw 계산 함수에 **없을 수 있다.** Threshold / Rule 계층에만 존재한다면, D-13은 그 계층에 들어가지 않기로 스스로 막아놨다(§0-5).

```
코드 근거 있음   → HIGHER_IS_BETTER / LOWER_IS_BETTER / NEUTRAL + evidence 기록
코드 근거 없음   → UNKNOWN + performance_direction_evidence: NONE_IN_FORMULA_LAYER
```

> "생존율이니까 당연히 HIGHER_IS_BETTER" 는 **코드-only 원칙 위반이다.**
> `UNKNOWN`은 실패가 아니다. 근거 없이 방향을 만드는 것이 실패다.

### 추적이 범위 밖으로 나갈 때

계산이 raw SQL / DB view / stored procedure / 외부 서비스로 이어지면 **DB로 쫓아가지 않는다.**
- 경계 지점(파일·함수·쿼리 위치)만 기록
- `implementation_status = UNRESOLVED_OUTSIDE_SCOPE`
- **§5-2의 P0-1B(기술 추적)로 넘긴다. P0-2(사람 결정)로 보내지 않는다.**

### as_of는 전 KPI 공통 감사 항목

NPD만이 아니라 **모든 KPI**에 대해 확인한다.
- `as_of`가 명시적으로 전달되는가
- `now()` / `today()` / `datetime.now` 등 wall-clock에 의존하는가
- closed/open record 처리, future date 처리, 기간 clipping

wall-clock 의존이 남아 있는 KPI가 발견되면 **발견 사항으로 기록**한다. **이번 run에서 고치지 않는다.**

### 번식 사이클 의존성

PSY / farrowing_rate 계열은 번식 사이클 상태에 의존한다. 계산이 사이클 close 상태를 전제하는지, 미종료 사이클을 어떻게 처리하는지를 `calculation_dependencies`에 기록한다. (사이클 idempotency 결함 수정 이력이 있으므로 현재 처리 방식을 명시적으로 남긴다.)

### 다국가 / 멀티테넌트

`aggregation_scope`를 반드시 채운다. 단일 농장 기준 계산인지, 다농장 합산인지에 따라 후속 mapping 판정이 달라진다. 확인 불가면 `UNKNOWN`.

### measure_kind 정확성

**COUNT와 RATE를 절대 섞지 않는다.** 이름이 `stillborn`이라는 이유로 rate로 추정하지 않는다. `measure_kind`는 **실제 계산식과 unit으로만** 판정한다. 통화 단위가 개입하면 `COST`를 쓰고 currency를 `output_unit`에 명시한다.

---

## 4. NPD / WEI 특별 규칙 (오염 이력)

과거 대시보드의 `NPD` 필드가 실제로는 **WEI(이유–교배 간격)** 를 계산하던 결함이 있었고 M1 STEP 1에서 수정됐다.

따라서 **변수명·필드명·response key·함수명만으로 NPD/WEI를 판정하면 안 된다.**

**교차확인 절차:**
1. `npd` 로 식별된 코드의 계산 본문을 읽는다.
2. 입력이 `weaning_date → next_service_date` 간격이면 → **의미상 WEI**. 이름이 npd여도 CONFIRMED(NPD) 금지.
3. `wei` 로 식별된 코드도 동일하게 역방향 확인한다.
4. 두 지표가 코드 / API response / android / ios 각 계층에서 동일한 의미로 일관되는지 확인하고, 불일치 계층이 있으면 그 계층을 명시한다.
5. `api/tests`에 두 지표를 구분하는 assertion이 있으면 `known_tests`에 기록한다 (corroboration).

산출:

```
NPD_WEI_CONTAMINATION_AUDIT
- npd identifier    : (위치)
- npd 실제 계산 의미  : (본문 근거)
- wei identifier    : (위치)
- wei 실제 계산 의미  : (본문 근거)
- 계층별 일관성      : backend / API response / android / ios
- test evidence     :
- verdict           : CLEAN | RESIDUAL_RISK | CONTAMINATED
```

---

## 5. 미확정 항목의 두 갈래 — 절대 혼동 금지

### 5-1. AMBIGUOUS — 코드를 다 봤는데 후보가 둘

```
candidate A : <file>:<function>  평균 상시모돈 사용
candidate B : <file>:<function>  기말 모돈두수 사용
→ implementation_status = AMBIGUOUS, 두 위치 모두 기록
```

**금지 표현:** "아마 A일 것이다" / "문서상 A니까 A" / "일반적으로 A를 쓴다".

기존 문서에 PSY 분모가 상시모돈이라고 적혀 있더라도, **코드에서 재도출되지 않으면 AMBIGUOUS다.**

**후속: P0-2 (사람 결정)** — `PROPOSED → REVIEW → APPROVED`. 코드에 근거가 다 나와 있고 어느 쪽을 canonical로 삼을지가 정책 판단이므로 사람이 결정할 수 있다.

**단, `Decision APPROVED ≠ formula CONFIRMED`.**

사람이 정의를 골랐다고 실행 코드가 자동으로 하나가 되지 않는다. 두 후보가 모두 live path라면 이는 정의 선택 문제가 아니라 **implementation divergence**다.

```
AMBIGUOUS
   ↓  P0-2 canonical definition 결정 (APPROVED)
   ↓  필요 시 code alignment + regression test
   ↓  D-13 재실사
CONFIRMED
```

`AMBIGUOUS → APPROVED → 곧바로 CONFIRMED` 로 승격시키면, 실행 코드는 여전히 둘인 채 문서만 하나가 된다. **또 하나의 위조 우회로다.**

**추가 판정 — reachability 근거 필수.** 함수가 둘이라는 사실만으로 `LIVE_DIVERGENCE`를 찍지 않는다. 한쪽이 legacy / dead helper / 테스트 전용일 수 있다.

```
divergence_severity = LIVE_DIVERGENCE
  ONLY IF  같은 canonical KPI 에 대해 서로 다른 의미의 계산 경로가 2개 이상
      AND  두 경로 모두 path_reachability = LIVE
      AND  각 경로에 reachability_evidence (route → service → function) 기록됨

그 외 → AUDIT_ONLY
```

`LIVE_DIVERGENCE`이면 단순 audit finding이 아니라 **데이터 정합성 findings**다 — 현재 사용자별로 다른 값을 받고 있을 수 있다는 뜻이며, D-8 이전에 별도 대응이 필요하다.

**reachability 추적 범위 제한:** 호출경로 추적은 `api/app` 안에서만 한다. 경로가 밖으로 나가거나 동적 디스패치로 특정 불가하면 `path_reachability = UNKNOWN`이고, 이 경우 `LIVE_DIVERGENCE`로 승격하지 않는다. 추적 자체가 §0-5의 threshold 계층으로 들어가면 거기서 멈춘다.

### 5-2. UNRESOLVED_OUTSIDE_SCOPE — 아직 실제 계산 코드를 못 봄

SQL / view / stored procedure / 외부 서비스로 넘어가 이번 범위에서 본문을 읽지 못한 경우.

**후속: P0-1B (기술 추적)** — scope extension으로 실제 구현을 추가 판독한 뒤 `CONFIRMED` 또는 `AMBIGUOUS`로 재판정한다.

> **이것을 P0-2 사람 결정으로 보내면 안 된다.**
> 아직 코드를 안 본 상태에서 사람이 "A로 승인"하면, 우리가 막으려던 **위조가 그대로 재진입한다.**

```
AMBIGUOUS                 → 근거 있음, 선택의 문제      → P0-2 DECISION
UNRESOLVED_OUTSIDE_SCOPE  → 근거 없음, 판독의 문제      → P0-1B TECHNICAL TRACE
```

---

## 6. NOT_APPLICABLE 규율

`NOT_APPLICABLE`은 escape hatch가 아니다.

- **허용:** numerator/denominator 형태의 산식이 구조적으로 존재하지 않는 metric (단순 observed count, 복합 index 등)
- **금지:** "산식을 못 찾음" → 이것은 `AMBIGUOUS` 또는 `UNRESOLVED_OUTSIDE_SCOPE`다

후속 evidence mapping gate에서 `formula_status = NOT_APPLICABLE`은 양쪽 `measure_kind`와 구조가 실제로 N/A일 때만 허용되며, 이때 mapping은 `EXACT`가 아니라 `STRUCTURAL_EQUIVALENCE` 대상이다.

---

## 7. STEP 3 — Mobile KPI Presentation Path 확인

read-only. 질문은 2개뿐이다.

1. Android / iOS 클라이언트가 `/kpi/presentation` 응답을 소비하는가?
2. 아니면 KPI 카드 목록·순서·표시 여부를 모바일 코드에 hard-code 했는가?

```
MOBILE_PRESENTATION_AUDIT

Android (C:\dev\pigos-android)
- repo_status           : FOUND | REPO_NOT_FOUND
- commit                :
- endpoint consumer     :
- hardcoded KPI list    :
- hardcoded visibility  :
- null benchmark 처리    : (benchmark_value=null 수신 시 동작)
- file/function evidence:
- verdict               : CONSUMES_API | HARDCODED | MIXED | UNKNOWN

iOS (C:\dev\pigos-ios)
- (동일 항목)
```

**판정 규칙**
- repo는 있으나 판독 불가 → `UNKNOWN` 허용
- 경로 자체가 없음 → `REPO_NOT_FOUND` 명시
- **모바일 감사 실패는 D-13 전체 STOP 사유가 아니다.** `MOBILE_AUDIT: INCOMPLETE`로 분리 기록하고 canonical formula audit은 계속한다. 목적이 다르기 때문이다.

**모바일 코드는 수정하지 않는다.**

> 이 확인이 필요한 이유: 모바일이 KPI 목록을 하드코딩하고 있거나 null benchmark를 처리하지 못하면, 백엔드 `/kpi/presentation` 기반 표시 통제가 모바일에서 뚫린다.

---

## 8. 기존 3축 Gate와의 관계 (문구 고정)

D-13은 **새로운 governance axis를 만들지 않는다.** ADR-KPI-00의 기존 activation gate는 그대로 유지한다.

```
definition_compatible   ← formula_status + mapping_status   (내부 분해)
rights_cleared          ← 내부 분해 (아래 §10 FOLLOW-UP)
evidence_verified       ← benchmark_status + terminology_status (내부 분해)
```

향후 세부 상태는 **기존 3축 바깥의 병렬 신규 gate가 아니라, 각 축의 내부 판정 근거 분해**다. ADR amendment 문안에 "3축 → N축 확장" 같은 표현을 쓰지 않는다.

**D-13에서는 ADR constraint / DB schema / `benchmark_enabled` 를 수정하지 않는다.** `CANONICAL_FORMULA_SPEC`이 후속 definition compatibility 판정의 **입력**이 되도록 만드는 것까지만 한다.

---

## 9. 산출물 — CANONICAL_FORMULA_SPEC.md

경로: `C:\dev\PigOS\docs\kpi\CANONICAL_FORMULA_SPEC.md`

### 문서 관할 (엄수)

```
CANONICAL_FORMULA_SPEC : PigOS 내부 사실만
                         (분자/분모/포함·제외/기간/as_of/unit/scope)
US_KPI_RESEARCH 등      : 외부 source facts (PigCHAMP / MetaFarms / 각국 출처)
D-8 mapping artifact    : 위 둘의 관계
```

> **이 문서에 외부 benchmark 수치·출처·항등식을 넣지 않는다.**
> D-13은 external evidence audit이 아니라고 스스로 선언했으므로, 내부 산식 SSOT에 외부 evidence를 섞으면 자기모순이다. 관련 관찰은 전부 D-8 입력자료로 보낸다.

### 문서 상단 필수 선언

```
CANONICAL_FORMULA_SPEC : PigOS 내부 계산 의미
COUNTRY_KPI_RULE_SPEC  : 국가 정책·표시·룰 적용

관계: CANONICAL_FORMULA_SPEC 이 COUNTRY_KPI_RULE_SPEC 의 입력이다.
      산식 변경은 CANONICAL_FORMULA_SPEC 에서만 정의한다.
      국가 표시 정책이 canonical formula 를 재정의해서는 안 된다.
```

`PIGOS_SPEC_INDEX` 등록 필요성은 FOLLOW-UP으로만 명시한다. **이번 run에서 인덱스 파일 자체는 수정하지 않는다.**

### 문서 구조

```
0.  Status (audit_date / machine / pigos·android·ios commit /
    test_count / alembic_heads / audit_scope / source_of_truth_statement)
1.  Scope / Non-Scope
2.  KPI Identifier Discovery      (STEP 1 표)
3.  Canonical KPI Summary         (code / formula_id / version / measure_kind / status)
4.  KPI Detail                    (KPI별 §3 필수 항목 전체)
5.  Alias / Legacy / Field-name Risks
6.  NPD / WEI Contamination Audit
7.  as_of / Wall-clock Dependency Findings
8.  Test / Code Mismatch Findings
9.  Mobile Presentation Audit
10. AMBIGUOUS Items → P0-2 Decision
11. UNRESOLVED_OUTSIDE_SCOPE Items → P0-1B Technical Trace
12. Follow-up Governance Requirements
13. Explicit Non-Changes
```

---

## 10. Follow-up Governance Requirements (기록만, 구현 금지)

- **D-9 세부 분해** — `terminology / formula / benchmark / mapping` 4개 상태를 기존 3축의 **내부 판정 근거**로 사용. 신규 병렬 gate 아님.
- **evidence 식별키** — `(country, kpi, source, source_edition, period)`. `source_edition` 필수.
- **serving 계층 provenance** — evidence에서만 versioning하면 `default_metric_values` INSERT 시 provenance가 다시 소실된다. serving row에 **`selected_evidence_id`** 를 연결할 것.
- **`source_statistic_label` 원문 보존** + `statistic_position` + `performance_direction` 3층 분리.
- **`source_linkage`** — 타 문헌 산식을 현재 benchmark source의 산식으로 덮어쓰기 방지.
- **`cohort_or_population_basis`** — census / 행정 전수자료에 억지 cohort 요구하지 않기 위함.
- **`population_scope`** enum 후보: `NATIONAL / ADMIN_UNIVERSE / ENTERPRISE / RESEARCH_CENTER / GENETIC_LINE / FARM_COHORT / REGIONAL / MARKETING_TARGET`. **`MARKETING_TARGET`은 실측 national benchmark로 승격 금지.**
- **`formula NOT_APPLICABLE` 제약** 및 **`APPROVED_TRANSFORM` 필수 동반 필드**.
- **rights 판정 정밀화** — `rights_scope` × `policy_scope` 2축 유지 (D-18).
- **표시 안전 회귀 불변조건 3건** (구현은 후속, D-17):
  > ① visible KPI + benchmark 없음 → HTTP 200 / farm value 유지 / `benchmark_value=null` / silent GLOBAL·KR fallback 없음 / benchmark 기반 severity 없음
  > ② registry에 KPI가 추가되어도 `country_kpi_presentation` 행이 없거나 `priority_class IS NULL` 이면 `/kpi/presentation` 응답 카드 수가 자동 증가하지 않는다
  > ③ `threshold_source = code_default` → severity 없음 (기존 활성 국가는 FLAGGED_FOR_REVIEW, 신규 국가만 차단) — **D-19 입력**

---

## 11. 종료 검증 (write 무결성)

SPEC 작성 후 3개 저장소 전부에서 실행한다.

```powershell
git status --short    # PigOS / pigos-android / pigos-ios
```

각 baseline과 비교하여 **차이가 `docs/kpi/CANONICAL_FORMULA_SPEC.md` untracked 1건뿐**임을 확인한다(모바일 2개는 차이 0).

- 소스 파일에 수정 흔적이 있으면 → `D-13 verdict: STOPPED`, `STOP_REASON: UNEXPECTED_SOURCE_MODIFICATION` 로 보고하고 **직접 되돌리지 않는다** (사람이 판단).
- `git add` / `commit` / `push` 는 어떤 경우에도 실행하지 않는다.

---

## 12. Gate 판정

**PASS 조건 (전항 충족, 부분 PASS 금지):**

1. hostname = `bjh`
2. 3개 repo baseline commit 기록 (없으면 `REPO_NOT_FOUND` 명시)
3. test count 기록
4. Alembic head 상태 기록
5. KPI identifier discovery 완료 (`api/app` + `api/tests`)
6. MSY 포함 여부 실사 완료
7. 각 `IN_SCOPE` KPI가 `CONFIRMED` / `AMBIGUOUS` / `NOT_APPLICABLE` / `UNRESOLVED_OUTSIDE_SCOPE` 중 하나로 판정
8. `AMBIGUOUS`와 `UNRESOLVED_OUTSIDE_SCOPE`가 분리되어 각각 P0-2 / P0-1B로 라우팅됨
9. NPD/WEI 계산 본문 교차확인 완료
10. as_of semantics 코드 근거 확보 (전 IN_SCOPE KPI)
11. `measure_kind` / `output_unit` / `performance_direction` 각각이 **코드 근거로 확정되거나 `UNKNOWN`으로 명시**됨
12. `aggregation_scope` 기록
13. mobile presentation path 확인 (또는 `MOBILE_AUDIT: INCOMPLETE` 명시)
14. 3개 repo `git status` 대조로 소스 변경 0 확인
15. git add/commit/push 0
16. `CANONICAL_FORMULA_SPEC.md` 1개만 산출, 외부 benchmark 수치 미포함

> **특정 KPI가 AMBIGUOUS / UNRESOLVED / performance_direction=UNKNOWN 인 것은 D-13 실패가 아니다.**
> **근거 없이 CONFIRMED·방향을 만들어내는 것이 실패다.**

---

## 13. stdout 최종 출력 형식

```
D-13 RESULT

Machine            :
PigOS commit       :
Android commit     :
iOS commit         :
Test count         :
Alembic heads      :

Discovered canonical KPI codes (IN_SCOPE):
- ...
DEFERRED:
- ...

CONFIRMED:
- <code> / <formula_id> v<n> / <measure_kind> / <direction or UNKNOWN>

AMBIGUOUS  → P0-2 DECISION:
- <code> — candidate A: <loc> [reachability] / candidate B: <loc> [reachability]
  divergence_severity: AUDIT_ONLY | LIVE_DIVERGENCE

LIVE_DIVERGENCE (데이터 정합성 findings):
- ...

UNRESOLVED_OUTSIDE_SCOPE  → P0-1B TECHNICAL TRACE:
- <code> — 경계지점: <loc>

NOT_APPLICABLE:
- ...

performance_direction UNKNOWN (NONE_IN_FORMULA_LAYER):
- ...

as_of wall-clock dependency found:
- ...

Test/Code mismatch:
- ...

NPD/WEI contamination verdict : CLEAN | RESIDUAL_RISK | CONTAMINATED

Mobile presentation:
- Android :
- iOS     :
- MOBILE_AUDIT : COMPLETE | INCOMPLETE

Source modifications : 0   (3개 repo git status 대조 결과 첨부)
Git add/commit/push  : NONE
Spec output          : docs/kpi/CANONICAL_FORMULA_SPEC.md
External benchmark in spec : NONE

D-13 verdict         : PASS | STOPPED
STOP_REASON          : (STOPPED 인 경우)

P0-2 decisions required   : ...
P0-1B traces required     : ...
```

---

## 14. 실행 흐름 요약

```
hostname gate
      ↓
baseline (3 repo commit / tests / alembic / git status)
      ↓
STEP 1  identifier discovery (api/app + api/tests)   ← 목록을 미리 고정하지 않는다
      ↓
audit 대상 확정 (IN_SCOPE ≤12, 우선범주 9, 초과분 DEFERRED)
      ↓
STEP 2  calculation body 추적                        ← 문서·상식 아닌 코드 본문
      ↓
NPD/WEI 교차확인 · as_of 전수 확인 · test 대조
      ↓
STEP 3  mobile presentation path (별도 verdict)
      ↓
CANONICAL_FORMULA_SPEC.md 작성 (외부 evidence 미포함)
      ↓
3 repo git status 대조 → verdict
```

---

## 후속 (이번 run 대상 아님)

```
P0-1B  UNRESOLVED_OUTSIDE_SCOPE 기술 추적 → CONFIRMED 또는 AMBIGUOUS 재판정
P0-2   AMBIGUOUS 항목 → PROPOSED / REVIEW / APPROVED 결정표
D-19   threshold source 감사              ← D-13 직후, 별도 run
D-15   MetaFarms 2021–2025 원문 실사       ← D-13과 독립 병렬. 이 문서에 합치지 않는다
D-8    PigOS canonical ↔ 개별 external source 정의 호환 (항상 1:1)
D-14   source_edition + selected_evidence_id
D-17   G3 표시 안전 계약 (API 응답 + 회귀 3건 + 모바일)
D-18   rights_scope / policy_scope 2축 분리
D-16   VFD conditional rule                 ← 병렬 트랙, critical path 외
```

**불변조건 (전 단계 공통):**
```
VERIFIED = 원문이 그 주장을 실제로 뒷받침한다.
VERIFIED ≠ 그 나라 전체를 대표한다.
VERIFIED ≠ PigOS 정의와 동치다.
VERIFIED ≠ 제품에 표시하도록 승인됐다.
DERIVED value does not inherit benchmark_verified from its inputs.
```
