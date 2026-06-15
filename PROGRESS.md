# PigOS 진행 상황

## [야간스프린트 시작 2026-06-15 / DB_OK=false (partial)]
- 환경: Cowork 샌드박스(리눅스). Docker/Postgres/psql 없음, root 불가 → 운영 DB·테스트 DB 연결 불가.
- 그러나 시스템 Python 3.10 + `datetime.UTC` shim(/tmp/shim, 저장소 미변경)으로 **import-smoke + unit 테스트 실제 실행 가능**.
- 베이스라인 green: `import app.main` OK / unit **219/219 pass** / ruff clean / `tsc --noEmit` EXIT 0.
- 검증 게이트(이번 스프린트): ruff + tsc + import-smoke + unit pytest. **통합(integration)·Alembic은 DB 필요 → 사용자 머신에서 `uv run pytest tests/` 재검증 필요.**
- 작업 트리 노트: 윈도우 마운트로 ~101개 파일이 CRLF 노이즈로 표시됨. 실제 WIP는 settings/users·login·onboarding·members.ts 4개(사용자 작업, 미변경 유지). 커밋 시 건드린 파일만 LF 정규화 후 add.

## 2026-06-15 야간스프린트 — N1 알림 영구화 Producer (P12-6 백엔드)
- [x] `notification_service.create_from_alerts(db, farm_id, today=None)` — 과기한 모돈(6유형)+도태권고+KPI(WARNING/CRITICAL) → OWNER/MANAGER 멤버에게 IN_APP Notification 적재. KPI 집계 실패는 격리(try/except)하여 과기한/도태 알림은 계속 생성.
- [x] 멱등성: 같은 (user_id, alert_type, related_entity_id) 미읽음 알림 존재 시 재생성 안 함. related_entity_type/id 채워 클릭 이동 가능.
- [x] 수신자: user_farms 조인, 유효역할=COALESCE(role_override, system_role)∈{FARM_OWNER,FARM_MANAGER}, 활성 유저.
- [x] `POST /api/v1/farms/{farm_id}/notifications/generate` (farm_router 분리, require_role OWNER/MANAGER/SUPER_ADMIN) — OpenAPI 등록 확인.
- [x] 통합 테스트 `tests/integration/test_notification_producer.py` (생성/멱등/수신자없음 3케이스) 작성.
- 검증: ruff clean / import-smoke OK / unit 219/219 / 라우트 OpenAPI 등록 확인. **integration은 DB 필요 → 사용자 머신 재검증.** [degraded: no-db]

## 2026-06-15 야간스프린트 — N2 웹 알림 페이지 연동 (P12-6 프론트)
- [x] `lib/api/endpoints/notifications.ts` (list/markRead/markAllRead) + api.types.ts(NotificationItem/ListResponse/MarkReadResult) + queryKeys.notifications.
- [x] notifications/page.tsx: 실시간 KPI 알림 유지 + 영구 알림 섹션(개별 읽음/전체읽음/미읽음 필터/related_entity 클릭 이동/더보기 페이지네이션).
- [x] 배지 unread 연결: Sidebar(/notifications 항목 unread 배지) + Topbar Bell(alertCount=unread, onBell→/notifications) + BottomNav(alertCount=unread).
- [x] i18n 5개 언어 +9키(realtimeSection/savedSection/markAllRead/filterUnread/savedEmpty/unreadBadge/markRead/loadMore/realtimeEmpty). 전수 정합성 873키 일치.
- 검증: tsc --noEmit EXIT 0 / i18n 5×873 일치.

## 2026-06-15 야간스프린트 — N3 Task/알림 잡 자동화 (ARQ)
- [x] `jobs/tasks.py::generate_tasks_job` — 전 활성 농장 순회 → task_service.generate_tasks (멱등). 농장별 오류 격리.
- [x] `jobs/notifications.py::generate_notifications_job` — 전 활성 농장 순회 → notification_service.create_from_alerts (멱등).
- [x] worker.py cron 등록: tasks 05:30 UTC, notifications 06:00 UTC (cron 5개, functions 6개).
- 검증: ruff clean / import-smoke(WorkerSettings 로드·잡 등록 확인) / unit 219/219. [degraded: no-db — 실제 잡 실행은 DB+Redis 필요]

## 2026-06-15 야간스프린트 — N4 PRRS 유전자 성과 추적 (Phase 2)
- [x] 선행 스키마 확인: health_events(disease_code) + sow.breed/breed_company/genetics_id 모두 존재 → 구현 진행.
- [x] `analytics_service.prrs_by_genetics(db, farm_id)` — 품종/유전자 그룹별 전체모돈 × PRRS(disease_code ILIKE 'PRRS%') 집계, 발생률(affected/total*100) 계산, 발생률 내림차순.
- [x] `GET /api/v1/farms/{farm_id}/analytics/prrs-by-genetics` + schemas/analytics.py + main.py 등록.
- [x] 통합 테스트 `tests/integration/test_prrs_analytics.py` (PRRS 집계/비-PRRS 제외/발생률).
- 검증: ruff clean / import-smoke / 라우트 OpenAPI 등록 / unit 219/219. [degraded: no-db — integration은 사용자 머신 재검증]

## 2026-06-15 야간스프린트 — N5 프론트 스모크 테스트 (Phase 13 연장)
- [x] `lib/utils/csv.ts` 공용 CSV 유틸(toCsv/downloadCsv) 추출 + reports reproduction·grow-finish 페이지 연결(동작 동일, 무회귀).
- [x] `tests/utils/csv.test.ts` (toCsv 3케이스), `tests/components/RecentEventsSection.test.tsx` (제목/빈상태), `tests/pages/tasks.test.tsx` (제목/allClear). next-intl 모킹으로 견고화.
- 검증: tsc --noEmit EXIT 0 (리팩터 페이지+신규 테스트 타입 통과). 
- ⚠ **vitest 실행 불가(샌드박스)**: node_modules가 윈도우용 + vitest4 rolldown 네이티브 바이너리가 Bus error(core dumped). 리눅스 바이너리 추가해도 크래시. → **사용자 머신에서 `npm run test` 실행 필요.** [exec-blocked: sandbox]

## 현재 작업
**MVP 스프린트 진행 중** — 디자인 구현 + Rule Engine DB화 완료

## UI Shell 체크리스트

- [x] `globals.css` 라이트 테마 CSS 변수 토큰 (`bg-surface`, `text-text`, `border-border`, `bg-navy` 등)
- [x] `src/components/Sidebar.tsx` — props: `{ lang?, onAskAI? }`, collapsed 내부 state
- [x] `src/components/Topbar.tsx` — props: `{ lang?, onLangToggle?, onQuickInput?, onBell?, alertCount? }`
- [x] `src/components/BottomNav.tsx` — props: `{ lang?, onAskAI?, alertCount? }`, md:hidden
- [x] `src/components/QuickInputDrawer.tsx` — props: `{ open, onClose, lang? }`
- [x] `src/components/AskAiDrawer.tsx` — props: `{ open, onClose, context?, lang? }`
- [x] **7단계: Shell 통합** — `(app)` 라우트 그룹 신설 + 파일 이동 + `(app)/layout.tsx` 작성
  - [x] `src/app/(app)/layout.tsx` 생성 (lang/collapsed/askAiOpen/quickInputOpen 상태 보유)
  - [x] 페이지 8개 `(app)/`로 이동 + 각 페이지에서 `<Sidebar>` + `ml-[220px]` wrapper 제거
  - [x] `Sidebar` 의 `/dashboard` 링크를 `/`로 수정
  - [x] `BottomNav` 의 `/dashboard` 링크를 `/`로 수정
  - [x] `Sidebar` 에서 collapsed 상태를 Shell로 lift-up + `hidden md:flex` 모바일 대응
- [x] **8단계: 검증·커밋** — `tsc --noEmit` 통과 (기존 badge 타입 에러 포함 수정) + commit 완료
- [x] **백엔드 /chat 엔드포인트** 연결 확인 + 프론트-백 타입 계약 완전 일치
- [x] **Record 페이지 리디자인** — Event Flow 레이아웃 (좌: 모돈 목록+검색, 우: 이벤트 드로어), 분만 스테퍼+자동계산+난이도+양자조정
- [x] **Essential 페이지 10종** — /legal, /verify-email, /settings/(profile·billing·delete-account), /announcements, /support, /maintenance, /update
- [x] **Rule Engine DB화** — `default_metric_values`에 warning/critical/direction 컬럼 추가, `effective_metric_values()` 업데이트, KR/US/BR/CN/VN 5개국 시드, base.py 하드코딩 완전 제거, 76/76 unit test pass
- [x] **KPI trend 엔드포인트** — GET /kpi/trend (월별 PSY/NPD/FR), unit 15개 추가, 91/91 pass
- [x] **Weaning 버그 수정** — farrowing_id Optional 처리 + 최근 분만 자동 조회
- [x] **모돈 도폐사 관리** — removals 테이블 + cull_sow (AuditLog 연동) + GET /sows/removals 이력 조회
- [x] **Supabase 운영 DB 마이그레이션** — SQL Editor로 전체 스키마(e3f9a2b4c8d1) 적용 완료
- [x] **번식기록 6종 완성** — 교배/분만/이유/임신사고/도폐사/포유자돈폐사 API 연동 + CullPanel 필드 수정
- [x] **포유자돈폐사 API** — POST/GET /events/piglet_events, farrowing_id 자동조회, AuditLog
- [x] **웅돈관리** — /boars 페이지 + boarsApi 신규, Sidebar 메뉴 추가
- [x] **Sidebar 메뉴 추가** — /record, /kpi, /chat, /boars(웅돈) 추가 (총 10개 메뉴)
- [x] **/farrowing · /reports 페이지** — API 연결 완료 (이전 세션에서 완성됨 확인)
- [x] **Codex 교차검증 체크리스트** — `docs/CODEX_VALIDATION.md` (8개 섹션, P0~P2 우선순위)
- [x] **sync piglet_events 푸시** — SyncChanges.piglet_events + _process_piglet_event()
- [x] **sync removals 풀** — ServerChanges.removals + _pull_server_changes() 보완
- [x] **api.types.ts 보완** — SyncPigletEvent, SyncChanges.piglet_events, ServerChanges.removals
- [x] **/notifications 페이지** — KPI 알림 목록 (CRITICAL/WARNING/INFO/OK 구분, dashboard.alerts 연동)
- [x] **/addons 페이지** — Addon 스토어 (8종 카드, AI Insight Beta + 출시예정 7종)
- [x] **/reports 페이지 강화** — SVG 바차트 + 차트/표 전환, KPI 카드 클릭으로 트렌드 전환
- [ ] **다음**: i18n (5개 언어), 배포 (Vercel/AWS)

## 전략 메모 (월간 보고 포함 대상)

### pigos.io 랜딩페이지
- 아직 미존재 — 별도 Next.js 프로젝트로 신규 생성 필요
- blog-pigos는 블로그 파이프라인, blog-pigsignal은 pigsignal 블로그 (별개)
- 언어: en/ko 우선 출시 → zh/es/vi 순차 추가 (번역 품질 주의)
- 구성: Hero + Features + Pricing + CTA + 시장별 현지화

### SEO / 유입 전략
- 타겟 키워드: "pig farm management software", "양돈 관리 프로그램", "软件猪场管理", "phần mềm quản lý trang trại heo" 등 시장별
- 콘텐츠 마케팅: blog-pigos 파이프라인 활용 가능
- 지역별 검색엔진: 중국(바이두), 베트남/동남아(구글), KR(네이버+구글)
- 결정 필요: 도메인 구조 (pigos.io/ko vs pigos.io?lang=ko vs ko.pigos.io)

## Phase 2 예정 항목

### 다국어 (i18n)
- **랜딩페이지 (blog-pigos)**: en/ko 우선 출시 → zh/es/vi/th/id 순차 추가
  - 필리핀은 영어 공용어라 en으로 커버 가능
  - 번역 품질 주의 (기계번역 그대로 쓰면 역효과)
- **앱 내 언어 확장**: 백엔드 이미 en/ko/es/zh 지원, 프론트 lang 타입은 en/ko만 연결됨
  - zh/es 추가 시: Topbar 토글 드롭다운으로 전환 + 컴포넌트 라벨 번역 필요
  - vi/th는 백엔드 locale 확장부터 필요

## 완료된 스프린트 항목 (MVP)

- DB 스키마 v2.1, Alembic 마이그레이션 (40테이블) 완료
- Rule Engine + Q&A API 완료
- KPI Snapshot 잡 (ARQ) 완료
- 오프라인 동기화 프로토콜 완료
- OpenAPI 3.1 스펙 v1 완료
- Docker Compose 로컬 개발환경 완료
- Next.js 15 프론트엔드 기반 완료
- API Contract 검증 + 수정 완료 (unit 43/43 pass)

## 2026-06-10 (저녁) — 상태 코드 v2 + CRUD 완성
- [x] **모돈 상태 코드 v2** — GILT/OPEN/PREGNANT/LACTATING/ACCIDENT (SCREEN_MENU_SPEC 정렬, Alembic d2a8c5e7f1b3, 건유(DRY) 제거, 웹/모바일 이유 전이 불일치 수정, 테스트 106/106)
- [x] **모돈 수정/도폐사·판매 UI** — 수정 모달 + 도태/폐사/판매/전출 모달 (사유 9종)
- [x] **웅돈 CRUD** — 등록/수정/상태변경 완성
- [x] **/settings 허브 페이지** — 계정/농장/지원/기타 섹션
- [x] **Sidebar 개편** — 공식 로고 + lucide 아이콘 + 그룹핑(돈군관리/기록/분석) + 5개 언어 현지 용어
- [x] **로그인/온보딩 라이트모드** — 공식 로고, 2단 레이아웃, 5개 언어 (기본 ko)
- [x] **Addon 스토어 리디자인** — Data Dividend 히어로 + 카테고리 필터
- [x] **가입 500 해결 검증** — onboarding/complete, auth/register 둘 다 201 실측

## 2026-06-10 — Phase 1 이벤트 입력 검증 (Backend Validators) 완료
- [x] **[P1-1]** `app/validators/base.py` + `__init__.py` — ValidationError(422) 재사용 + 날짜 헬퍼
- [x] **[P1-2]** `validators/farrowing.py` — TB<=35, SB/MUM<=25, BA<=TB, 암수합, 체중<=3.0kg (12 tests)
- [x] **[P1-3]** `validators/weaning.py` — 이유두수 항등식 weaned=nursing-(deaths+out-in) (7 tests)
- [x] **[P1-4]** `validators/mating.py` — 상태 GILT/OPEN/ACCIDENT + 웅돈 순차 (9 tests)
- [x] **[P1-5]** `validators/cross_fostering.py` — 양자 <=25/transfer (3 tests)
- [x] **[P1-6]** `validators/date_rules.py` — 입식/제거 경계 + 교배/분만/이유 순서 (12 tests)
- [x] **[P1-7]** `event_service.py` 연결 — mating/farrowing/weaning/piglet 처리 전 validator 호출
- 검증: unit 134/134 pass (기존 91 + 신규 43). 샌드박스 Python 3.10 + UTC shim 환경.

## 2026-06-10 — Phase 2 모돈 상태 전이 + 알람 (Backend)
- [x] **[P2-1]** `validators/sow_state.py` — ALLOWED_TRANSITIONS 전이 강제 (17 tests)
- [x] **[P2-3]** `services/alert_service.py` — 6 과기한 유형 + 3 도태기준, farm_configs 임계값 (pure classify, 20 tests)
- [x] **[P2-4]** `routers/base/alerts.py` + `schemas/alert.py` — GET /alerts/overdue, /alerts/cull-candidates, main.py 등록
- 검증: unit 171/171 pass, FastAPI 앱 빌드 + 라우트 등록 확인. (P2-2 상태코드 v2는 기완료)

## 2026-06-10 — Phase 3 Rule Engine 확장 (Reproduction Rules)
- [x] **[P3-2]** Finding.grade 필드 + psy_grade 헬퍼(Excellence/Advanced/Stable/Developing), psy.below_target에 부착 (severity는 벤치마크 기반 유지)
- [x] **[P3-1]** `engine/rules/reproduction.py` — wsi.overdue(10/14), rts.rate_high(15/25), pwmr.high(15/20, method A/B), 벤치마크 오버라이드 가능
- [x] **[P3-3]** `tests/unit/test_reproduction_rules.py` — 경계값 17 cases
- 검증: unit 188/188 pass, 규칙 8종 등록 확인.

## 2026-06-10 — Phase 4 프론트엔드 (부분: P4-1/P4-4/P4-5)
- [x] **[P4-1]** `/alerts` 페이지 + alertsApi + 타입 + queryKeys + Sidebar 메뉴 (요약카드/테이블/도태권고, /record 링크)
- [x] **[P4-4]** 대시보드 관리대상 모돈 카드 + /alerts 링크 + 도태권고 건수
- [x] **[P4-5]** QuickInputDrawer 이모지 → lucide-react 아이콘
- 검증: npx tsc --noEmit 통과(EXIT 0). (P4-2 모돈수정모달 기완료, P4-3 상세페이지·P4-6 record 모바일은 후속)

## 2026-06-10 — Phase 7 보고서 API (Reports Backend)
- [x] **[P7-1/2/3]** `services/report_service.py` — 번식(기간 버킷팅: 월/분기/연), 비육(ADG/FCR/폐사율), 모돈 이력(산차별 사이클) 순수 빌더 + DB 래퍼
- [x] **[P7-4]** `schemas/report.py` + `routers/base/reports.py` — /reports/reproduction·grow-finish·sows/{id}/history, >2년 400, main.py 등록
- 검증: unit 199/199 pass, 3개 라우트 등록 확인. (스냅샷 스키마가 얇아 이벤트 테이블 직접 집계)

## 2026-06-10 — Phase 14 Addon #1 AI Insight (LLM Renderer)
- [x] **[P14-1]** `engine/llm_renderer.py` — 벤더 중립, lazy SDK, 템플릿 폴백(키없음/use_llm=False/쿼터초과)
- [x] **[P14-2]** `chat_service.py` — use_llm/usage_count 파라미터 + rendered_by 반환
- [~] **[P14-3]** 쿼터 폴백(within_quota) 구현 완료; 영속 llm_usage_logs 테이블/마이그레이션은 DB 필요로 deferred
- 검증: unit 206/206 pass (외부 API 호출 없음 — 폴백 경로만 테스트)

## 2026-06-10 — Phase 8 설정 페이지 (Settings)
- [x] **[P8-1]** 백엔드 `GET/PATCH /farms/{id}/config/repro` (resolve_repro_config + 범위검증, unit 8) + 프론트 `/settings/farm` 폼
- [x] **[P8-2]** `/settings/benchmarks` — 국가별 KPI 참고표 + 현재 농장 설정값
- [x] **[P8-3]** settings 허브에 번식설정/벤치마크 링크 추가
- 검증: backend unit 214/214, frontend tsc clean

## 2026-06-10 — Phase 11 배포 준비 + Phase 5 i18n 감사
- [x] **[P11-1]** `src/.env.example` + `api/.env.example`에 LLM/Sentry 옵션 키
- [x] **[P11-2]** `src/vercel.json` (nextjs, icn1)
- [x] **[P11-4]** `.github/workflows/ci.yml` (ruff+pytest+tsc+build, PR→development, 수동 배포)
- [x] **[P11-5]** `docs/DEVELOPMENT.md` 로컬 온보딩 가이드
- [P11-3] Dockerfile/compose/`/health` 기존 존재 확인
- [x] **[P5-4]** i18n 키 정합성 감사 — 5개 언어 × 98키 완전 일치(누락/초과 0) 스크립트 검증

## 2026-06-10 — Phase 12 CRUD (백엔드)
- [x] **[P12-1 백엔드]** events PATCH/DELETE (matings/farrowings/weanings) + 상태 롤백(rollback_status_on_delete, 5 tests) + period_locks 423 + 다운스트림 가드
- [x] **[P12-3 백엔드]** finishers PATCH (FinisherGroupUpdate)
- 잔여(프론트): P12-1/2 이벤트 수정·삭제 UI, P12-3 그룹 수정 모달, P12-4 페이지네이션, P12-5 CSV, P12-6 알림 개선
- 검증: backend unit 219/219 (event_rollback 5 신규), 라우트 등록 확인

## 2026-06-10 — Phase 9 보고서 화면 + Phase 12 프론트 API
- [x] **[P9-1]** `/reports/reproduction` — Phase 7 API 연동, 기간 프리셋(3/6/12개월), 월별 테이블(교배/분만/이유/FR/총산/생존산/이유두수/PWMR-A·B/RTS), CSV 내보내기
- [x] **[P9-2]** `/reports/grow-finish` — 그룹별 ADG/FCR/폐사율 테이블 + CSV
- [x] **[P12-5 일부]** 보고서 CSV 클라이언트 내보내기 (BOM 포함 한글 호환)
- [x] **[P12-1/3 프론트 API]** eventsApi update/remove, finishersApi update + 타입
- Sidebar 분석 그룹에 번식/비육 보고서 링크 추가. tsc clean.

## 2026-06-10 — Phase 9-3 / Phase 12-3 프론트
- [x] **[P9-3]** `/finishers` 그룹 수정 모달 추가 (EditGroupModal, finishersApi.update 연동) — 목록/입식/출하/수정 완비
- 검증: tsc clean

## 2026-06-10 — Phase 12/4 프론트 마무리 배치
- [x] **[P12-4]** finishers 페이지네이션 (boars+finishers 완료)
- [x] **[P12-6]** notifications 심각도 필터 탭 (전체/위험/주의/정보)
- [x] **[P4-6]** /record 모바일 상하 스택 레이아웃 (반응형)
- 검증: tsc clean (5개 커밋 연속)

## 2026-06-10 — Phase 12/5/10 연속 배치
- [x] **[P12-2]** 모돈 상세 이벤트 삭제+롤백 UI (eventsApi.remove, 확인 다이얼로그)
- [x] **[P5-2]** 5개 언어 sowStatus i18n 키 (정합성 105키 유지)
- [x] **[P10-2]** 검증 오류 E2E 통합 테스트 7케이스 (수집 OK, Docker DB 실행)
- [x] **[P10-3]** 알람 서비스 통합 테스트 4케이스 (today= 결정적, 수집 OK)
- 통합 테스트는 샌드박스에 Docker Postgres 없어 '수집/구문 검증'까지 — 사용자 머신 `uv run pytest tests/` 실행 필요
- 검증: unit 219/219, tsc clean

## 2026-06-10 — Phase 10 통합 테스트 (4파일 13케이스)
- [x] **[P10-1]** test_full_breeding_cycle — 2산차 상태전이 + 이유두수 가드
- [x] **[P10-2]** test_validation_errors — validator 7케이스
- [x] **[P10-3]** test_alert_service — 과기한/도태 4케이스 (today= 결정적)
- [x] **[P10-4]** test_reports — 번식 월별집계 + 비육 ADG/폐사율
- [x] **[P6-1]** 통합 테스트 기반 (conftest db/client fixture 기존 + 위 4파일 추가)
- 모두 pytest 수집 통과. 실행은 사용자 머신 `cd api && uv run pytest tests/`(Docker pigos_test 필요).

## 2026-06-10 — Phase 9-4 / Phase 5 i18n 완료
- [x] **[P9-4]** Sidebar Alerts 실시간 과기한 배지 (5분 refetch)
- [x] **[P5-1]** alerts i18n 키 5개 언어 (title + 6유형 + 도태)
- [x] **[P5-3]** validation 422 메시지 i18n 키 5개 언어
- 검증: 5개 언어 정합성 123키, tsc clean

## 2026-06-10 — 잔여 일괄 완료 (Phase 6/11/13/14)
- [x] **[P6-2]** vercel.json (P11-2 동일), **[P6-3]/[P11-3]** 프로덕션 Dockerfile(non-root+healthcheck) + dev compose --reload
- [x] **[P14-3]** llm_usage_logs 모델 + 마이그레이션 + usage 서비스 (런타임 쿼터 폴백 기존)
- [x] **[P13-1/2/3/4]** Vitest config+setup+test-utils + 컴포넌트(QuickInputDrawer/Sidebar) + 페이지(alerts) 스모크 테스트
  - ⚠ 샌드박스 npm install 차단(마운트 ENOTEMPTY) → 사용자 머신에서 `npm i -D vitest jsdom @vitejs/plugin-react @testing-library/{react,jest-dom,user-event}` 후 `npm test`
- **자율 플랜 54/54 항목 처리 완료.** backend unit 219/219, tsc clean, 통합테스트 수집 통과.
