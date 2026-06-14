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
| Infra | AWS (서울 리전, ap-northeast-2) + Docker + Kubernetes |
| Mobile Android | Kotlin + Jetpack Compose + Room + WorkManager + Retrofit |
| Mobile iOS | Swift + SwiftUI (Android 안정화 후 Phase 2) |
| Offline Sync | Room (Android) / Core Data (iOS) — sync protocol: docs/specs/2026-05-19_offline-sync-spec.md |
| Background Jobs | ARQ (Redis 기반) |

> **Mobile 결정 근거 (2026-06-05)**: 현장 작업자 + Android 우선 + 오프라인 입력 + 저사양 기기 + 백그라운드 동기화 조합에서
> React Native보다 Native가 더 안정적. Room/WorkManager/DataStore로 오프라인-퍼스트 아키텍처가 구조적으로 깔끔하고,
> 카메라·푸시·배터리·네트워크 복구 대응도 Native가 유리. 공용 자산: FastAPI API, OpenAPI 스펙, sync protocol, KPI 공식, 디자인 토큰.

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

> **실행 명령**: `cd C:/dev/PigOS && claude --dangerously-skip-permissions`
> 그 다음 프롬프트: `/loop CLAUDE.md의 자율 실행 플랜을 위에서부터 순서대로 진행해. 완료된 항목은 체크하고 git commit.`

### 실행 원칙
1. 세션 시작 시 CLAUDE.md + PROGRESS.md 읽고 현재 상태 파악
2. **아래 "자율 실행 플랜"을 Phase 1부터 순서대로** 진행
3. 각 태스크 완료 시 즉시 `git commit -m "feat(phase-N): [태스크ID] 설명"`
4. 태스크 완료 시 해당 `- [ ]`를 `- [x]`로 변경
5. 불확실한 사항은 **최선의 판단**으로 진행 — 절대 멈추지 않는다
6. TypeScript/Python 타입 에러 없을 것 (`tsc --noEmit`, `python -m pytest` 확인)
7. 각 Phase 완료 시 PROGRESS.md 업데이트

### 금지 사항
- `git push` 금지 (사람이 확인 후 직접 push)
- 실제 Supabase/운영 DB 데이터 직접 변경 금지
- AWS 리소스 생성/변경 금지
- 외부 유료 API 호출 금지

---

## 자율 실행 플랜 (Multi-Day Autonomous Sprint)

> 현재 상태 (2026-06-10 갱신):
> - **Phase 1 (이벤트 입력 검증 Validators) 완료** — app/validators/ 6모듈 + event_service 연결, unit 134/134 통과
> - 백엔드 API 13개 라우터 완성, Rule Engine 구현됨, 테스트 106/106 통과
> - **모돈 상태 코드 v2 적용 완료** (GILT/OPEN/PREGNANT/LACTATING/ACCIDENT — P2-2 완료, 재작업 금지)
> - **완료된 UI**: 로그인/온보딩 라이트모드+공식로고, Sidebar(lucide+그룹핑), /settings 허브,
>   웅돈 CRUD, 모돈 수정/도폐사·판매 모달, Addon 스토어 리디자인
> - validators 폴더 없음, /alerts 페이지 없음, 프론트 테스트 0개
> - 테스트 실행: `cd api && uv run pytest tests/ -q` (python -m pytest 아님, Docker postgres + pigos_test DB 필요)
> - 타입체크: `cd src && npx tsc --noEmit`
> - 목표: PigPlan 동등 검증 + 미완성 화면 완성 + 테스트

---

### Phase 1 — 이벤트 입력 검증 (Backend Validators)

> `api/app/validators/` 폴더 신규 생성. 각 파일은 Pydantic validator + raise HTTPException(422) 패턴.

- [x] **[P1-1] validators/__init__.py + base.py**
  - `ValidationError` 커스텀 예외 정의
  - `validate_date_after(date, reference, field_name)` 공통 헬퍼

- [x] **[P1-2] validators/farrowing.py** — 분만 검증
  - `total_born > 35` → 422 `"Total Born cannot exceed 35"`
  - `stillborn > 25` or `mummified > 25` → 422
  - `born_alive > total_born` → 422
  - `born_alive != male + female` (암수 입력 시) → 422
  - `avg_birth_weight > 3.0` → 422 `"Average birth weight cannot exceed 3.0 kg"`
  - unit test: `tests/unit/test_farrowing_validator.py` (정상케이스 5개 + 오류케이스 7개)

- [x] **[P1-3] validators/weaning.py** — 이유 검증
  - `weaned != nursing_head - (deaths + transfers_out - transfers_in)` → 422
  - 메시지에 공식 명시: `"Weaned count must equal: nursing_head - (deaths + out - in)"`
  - unit test: `tests/unit/test_weaning_validator.py`

- [x] **[P1-4] validators/mating.py** — 교배 검증
  - 모돈 상태 `GILT / OPEN / ACCIDENT`만 허용, 나머지 422
  - `boar_2 is set AND boar_1 is None` → 422 `"Boar 1 required before Boar 2"`
  - `boar_3 is set AND boar_2 is None` → 422
  - unit test: `tests/unit/test_mating_validator.py`

- [x] **[P1-5] validators/cross_fostering.py** — 양자 검증
  - `transfer_count > 25` → 422 `"Cross-fostering cannot exceed 25 piglets per transfer"`
  - unit test: `tests/unit/test_cross_fostering_validator.py`

- [x] **[P1-6] validators/date_rules.py** — 날짜 범위 검증
  - 이벤트 날짜 < `sow.entry_date` → 422
  - 이벤트 날짜 > `sow.cull_date` (도폐사 후) → 422
  - 교배일 < 이전 이유일 → 422
  - 분만일 < 이전 교배일 → 422
  - 이유일 < 이전 분만일 → 422
  - unit test: `tests/unit/test_date_rules.py`

- [x] **[P1-7] validators를 event_service.py에 연결**
  - Farrowing/Weaning/Mating/CrossFostering 이벤트 처리 전 해당 validator 호출
  - 기존 서비스 코드 수정 (Pydantic 스키마 레벨 검증과 분리)

---

### Phase 2 — 모돈 상태 전이 + 알람 엔드포인트 (Backend)

- [x] **[P2-1] validators/sow_state.py** — 상태 전이 강제
  - 전이 허용 맵:
    ```python
    ALLOWED_TRANSITIONS = {
        "mating":    ["GILT", "OPEN", "ACCIDENT"],
        "farrowing": ["PREGNANT"],
        "weaning":   ["LACTATING"],
        "rts":       ["PREGNANT"],
        "culling":   ["GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT"],
    }
    ```
  - 허용되지 않는 전이 시 422 + 현재 상태 + 허용 상태 목록 반환
  - unit test: `tests/unit/test_sow_state_validator.py`

- [x] **[P2-2] 모돈 상태 코드 업그레이드 (현재 DB → 스펙 정렬)** ✅ 2026-06-10 완료 — Alembic `d2a8c5e7f1b3` 적용, 테스트 106/106, 웹/모바일 이유 전이 불일치 수정 포함. **재작업 금지**
  - 현재 DB 값 (sow.status): `ACTIVE / GESTATING / LACTATING / WEANED / DRY / CULLED / DEAD`
  - 목표 값 (SCREEN_MENU_SPEC): `GILT / OPEN / PREGNANT / LACTATING / ACCIDENT / CULLED / DEAD`
  - 변환 매핑:
    - `ACTIVE` (공태) → `OPEN`
    - `GESTATING` (임신) → `PREGNANT`
    - `WEANED` (이유 후 대기) → `OPEN` (이유 완료 후 즉시 공태 전이)
    - `DRY` (번식사고/RTS) → `ACCIDENT`
    - `LACTATING`, `CULLED`, `DEAD` — 유지
    - GILT 상태: DB에 없으므로 `status="GILT"` 추가 (entry_type="GILT"인 미교배 모돈 대상)
  - 작업 순서:
    1. `models/sow.py` 주석 및 default 값 수정 (`ACTIVE` → `OPEN`)
    2. Alembic migration: `UPDATE sows SET status = 'OPEN' WHERE status = 'ACTIVE'` 등 데이터 마이그레이션 포함
    3. `api.types.ts` `SowStatus` 타입 동기화
    4. `sows` 라우터, 서비스, 필터 쿼리 전체 `ACTIVE/GESTATING/WEANED/DRY` → 신규 값으로 교체
  - Alembic migration: `alembic revision -m "upgrade_sow_status_codes"`

- [x] **[P2-3] Alert Service 신규 구현**
  - `api/app/services/alert_service.py` 신규
  - `get_overdue_sows(farm_id, db, farm_config)` — 6유형 반환
    ```python
    # farm_config 기본값
    GESTATION_DAYS = 114   # farm_config.gestation_length or 114
    LACTATION_DAYS = 21    # farm_config.lactation_length or 21
    WSI_DAYS = 7           # farm_config.wsi_days or 7
    GILT_FIRST_MATING_AGE = 240  # days
    GILT_UNMATED_ALERT_AGE = 300  # days

    # 6유형
    gilt_no_estrus: 도입 후 발정 미확인
    gilt_overdue_mating: 일령 > 240일 미교배
    pregnant_overdue_farrowing: 교배 후 114일 초과 미분만
    lactating_overdue_weaning: 분만 후 21일 초과 미이유
    open_overdue_mating: 이유 후 7일 초과 미교배
    accident_overdue_mating: RTS 후 7일 초과 미교배
    ```
  - `get_cull_candidates(farm_id, db)` — 도태 권고 3기준
    - 3회 이상 연속 RTS
    - parity > 7 AND 마지막 이유두수 < 9
    - gilt age > 300일 미교배

- [x] **[P2-4] Alert Router 신규 구현**
  - `api/app/routers/base/alerts.py` 신규
  - `GET /api/v1/farms/{farm_id}/alerts/overdue` → 6유형 목록
  - `GET /api/v1/farms/{farm_id}/alerts/cull-candidates` → 도태 권고 목록
  - main.py에 라우터 등록
  - unit test: `tests/unit/test_alert_service.py`

---

### Phase 3 — Rule Engine 확장 (Reproduction Rules)

- [x] **[P3-1] engine/rules/reproduction.py 신규**
  - `wsi.overdue`: WSI > 10일 → WARNING, > 14일 → CRITICAL
  - `rts.rate_high`: RTS율 > 15% → WARNING, > 25% → CRITICAL
  - `pwmr.high`:
    - Method A: `deaths / (weaned + deaths) * 100`
    - Method B: `(avg_tb - avg_weaned) / avg_tb * 100`
    - > 15% → WARNING, > 20% → CRITICAL
    - `Finding`에 `method: "A"` or `"B"` 명시
  - Rule Registry에 등록

- [x] **[P3-2] engine/rules/base.py PSY 등급 확장**
  - `psy.below_target` 규칙을 4등급으로 확장
  - Grade 1 (≥28): OK, Grade 2 (24-28): INFO, Grade 3 (20-24): WARNING, Grade 4 (<20): CRITICAL
  - `Finding`에 `grade: str` 필드 추가 (rule_engine.py의 `Finding` dataclass 수정)

- [x] **[P3-3] Rule Engine 테스트**
  - `tests/unit/test_rule_engine.py`
  - 각 규칙별 WARNING/CRITICAL 경계값 테스트

---

### Phase 4 — 프론트엔드 완성

- [x] **[P4-1] /alerts 페이지 신규** `src/app/(app)/alerts/page.tsx`
  - 상단 요약 카드: 유형별 건수 (6유형 + 도태권고)
  - 관리대상 모돈 테이블: 유형 / 귀표번호 / 상태 / 경과일수 / 액션버튼
  - 액션버튼: 교배입력 → `/record?tab=mating&sowId={id}`, 이유입력 → `/record?tab=weaning&sowId={id}`
  - 도태권고 섹션: 사유 / 귀표번호 / 산차 / 최근이유두수
  - API: `GET /alerts/overdue`, `GET /alerts/cull-candidates` 연동
  - Sidebar에 "Alerts" 메뉴 추가 + badge(건수)

- [x] **[P4-2] /sows 모돈 수정 모달** ✅ 2026-06-10 기본 완료 — ear_tag/breed/rfid_tag 수정 모달 + 도폐사·판매 모달(사유 9종, 판매 시 체중/가격) 구현됨.
  - 잔여(선택): entry_type / date_of_birth 편집은 백엔드 `SowUpdate` 스키마 확장 후 추가

- [ ] **[P4-3] /sows/[id] 상세 페이지 검증 및 보완**
  - 현재 구현 확인 후 누락 항목 보완
  - 번식 이력 타임라인: 사이클별 카드 (교배일 / 분만일 / 이유두수 / 이유일령)
  - 산차별 성적 테이블
  - 현재 상태 + 다음 예정 이벤트 (farm_config 기준)

- [x] **[P4-4] Dashboard KPI 카드 Alerts 연동**
  - 관리대상 모돈 수 카드 추가 (`GET /alerts/overdue` 건수 합산)
  - 클릭 시 `/alerts`로 이동
  - 도태권고 건수 badge

- [x] **[P4-5] QuickInputDrawer 아이콘 교체**
  - 이모지(💉🐖🌱) → lucide-react 아이콘으로 교체
  - 버튼별 적절한 아이콘 선택 (Heart, Baby, Baby 등)

- [ ] **[P4-6] /record 모바일 최적화**
  - md 이하에서 좌우 분할 레이아웃 → 스택(위아래) 레이아웃으로 전환
  - 모돈 검색을 상단 고정 drawer 또는 모달로 변경

---

### Phase 5 — i18n 5개 언어

> **주의**: 감사 결과 현재 5개 언어 × 140키 이미 동기화됨 (2026-06-10 기준).
> 새 UI(Phase 1~4에서 추가되는 텍스트)에 대해서만 키 추가 작업 필요.
> `src/messages/` 아래 en/ko/zh/es/vi 5개 파일 동시 업데이트 필수.

- [ ] **[P5-1] /alerts 페이지 i18n 키 추가** (Phase 4-1에서 생성한 텍스트)
- [ ] **[P5-2] Sow 상태 용어 i18n 정렬**
  - "OPEN" → en: "Open", ko: "공태", zh: "空怀", es: "Vacía", vi: "Nái trống"
  - "GILT" → en: "Gilt", ko: "후보돈", zh: "后备母猪", es: "Gilta", vi: "Heo nái hậu bị"
  - "PREGNANT" → en: "Pregnant", ko: "임신", zh: "妊娠", es: "Gestante", vi: "Mang thai"
  - "LACTATING" → en: "Lactating", ko: "포유", zh: "哺乳", es: "Lactante", vi: "Nuôi con"
  - "ACCIDENT" → en: "RTS/Accident", ko: "사고", zh: "事故", es: "Accidente", vi: "Sự cố"
- [ ] **[P5-3] 에러 메시지 i18n** — validator 422 메시지들 다국어화
- [ ] **[P5-4] 누락 키 전수 점검** — en 기준 다른 언어에 없는 키 발견 시 번역 추가

---

### Phase 6 — 통합 테스트 + 배포 준비

- [ ] **[P6-1] pytest 설정 + 통합 테스트 기반**
  - `tests/conftest.py`: TestClient + 테스트 DB fixture
  - `tests/integration/test_event_flow.py`: 교배→임신→분만→이유 전체 사이클 E2E
  - `tests/integration/test_validation_errors.py`: 각 validator 422 케이스

- [ ] **[P6-2] Vercel 배포 설정**
  - `vercel.json` 생성 (Next.js 15, env vars)
  - `.env.production` 템플릿 (`NEXT_PUBLIC_API_URL` 등)

- [ ] **[P6-3] API Dockerfile 최종 점검**
  - `api/Dockerfile` 확인
  - `docker-compose.yml` 로컬 개발 환경 검증 (`docker-compose up` 정상 동작)

---

### Phase 7 — 보고서 API (Reports Backend)

> 보고서는 스냅샷 기반 조회. 기간(start_date~end_date)과 집계 단위(monthly/quarterly/annual) 파라미터 수신.

- [x] **[P7-1] 번식 성적 보고서 API**
  - `GET /api/v1/farms/{farm_id}/reports/reproduction`
  - 파라미터: `start_date`, `end_date`, `period=monthly|quarterly|annual`
  - 반환: 기간별 `{ period, psy, npd, fr, pwmr_a, pwmr_b, total_matings, total_farrowings, total_weanings, avg_tb, avg_ba, avg_weaned, avg_lactation_days, rts_rate }`
  - 계산: `kpi_snapshots` 테이블 집계 (실시간 재계산 아님)
  - 기간 범위 초과(>2년) 시 400 반환
  - unit test: 3개월 데이터 fixture → 월별 3행 반환 검증

- [x] **[P7-2] 비육 성적 보고서 API**
  - `GET /api/v1/farms/{farm_id}/reports/grow-finish`
  - 파라미터: `start_date`, `end_date`, `group_id?` (finisher_group 필터)
  - 반환: `{ period, adg_g, fcr, mortality_rate, avg_entry_weight_kg, avg_exit_weight_kg, total_head, total_groups }`
  - 공식: ADG = (avg_exit_weight - avg_entry_weight) / avg_days × 1000 (g/day)
  - FCR = total_feed_kg / total_gain_kg
  - unit test

- [x] **[P7-3] 모돈 이력 상세 엔드포인트**
  - `GET /api/v1/sows/{sow_id}/history`
  - 반환: 산차별 번식 사이클 배열
    ```
    { parity, mating_date, boar_ids, farrowing_date, tb, ba, sb, mum,
      avg_birth_weight, nursing_head, weaned, weaning_date, lactation_days,
      wsi_days, status: "completed"|"in_progress" }
    ```
  - 미완료 사이클(현재 진행 중)은 `status: "in_progress"` + 빈 필드

- [x] **[P7-4] 보고서 라우터 등록**
  - `api/app/routers/base/reports.py` (신규 또는 기존 확장)
  - main.py에 등록

---

### Phase 8 — 설정 페이지 (Settings Frontend)

> `/settings/` 하위 페이지. Next.js 라우트: `(app)/settings/` 폴더.

- [ ] **[P8-1] Farm Config 설정 페이지** `src/app/(app)/settings/farm/page.tsx`
  - 농장 기본 설정 편집: 임신기간(Gestation Length, 기본 114일), 포유기간(Lactation Length, 기본 21일), WSI 목표(Target WSI, 기본 7일), 후보돈 초교배 목표일령(Gilt First Mating Target, 기본 240일), 출하일령(Slaughter Age, 기본 180일)
  - PATCH `/api/v1/farms/{farm_id}/config` 연동
  - 저장 시 즉시 적용(alert 기준일 변경)
  - 숫자 범위 검증: gestation 100-120, lactation 14-28, wsi 5-14

- [ ] **[P8-2] Benchmark 설정 페이지** `src/app/(app)/settings/benchmarks/page.tsx`
  - 국가별 벤치마크 목표값 표시 (읽기 전용 참고용)
  - 표: KPI 이름 / 현재값 / KR 벤치 / US 벤치 / BR 벤치 / CN 벤치
  - 데이터: `GET /api/v1/farms/{farm_id}/kpi/snapshots` + `GET /api/v1/farms/{farm_id}/config`

- [ ] **[P8-3] Settings Sidebar 연결**
  - Sidebar에 "Settings" 메뉴 그룹 추가
  - 하위: Farm Config / Benchmarks / Profile / Billing

---

### Phase 9 — 누락 화면 완성 (Frontend Gaps)

> SCREEN_MENU_SPEC.md 기준 미구현 화면 확인 후 완성.

- [ ] **[P9-1] /reports 페이지 번식 보고서 연동**
  - Phase 7-1 API 연결
  - 기간 선택 UI (DateRangePicker — 3개월/6개월/1년/사용자지정)
  - 월별 테이블: PSY / NPD / FR / PWMR-A / PWMR-B / RTS율
  - CSV 다운로드 버튼 (`/reports/reproduction?format=csv`)

- [ ] **[P9-2] /reports 비육 보고서 탭 추가**
  - Phase 7-2 API 연결
  - 탭 전환: Reproduction | Grow-Finish
  - Grow-Finish 테이블: ADG / FCR / 폐사율 / 입식두수

- [ ] **[P9-3] /finishers 비육돈 페이지 완성**
  - 현재 상태 확인 후 누락 항목 보완
  - 그룹 목록: 그룹ID / 입식일 / 두수 / 현재주령 / ADG / FCR
  - 그룹 상세: 주간 성적 입력 (체중/사료/폐사) 폼
  - GET `/api/v1/farms/{farm_id}/finisher-groups` 연동

- [ ] **[P9-4] Sidebar 메뉴 최종 정비** (⚠️ 2026-06-10 부분 완료: lucide 아이콘 + 공식 로고 + 그룹핑(대시보드/돈군관리/기록/분석/Addon) + 5개 언어 현지 용어 + active 하이라이트 적용됨. `src/components/Sidebar.tsx` 먼저 읽고 기존 구조 유지할 것 — 전면 재작성 금지)
  - 잔여: Alerts 메뉴 항목 추가 + unread badge (숫자) — P4-1 /alerts 페이지 완성 후

---

### Phase 10 — 통합 테스트 강화

- [ ] **[P10-1] 번식 사이클 E2E 통합 테스트**
  - `tests/integration/test_full_breeding_cycle.py`
  - 시나리오: 후보돈 등록 → 교배(GILT→PREGNANT) → 분만(PREGNANT→LACTATING) → 이유(LACTATING→OPEN) → 교배(OPEN→PREGNANT) 2사이클
  - 각 단계 상태 전이 검증
  - 이유두수 공식 검증 (nursing_head - deaths = weaned)
  - 최종 KPI(PSY) 계산값 검증

- [ ] **[P10-2] 검증 오류 E2E 테스트**
  - `tests/integration/test_validation_errors.py`
  - 시나리오별 422 응답 코드 + 오류 메시지 검증
  - 커버리지: farrowing(7개), weaning(3개), mating(3개), state_transition(5개)

- [ ] **[P10-3] 알람 서비스 통합 테스트**
  - `tests/integration/test_alert_service.py`
  - fixture: 과기한 모돈 6유형 시나리오 세팅
  - 도태 권고 3기준 각각 검증

- [ ] **[P10-4] 보고서 API 통합 테스트**
  - `tests/integration/test_reports.py`
  - fixture: 12개월 kpi_snapshots 시드 데이터
  - 월별/분기별/연간 집계 정확성 검증

---

### Phase 11 — 배포 준비 (Deployment)

- [ ] **[P11-1] 환경 변수 템플릿 정비**
  - `.env.example` (백엔드): DATABASE_URL, REDIS_URL, JWT_SECRET, OPENAI_API_KEY(옵션), SENTRY_DSN(옵션)
  - `src/.env.example` (프론트): NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SUPABASE_URL(옵션)
  - 실제 비밀값 절대 포함 금지

- [ ] **[P11-2] Vercel 배포 설정**
  - `vercel.json`: Next.js 15 빌드 설정, env 매핑
  - `src/next.config.ts`: API 프록시 설정 (`/api/v1` → FastAPI 서버)

- [ ] **[P11-3] API 서버 배포 설정**
  - `api/Dockerfile` 최종 점검 (multi-stage, non-root user)
  - `api/docker-compose.prod.yml` 프로덕션 compose
  - Health check 엔드포인트: `GET /health` → `{ status: "ok", version: "..." }`

- [ ] **[P11-4] GitHub Actions CI 설정**
  - `.github/workflows/ci.yml`
  - 트리거: PR to development 브랜치
  - 단계: Python lint(ruff) + pytest + TypeScript tsc --noEmit + Next.js build
  - 운영 배포는 수동 트리거만 허용 (auto-deploy 금지)

- [ ] **[P11-5] 로컬 개발 온보딩 문서**
  - `docs/DEVELOPMENT.md` 신규 (간단한 로컬 실행 가이드)
  - `docker-compose up` → API + DB + Redis 실행
  - `npm run dev` → 프론트 실행
  - 초기 seed 실행 방법


---

### Phase 12 — 화면 CRUD 완성 (Edit / Delete / Pagination)

> 감사 결과 확인된 누락 기능. 이미 등록(Create)은 모두 작동함.
> 우선순위: 번식기록 수정 > 비육돈 수정 > 페이지네이션 > CSV

#### [P12-1] 번식기록 이벤트 수정/삭제

**백엔드** (`api/app/routers/base/events.py`):
- [ ] `PATCH /api/v1/farms/{farm_id}/events/matings/{id}` — 교배 기록 수정 (교배일, 웅돈, 메모)
- [ ] `DELETE /api/v1/farms/{farm_id}/events/matings/{id}` — 교배 기록 삭제 + 모돈 상태 롤백
- [ ] `PATCH /api/v1/farms/{farm_id}/events/farrowings/{id}` — 분만 기록 수정 (TB/BA/SB 등)
- [ ] `DELETE /api/v1/farms/{farm_id}/events/farrowings/{id}` — 분만 기록 삭제 + 상태 롤백
- [ ] `PATCH /api/v1/farms/{farm_id}/events/weanings/{id}` — 이유 기록 수정
- [ ] `DELETE /api/v1/farms/{farm_id}/events/weanings/{id}` — 이유 기록 삭제 + 상태 롤백
- [ ] 삭제 시 sow.status 롤백 규칙:
  - mating 삭제 → PREGNANT → OPEN
  - farrowing 삭제 → LACTATING → PREGNANT
  - weaning 삭제 → OPEN → LACTATING
- [ ] 월마감 잠금 검사: `period_locks`에 해당 기간이 잠겨있으면 423 반환

**프론트엔드** (`src/app/(app)/record/page.tsx`):
- [ ] 모돈 리스트 선택 후 우측 이벤트 탭에 "최근 이벤트 이력" 섹션 추가
  - 현재 모돈의 최근 이벤트 3~5개 카드로 나열
  - 각 카드에 연필(Edit) 아이콘 + 휴지통(Delete) 아이콘
- [ ] Edit 아이콘 클릭 → 해당 이벤트 타입의 수정 모달 (기존 폼과 동일, 값만 pre-fill)
- [ ] Delete 아이콘 클릭 → 확인 다이얼로그 ("이 기록을 삭제하면 모돈 상태가 롤백됩니다") → DELETE API 호출
- [ ] `api.types.ts`에 수정 스키마 타입 추가
- [ ] `src/lib/api/endpoints/events.ts`에 update/delete 함수 추가

#### [P12-2] 모돈 상세 페이지 이벤트 수정/삭제

(`src/app/(app)/sows/[id]/page.tsx`):
- [ ] 번식 이력 타임라인 각 항목에 Edit / Delete 버튼 추가
- [ ] Edit 클릭 → 수정 모달 (P14-1과 동일 API 사용)
- [ ] Delete 클릭 → 확인 후 삭제 → 페이지 데이터 재조회

#### [P12-3] 비육돈 그룹 수정

**백엔드** (`api/app/routers/base/finishers.py`):
- [ ] `PATCH /api/v1/farms/{farm_id}/finisher-groups/{id}` — 그룹명, 입식두수, 평균입식체중 수정

**프론트엔드** (`src/app/(app)/finishers/page.tsx`):
- [ ] 각 그룹 카드에 Edit 버튼(연필 아이콘) 추가
- [ ] 그룹 수정 모달: 배치명, 입식두수, 평균체중 편집
- [ ] PATCH API 연동 + 성공 시 목록 invalidate

#### [P12-4] 페이지네이션 추가

- [ ] **웅돈** (`boars/page.tsx`): 20개 단위 페이지네이션 추가 (`page`, `page_size` query 파라미터)
- [ ] **비육돈** (`finishers/page.tsx`): 20개 단위 페이지네이션 추가
- [ ] **번식기록 모돈 리스트** (`record/page.tsx`): 현재 500개 일괄 로드 → 무한스크롤 또는 50개 단위 페이지네이션으로 변경
- [ ] 백엔드 라우터에서 `limit`/`offset` 이미 지원하는지 확인 후 필요시 추가

#### [P12-5] 보고서 기간 필터 + CSV 내보내기

**프론트엔드** (`src/app/(app)/reports/page.tsx`):
- [ ] 기간 선택 UI 추가:
  - 프리셋 버튼: 최근 3개월 / 6개월 / 1년
  - 직접 입력: 시작월 ~ 종료월 (월 단위 피커)
  - 선택한 기간으로 `kpiApi.trend()` 파라미터 변경
- [ ] CSV 내보내기 버튼 구현:
  - 현재 표시 데이터를 클라이언트 사이드에서 CSV 변환 후 다운로드
  - 파일명: `pigos_report_{farm_id}_{start}_{end}.csv`
  - 라이브러리: `papaparse` 또는 직접 구현 (의존성 최소화)
- [ ] 보고서 탭 분리: "번식 성적" | "비육 성적" 탭 (Phase 7 API 완료 후 연결)

#### [P12-6] 알림/Notifications 페이지 개선

(`src/app/(app)/notifications/page.tsx` 현황 확인 후):
- [ ] 알림 읽음 처리: 개별 읽음 + 전체 읽음 버튼
- [ ] 알림 유형 필터: CRITICAL / WARNING / INFO 탭
- [ ] 알림 클릭 시 해당 모돈 상세 또는 이벤트 입력 페이지로 이동
- [ ] 무한스크롤 또는 페이지네이션 (알림이 많을 경우)


---

### Phase 13 — 프론트엔드 테스트 (Vitest)

> 현재 `src/` 폴더에 테스트 파일 0개. 최소한의 회귀 방지용 테스트 추가.

- [ ] **[P13-1] Vitest + Testing Library 설정**
  - `npm install -D vitest @testing-library/react @testing-library/user-event @vitejs/plugin-react`
  - `vitest.config.ts` 생성 (jsdom 환경)
  - `package.json` scripts에 `"test": "vitest"` 추가

- [ ] **[P13-2] API 클라이언트 모킹 유틸**
  - `src/tests/setup.ts` — `src/lib/api/client.ts` axios 인스턴스 mock
  - MSW(Mock Service Worker) 또는 vi.mock으로 API 호출 가로채기 설정

- [ ] **[P13-3] 핵심 페이지 스모크 테스트**
  - `src/tests/pages/dashboard.test.tsx` — KPI 카드 렌더링 검증
  - `src/tests/pages/sows.test.tsx` — 모돈 목록 표시 + 등록 버튼 존재 검증
  - `src/tests/pages/record.test.tsx` — 탭 전환 (교배/분만/이유) 동작 검증
  - `src/tests/pages/alerts.test.tsx` — Alerts 페이지 마운트 검증 (Phase 4-1 완료 후)

- [ ] **[P13-4] 컴포넌트 단위 테스트**
  - `src/tests/components/Sidebar.test.tsx` — 10개 메뉴 링크 렌더링 검증
  - `src/tests/components/QuickInputDrawer.test.tsx` — open/close 동작 검증

---

### Phase 14 — Addon #1 AI Insight LLM 통합

> Rule Engine 구조에서 Renderer를 LLM으로 교체. MVP에서는 Template Renderer만 사용,
> Addon #1 활성화 시 LLM API 호출로 자연어 설명 생성.

- [ ] **[P14-1] LLM Renderer 구현**
  - `api/app/engine/llm_renderer.py` 신규
  - `TemplateRenderer`와 동일 인터페이스: `render(result: StructuredResult, lang: str) → str`
  - Claude API (`claude-haiku-4-5-20251001`) 사용 (저비용)
  - StructuredResult를 시스템 프롬프트에 주입 → "판단은 하지 말고 이 데이터를 자연어로 설명만 해"
  - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` 환경변수 없으면 TemplateRenderer로 폴백

- [ ] **[P14-2] chat_service.py 연결**
  - `use_llm: bool = False` 파라미터 추가 (farm.addon_ai_insight 활성화 여부)
  - 활성화된 농장만 LLM Renderer 사용, 나머지는 Template Renderer 유지
  - 응답에 `rendered_by: "template"|"llm"` 필드 추가

- [ ] **[P14-3] 사용량 제한 + 로깅**
  - `llm_usage_logs` 테이블 존재 확인 (없으면 마이그레이션 추가)
  - 농장별 월간 LLM 호출 횟수 제한 (기본 100회/월)
  - 초과 시 TemplateRenderer로 자동 폴백 + 알림


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