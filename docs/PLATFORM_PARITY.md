# PLATFORM_PARITY — Web · Android · iOS 구현 상태 SSOT

> **이 문서가 플랫폼 구현 상태의 유일한 SSOT다.**
> `pigos-android/docs/*` · `pigos-ios/docs/*` 에 이 상태값을 복제하지 않는다.
> 모바일 저장소 문서는 build·signing·store release·platform-specific architecture ·
> offline 구현 세부 · native dependency · push 설정 등 **플랫폼 고유사항만** 다룬다.
>
> **Renamed from `docs/MOBILE_PARITY.md` at `4ff8a30`.**
> Pre-rename history: `git log docs/MOBILE_PARITY.md`
>
> `git log --follow docs/PLATFORM_PARITY.md` 는 이 연결을 자동으로 잇지 못한다.
> rename 과 대규모 내용 수정이 **같은 commit** 에 들어가 Git rename heuristic 의
> 유사도 임계 아래로 떨어졌기 때문이다. **pre-rename commit 은 전부 보존돼 있고**
> 위 명령으로 조회된다. history rewrite 는 하지 않는다.

### 규율 — 문서 rename 은 commit 을 분리한다

```
1. rename-only commit      (git mv 만. 내용 변경 0)
2. content-change commit   (내용 수정)
```

한 commit 에 섞으면 `--follow` 가 끊긴다. 이 문서가 그 사례다.

```
STEP 0 완료   2026-08-28
범위          문서 이관 + 기존 evidence 재판정 + Track B 사실 고정 + blocker 확인
미포함        D-19 실행 · Product v1.1 patch · FEATURE_REGISTRY · 코드 수정 ·
              CI/Release Gate 구현 (전부 후속 STEP)
```

---

## 0. 규율

### 0-1. Parity 기준은 화면 동일성이 아니다

```
same farm · same as_of · same country · same permission · same entitlement
   →  same KPI value
   →  same severity
   →  same benchmark availability
   →  same rule meaning
   →  same action semantics
```

Web/Android/iOS 화면은 달라도 된다. **공통 business logic 을 모바일에 다시
하드코딩하지 않는다.**

### 0-2. 상태 필드 이름 — `status` 단독 사용 금지

상태 축마다 의미가 드러나는 이름을 쓴다. 한 저장소에 `status` 가 여럿이면
어느 축의 상태인지 추적이 끊긴다.

```
formula_status · audit_status · migration_status · gate_status ·
platform_implementation_status · parity_result · runtime_verification_status
```

**이 문서의 셀 상태 이름은 `platform_implementation_status` 다.**

### 0-3. 셀 enum

```
PLANNED · IN_PROGRESS · DONE · PENDING_RECHECK · BLOCKED · NOT_APPLICABLE
```

`NOT_APPLICABLE` 은 반드시 `not_applicable_reason` 을 가진다. **사유 없는 N/A 금지.**

### 0-4. `DONE` 은 evidence commit 필수

```
implementation_commit   immutable SHA
evidence_paths          영향 코드 경로
verified_at             확인 일자
```

자기 커밋 안에 자기 SHA 를 못 쓰므로 **2-phase** 다:

```
① implementation commit  (모바일 저장소)
② central parity evidence commit  (이 문서에 그 SHA 등록)
```

**SHA 없으면 `DONE` 금지.** 기존 문서였다는 이유의 grandfathering 도 금지.

### 0-5. `parity_result` 는 사람이 쓰지 않는다

셀에서 계산한다(스크립트는 후속 STEP).

```
required 플랫폼 셀이 전부 DONE | NOT_APPLICABLE  →  PARITY_VERIFIED candidate
그 외                                            →  PARTIAL
```

### 0-6. Evidence staleness

`implementation_commit` 이후 `evidence_paths` 중 하나라도 바뀌면
`DONE → PENDING_RECHECK` 후보다.

```
git diff <implementation_commit>..HEAD -- <evidence_paths>   → non-empty 면 stale
```

`CANONICAL_FORMULA_SPEC` 에서 겪은 *"예전에 CONFIRMED → 코드 변경 → 문서는 계속
CONFIRMED"* 를 여기서 반복하지 않는다. 검출 스크립트는 후속 STEP.

---

## 1. ★ 이번 실사의 핵심 사실 — 위험의 종류를 나눈다

```
VALUE_INTEGRITY_RISK       NO    양 플랫폼에 KPI 산식 하드코딩이 없다
DECISION_INTEGRITY_RISK    YES   판정을 플랫폼이 자체 생성한다
PRESENTATION_PARITY_RISK   YES   같은 응답에 두 플랫폼이 다른 의미를 표시한다
```

**같은 `benchmark = null` 에 대해:**

```
Android  →  TextMuted / 회색   (fail-closed)
iOS      →  success / 초록      (fail-OPEN)
```

같은 farm · 같은 `as_of` · 같은 country · 같은 backend response 인데
**두 앱이 사용자에게 서로 다른 의미를 말한다.** 이것이 현존하는 parity violation 이다.

★ `meetsAvg` 는 **값을 바꾸지 않는다.** 그러나 **사용자 판정을 생성**하므로
위험을 낮게 평가하지 않는다. 계산엔진을 모바일마다 재구축할 필요는 없다 —
고칠 것은 **판정의 출처**다.

---

## 2. 기존 6행 재판정 — grandfathering 없음

`MOBILE_PARITY.md` 시절 `DONE` 이던 2건을 evidence 규칙으로 다시 봤다.

```
모바일 저장소 implementation commit 조회 결과
  pigos-android  최근 = 7545841 (FCM google-services.json)   ← parity 구현 커밋 없음
  pigos-ios      최근 = 6f5dad7 (SUBMISSION 문서 갱신)        ← parity 구현 커밋 없음
```

| 기존 행 | 기존 | 재판정 | 사유 |
|---|---|---|---|
| `/kpi/trend` npd null 화 | DONE | **IN_PROGRESS** | 모바일 implementation SHA **없음**. DTO 가 이미 nullable 이라 크래시는 없으나 그것은 **audit finding** 이지 구현 DONE 이 아니다. trend npd 계열을 그리는 화면이 있는지 **미확인** |
| benchmark null 처리 | DONE | **IN_PROGRESS** | 모바일 implementation SHA **없음**. Android `data.benchmarks?.let{}` 는 기존 코드이지 parity 작업 산출물이 아니다 |
| iOS 계정 삭제 화면 | NEEDED | **BLOCKED** | App Store 5.1.1(v). `AuthService`/`DTO` 는 있으나 View 미발견 |
| 양자(cross-foster) 입력 | NEEDED | **PLANNED** | 웹 `2fedb9c` 로 신규. 모바일 양쪽 없음 |
| `/kpi/presentation` 미소비 | NEEDED | **BLOCKED** | §3 참조 |
| `pigos.io/privacy` 구 방침 링크 | NEEDED (확인) | **PENDING_RECHECK** | 앱이 어느 URL 을 여는지 미확인 |

```
LEGACY_ROWS
  total                        6
  previous_done                2
  done_with_sha                0
  downgraded_due_missing_sha   2
```

★ **`done_with_sha = 0` 이다.** 첫날부터 예외를 두지 않았다.

---

## 3. Track B 실측 — 2026-08-28 (read-only)

> Android: 코드 정적분석. iOS: `STATIC_CONFIRMED` / `NOT_RUNTIME_VERIFIED` (빌드 환경 없음).

### 3-1. `COUNTRY_KPI_PRESENTATION`

| | `platform_implementation_status` | 근거 |
|---|---|---|
| Core/Web | DONE | `/kpi/presentation` 제공 · 웹은 registry-map 렌더 |
| **Android** | **BLOCKED** | `/kpi/presentation` 미소비. `DashboardScreen.kt:100-101` `KpiCard("PSY")`/`("NPD")` · `KpiDto.kt:31-33` `@SerializedName` 고정 |
| **iOS** | **BLOCKED** | 미소비. `DashboardScreen.swift:162-165` 하드코딩. `runtime_verification_status = NOT_RUNTIME_VERIFIED` |

`hardcode_classification = LABEL_ONLY + PRESENTATION_POLICY`

### 3-2. `KPI_STATUS_CONSUMPTION`

| | 상태 | 근거 |
|---|---|---|
| Core/Web | DONE | `(app)/page.tsx:120,158-160` `resolveTier(kpi_status,…)` + `reportStatusMismatches` |
| **Android** | **BLOCKED** | `kpi_status` 소비 **0건** (전 소스 grep) |
| **iOS** | **BLOCKED** | `kpi_status` 소비 **0건** |

### 3-3. `MOBILE_LOCAL_SEVERITY` — DECISION_INTEGRITY_RISK

> ### ★ 정정 (2026-08-28) — Web 행은 틀렸다
>
> 이전 판정 `Core/Web = NOT_APPLICABLE · 자체 판정 경로 없음` 은 **사실이 아니다.**
> D-19 v1.4 감사(N-7)에서 웹 프론트 자체 임계가 발견됐다.
> **"Web 은 판정 reference implementation 이다" 라는 전제를 폐기한다.**

| | 상태 | 근거 |
|---|---|---|
| **Core/Web** | **BLOCKED** — `WEB_LOCAL_STATUS_FALLBACK` | `src/lib/kpi/status.ts` — `psyTier >=28/>=22` · `npdTier <=35/<=50` · `farrowingRateTier >=90/>=80`. `statusObservation.ts:53 resolveTier()` 가 backend `kpi_status` 부재 시 이 값으로 폴백 |
| **Android** | **BLOCKED** | `DashboardScreen.kt:238-243` `meetsAvg = myValue >= b.avg` → Success/Warning. **벤치마크를 판정으로 변환** |
| **iOS** | **BLOCKED** | `DashboardScreen.swift:241-246` alert 없음 → `AppColor.success`. **판정 없음이 초록(FAIL-OPEN)** |

### 3-3-1. ACTIVE vs DORMANT — 같은 BLOCKED 가 아니다

```
Android · iOS   ACTIVE   매 렌더마다 자체 판정이 실행된다
Web             DORMANT  backend kpi_status 가 있는 동안은 발동하지 않는다
```

```
WEB_LOCAL_STATUS_FALLBACK
platform_implementation_status = BLOCKED
risk                = CROSS_COUNTRY_DECISION_RISK
current_user_impact = NOT_OBSERVED
trigger             = backend kpi_status 부재 / 배포 스큐 / contract mismatch
```

★ `CROSS_COUNTRY_DECISION_RISK` 인 이유: 이 임계는 **국가 구분이 없다.**
`psyTier >= 28` 은 KR 기준이고, 서버 DMV 는 US PSY 임계를 26/23 으로 둔다.
폴백이 발동하는 순간 **미국 농장에 한국 기준이 적용된다.**

현재 미발동 근거(도달성 확인함):

```
backend kpi_status 키   PSY · NPD · FARROWING_RATE · SOW_TURNOVER
KPI_CARD_REGISTRY      동일 4종
presentation 미지 코드  unknownCodes 로 분리되어 렌더되지 않음
→ 오늘은 발동하지 않는다. 그러나 응답에서 kpi_status 가 빠지는 순간 발동한다.

### 3-4. `KPI_FORMULA_LOCAL_CALCULATION`

> 사실 확인과 구현 DONE 을 혼동하지 않는다.

```
audit_finding = NO_LOCAL_FORMULA_FOUND     (양 플랫폼)
```

| | 상태 | 근거 |
|---|---|---|
| **Android** | **IN_PROGRESS** | `ui/` 전수에서 KPI 산식 계산 **0건**. DTO 계산 프로퍼티 0건. 그러나 이를 잠그는 회귀 수단이 없어 `DONE` 아님 |
| **iOS** | **IN_PROGRESS** | `Domain/`·`Data/` 계산 프로퍼티 **0건**. `STATIC_CONFIRMED` only |

★ `VALUE_INTEGRITY_RISK = NO`. **모바일 수정 범위가 값이 아니라 판정·표시로 좁혀진다.**

### 3-5. `BENCHMARK_NULL_BEHAVIOR`

| | 상태 | 근거 |
|---|---|---|
| **Android** | IN_PROGRESS | `DashboardScreen.kt:131` `data.benchmarks?.let{}` · `:241` `null → TextMuted`. 로컬 상수 fallback 미발견. implementation SHA 없어 DONE 아님 |

```
Android safety_behavior   = FAIL_CLOSED_BY_COINCIDENCE
Android contract_compliance = NO
```

★ Android 가 무채색을 내는 것은 결과적으로 fail-closed 이지만, 서버 `kpi_status=insufficient` 를
  **소비한 결과가 아니다.** benchmark 가 null 이라서 그런 것이다. benchmark 가 채워지면
  서버가 `insufficient` 를 내더라도 `meetsAvg` 가 다시 판정을 만든다(§3-3). **contract 준수 아니다.**
| **iOS** | **BLOCKED** | `benchmarks` 모델은 존재하나 alert 부재를 초록으로 표현 = **fail-OPEN** |

★ **두 플랫폼이 같은 입력에 다른 의미를 낸다** — §1 의 `PRESENTATION_PARITY_RISK` 실체.

### 3-6. `APP_VERSION_REQUEST_REPORTING`

| | 상태 | 근거 |
|---|---|---|
| **Core/Web** | **BLOCKED** | 요청 헤더에 앱/클라이언트 버전 없음 |
| **Android** | **BLOCKED** | `DeviceRepository.kt:26` **기기등록 시 1회만**. `NetworkModule` 인터셉터는 `auth`·`logging` 둘뿐 → **per-request 헤더 없음** |
| **iOS** | **BLOCKED** | `PushNotificationService.swift:47` **기기등록 시 1회만**. `APIClient`/`Endpoint` 헤더는 `Authorization`·`Content-Type`·`Accept` 뿐 |

### 3-7. `FORCE_UPDATE / LEGACY_CONTROL`

| | 상태 | 근거 |
|---|---|---|
| **Android** | **BLOCKED** | `forceUpdate`/`minVersion`/`426` 등 **0건** (`Color.kt` 매치는 hex `0xFF0E1426` 오탐) |
| **iOS** | **BLOCKED** | **0건** |

★ **새 앱에 force-update 를 넣어도 이미 설치된 구버전에는 그 코드가 없다.** §5 참조.

### 3-8. `PRODUCT_INSTRUMENTATION`

| | 상태 | 근거 |
|---|---|---|
| **Core/Web** | **BLOCKED** | `lib/analytics.ts` 는 존재하나 `NEXT_PUBLIC_POSTHQ_KEY` 미설정 → `enabled()` false → **전면 no-op**. 배포 번들 전량(12청크) 검사에서 `phc_` 키 0건, 모듈은 번들됨 |
| **Android** | **BLOCKED** | 제품 계측 **0건** |
| **iOS** | **BLOCKED** | 제품 계측 **0건** |

> ★ **정정 기록**: `AnalyticsApi.kt`(Android) · `AnalyticsRepository.swift`(iOS) 를
> 계측으로 보고했던 것은 **틀렸다.** 둘 다 `prrs-by-genetics` **조회 API** 다.
> **이름만 보고 판단하지 않는다.**

### 3-9. `OFFLINE_CONTRACT` (발견 기록만 — 설계는 후속 STEP)

| | 발견 |
|---|---|
| **Android** | `Room` · `SyncQueueEntity` · `PigOsDatabase` — **기존 offline write queue 존재**. 로컬 엔티티는 `Event`·`Sow`·`SyncQueue` 뿐 → **KPI/presentation 캐시 없음** → `stale KPI local cache risk = not observed`, KPI 는 사실상 **online-only** |
| **iOS** | `NetworkMonitor` · `Core/Sync` 존재. KPI 캐시 여부 **미확인** |

★ 후속 설계 시 **Android 는 기존 `SyncQueueEntity` 를 재사용**한다. 별도 큐 생성 금지.

---

## 4. `BACKEND_NO_JUDGMENT_STATE` — ★ PRESENT

> 모바일 SAFETY FIX 의 선행조건 확인 (read-only)

```
result   : PRESENT
evidence : api/app/schemas/kpi.py  class KpiStatus
           status: normal | warning | critical | insufficient
           reason 어휘 8종: no_data · insufficient_sample · out_of_valid_range ·
                            no_policy · policy_pending · evaluation_skipped ·
                            rule_disabled · context_missing
```

★ 그리고 docstring 이 결정적이다:

> *"reason: 항상 존재(없으면 None). optional 로 두면 프론트가 유무로 분기 →
> **판단 로직의 입구가 됨**."*

**프론트 판단 금지를 스키마 설계 단계에서 이미 의도했다.**

```
SAFETY_FIX_PREREQUISITE : 불필요
```

→ 모바일은 **새 상태를 설계할 필요가 없다.** 이미 있는 `insufficient` 를 소비하면 된다.
   `alert 없음 → NEUTRAL` 을 모바일이 **새로 판단하게 하지 않는다.**

> 참고: 룰엔진 내부 `Severity` enum 은 `OK/INFO/WARNING/CRITICAL` 로 "판정 없음" 이
> 없으나, 룰이 발화하지 않으면 `Finding` 자체가 없으므로 다른 축이다.
> 사용자에게 나가는 계약은 `KpiStatus` 다.

---

## 5. `LEGACY_CLIENT_GATE` — 구현 순서 강제 (메모)

**잘못된 순서** — 이대로 켜면 Web 자신이 차단된다:

```
server: missing app-version header → LEGACY_CLIENT → deny     ✗
```

Web 도 현재 버전 헤더를 보내지 않는다(§3-6).

**정확한 순서:**

```
1. Web    version/platform header 송출
2. Android version/platform header 송출
3. iOS    version/platform header 송출
4. 서버에서 세 표면 header 수신 검증 (observability)
5. 이후에만  missing version = LEGACY_CLIENT  fail-closed 활성화

HEADER_TRANSMISSION → SERVER_OBSERVABILITY → LEGACY_FAIL_CLOSED
```

---

## 6. `LEGACY_CLIENT_TEST_CAPABILITY`

| | 결과 | 근거 |
|---|---|---|
| **Android** | **PARTIAL** | 저장소·빌드산출물에 APK/AAB **0건**, `app/build/outputs` 없음. CI(`android.yml`)가 `assembleDebug` 로 debug APK 를 만들지만 **artifact 업로드는 test report 뿐**. **과거 버전 APK 를 구할 수단이 없다** |
| **iOS** | **PARTIAL** | IPA/`xcarchive` **0건**. CI(`ci.yml`, `macos-15`)가 XcodeGen→`xcodebuild test` 로 **시뮬레이터 빌드·테스트는 가능**. **실기기 설치 가능한 과거 build 는 없음** |

★ 이번 STEP 0 에서 테스트를 억지로 실행하지 않았다. **수단 존재 여부만 확인했다.**

### 6-1. `ANDROID_RELEASE_ARTIFACT_RETENTION` — OPEN ISSUE

```
platform_implementation_status = NOT_IMPLEMENTED
current_build_capability       = AVAILABLE      (assembleDebug 가능)
artifact_retention             = NONE           (APK/AAB 업로드 없음. test report 만)
```

**권고**: 향후 버전별 APK/AAB artifact 를 저장하여 legacy-client regression test
자산을 축적한다. 지금 저장을 시작하지 않으면 **다음 버전부터도 과거 build 가 없다.**

★ 이번 STEP 에서 **CI 수정 금지.** 기록만 한다.

→ 구버전이 새 국가 API 거부에 어떻게 반응하는지 **검증할 수단이 현재 없다.**
   `COUNTRY_ROLLOUT_BLOCKER` 후보로 등록한다.

---

## 7. `IOS_RELEASE_CAPABILITY`

```
IOS_RELEASE_CAPABILITY = CI_EXTENSION_REQUIRED
```

| 항목 | 상태 | 근거 |
|---|---|---|
| CI macOS runner | **AVAILABLE** | `.github/workflows/ci.yml` — `runs-on: macos-15` |
| XcodeGen | **AVAILABLE** | 커밋된 `.xcodeproj` 없음. CI 가 생성 |
| `xcodebuild test` | **AVAILABLE** | 시뮬레이터 빌드·테스트 통과 경로 존재 |
| `xcodebuild archive` | **NOT_IMPLEMENTED** | ci.yml 에 단계 없음 |
| code signing | **NOT_IMPLEMENTED** | 〃 |
| TestFlight / distribute | **NOT_IMPLEMENTED** | fastlane·App Store Connect 단계 없음 |
| 로컬 빌드 | UNAVAILABLE | 현재 머신이 Windows(MINGW64). macOS/Xcode 없음 |

★ **`iOS build infrastructure unavailable` 이라고 일반화하지 않는다.**
  빌드·테스트 인프라는 **있다.** 없는 것은 **배포 파이프라인** 이고, 이는 기존 CI 를
  확장하면 되는 문제다 — 새 인프라 조달이 아니다.

**향후 확인 대상** (이번 STEP 구현 금지):

```
xcodebuild archive
code signing
provisioning profile
App Store Connect credentials / API key
export (ExportOptions.plist)
TestFlight / App Store distribution
```

`country_rollout_impact`:

> **iOS 가 required platform 인 국가에 한해**, 수정 버전을 build·sign·distribute 할 수
> 있는 capability 가 rollout prerequisite 다. **현재 build·test 는 CI 로 가능하나
> distribute 경로가 없다.**
>
> ★ iOS 를 지원하지 않는 국가까지 막지 않는다. *"iOS 빌드 인프라가 모든 국가 rollout 의
> 무조건 blocker"* 로 일반화하지 않는다.

---

## 8. `INSTRUMENTATION_REALITY` — Handoff 14개 이벤트의 실제 지위

```
Web        PostHog key 미설정 → no-op          BLOCKED
Android    제품 계측 0건                        BLOCKED
iOS        제품 계측 0건                        BLOCKED
```

→ `PIGOS_PRODUCT_IMPLEMENTATION_HANDOFF v1.0 §11` 의 14개 이벤트는
**`EXISTING_BASELINE` 이 아니라 `PLANNED_INSTRUMENTATION` 이다.**

`OPEN ISSUE` 로 등록 — Product v1.1 patch 대상(후속 STEP). **이번 STEP 0 에서 계측 구현 금지.**

---

## 9. `P0_CORRECTNESS_BLOCKERS` — parity 미구현이 아니라 **현재 결함**

> ★ 아래는 "아직 안 만든 것" 이 아니라 **지금 사용자에게 잘못된 판단을 표시하는 것** 이다.
> `OPEN_BLOCKERS`(§9-1) 와 분리한다. 우선순위가 다르기 때문이다.

### P0-1. iOS `insufficient` / no-judgment → `success`(초록)

```
Backend
  KpiStatus.status = insufficient        데이터 불충분 / 판정 불가

iOS
  DashboardScreen.swift:241-246
  alert 없음 → AppColor.success          정상 / 초록
```

**서버의 "판정 불가" 를 클라이언트가 "정상" 으로 뒤집는다.**

```
platform_implementation_status = BLOCKED
risk                           = SERVER_DECISION_OVERRIDE
class                          = CORRECTNESS_DEFECT   (parity gap 아님)
```

이는 제품 선택이 아니라 결함이므로 **결재 대상이 아니다.** 서버는 이미
`insufficient` 를 갖고 있으므로(§4) 신규 상태 설계 없이 소비하면 된다.

---

## 9-1. `OPEN_BLOCKERS`

| # | blocker | 영향 |
|---|---|---|
| B-1 | 양 플랫폼 `/kpi/presentation` 미소비 | 국가를 데이터로 켜도 모바일 미반영 |
| B-2 | 양 플랫폼 `kpi_status` 미소비 + 자체 판정 | 서버 G3 강제가 모바일에서 무력화 |
| B-3 | **→ P0-1 로 승격.** iOS FAIL-OPEN | (§9 참조) |
| B-4 | ~~Android `benchmark → severity` 변환~~ → **해소** `5ed3dd7` (§9-2) | — |
| B-5 | 3표면 모두 per-request 앱버전 헤더 없음 | `min_supported_version` 게이트 불가 |
| B-6 | 양 플랫폼 force-update 없음 | 구버전 차단 불가 (§5 순서 필요) |
| B-7 | 구버전 테스트 수단 없음 | rollout 안전성 검증 불가. `ANDROID_RELEASE_ARTIFACT_RETENTION`(§6-1) 이 선행 |
| B-8 | iOS distribute 경로 없음 → **`CI_EXTENSION_REQUIRED`**(§7) | iOS required 국가의 rollout prerequisite. 인프라 부재가 아니라 CI 확장 |
| B-9 | 3표면 모두 제품 계측 없음 | baseline 수집 불가 |
| **B-10** | `WEB_LOCAL_STATUS_FALLBACK` (§3-3) | DORMANT. 발동 시 한국 임계가 타국에 적용 |
| **B-11** | `SNAPSHOT_PIPELINE_CORRECTNESS` — **부분 해소** `2e372b1` | 크래시는 고쳤으나 `psy`·`farrowing_rate` 는 산식 미확정으로 여전히 보류. 배포 전까지 프로덕션 0행 유지 |
| **B-12** | ~~`ARQ_FALSE_SUCCESS_OBSERVABILITY`~~ → **해소** `2e372b1` (로컬. 미배포) | 배포 전까지 프로덕션은 그대로 |
| **B-13** | `ALERT_DECISION_REPRODUCIBILITY` | 고객 대면 알림 468건에 threshold · authority · formula version 미저장 |
| **B-14** | `UNAUDITED_AUTHORITY_CONFIG_CHANGE` | `use_governance_benchmarks` 는 GLOBAL scope 인데 변경 기록이 남는 곳이 없다 |

---

## 9-2. ★ 구현 evidence 등록 (2026-08-28 야간)

> `DONE` 은 implementation commit SHA 필수(§0-4). 2-phase 규율대로
> **구현 commit 이 먼저 만들어진 뒤 이 evidence 를 별도 commit 으로 기록**한다.
> 자기 commit SHA 를 같은 commit 에 기록하지 않는다.

### 9-2-1. 구현 commit

| 대상 | repo | commit | 내용 |
|---|---|---|---|
| Core | PigOS | `2e372b1` | ARQ false-success 제거 · snapshot supported-field contract |
| Core | PigOS | `c3a46cc` | client version 수신·관측 미들웨어 |
| CI | PigOS | `9da765c` | frontend unit test 스텝 신설 (그전엔 실행 0) |
| Web | PigOS | `fdd9ca5` | local threshold fallback → `insufficient` fail-closed |
| Web | PigOS | `c3a46cc` | platform/app version 헤더 송출 |
| Android | pigos-android | `5ed3dd7` | `kpi_status` 소비 · benchmark→severity 제거 · version 헤더 · APK 보관 |
| iOS | pigos-ios | `c516e2d` | `kpi_status` 소비 · `insufficient` FAIL-OPEN 제거 |
| iOS | pigos-ios | `8ecfdfe` | platform/app version 헤더 송출 |
| iOS | pigos-ios | `1d303bc` | unsigned archive validation job |
| iOS | pigos-ios | `4b07d3c` | severity default 기대값을 fail-closed 로 갱신 (CI 가 잡음) |

브랜치: 모바일 두 repo 는 `fix/kpi-status-consumption` (main 병합 안 함).

### 9-2-2. 셀 재판정

| 항목 | Core/Web | Android | iOS |
|---|---|---|---|
| `KPI_STATUS_CONSUMPTION` | **DONE** `fdd9ca5` | **DONE** `5ed3dd7` | **IN_PROGRESS** `c516e2d` — §9-2-3 |
| `LOCAL_SEVERITY_REMOVAL` | **DONE** `fdd9ca5` | **DONE** `5ed3dd7` | **IN_PROGRESS** `c516e2d` |
| `APP_VERSION_REQUEST_REPORTING` | **IN_PROGRESS** `c3a46cc` | **IN_PROGRESS** `5ed3dd7` | **IN_PROGRESS** `8ecfdfe` |
| `COUNTRY_KPI_PRESENTATION` | DONE(기존) | **BLOCKED** 변화 없음 | **BLOCKED** 변화 없음 |
| `FORCE_UPDATE / LEGACY_CONTROL` | BLOCKED | BLOCKED | BLOCKED |
| `PRODUCT_INSTRUMENTATION` | BLOCKED | BLOCKED | BLOCKED |

`APP_VERSION_REQUEST_REPORTING` 이 `DONE` 이 아닌 이유: 송출·관측까지만 했고
`min_supported_version` 게이트는 의도적으로 켜지 않았다(§12-1 순서). 계약 미완성이다.

### 9-2-3. ★ verification 상태 — 거짓 DONE 을 만들지 않는다

| 대상 | 검증 수단 | 결과 |
|---|---|---|
| Core | `pytest tests/unit` 721 passed · `ruff` clean | **VERIFIED** |
| Web | `tsc --noEmit` clean. vitest 실행 불가 → **CI 에 테스트 스텝 신설**(`9da765c`) | **PARTIAL** — 아래 |
| Android | `:app:compileDebugKotlin` + `:app:testDebugUnitTest` BUILD SUCCESSFUL (로컬 실행) | **VERIFIED** |
| iOS | 로컬 빌드 불가(Windows). CI `workflow_dispatch` macos-15 — run `33156495747` **success** (`build-test-lint` + `archive-validation` 둘 다) | **COMPILED_AND_UNIT_TESTED** / `runtime_verification_status = NOT_RUNTIME_VERIFIED` |

★ **Web 이 PARTIAL 인 이유 — 환경 blocker**

```
vitest 실행 불가
원인  Node v20.11.1 < 20.12.
      vitest → rolldown 이 node:util 의 styleText 를 import 하는데
      20.11 에는 없다 → SyntaxError: does not provide an export named 'styleText'
```

★ 이전 세션에 *"vitest 가 워커를 못 띄운다"* 로 기록했던 것은 **원인 오진**이었다.
  워커 문제가 아니라 **Node 버전 문제**다. `Node >= 20.12` 로 올리면 해소된다.

  ★ 더 큰 문제를 같이 찾았다 — **PigOS CI 의 frontend job 에 테스트 스텝이 아예 없었다.**
    `tsc --noEmit` + `npm run build` 뿐이었다. 즉 프론트 테스트는 로컬에서도
    CI 에서도 **어디서도 실행된 적이 없다.** CI 는 이미 Node 22 를 쓰므로
    스텝 한 줄을 추가했다(`9da765c`).

  → 이 머신 기준: `regression_test_status = PRESENT_BUT_NOT_EXECUTED`
    다음 CI run 부터는 실행된다.

★ iOS 는 CI 에서 컴파일·SwiftLint·단위테스트·unsigned archive 가 전부 통과했다.
  그래도 `NOT_RUNTIME_VERIFIED` 를 유지한다 — **시뮬레이터에서 실제 카드가
  무채색으로 그려지는지 눈으로 확인하지 않았다.** 거짓 DONE 을 만들지 않는다.

★ CI 가 잡아낸 것 하나 (가치 있는 실패):
  `APIErrorTests.testSeverityColorMapping` 이 `SeverityColor(severity: nil) == .ok`
  를 기대하고 있었다. **그 기대값 자체가 FAIL-OPEN 을 잠그고 있었다.**
  1차 run(`33155980980`)에서 이 테스트 하나만 실패했고, 그것이 정확히
  `c516e2d` 가 의도적으로 바꾼 동작이다 → `4b07d3c` 로 계약 갱신.

### 9-2-4. stale evidence 규율

evidence path 가 위 SHA 이후 변경되면 `DONE → PENDING_RECHECK` 후보다.
특히 `src/lib/kpi/statusObservation.ts` · `DashboardScreen.kt` ·
`DashboardScreen.swift` 세 파일은 판정 경로의 중심이라 변경 시 재확인이 필요하다.

---

## 10. 후속 STEP (이번 범위 아님)

```
STEP 1   D-19 v1.3 spec 검증 → 필요 시 v1.4 승격 → repo 편입 → current HEAD 재실행
STEP 2   Product v1.0 → v1.1 patch 4축
         ① Platform assumption correction  ② Offline contract
         ③ Mobile 포함 Instrumentation      ④ Country Rollout Gate + min app version
STEP 3   FEATURE_REGISTRY + code path mapping (실측 기반. 추정 금지)
STEP 4   EPIC 1 모바일 안전화 (local severity 제거 · insufficient 소비)
STEP 5   CI + Release Gate + App Version Gate
```

★ Mobile targeted audit 자체는 **GATE 0 blocker 가 아니다.**
  unsafe local judgment 제거는 **EPIC 1**, full parity 는 **국가 rollout blocker** 다.

---

## 11. 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-08-27 | `MOBILE_PARITY.md` 신설 |
| 2026-08-28 | `PLATFORM_PARITY.md` 로 `git mv`. STEP 0 — 기존 6행 evidence 재판정(DONE 2 → IN_PROGRESS, `done_with_sha=0`) · Track B 실측 고정 · `BACKEND_NO_JUDGMENT_STATE=PRESENT` 확인 · blocker 9건 등록 |
| 2026-08-28 | 야간 remediation evidence 등록(§9-2) — Core/Web/Android/iOS 8개 구현 commit. B-4·B-10·B-12 해소, B-11 부분 해소. iOS 는 NOT_RUNTIME_VERIFIED 유지, Web 은 vitest 환경 blocker 로 PRESENT_BUT_NOT_EXECUTED |
| 2026-08-28 | ★ Web 행 정정 — `NOT_APPLICABLE` → `BLOCKED / WEB_LOCAL_STATUS_FALLBACK` (D-19 N-7). ACTIVE(모바일) vs DORMANT(웹) 분리. blocker B-10~B-14 등록 |
| 2026-08-28 | STEP 1 착수 전 docs-only 보완 3건 — ① rename provenance + rename commit 분리 규율 ② B-3 → `P0-1` correctness blocker 승격 · Android `FAIL_CLOSED_BY_COINCIDENCE` 명기 ③ B-8 → `CI_EXTENSION_REQUIRED` 재분류 · `ANDROID_RELEASE_ARTIFACT_RETENTION` OPEN ISSUE 등록 |
