# FEATURE_REGISTRY

```
목적       기능 하나가 어느 코드에 사는지 — Web / Android / iOS / Core 를 한 줄로 잇는다
관계       상태(PLANNED/DONE 등)는 여기에 쓰지 않는다.  ← docs/PLATFORM_PARITY.md 소관
           여기는 identity 와 **실측 경로** 만 담는다
측정일     2026-08-28
측정 방식  파일 존재 확인 + grep. **추정 경로를 쓰지 않는다.**
           아직 없는 것은 경로를 지어내지 않고 `NOT_PRESENT` 로 둔다
```

## 0. ID 규율

```
형식        PIGOS-F-0001 …
재사용      금지 — 폐기된 ID 를 다른 기능에 다시 쓰지 않는다
의도적 결번  금지
rename      ID 유지. 이름만 바꾼다
split       기존 ID = SUPERSEDED, 신규 ID 를 발급하고 supersedes 를 남긴다
merge       살아남는 ID 하나를 정하고 나머지는 SUPERSEDED
```

`required_platforms` — 그 기능이 성립하려면 반드시 있어야 하는 surface.
`core` 는 백엔드다. 국가별로 required 가 달라지면 그 사실을 비고에 적는다.

---

## PIGOS-F-0001 — COUNTRY_KPI_PRESENTATION

```yaml
feature_id: PIGOS-F-0001
name: 국가별 KPI 표시 정책 소비 (/kpi/presentation)
required_platforms: [core, web, android, ios]
paths:
  core:
    - api/app/routers/base/kpi.py                     # 엔드포인트
    - api/app/services/kpi_policy_resolver.py         # GLOBAL→COUNTRY→FARM_TYPE→TENANT
    - api/app/db/models/kpi_presentation.py
  web:
    - src/lib/kpi/presentation.ts                     # resolveKpiCards
    - src/lib/kpi/cardRegistry.ts                     # 렌더 메타(임계·판정 금지)
  android: NOT_PRESENT                                # 소비 0건 (실측)
  ios:     NOT_PRESENT                                # 소비 0건 (실측)
offline_mode: READ_CACHE                              # 정책은 서버 확정. 클라 재정렬 금지
analytics_events: []                                  # 미정의
```

---

## PIGOS-F-0002 — KPI_STATUS_CONSUMPTION

```yaml
feature_id: PIGOS-F-0002
name: 서버 canonical 판정(kpi_status) 소비
required_platforms: [core, web, android, ios]
paths:
  core:
    - api/app/schemas/kpi.py                          # KpiStatus (normal|warning|critical|insufficient)
    - api/app/services/kpi_status_assembler.py        # Severity → canonical status 변환만
    - api/app/services/kpi_service.py                 # assemble_kpi_status 호출부
  web:
    - src/lib/kpi/statusObservation.ts                # resolveTier — 부재 시 insufficient
  android:
    - app/src/main/java/io/pigos/app/data/remote/dto/KpiDto.kt          # KpiStatusDto · KpiDecision
    - app/src/main/java/io/pigos/app/ui/screens/dashboard/DashboardScreen.kt
  ios:
    - PigOS/Domain/Model/KPI.swift                    # KpiStatusDto · KpiDecision
    - PigOS/UI/Screens/Dashboard/DashboardScreen.swift
offline_mode: READ_CACHE
analytics_events: [kpi_status_mismatch]               # web statusObservation 에서만 발생
notes: >
  status enum 은 서버 계약이다. 클라이언트에서 neutral/unknown/no_alert 를 만들지 않는다.
  insufficient 가 canonical no-judgment 상태다.
```

---

## PIGOS-F-0003 — LOCAL_SEVERITY_REMOVAL

```yaml
feature_id: PIGOS-F-0003
name: 클라이언트 자체 판정 제거 (fail-closed)
required_platforms: [web, android, ios]
paths:
  core: NOT_APPLICABLE                                # 서버는 판정 주체다
  web:
    - src/lib/kpi/status.ts                           # 임계 함수 — 관측용으로만 잔존
    - src/lib/kpi/statusObservation.ts                # 렌더 경로에서 분리
    - src/tests/lib/statusObservation.test.ts
  android:
    - app/src/main/java/io/pigos/app/ui/screens/dashboard/DashboardScreen.kt   # BenchmarkRow
    - app/src/test/java/io/pigos/app/data/remote/dto/KpiDecisionTest.kt
  ios:
    - PigOS/UI/Screens/Dashboard/DashboardScreen.swift                          # dotColor
    - PigOS/UI/Theme/AppColor.swift                                             # SeverityColor default
    - PigOSTests/KpiDecisionTests.swift
offline_mode: NOT_APPLICABLE
analytics_events: []
notes: >
  제거 대상 3종 — Web: 국가 구분 없는 psyTier/npdTier/farrowingRateTier 폴백 ·
  Android: meetsAvg = myValue >= benchmark.avg · iOS: alert 없음 → success.
  benchmark 는 비교 맥락이지 판정 권한이 아니다.
```

---

## PIGOS-F-0004 — APP_VERSION_CONTRACT

```yaml
feature_id: PIGOS-F-0004
name: 클라이언트 platform/app version 송출 · 서버 관측
required_platforms: [core, web, android, ios]
paths:
  core:    NOT_PRESENT                                # 수신·파싱·관측 미구현
  web:     NOT_PRESENT
  android:
    - app/src/main/java/io/pigos/app/di/NetworkModule.kt    # 인터셉터 추가 지점 (현재 auth·logging 둘뿐)
    - app/src/main/java/io/pigos/app/data/repository/DeviceRepository.kt  # 기기등록 시 1회만
  ios:
    - PigOS/Core/Network/APIClient.swift               # 헤더 추가 지점
    - PigOS/Core/Network/Endpoint.swift
offline_mode: NOT_APPLICABLE
analytics_events: []
notes: >
  활성화 순서 고정 — Web → Android → iOS 송출 → 서버 관측 확인 → 그 다음에야
  missing-version fail-closed. 역순 활성화는 정상 클라이언트를 전부 차단한다.
  (PRODUCT_IMPLEMENTATION_HANDOFF §12-1)
```

---

## PIGOS-F-0005 — PRODUCT_INSTRUMENTATION

```yaml
feature_id: PIGOS-F-0005
name: 제품 계측 (이벤트 송출)
required_platforms: [web, android, ios]
paths:
  core: NOT_PRESENT
  web:
    - src/lib/analytics.ts                            # 모듈 존재. key 미설정 → 전면 no-op
  android: NOT_PRESENT                                # 제품 계측 0건
  ios:     NOT_PRESENT                                # 제품 계측 0건
offline_mode: WRITE_QUEUE                             # 설계 시. 현재 transport 없음
analytics_events: PLANNED_14                          # HANDOFF §11 — baseline 아님
notes: >
  ★ AnalyticsApi.kt(Android) / AnalyticsRepository.swift(iOS) 는 계측이 아니라
    prrs-by-genetics 조회 API 다. 이름만 보고 계측으로 분류하지 말 것.
  ★ PostHog secret/key 를 생성하지 않는다.
```

---

## PIGOS-F-0006 — KPI_SNAPSHOT_PIPELINE

```yaml
feature_id: PIGOS-F-0006
name: KPI 스냅샷 집계·영속
required_platforms: [core]
paths:
  core:
    - api/app/jobs/kpi.py                             # 집계 + supported-field contract
    - api/app/jobs/_result.py                         # job 성공 semantics
    - api/app/jobs/worker.py                          # cron 등록
    - api/app/db/models/ops.py                        # KpiSnapshot
    - api/tests/unit/test_snapshot_supported_fields.py
    - api/tests/unit/test_job_result_semantics.py
  web:     NOT_APPLICABLE
  android: NOT_APPLICABLE
  ios:     NOT_APPLICABLE
offline_mode: NOT_APPLICABLE
analytics_events: []
notes: >
  2026-05-29 이래 71농장 전건 실패 상태였다(farrowing_rate 컬럼 부재).
  2026-08-28 supported-field contract 로 per-field fail-safe 적용.
  farrowing_rate · psy 는 산식 미확정으로 여전히 보류(_WITHHELD_FIELDS).
  이 기능에 의존하는 것: WHAT_CHANGED · snapshot-first Home · 과거 비교.
```

---

## PIGOS-F-0007 — NOTIFICATION_DECISION_PROVENANCE

```yaml
feature_id: PIGOS-F-0007
name: 알림 판정 근거 영속 (threshold · authority · formula version)
required_platforms: [core]
paths:
  core:
    - api/app/db/models/ops.py                        # Notification — decision_provenance 미존재
    - api/app/services/notification_service.py        # create_from_alerts
    - api/app/jobs/notifications.py
  web:     NOT_APPLICABLE
  android: NOT_APPLICABLE
  ios:     NOT_APPLICABLE
offline_mode: NOT_APPLICABLE
analytics_events: []
notes: >
  현재 고객 대면 알림 468건에 판정 근거가 없다 → historical_reproducibility = NO.
  설계는 D21_THRESHOLD_GOVERNANCE_DESIGN §11 (JSONB 한 덩어리).
  ★ 과거 468건 backfill 금지 — 오늘의 추정이지 그때의 근거가 아니다.
```

---

## PIGOS-F-0008 — ROLE_AWARE_HOME

```yaml
feature_id: PIGOS-F-0008
name: 역할별 홈 화면
required_platforms: [core, web, android, ios]
paths:
  core:    NOT_PRESENT
  web:     NOT_PRESENT
  android: NOT_PRESENT
  ios:     NOT_PRESENT
offline_mode: READ_CACHE
analytics_events: [home_open]                         # PLANNED
notes: >
  미착수. grep 실측으로 어느 repo 에도 구현이 없음을 확인했다.
  선행: PIGOS-F-0006 (snapshot-first 를 쓸 경우)
```

---

## PIGOS-F-0009 — WHAT_CHANGED

```yaml
feature_id: PIGOS-F-0009
name: 무엇이 바뀌었는가 (기간 대비 변화)
required_platforms: [core, web, android, ios]
paths:
  core:    NOT_PRESENT
  web:     NOT_PRESENT
  android: NOT_PRESENT
  ios:     NOT_PRESENT
offline_mode: READ_CACHE                              # SERVER_ONLY 계산. 오프라인 재계산 금지
analytics_events: [change_card_view, change_card_expand]   # PLANNED
notes: >
  ★ 선행조건 둘 — PIGOS-F-0006 snapshot pipeline correctness · as_of 재현성(G0-D).
    D-19 V-6 = TIMESTAMPED_ONLY 라 as_of 가 선행이다(병렬 불가).
```

---

## PIGOS-F-0010 — ACTION_CENTER

```yaml
feature_id: PIGOS-F-0010
name: 할 일 / 조치 센터
required_platforms: [core, web, android, ios]
paths:
  core:
    - api/app/jobs/tasks.py                           # 기존 task 자동생성 (부분 선행 자산)
    - api/app/services/sync_service.py                # WRITE_QUEUE 재사용 대상
  web:     NOT_PRESENT
  android:
    - app/src/main/java/io/pigos/app/data/local/entity/SyncQueueEntity.kt   # 기존 큐
    - app/src/main/java/io/pigos/app/data/repository/SyncRepository.kt
  ios:
    - PigOS/Core/Sync/SyncScheduler.swift
    - PigOS/Core/Sync/NetworkMonitor.swift
offline_mode: WRITE_QUEUE                             # SERVER_WINS · CLIENT_UUID 멱등 · conflict observable
analytics_events: [action_open, action_start, action_done]  # PLANNED
notes: >
  기존 sync queue 를 재사용한다. 새 큐를 만들지 않는다.
```

---

## 부록 — 다음에 등록할 후보 (아직 ID 미발급)

```
Weekly Brief · Health Watch · Feed Basic · Root Cause Candidate ·
Benchmark Depth · Multi-farm · Contextual AI Copilot
```

ID 는 **실제 착수 시점에** 발급한다. 미리 예약해 두면 결번이 생긴다.
