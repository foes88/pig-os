# PigOS 진행 상황

## 현재 작업
**UI Shell 통합** — 7단계 진행 중 (A안: `(app)` 라우트 그룹 신설)

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
- [ ] **백엔드 /chat 엔드포인트** 존재 확인 (`chatApi.query` → FastAPI `POST /api/v1/farms/{farm_id}/chat/query`)

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
