# PigOS

> Global Swine Farm Management SaaS + Data Monetization Platform
> 피그플랜 27년 양돈 노하우 기반 글로벌 버전

---

## 세션 프로토콜 규칙

1. **세션 시작 시** CLAUDE.md + PROGRESS.md를 읽고 현재 상태를 3줄 이내로 요약 보고
2. **태스크 완료마다** PROGRESS.md 현재상태 갱신 후 `git commit`
3. **컨텍스트가 커지면** 사람에게 `/clear` 권유 (대화가 길어져 응답이 느려지거나, 한 세션에서 대형 태스크 3개 이상 완료 시)
4. **UI 텍스트 추가/변경 시** `src/messages/` 아래 **en/ko/zh/es/vi 5개 파일 모두** 동시 업데이트 (누락 금지)

---

## 프로젝트 개요

- **제품**: PigOS — 해외 양돈 농장용 Farm Management SaaS
- **도메인**: **pigos.io** (2026-05-18 구매 확정)
- **포지셔닝**: 벤더-중립 독립 데이터 플랫폼 + 오픈 연동 생태계
- **전략**: 무료 제공 → 데이터 수집 → 수익화 → 농가 배분
- **타겟**: 5개 시장 (US/CN/SEA/LatAm/KR)

---

## 기술 스택 (MVP)

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python) → Phase 2+ Spring Boot (Java 21) |
| Frontend | Next.js + TypeScript |
| Mobile | React Native (Android + iOS 공용) |
| DB | PostgreSQL 16+ (Shared Schema + farm_id) + TimescaleDB (IoT) |
| Cache | Redis 7+ |
| Infra | AWS (싱가포르 리전) + Docker + Kubernetes |
| Offline Sync | WatermelonDB (모바일 로컬 SQLite) |
| Background Jobs | ARQ (Redis 기반) |

---

## 폴더 구조

```
pig-os/
├── CLAUDE.md           ← 이 파일
├── docs/
│   ├── specs/          ← DB 스키마, KPI 계산식, API 스펙
│   ├── master-data/    ← 시드 데이터 (질병코드, 백신, 벤치마크)
│   └── api/            ← OpenAPI 스펙
├── api/                ← 백엔드 소스 (FastAPI, uv) — app/engine, app/jobs, alembic
├── src/                ← 프론트엔드 (Next.js 15, npm)
└── tests/              ← 테스트
```

---

## 핵심 설계 원칙

1. **모듈형 구조**: 11개 모듈 독립 배포 가능 (49 테이블)
2. **지역 중립**: 단일 스키마로 5개 시장 커버 (country_configs)
3. **Multi-tenant Strategy**: Shared Database / Shared Schema
   - 모든 테넌트 범위 테이블은 반드시 `farm_id` 컬럼 포함
   - 접근 제어는 organization hierarchy + farm membership + row-level filtering으로 강제
   - 향후 엔터프라이즈 고객 요청 시 schema-per-tenant를 선택적 프리미엄 아키텍처로 검토 가능
4. **월마감 잠금**: `period_locks`로 확정 데이터 수정 차단
5. **감사 추적**: 모든 CUD → `audit_log`
6. **오프라인 동기화**: `sync_queue` + WatermelonDB (Last-Write-Wins)
7. **Soft Delete**: `deleted_at` 패턴 (모든 핵심 테이블)
8. **API 버전 관리**: `/api/v1/` URL prefix 고정 (헤더 방식 사용 안 함)

---

## Q&A Architecture Decision

PigOS Q&A는 Rule-grounded 아키텍처를 사용한다.

```
사용자 질문
    ↓
Intent 분류
    ↓
KPI / 이벤트 / Rule / Snapshot 조회
    ↓
Rule Engine → Structured Result 생성
    ↓
Renderer (Base: 템플릿 | Addon #1: LLM)
    ↓
사용자 응답
```

| 구분 | MVP / Base | Addon #1 (AI Insight) |
|------|-----------|----------------------|
| 엔진 | Rule Engine only | Rule Engine + LLM |
| 응답 | 정형 텍스트 (템플릿) | 자연어 설명 |
| 비용 | 없음 | LLM API 비용 발생 |
| 목적 | 기능 검증 | 유료 가치 제공 |

**핵심 원칙**:
- LLM은 **판단 금지** — 검증된 Rule Engine 결과를 자연어로 변환하는 역할만 수행
- Rule Engine은 항상 `Structured Result` (JSON)를 생성하고, Renderer가 응답 형태를 결정
- LLM 벤더 교체 (Claude ↔ GPT-4o) 시 Rule Engine 코드 변경 없이 Renderer만 교체 가능

**Structured Result 예시**:
```json
{
  "intent": "explain_fcr",
  "severity": "warning",
  "kpi": "FCR",
  "current_value": 3.12,
  "target_value": 2.85,
  "causes": [
    "feed_intake_increased",
    "daily_gain_decreased",
    "mortality_increased"
  ],
  "recommended_actions": [
    "check_feed_waste",
    "review_group_health",
    "compare_finisher_group_performance"
  ]
}
```

**통신 방식**: MVP는 REST (`POST /api/v1/farms/{farm_id}/chat/query`), 추후 WebSocket 추가

**구현 위치**:
- `api/app/engine/rule_engine.py` — RuleContext, Finding, StructuredResult, RuleRegistry, RuleEngine
- `api/app/engine/rules/base.py` — Base 규칙 (NPD/PSY/Farrowing/Inventory)
- `api/app/engine/renderer.py` — Template Renderer (en/ko) — Addon #1에서 LLM으로 교체
- `api/app/services/chat_service.py` — intent 분류 + RuleEngine 호출
- `api/app/routers/base/chat.py` — HTTP 엔드포인트

---

## KPI 계산 전략

| 용도 | 방식 |
|------|------|
| 대시보드 첫 화면 | `kpi_snapshots` 테이블 조회 (스냅샷) |
| 월간 리포트 | 스냅샷 |
| Q&A 분석 | 스냅샷 우선 + 필요 시 실시간 상세 조회 |
| 개별 이벤트 상세 | 실시간 계산 |
| 데이터 수정 직후 | 해당 기간 스냅샷 즉시 재계산 |

**백그라운드 잡 (ARQ)**:
- `daily_kpi_aggregation` — 매일 00:00
- `weekly_kpi_aggregation` — 매주 월요일
- `monthly_kpi_aggregation` — 매월 1일
- `recalculate_snapshot_on_event_change` — 이벤트 변경 시 트리거

---

## 기획 문서 (biz-report-os 프로젝트)

심층분석 기획서 및 회의 자료는 별도 프로젝트에서 관리:
- `c:/dev/biz-report-os/projects/pig-os/docs/`
- GlobalStrategy.html (심층분석 16개 섹션)
- Meeting2_Prep.html (2차 회의 준비)
- 참고문서/ (지역별 관리포인트, 경쟁사 분석, 개발반영사항)

---

## 다음 할 일

- [x] DB 스키마 v2.1 보완 (`period_locks`, `kpi_snapshots`, `finisher_groups`, `api_keys`, `notifications`, `sync_logs`)
- [x] `/api/v1` prefix 전체 반영
- [x] KPI 계산 공식 확정 (PSY/NPD/FCR 엣지케이스) — `docs/specs/2026-03-19_kpi-calculation-specs.md`
- [x] Rule Engine 구축 (`api/app/engine/`) — RuleRegistry + base rules (NPD/PSY/Farrowing/Inventory)
- [x] Rule-grounded Q&A API (`POST /api/v1/farms/{farm_id}/chat/query`) — Template Renderer (Addon #1에서 LLM으로 교체 가능)
- [x] 마스터 데이터 시드 완성 — `docs/master-data/2026-05-19_seed-v2.sql` + ORM models (`api/app/db/models/master.py`) + 러너 (`api/scripts/seed_master.py`)
- [x] KPI Snapshot 잡 설계 (ARQ) — `api/app/jobs/kpi.py` + `worker.py` (daily/weekly/monthly cron)
- [x] 오프라인 동기화 프로토콜 설계 (`POST /api/v1/farms/{farm_id}/sync`) — 스펙 `docs/specs/2026-05-19_offline-sync-spec.md` + 구현 완료
- [x] OpenAPI 3.1 스펙 v1 — `docs/api/openapi-v1.yaml`
- [x] Docker Compose 로컬 개발환경 — `docker-compose.yml` (postgres + redis + api)
- [x] 프론트엔드 기반 — Next.js 15 + Zustand + TanStack Query + axios + next-intl + /login 페이지
- [x] **Alembic 마이그레이션 생성 + DB 적용** — 40테이블 Docker PostgreSQL 적용 완료
- [x] **API Contract 검증 + 수정** — 프론트-백 계약 7종 수정, 코드리뷰 버그 8종 수정, unit 43/43 pass
- [ ] **MVP 스프린트 완료 (7/1 출시)** — /dashboard, /chat, Sidebar 완성, i18n, 배포

---

## Phase 2 기능 (MVP 이후)

### Task 자동배정 시스템 (노동력 절감)
> 출처: National Hog Farmer 2026-05-20 — AI 기반 노동력 절감이 양돈 산업 핵심 혁신 요소

```
Rule Engine Alert → Task 자동생성 → 담당자 배정 → 모바일 알림 → 완료 체크
```

- DB: `tasks` 테이블 (farm_id, assigned_to, rule_id, due_at, completed_at, priority)
- 모바일: "오늘 할 일" 홈 화면 (아침에 앱 열면 자동 목록)
- 예시: A-042 분만 115일 초과 → 수의사에게 자동 Task 발송

### PRRS 유전자 성과 추적
- `sow.breed` + `health_events.disease_code` 연결 → 품종별 PRRS 발생률 비교 분석

### Traceability Addon (소비자 투명성)
- 농장 이벤트 → 도축장 코드 → 소비자 QR 스캔 이력 추적
- B2B 데이터 판매 프리미엄 버전

---

## 🤖 자율 실행 지침 (Claude Code Autonomous Mode)

> 이 섹션은 Claude Code가 사람 없이 혼자 작업할 때의 지침입니다.
> `claude --dangerously-skip-permissions -p "자율 실행"` 으로 실행됩니다.

### 실행 원칙
1. **위 "다음 할 일" 목록을 위에서부터 순서대로 진행**한다
2. 각 태스크 완료 시 즉시 `git commit` (메시지: `feat: [태스크명]`)
3. 불확실한 사항은 **최선의 판단**으로 진행 — 멈추지 않는다
4. 외부 API 호출, DB 실데이터 변경, 배포는 하지 않는다
5. 작업 완료 후 `PROGRESS.md` 에 오늘 한 일 요약을 업데이트한다

### 작업 완료 기준
- 코드 작성 + 기본 동작 확인 가능한 수준
- TypeScript/Python 타입 에러 없을 것
- 각 태스크마다 git commit 1개 이상

### 금지 사항
- `git push` 금지 (사람이 확인 후 직접 push)
- 실제 DB (Oracle PKSU) 데이터 변경 금지
- AWS 리소스 생성/변경 금지

---

## 프론트엔드 구조 & 컨벤션

### 폴더 배치 (실제 확인, 2026-06-04 기준)

```
src/
├── app/
│   ├── layout.tsx               ← 루트: Providers(next-intl + TanStack + auth 인터셉터)
│   ├── globals.css              ← 라이트 테마 CSS 변수 토큰
│   ├── providers.tsx
│   ├── page.tsx                 ← 루트 "/" = 대시보드 (현재 Sidebar 직접 import, Shell 이전 예정)
│   ├── (auth)/
│   │   ├── layout.tsx           ← 로그인 전용 centered 레이아웃 (#0F1B2D 배경)
│   │   └── login/page.tsx
│   ├── onboarding/page.tsx      ← Shell 없는 독립 페이지 (다크 배경 #0F172A)
│   ├── kpi/page.tsx
│   ├── chat/page.tsx
│   ├── sows/page.tsx
│   ├── sows/[id]/page.tsx
│   ├── finishers/page.tsx
│   ├── piglets/page.tsx
│   └── record/page.tsx
├── components/
│   ├── Sidebar.tsx              props: { lang?: "en"|"ko", onAskAI?: () => void } — collapsed 내부 state
│   ├── Topbar.tsx               props: { lang?, onLangToggle?, onQuickInput?, onBell?, alertCount? }
│   ├── BottomNav.tsx            props: { lang?, onAskAI?, alertCount? } — md:hidden 고정
│   ├── QuickInputDrawer.tsx     props: { open: boolean, onClose: () => void, lang? }
│   ├── AskAiDrawer.tsx          props: { open: boolean, onClose: () => void, context?, lang? }
│   └── ui/                      ← Stat, AIBubble, AIAction, Card, PipeItem 등 공용 UI
├── store/
│   └── auth.store.ts            Zustand + persist(localStorage). 필드: user(UserProfile|null), accessToken, refreshToken, activeFarmId
├── lib/
│   └── api/
│       ├── client.ts            ← axios 인스턴스 + 인터셉터
│       ├── queryKeys.ts
│       └── endpoints/           ← auth, farms, kpi, chat, sows, events, finishers, piglets, sync
└── types/
    └── api.types.ts             ← UserProfile, ChatResponse, FindingOut, Alert, SowStatus, ...
```

### 페이지 구조 (Shell 통합 전)
- 모든 app 페이지가 직접 `<Sidebar />` import + `ml-[220px]` offset 사용
- `/dashboard` 페이지 없음 — 대시보드는 루트 `/`(page.tsx)
- Shell 통합 후 `(app)/` 라우트 그룹 아래로 이동 예정

### 상태관리 경계
| 계층 | 도구 |
|------|------|
| 서버 데이터 (fetch/cache) | TanStack Query |
| 전역 클라이언트 (auth) | Zustand (persist) |
| URL 연동 필터/탭 | `useSearchParams` / URL |
| UI 로컬 (open/close 등) | useState |

### 디자인 토큰 (globals.css CSS 변수)
- 배경: `bg-background`, `bg-surface`, `bg-bg`, `bg-bg2`, `bg-panel-hi`
- 텍스트: `text-text`, `text-text1`, `text-text2`, `text-text3`, `text-muted`, `text-faint`
- 테두리: `border-border`
- 브랜드: `bg-navy` (#0D1B3E), `bg-primary` (blue #2563EB), `bg-snout` (pig snout 색상), `text-gold`
- 시맨틱: `text-success`, `text-danger`, `text-warning`, `text-purple`
- 숫자·코드: `font-mono` (JetBrains Mono)