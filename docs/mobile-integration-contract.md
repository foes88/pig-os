# PigOS 모바일 ↔ 백엔드 연동 계약서 (Single Source of Truth)

> 웹/백엔드 세션과 모바일(iOS/Android) 세션이 **이 문서 하나를 보고** 개발을 맞춘다.
> 변경 시 이 문서를 먼저 갱신하고 양측에 공지. 최종 갱신: 2026-06-18.
> API 라우트는 `GET http://<host>:8000/docs` (OpenAPI)와 항상 일치해야 한다.
>
> 🧭 **이 문서로 완벽 개발하는 법(2벌 페어링)**: 이 MD = **무엇을/왜/화면구조·결정·Enum·비자명 규칙**(SSOT).
> **정확한 요청/응답 필드 스키마**는 중복·드리프트 방지 위해 **OpenAPI(`/docs` = `docs/api/openapi-v1.yaml`, 67 paths)** 에 둔다.
> 따라서 모바일은 **MD(이 문서) + OpenAPI**를 함께 보면 빠짐없이 구현 가능. 라우트 변경 시 둘 다 갱신(`scripts/gen_openapi.py` 재생성).
>
> 📌 **2026-06-18 변경(모바일 반영 필수)**: ① 화면/메뉴 구조 재설계(§3.0) ② 보고서 API 확장 — 품종별 `group_by=breed` + `/reports/production-summary`(국가 기준값 동봉) + 확장지표(§3 KPI/보고서) ③ 알림 통합 — '관리대상'+'시스템알림' 한 화면 탭(§3 할일/알림) ④ 국가별 KPI 차등 기준값(KR=PigPlan2025 실데이터 시드)(§3 임계값/§5) ⑤ UI 아이콘=벡터, **이모지 금지**(§5).
>
> ⛔ **이 문서가 유일한 기준.** 모바일 레포의 옛 문서(`03-api-endpoints.md`,
> `MOBILE_API_CHANGES_2026-06-09.md` 등)는 stale(모돈 상태값 오류·boars "미구현" 오인 등) →
> **폐기**하고 이 계약서로 대체한다. 라이브 백엔드 라우트에서 직접 생성됨(커밋 66528f7+).

---

## 1. API Base URL (환경별)

| 환경 | Base URL | 비고 |
|------|----------|------|
| 운영(prod) | `https://api.pigos.io` | 포트 없음, HTTPS |
| Android 에뮬레이터 | `http://10.0.2.2:8000` | 에뮬에서 본 PC localhost |
| iOS 시뮬레이터 | `http://localhost:8000` | 호스트 네트워크 공유 |
| 실기기(같은 와이파이) | `http://<PC-LAN-IP>:8000` | 예: 192.168.x.x, PC IP 바뀌면 교체 |

- dev API 포트 **8000 고정**. 웹 프론트는 3000.
- 환경 분리: Android `BuildConfig.API_BASE_URL`(debug/release), iOS `Debug/Release.xcconfig`.
- dev는 평문 HTTP → Android `usesCleartextTraffic`(debug만), iOS ATS `NSAllowsLocalNetworking`(debug만).
- 모든 경로 prefix: `/api/v1`.

---

## 2. 인증 (Bearer 토큰, 쿠키 아님)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/api/v1/auth/login` | `{email, password}` → `{access_token, refresh_token, user_id, name, email, role, farm_ids}` |
| POST | `/api/v1/auth/refresh` | `{refresh_token}` → `{access_token}` |
| POST | `/api/v1/auth/logout` | 로그아웃 |
| GET | `/api/v1/auth/me` | 현재 유저 프로필 |
| POST | `/api/v1/auth/register` | 가입(개별) |

- 모든 보호 API는 헤더 `Authorization: Bearer <access_token>`.
- access 만료 시 401 → refresh로 재발급 → 원요청 재시도 (모바일 인터셉터 구현 필요).
- 테스트 계정: `test001@pigos.io` / `123123` (FARM_OWNER).
- 온보딩(신규 농장): `POST /api/v1/onboarding/complete` 등 `/onboarding/*`.

---

## 3. 핵심 도메인 API (모바일 화면별)

### 3.0 화면/메뉴 구조 (웹과 동일하게 — 2026-06-18 재설계)
> 모바일 드로어/하단탭도 이 구조·명칭을 따른다(웹 `Sidebar.tsx` 기준). 라벨은 5개어.

| 그룹 | 화면(route) | 설명 | 주요 API |
|------|-------------|------|----------|
| — | **대시보드** `/` | 생산현황 요약 | `GET /kpi/dashboard`(alerts·benchmarks 포함) |
| — | **기록 입력** `/record` | 교배·분만·이유·사고·자돈폐사 **탭 통합 진입** | `POST /events/*` (응답에 `insights[]`) |
| 돈군 | 모돈 `/sows` · 웅돈 `/boars` · 자돈 `/piglets` · 비육돈 `/finishers` | 돈군 목록/상세/등록 | `GET|POST /farms/{id}/{sows\|boars\|piglets\|finishers}` |
| 할 일·알림 | **오늘 할 일** `/tasks` · **알림** `/alerts` | 알림은 한 화면 **2탭**: ①관리대상(과기한/도태권고) ②시스템알림 | `GET /tasks`, `/alerts/overdue`, `/alerts/cull-candidates`, `/notifications` |
| 보고서 | KPI현황 `/kpi` · 생산성적(번식) · 비육성적 · 모돈보고서 · PRRS | 성적/보고서 | `GET /kpi/*`, `/reports/*`, `/analytics/prrs-by-genetics` |
| — | Addon `/addons` · 설정 `/settings` | | |

- **'분만사(Farrowing)' 메뉴 제거** — 분만은 `/record`의 분만 탭으로. (구 `/farrowing` 라우트는 직접 쓰지 말 것.)
- **알림 통합**: 과거 '관리 알림'(/alerts)과 '알림'(/notifications)이 분리돼 있었으나 → **'알림' 하나**로. 모바일은 알림 화면에서 탭 2개로 표현(관리대상/시스템알림), 배지 = `overdue.total + notifications.unread_count`.
- **KPI**는 '보고서' 그룹에 속함(별도 '분석' 그룹 없어짐).

### 농장 컨텍스트 / 설정
- `GET /farms` · `GET /farms/{farm_id}` · `PATCH /farms/{farm_id}`
- `GET /farms/{farm_id}/config` → 단위/통화 (`weight_unit, currency_code, currency_symbol, ...`, **country 기준 자동 분기**)
- `GET|PATCH /farms/{farm_id}/config/repro` → 임신/포유/WSI 기준일

### 모돈 / 웅돈 / 자돈 / 비육
- 모돈: `GET|POST /farms/{farm_id}/sows`, `GET|PATCH|DELETE /sows/{sow_id}`, `POST /sows/{sow_id}/cull`, `GET /sows/removals`
  - 목록 쿼리: `status, building_id, parity_min, parity_max, search(ear_tag 부분일치), page, per_page`
- 웅돈: `GET|POST /farms/{farm_id}/boars`, `GET|PATCH /boars/{boar_id}`
- 자돈: `GET|POST /farms/{farm_id}/piglets`, `/piglets/{group_id}/deaths`, `/piglets/{group_id}/transfer`, `/piglets/transfers`
- 비육: `GET|POST /farms/{farm_id}/finishers`, `PATCH|DELETE /finishers/{group_id}`, `POST /finishers/{group_id}/ship`

### 번식 이벤트 (수정/삭제 = 상태 롤백 + 월마감 423 포함)
- 교배: `GET|POST /events/matings`, `PATCH|DELETE /events/matings/{id}`
- 분만: `GET|POST /events/farrowings`, `PATCH|DELETE /events/farrowings/{id}`
- 이유: `GET|POST /events/weanings`, `PATCH|DELETE /events/weanings/{id}`
- 기타: `POST /events/reproductive`(임신사고/RTS 등), `GET|POST /events/piglet_events`(포유자돈 폐사)
- 이벤트 정의: `GET /events/definitions`
- **작업대장(Work Ledger, 2026-06-18 신규)**: `GET /events/ledger?start_date&end_date&kind&limit` → `LedgerEntry[]`
  `{ id, kind(mating|farrowing|weaning|reproductive|piglet|removal), event_date, sow_id, ear_tag, summary }`.
  전 이벤트 유형 **통합·최신순**, soft-delete 제외. PigPlan '작업대장' 대응. 모바일 '작업 이력' 화면에 사용.
- ⚠️ **soft-delete(2026-06-18)**: 이벤트 `DELETE`는 soft-delete(204) + **모돈 상태 롤백**(mating→OPEN / farrowing→PREGNANT / weaning→LACTATING). `GET` 목록은 `deleted_at` 건을 **반환하지 않음**(삭제 즉시 목록에서 사라짐). 모바일 로컬(Room/CoreData)도 삭제 sync 시 해당 행 제거 + 상태 롤백 미러링.

#### ⚠️ P0 입력 검증 + 신규 필드 (2026-06-19 — 모바일도 동일 적용)
> 검증의 **최종 권위는 백엔드**(웹·모바일·sync 공용). 모바일은 동일 기준으로 **클라 사전검증**해 즉시 피드백 + 422 폴백.
> 전체 기준: `docs/VALIDATION_SPEC.md`, `docs/DEV_GUIDE.md §5`.

- **분만 `POST /events/farrowings`** 요청에 선택 필드 추가: `avg_birth_weight_kg`(≤3.0kg), `born_alive_male`, `born_alive_female`(입력 시 합 = born_alive). 응답에 `nursing_head`(포유개시두수, 초기값=born_alive), `avg_birth_weight_kg` 추가. 검증: TB≤35, SB/MUM≤25, BA≤TB, TB=BA+SB+MUM.
- **이유 `POST /events/weanings`**: `weaned_count == nursing_head - 폐사 - 양자out + 양자in` **항등식 강제**(불일치 시 422). 즉, 폐사·양자를 piglet_events로 먼저 기록해야 적게 이유 가능. `avg_weaning_weight_kg`는 **2~12kg** 범위.
  - **🆕 부분이유 `is_partial: bool=false`(2026-06-19, P1)**: 잔여 포유두수 = 유효복당 − 기존이유합. `is_partial=true`면 `weaned_count ≤ 잔여` 허용 + 모돈 **LACTATING 유지**(여러 번 이유 가능). `is_partial=false`(기본/최종)면 `weaned_count == 잔여` 강제 + 모돈 **OPEN** 전이. 잔여 0인데 추가 이유 시 **409**. 미전송 시 최종이유(하위호환). 스펙: `docs/specs/2026-06-19_partial-weaning-spec.md`.
- **교배 `POST /events/matings`**: 동일 모돈·동일 날짜 중복 교배 **409**, 웅돈은 **ACTIVE 상태만** 사용 가능(아니면 422). 교배가능 상태 GILT/OPEN/ACCIDENT.
- **자돈 이벤트 `POST /events/piglet_events`**: 응답에 `age_days`(=event_date−farrowing_date) 추가. **양자(FOSTER_IN/OUT)는 `target_sow_id` 필수 + 대상 모돈 LACTATING**. 서버가 **반대편 거울 레코드 자동생성**(FOSTER_OUT→대상에 FOSTER_IN) — 모바일은 한쪽만 보내면 됨(양쪽 보내면 중복). 폐사두수 > 현재 포유두수면 422.
- **임신 중 도폐사**(`POST /events/reproductive` event_type=CULLED/DEAD, 모돈 PREGNANT): **사유(notes) 필수**(없으면 422).
- **🆕 수정/삭제 경로 견고화(2026-06-19)**: 생성과 동일 제약을 **수정(PATCH)에도 재적용**. `update_mating`: 웅돈 변경 시 ACTIVE 검사·교배일 변경 시 동일날짜 중복 409. `update_farrowing`: 실산을 이미 이유한 두수 밑으로 축소 시 422(두수 꼬임 방지)+nursing_head 동기화. `update_weaning`: 부분이유 형제 합계까지 ≤ 유효복당 검증. **양자 self-target(target==sow) 422**. 모바일 편집 화면도 동일 동작.
- **비육돈 `POST /finishers`**: 입식두수≥1, 입식체중 5~50kg. **출하 `POST /finishers/{id}/ship`**: 출하두수≤입식두수, 출하체중≤200kg & 입식체중 초과, 출하완료 그룹 재출하 차단.
- 신규 DB 컬럼(마이그레이션 `dbeb4c5ed00f`): `farrowings.nursing_head`, `farrowings.avg_birth_weight_kg`, `piglet_events.age_days`. **sync pull 스키마에 반영**.

### KPI / 보고서 / 분석
- `GET /farms/{farm_id}/kpi/dashboard` (PSY/NPD/FR + 모돈현황 + alerts + **country별 benchmarks**)
- `GET /kpi/psy` · `/kpi/npd` · `/kpi/trend?kpi=&months=`
- `GET /farms/{farm_id}/analytics/prrs-by-genetics`

#### 보고서 (2026-06-18 확장 — cowork R3/R5)
- **일일 사육현황**: `GET /reports/daily?date=YYYY-MM-DD` → `DailyReport`
  `{ date, herd:{active_sows,gilts,open,pregnant,lactating,accident}, matings, farrowings:{count,total_born,born_alive}, weanings:{count,weaned}, accidents, piglet_deaths:{count,piglets}, removals }`. 당일 이벤트 집계 + 돈군 스냅샷(soft-delete 제외). PigPlan '일일보고서' 대응.
- **번식 성적**: `GET /reports/reproduction?start&end&period={monthly|quarterly|annual}&group_by={period|breed}`
  - `group_by=breed` → 기간 대신 **품종별 행**. 반환 `ReproductionRow[]`:
    `period`(기간 또는 품종명), `total_matings, total_farrowings, total_weanings, fr, avg_tb, avg_ba, avg_weaned, avg_lactation_days, pwmr_a, pwmr_b, rts_rate`
    + **확장지표**: `total_born_sum, born_alive_sum, total_stillborn, total_mummified, stillborn_rate, mummified_rate, birth_loss_rate, mating_1_count, mating_2_count, mating_3plus_count, ai_count, natural_count` (미집계 시 null)
- **통합표(피그플랜식)**: `GET /reports/production-summary?start&end&period&group_by` → `ProductionSummary`:
  `{ group_by, period, country_scope, benchmarks: BenchmarkValue[], rows: ReproductionRow[] }`
  - `BenchmarkValue`: `{ metric_code, target, benchmark_avg, benchmark_top25, warning, critical, alert_direction, unit, source_ref, confidence }` — **농장 country 기준값**. 모바일은 행 값과 **비교 표시만**(목표/상위25% 대비), 판정·임계계산 재구현 금지.
- **비육 성적**: `GET /reports/grow-finish?start&end&group_id?` → `GrowFinishRow[]`:
  `{ group_code, start_date, end_date, head_in, head_out, avg_entry_weight_kg, avg_exit_weight_kg, adg_g, fcr, mortality_rate }`
- **모돈 이력**: `GET /reports/sows/{sow_id}/history` → `SowHistoryCycle[]`:
  `{ parity, mating_date, boar_ids[], farrowing_date, tb, ba, sb, mum, weaned, weaning_date, lactation_days, status }`
- **종합일보 (2026-06-19, PigPlan .mrd 6섹션)**: `GET /reports/comprehensive-daily?date=YYYY-MM-DD` → `ComprehensiveDailyReport`:
  `{ date, herd:{gilt,open,pregnant,lactating,accident,sows_total,boars,nursing_piglets,finishers}, mating:{day,month}, accidents:{day,month}, production:{day,month}, inout:{day,month} }`.
  mating={total,gilt,sow,rebreed} · accidents={total,rts,abortion,empty,infertile} · production={farrowings,total_born,born_alive,stillborn,mummified,avg_birth_weight,weanings,weaned,avg_weaning_weight,avg_weaning_age,piglet_deaths} · inout={gilt_in,sow_in,dead,culled,sold,transfer,boar_in}. 일계(당일)+월계(당월). ⑦⑧ 사료·도축 제외(모듈 없음).
- **모돈 현재 상태표 (2026-06-19, MVP #1)**: `GET /reports/sow-status` → `SowStatusReport`:
  `{ total, by_status:{GILT,OPEN,PREGNANT,LACTATING,ACCIDENT}, sows:[{sow_id,ear_tag,status,parity,entry_date}] }`. 활성 모돈만.
- **분만·포유·이유 성적표 (2026-06-19, MVP #3)**: `GET /reports/farrowing?start_date&end_date` → `FarrowingPerfRow[]` (산차별):
  `{ parity, farrowings, avg_total_born, avg_born_alive, avg_stillborn, avg_mummified, avg_weaned, avg_lactation_days, litters_weaned }`.
- **도폐사·포유폐사 리포트 (2026-06-19, MVP #4)**: `GET /reports/mortality?start_date&end_date` → `MortalityReport`:
  `{ removals_by_type:[{key,count}], removals_by_reason:[{key,count}], piglet_deaths_by_reason:[{key,count,piglets}], total_removals, total_piglet_deaths, born_alive_in_period, preweaning_mortality_rate }`. key는 enum 원값(CULLED/REPRODUCTIVE/CRUSHING 등) — 라벨은 클라가 i18n 매핑.
- **데이터 품질/정합성 (2026-06-19 신규, MVP #5)**: `GET /reports/data-quality?as_of=YYYY-MM-DD?` → `DataQualityIssue[]`:
  `{ issue_type, severity(CRITICAL|WARNING), sow_id, ear_tag, detail, event_date }`.
  `issue_type`: `LITTER_MISMATCH`(총산≠BA+SB+MUM) · `WEANED_MISMATCH`(이유>유효복당) · `DATE_REVERSAL`(분만<교배/이유<분만) · `STATUS_ORPHAN`(PREGNANT인데 교배無 등) · `MISSING_FARROWING`(교배 후 130일↑ 미분만) · `MISSING_WEANING`(분만 후 60일↑ 미이유). 모바일 '데이터 점검' 화면에 사용. PigPlan '오류/누락 점검' 대응.
- 기간 범위 >2년 → 400. CSV는 웹에서 클라이언트 변환(모바일은 표시/공유 자체 구현).

### 할 일 / 알림  (2026-06-18: '알림' 화면은 2탭 통합)
- **오늘 할 일** `/tasks`: `GET /farms/{farm_id}/tasks?status=&assigned_to=`, `POST /tasks/generate`, `PATCH /tasks/{id}`(DONE/DISMISS/assign)
- **알림** `/alerts` = 한 화면 **2탭**:
  - 탭① **관리대상**: `GET /farms/{farm_id}/alerts/overdue`(6유형, `total` 포함) · `/alerts/cull-candidates`
  - 탭② **시스템 알림**: `GET /api/v1/notifications?unread_only=&limit=&offset=` (유저 스코프, `unread_count` 포함),
    `PATCH /notifications/{id}/read`, `POST /notifications/read-all`, 생성배치 `POST /farms/{farm_id}/notifications/generate`
  - 화면/탭 배지 = `overdue.total + notifications.unread_count`. (웹은 사이드바 '알림' 1개 + 통합배지, 화면 안에서 탭 전환.)

### 입력 즉시 분석 (Event Insight / Rule Engine) — 모바일 별도 구현 불필요
- **Rule Engine·국가별 임계값·손실계산은 전부 백엔드.** 모바일은 재구현하지 않는다(웹과 동일 "렌더만").
- 분만/교배/이유 `POST` 응답에 **`insights: EventInsight[]`** 동봉 → 모바일은 그대로 배너 렌더.
- `EventInsight` 필드: `metric_code, severity(INFO|WARNING|CRITICAL), value, threshold, unit, direction,
  normalized_gap, priority, confidence, is_proxy, source, is_global_fallback, loss{amount,currency,lost_pigs,demo}|null, relative|null`.
- **판정·국가분기 0줄**: 백엔드가 farm.country로 임계값을 자동 해석(KR→PigPlan/한돈팜스, US→PigCHAMP, 없으면 글로벌 폴백).
  모바일은 severity로 스타일만, gap/priority로 정렬만, 문구는 i18n(metric+severity 템플릿).
- 표시 규칙(웹과 동일): WARNING/CRITICAL 강하게, INFO/정상은 작게, `loss`는 데이터 있을 때만(금액/통화 없으면 숨김),
  `demo:true`면 Demo 배지, `is_global_fallback`/`is_proxy`면 참고 배지.
- ⚠ **오프라인**: 로컬 저장 시점엔 인사이트 없음(서버 판정). 온라인 `POST`는 즉시 insights, 오프라인 입력은
  `POST /sync` 시점에 서버가 분석 → 동기화 후 알림(notifications)으로 확인. 단말 인라인 즉시판정은 안 함(원칙: 판정은 서버).

### 임계값 관리 (#4 — 농장별 KPI 임계값)
- `GET /api/v1/farms/{farm_id}/thresholds` → 유효 임계값 목록 `ThresholdRow[]`. 각 metric: `metric_code, warning|null, critical|null, avg|null, top25|null, target|null, direction, unit, confidence, is_proxy, source, scope(farm|country|global), is_override`.
- `PATCH /api/v1/farms/{farm_id}/thresholds/{metric_code}` `{warning?, critical?}` → 농장 스코프 override upsert(우선순위 **농장>국가>글로벌**). direction/unit은 상위 scope에서 상속.
- `DELETE /api/v1/farms/{farm_id}/thresholds/{metric_code}` → override 삭제 → 국가/글로벌 값으로 복귀.
- 판정·해석은 백엔드. 모바일/웹은 목록 표시·override 입력만(렌더+편집), 임계 계산 재구현 금지.
- **국가별 차등(2026-06-18)**: 기준값/임계/단위/정의가 국가(KR/US/CN/SEA/LatAm)마다 다름. scope 체인 **농장>국가(region)>글로벌**로 백엔드가 자동 해석 → 모바일은 `thresholds`·`kpi/dashboard`·`reports/production-summary` 응답의 country 기준값을 **그대로 표시**(국가분기 하드코딩 0줄). KR은 PigPlan2025 실데이터 벤치마크 시드 적용(region scope). 차등 근거 문서: `docs/specs/2026-06-17_country-kpi-differences.md`, `docs/specs/2026-06-17_pigplan-metrics-mapping.md`.

### 푸시 디바이스 (G2 — 신설)
- `POST /api/v1/devices` `{platform: ANDROID|IOS|WEB, token, app_version?}` → 등록(토큰 기준 upsert)
- `GET /api/v1/devices` → 내 단말 목록
- `DELETE /api/v1/devices/{token}` → 로그아웃/토큰만료 시 해제
- 모바일 흐름: 로그인 직후 FCM/APNS 토큰 등록 → 토큰 갱신 시 재등록 → 로그아웃 시 삭제.

### Q&A
- `POST /farms/{farm_id}/chat/query` (Rule-grounded, addon 활성 농장은 LLM 응답)

### 팀원 / 조직 (멤버·조직 관리)
- **팀원(농장 멤버)**: `GET /farms/{farm_id}/members` → `MemberResponse[]`(`user_id, email, name, role`) ·
  `POST /farms/{farm_id}/members`(`MemberCreate {email, role(기본 FARM_WORKER)}`) ·
  `PATCH /farms/{farm_id}/members/{user_id}`(`MemberUpdate {role}`). 역할은 농장 레벨 override(없으면 org role). 변경 권한=OWNER/MANAGER.
  - 모바일 '팀/멤버' 화면이 있으면 이 API 사용(Task 담당자 배정의 `assigned_to`도 멤버 user_id).
- **조직(엔터프라이즈 계층)**: `GET /orgs` · `GET /orgs/{org_id}` · `POST /orgs` · `PATCH /orgs/{org_id}` · `GET /orgs/{org_id}/farms` · `GET /orgs/{org_id}/tree`.
  - 다농장/조직 관리용(주 사용=웹 관리자). 모바일 MVP는 보통 단일농장 컨텍스트라 **선택**. 다농장 계정이면 `auth/login`의 `farm_ids`로 농장 전환 + 위 트리 참고.

---

## 4. 오프라인 동기화 (Offline Sync)

- 엔드포인트: `POST /api/v1/farms/{farm_id}/sync`
- 스펙 문서: `docs/specs/2026-05-19_offline-sync-spec.md` (Last-Write-Wins)
- **Push(클라→서버)** 커버 엔티티(SyncChanges 기준): `matings, farrowings, weanings, reproductive_events, health_events, piglet_events`
  (sows는 push 대상 아님 — 모돈 등록/수정은 REST. sow 상태는 이벤트 sync로 서버가 전이.)
- **Pull(서버→클라)** 커버 엔티티(ServerChanges 기준): `sows, matings, farrowings, weanings, piglet_events, removals`
- 충돌: 자동 LWW 병합, 해소 불가(DUPLICATE_EVENT/CYCLE_CONFLICT)만 `sync_conflict_queue` 적재.
- ⚠️ 모바일 로컬 스키마(Room/CoreData)는 위 엔티티 + 필드와 1:1 유지. 필드 추가 시 이 문서 갱신.

---

## 5. 공유 상수 / Enum (양측 동일하게)

- **모돈 상태(SowStatus v2)**: `GILT, OPEN, PREGNANT, LACTATING, ACCIDENT`(활성) / `CULLED, DEAD, SOLD, TRANSFER`(종료)
  - 상태 머신 출처: `docs/SCREEN_MENU_SPEC.md`. PATCH로는 활성값만, 종료는 `/cull` 전용.
- **입식유형(entry_type)**: `GILT, PURCHASE, TRANSFER, BORN`
- **번식 이벤트(reproductive) event_type (9종)**: `RETURN_TO_ESTRUS, ABORTION, EMPTY, INFERTILE, HEAT_DETECTED, CULLED, DEAD, TRANSFER_OUT, SOLD`
  - `detected_method`(선택): `ULTRASOUND, VISUAL, BEHAVIOR, BLOOD_TEST`
- ⚠️ `GET /sows?status=` 는 위 SowStatus 값만 허용 — 잘못된 값은 **422**(빈 목록 조용히 반환 아님). 옛 값(ACTIVE/GESTATING/DRY/WEANED) 사용 금지.
- **Task 유형**: overdue 6유형(`gilt_no_estrus, gilt_overdue_mating, pregnant_overdue_farrowing, lactating_overdue_weaning, open_overdue_mating, accident_overdue_mating`) + `cull_candidate`
- **알림 severity**: `INFO, WARNING, CRITICAL` / **alert_type**: `OVERDUE_*, CULL_CANDIDATE, KPI_*`
- **역할**: `FARM_OWNER, FARM_MANAGER, FARM_WORKER, VET, VIEWER` (org: `SUPER_ADMIN` 등)
- **단위/통화**: 하드코딩 금지 — 반드시 `GET /farms/{id}/config` 응답 사용. country는 계정별로 다름(언어≠국가).
- **UI 아이콘(2026-06-18)**: 유니코드 **이모지 금지**(웹은 R7에서 lucide 벡터로 전면 교체). 모바일도 SF Symbols(iOS)/Material Symbols(Android) 등 **벡터 아이콘**으로 통일 — 의미 아이콘(검색/알림/경고/심각/정보/완료/번식단계)은 웹 lucide 매핑에 맞춤.

---

## 6. 갭 현황 (2026-06-16 갱신)

| # | 갭 | 상태 | 비고 |
|---|----|------|------|
| **G1** | 푸시 전송(FCM HTTP v1) | ✅ **코드 완성** | `push_service.send_push` + 알림 잡 연동. **배포 활성화 2단계 필요**: ① `uv add google-auth` ② env `FCM_PROJECT_ID`+`FCM_CREDENTIALS_PATH`(서비스계정 JSON). 미설정 시 graceful skip. |
| **G2** | 디바이스/푸시토큰 등록 API | ✅ **완성** | `POST/GET/DELETE /api/v1/devices` + `devices` 테이블 + 테스트. |
| **G3** | 알림 producer 자동 실행 | ✅ **cron 등록됨** | `worker.py`: tasks 05:30 / notifications 06:00 (UTC). **배포 시 ARQ worker 컨테이너 상시기동 확인 필요**(인프라). |
| **G4** | sync 실단말 E2E 검증 | 🟡 **모바일 대기** | 서버측 구현·테스트 완료. 닫는조건: 실기기에서 오프라인 입력→온라인 복귀→`POST /sync` 왕복 + 충돌 1건 시나리오 통과(모바일+백엔드 합동). |
| **G5** | 이미지 업로드(사진 첨부) | ⚪ **보류(요구 확정 전)** | 닫는조건: ① 제품 요구 확정 ② S3 버킷+IAM 준비 → `POST /api/v1/uploads/presign` 신설. AWS 리소스는 사람이 생성. |
| **G6** | `/sync` 분만·자돈 영속(#8) | ✅ **수정+가드(2026-06-16)** | `_process_farrowing` kwarg(born_dead→stillborn 등)+mating_id+flush 교정(`9fc008a`). **2회 회귀 이력** — `_process_*` 직접 path만 테스트돼 `/sync` path가 무방비였음. **회귀테스트 `tests/integration/test_sync_farrowing.py`(`5511236`) 추가** → ⚠️ **`sync_service.py` 수정 시 반드시 `uv run pytest tests/integration/test_sync_farrowing.py` 확인**. 라이브 §8a 그린(farrowings/piglet_events 영속 확인). |

> **G1 활성화 메모(배포 담당)**: google-auth 설치 + 서비스계정 JSON 마운트 + env 2개. 그 전까지 푸시는 자동 skip이며
> 인앱 알림(GET /notifications)은 polling으로 정상 동작 → 기능 차단 없음.

---

## 7. 개발 체크리스트 (양 팀 공통)

**백엔드(웹 세션)**
- [x] G1 FCM HTTP v1 전송 구현 (env-gated, graceful skip)
- [x] G2 `POST /devices` 토큰 등록 엔드포인트
- [ ] 배포 시 G1 활성화(google-auth + FCM env) + G3 worker 컨테이너 기동
- [x] OpenAPI 스펙 자동생성기(`api/scripts/gen_openapi.py`) — 라우트 변경 후 재생성하면 항상 일치
- [ ] 신규/변경 엔드포인트는 이 문서 §3 갱신 + `gen_openapi.py` 재생성 + 모바일 공지

**모바일(iOS/Android 세션)**
- [ ] §1 Base URL 환경분리 + dev 평문 예외(디버그만)
- [ ] §2 auth 인터셉터(401→refresh→재시도)
- [ ] §3 로그인 직후 `POST /devices`로 FCM/APNS 토큰 등록, 로그아웃 시 `DELETE /devices/{token}`
- [ ] §4 로컬 스키마를 sync 엔티티와 1:1 정렬 → G4 실단말 E2E
- [ ] §5 Enum/상수 하드코딩 금지, config 응답 사용
- [ ] **§3.0 화면/메뉴 구조**를 웹과 동일하게(기록입력 탭통합, 돈군, 할일·알림 2탭, 보고서 그룹). '분만사' 메뉴 만들지 말 것.
- [ ] **보고서 화면**: 번식(품종별 `group_by=breed` 토글) · 통합표(`production-summary`, 국가 기준값 대비 표시) · 비육 · 모돈이력. 국가분기 하드코딩 0.
- [ ] **알림 화면 2탭**(관리대상/시스템알림) + 통합 배지(`overdue.total + unread_count`).
- [ ] UI 아이콘 = 벡터(이모지 금지).

**공통**
- [ ] 계약 변경 = 이 문서 먼저 수정 → 커밋 → 양측 공지
- [ ] 릴리스 전 §6 갭 전부 closed 또는 "다음 버전" 명시 합의

---

## 8. 검증 분리 — "계약 1벌 + 플랫폼별 통합 2벌"

API/계약은 플랫폼 무관 → **공유 검증 1벌**. 단말 글루는 **iOS/Android 각각** 검증.

### 8a. 공유 계약 검증 (플랫폼 무관, 한 번만 — 라이브 API 대상)
1. auth: login → `Authorization: Bearer` → 401 시 refresh → 재시도
2. 농장/설정: `GET /farms/{id}/config` 단위·통화 수신, country별 KPI 분기
3. 모돈/이벤트: 모돈 목록·검색, 교배/분만/이유 POST→PATCH→DELETE(상태 롤백)
4. 할 일/알림: `GET /tasks`, `GET /notifications`(+unread_count), read/read-all
5. sync: `POST /sync` push/pull 왕복, 6개 엔티티 필드 매핑
6. devices: `POST /devices` 등록 → `DELETE /devices/{token}` 해제
7. **P0 검증(2026-06-19)**: 분만 TB=BA+SB+MUM·체중≤3 · 이유 항등식 422 · 이유체중 2~12 · 동일날짜 교배 409 · 웅돈 ACTIVE만 · 임신중 도폐사 사유필수 · 양자 거울레코드 자동(한쪽만 전송) · 비육 입식5~50/출하≤200. 클라 사전검증 + 422 메시지 노출 일치 확인.
8. **보고서(2026-06-19)**: `GET /reports/{sow-status,farrowing,mortality,data-quality}` 200·스키마 일치(§보고서). 빈/대량 농장 양쪽.

> 이 시나리오는 응답 JSON·상태코드 기준이라 iOS/Android 결과가 같아야 한다. 다르면 클라 글루 버그.
> 백엔드/웹 검증 현황: `docs/verification/qa_qc_2026-06-19.md` (ruff·tsc·i18n·build·pytest379·live30 그린, vitest는 Node<20.12 보류).

### 8b. 플랫폼별 글루 검증 (iOS / Android 각각)
| 검증 항목 | Android | iOS |
|---|---|---|
| dev 연결 | 에뮬 `10.0.2.2:8000` 도달 | 시뮬 `localhost:8000` 도달 |
| 평문 허용(디버그) | `usesCleartextTraffic` 적용 | ATS `NSAllowsLocalNetworking` |
| 토큰 갱신 인터셉터 | OkHttp Authenticator | URLSession retry / Alamofire |
| 푸시 등록 | FCM 토큰 → `POST /devices {platform:"ANDROID"}` | APNS→FCM → `{platform:"IOS"}` |
| 오프라인 저장 | Room ↔ sync 엔티티 1:1 | CoreData ↔ sync 엔티티 1:1 |
| 백그라운드 sync | WorkManager 주기/재시도 | BGTaskScheduler |
| G4 E2E | 비행기모드 입력→복귀→sync 왕복 | 동일 시나리오 |

### 결론
- **계약(8a)**: 변경 시 이 문서 기준으로 양 플랫폼이 동일 결과 확인 → 공유.
- **글루(8b)**: 네트워크 설정·푸시·로컬DB·백그라운드는 OS API가 달라 **반드시 별개 검증**.
- 릴리스 게이트: 8a 공통 통과 + 8b를 iOS·Android **각각** 통과.
