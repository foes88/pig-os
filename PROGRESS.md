# PigOS 진행 상황

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
