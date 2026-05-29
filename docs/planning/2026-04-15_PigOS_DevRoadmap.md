# PigOS 백엔드 개발 STEP

> 2026-04-15 | 7월 1일 베이직 출시 기준
> 5개 시장 동시 출시: US / CN / SEA(VN·TH) / LatAm(BR) / KR
> **도메인**: pigos.io (2026-05-18 구매 확정)

---

## 전체 일정 개요

```
4월 (지금)  — 설계 확정
5월         — MVP 개발 (8주 스프린트)
6월         — 코드 리뷰 / QA / 안정화
7월 1일     — 베이직 출시 (L1·L2)
8~11월      — 애드온 #1~3 순차 출시
9월         — 애드온 #2 출시 (건강·방역 + 항생제 추적)
12월        — KPI 풀라인업 + Gemma4 전환 검토
```

---

## STEP 1 — 설계 확정 (4월, 지금)

### 1-1. DB 스키마 v2 검증
- [ ] `db-schema-v2.sql` 로컬 PostgreSQL에 실제 적용
- [ ] `effective_metric_values()` View 우선순위 쿼리 동작 검증
- [ ] `scope_kpi_recommendations` KR/NA/EU 시드 데이터 확인
- [ ] `compliance_profiles` 5개 시장 커버 확인
- [ ] Schema-per-tenant 구조 테스트 (tenant 간 격리 확인)

### 1-2. 미결 DB 결정 (개발 전 확정)
- [ ] CN 권역: NEA vs 독립 시장
- [ ] `farms.market_code` 컬럼 추가 vs region 조인
- [ ] feed_price: `market_price_reference` 통합 vs 별도 테이블

### 1-3. OpenAPI 3.1 스펙 v1
- [ ] 인증 (JWT + refresh token)
- [ ] 농장 온보딩 API
- [ ] 이벤트 입력 API (분만/이유/교배/폐사)
- [ ] KPI 조회 API (`/farms/{id}/kpi`)
- [ ] 대시보드 API (`/farms/{id}/dashboard`)
- [ ] 마스터 데이터 API (코드그룹, 질병, 백신)

### 1-4. 양돈 Rule 문서화 (KPI 기준값 채우기)
- [ ] 권역·국가별 PSY·MSY·NPD 평균·상위25%·목표값
- [ ] 폐사율 경보 기준 (자돈·육성·비육 구간별)
- [ ] FCR 정상 범위 (구간별)
- [ ] 번식 장애 원인별 진단 기준
- [ ] ASF·PRRS·PED 대응 가이드

---

## STEP 2 — FastAPI 백엔드 MVP (5월 2주~, 7주)

> 2026-05-11 업데이트: Claude Design 시안 → 퍼블리싱 → Base/Addon API 병렬 개발
> 외부 AI API 연동 없음 — Rule Engine 기반으로만 구현 (Claude API는 추후 계획)

### Phase A: UI 시안 + 퍼블리싱 (5월 2주~3주, 병렬 진행)

**Claude Design으로 UI 시안 제작:**
- 웹 대시보드 (농장 현황, KPI, 알림)
- 이벤트 입력 화면 (분만/이유/교배/폐사)
- 온보딩 플로우
- Addon 화면 (FCR / 건강·방역 / 원가 / 시장연동)

**퍼블리싱:**
- Next.js 웹: 시안 기반 퍼블리싱 + 반응형·iPad 대응
- Android Native + iOS Native: 앱 퍼블리싱
- 7개 언어 i18n 구축: en / ko / vi / th / pt / zh / da

---

### Phase B: 프로젝트 셋업 + 인증 (5월 2주, Phase A 병렬)

```
src/
├── main.py
├── core/
│   ├── config.py         ← 환경변수, DB URL
│   ├── database.py       ← SQLAlchemy + Schema-per-tenant
│   ├── security.py       ← JWT, 비밀번호 해시
│   └── tenant.py         ← tenant context (farm_schema 전환)
├── api/
│   └── v1/
│       ├── auth.py       ← 로그인, 토큰 갱신
│       ├── farms.py
│       ├── events.py
│       ├── kpi.py
│       ├── dashboard.py
│       └── addons/
│           ├── fcr.py
│           ├── health.py
│           ├── cost.py
│           └── market.py
├── models/               ← SQLAlchemy ORM
├── schemas/              ← Pydantic v2 스키마
└── services/             ← 비즈니스 로직 분리
```

**산출물:**
- 회원가입 / 로그인 / 토큰 갱신
- 농장 생성 시 schema-per-tenant 자동 생성
- 권한 미들웨어 (7단계 role)

---

### Phase B: OpenAPI 3.1 스펙 v1 (5월 2주)

Base API:
- 인증 (JWT + refresh token)
- 농장 온보딩 (`GET /onboarding/detect-country`, `POST /onboarding/start`, `POST /onboarding/complete`)
- 이벤트 입력 (`POST /farms/{id}/events`)
- KPI 조회 (`GET /farms/{id}/kpi`)
- 대시보드 (`GET /farms/{id}/dashboard`)
- 마스터 데이터 (코드그룹, 질병, 백신)

Addon API (Base와 동시 설계):
- Addon #1 FCR: 사료 입력 + FCR 계산 (`/addons/fcr/`)
- Addon #2 건강·방역: 항생제 추적 + 질병 이력 (`/addons/health/`)
- Addon #3 원가·재무: 두당 수익 + 출하 최적화 (`/addons/cost/`)
- Addon #4 시장연동: 시장가 조회 + 출하 추천 (`/addons/market/`)

---

### Phase B: 마스터 데이터 + 온보딩 (5월 3주)

**마스터 데이터 API:**
- 이벤트 48종 코드 (`code_groups` / `code_values`)
- 질병 30종, 백신 22종, 항생제 22종 시드
- `default_metric_values` KR/NA/EU/SEA/SA 기준값

**온보딩 플로우 API:**
```
GET /onboarding/detect-country
  → IP 기반 감지 → { ip_detected_country: "US" }  # 힌트만, 강제 아님

POST /onboarding/start
  body: {
    farm_country_code: "KR",   ← 필수 (사용자가 직접 선택한 농장 소재 국가)
    ip_detected_country: "US", ← 선택 (프론트 참고용)
    sow_count: 300,
    farm_type: "INTEGRATED"
  }
  → farm_country_code 기준으로 scope_kpi_recommendations 조회
  → compliance_profiles 필수 KPI 강제 포함

POST /onboarding/complete
  → farm 생성 + tenant schema 초기화
  → default_metric_values (farm_country_code 기준) 적용
```

---

### Phase B: 이벤트 입력 + KPI 계산 (5월 4주)

**이벤트 입력 (Layer 1 — Data):**
```
POST /farms/{id}/events
  type: MATING / FARROWING / WEANING / DEATH / TRANSFER
```

**KPI 계산 엔진:**
- PSY = 연간이유두수 / 평균모돈수
- MSY = 연간출하두수 / 평균모돈수
- NPD = 비생산일수 (교배 전 + 반복교배 + 유산)
- `kpi_snapshots` 월별 집계 (MONTHLY / QUARTERLY)

**기준값 비교 API:**
```
GET /farms/{id}/kpi?period=2026-07
  → effective_metric_values() 호출
  → { current: 22.1, avg: 24.3, top25: 27.0, target: 28.0 }
```

---

### Phase B: 대시보드 + Rule Engine (6월 1~2주)

**대시보드 API (Layer 2 — Insight):**
- 농장 점수화 (KPI vs benchmark 비교)
- 이상 감지: `default_value` 기준 ±N% 이탈 시 알림
- `alerts` 테이블 → 푸시 알림 트리거

**Rule Engine (외부 AI 없음, 기준값 기반):**
```python
def check_kpi_alerts(farm_id, region_code, market_code):
    metrics = effective_metric_values(farm_id, region_code, market_code)
    current = get_current_kpi(farm_id)
    for m in metrics:
        deviation = (current[m.metric_code] - m.benchmark_avg) / m.benchmark_avg
        if abs(deviation) > ALERT_THRESHOLD:
            create_alert(farm_id, m.metric_code, deviation)

def validate_compliance(farm_id, profile_code):
    profile = get_compliance_profile(profile_code)
    if profile.min_wean_period:
        validate_wean_period(farm_id, profile.min_wean_period)
```

**Addon API 구현 (Base와 병렬):**
- Addon #1 FCR: 사료 입력 + FCR 계산 + Rule 기반 최적화 추천
- Addon #2 건강·방역: 항생제 사용 추적 + 질병 이력 관리
- Addon #3 원가·재무: 두당 수익 계산 + 출하 최적화
- Addon #4 시장연동: 시장가 연동 + 출하 시기 추천

> Claude API / 외부 AI 연동은 이후 단계에서 추가 계획

---

## STEP 3 — 코드 리뷰 / QA (6월 전체)

### 6월 1~2주: 코드 리뷰
- [ ] API 엔드포인트 전수 리뷰
- [ ] Schema-per-tenant 격리 보안 검증
- [ ] SQL injection / XSS / 인증 취약점 점검
- [ ] `audit_log` CUD 추적 누락 확인

### 6월 3~4주: QA + 성능
- [ ] 5개 시장 온보딩 플로우 E2E 테스트
  - KR: PSY·MSY·NPD Base, FCR Addon
  - NA: PSY·NPD·FCR Base
  - EU: PSY·ANTIBIOTIC_USE Base (규제 강제)
- [ ] `effective_metric_values()` 우선순위 정확도 검증
- [ ] 부하 테스트 (동시 농장 100개 기준)
- [ ] 오프라인 동기화 `sync_queue` 충돌 해결 테스트

---

## STEP 4 — 7월 1일 베이직 출시

### 출시 범위 (Layer 1·2)
| 기능 | 포함 여부 |
|------|-----------|
| 농장 가입 + 온보딩 (IP 기반) | ✅ |
| 이벤트 입력 (분만/이유/교배/폐사) | ✅ |
| PSY·MSY·NPD KPI 대시보드 | ✅ |
| 기준값 비교 (avg/top25/target) | ✅ |
| 이상 감지 알림 | ✅ |
| 월간 AI 분석 리포트 (Claude) | ✅ |
| 7개 언어 i18n (en/ko/vi/th/pt/zh/da) | ✅ |
| 반응형 웹 + iPad 최적화 | ✅ |
| FCR / Advisor / Autopilot | ❌ (애드온 8월~) |
| 모바일 앱 | ✅ Android + iOS 동시 출시 |

### 인프라 (AWS 싱가포르)
- [ ] ECS + RDS PostgreSQL 16 세팅
- [ ] Redis 7 (세션 캐시)
- [ ] S3 (첨부파일)
- [ ] CloudFront (정적 에셋)
- [ ] Route53 + SSL

---

## STEP 5 — Addon 순차 출시 (8~12월)

> Addon 6개 확정 (2026-05-13). 상세 스펙: [2026-05_PigOS_AddonSpec.md](2026-05_PigOS_AddonSpec.md)

| 시점 | Addon | 내용 | 과금 |
|------|-------|------|------|
| 8월 | **#1 FCR Optimizer AI** | 사료 입력 + FCR 계산 + Rule Engine 추천 | $15~50/월 |
| 9월 | **#2 Health & Mortality AI** | 폐사·치료 기록 + 군집 감지 + SEA ASF 경보 | $20~60/월 |
| 10월 베타 | **#5 Breeding & Farrowing AI** ★ | NPD 계산 + 재교배 알림 + 모돈 Lock-in | $15~100/월 |
| 10월 베타 | **#6 Biosecurity Audit AI** ★ | 방역 체크리스트 + 점수화 + 취약점 Top 5 | $10~60/월 |
| 10월 통합 | **#3 Cost/Profit Layer** | 각 Addon ROI 카드 자동 파생 (독립 과금 없음) | $0 |
| 11월 베타 | **#4 Market Advisor** | 소농 Base 무료 / 대형 Lite / B2B PigSignal API | B2B $2k~10k |
| 12월 | #5/#6 GA 여부 Kill Criteria 평가 | 유료 전환 기준 달성 시 GA | — |

---

## STEP 6 — 모바일 (7월 1일, 베이직과 동시)

### 플랫폼: Android Native + iOS Native
- **공통 API**: STEP 2에서 구축한 FastAPI 그대로 사용
- **오프라인 동기화**: WatermelonDB (모바일 로컬 SQLite)
  - `sync_queue` Last-Write-Wins
  - 인터넷 없어도 이벤트 입력 가능 → 연결 시 자동 업로드
- **핵심 화면**: 이벤트 입력 / KPI 대시보드 / 알림

---

## 기술 스택 요약

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python 3.12+) |
| ORM | SQLAlchemy 2.0 + Alembic (마이그레이션) |
| DB | PostgreSQL 16 + TimescaleDB (IoT) |
| Cache | Redis 7 |
| AI | Claude API (출시) → Gemma4 로컬 (12월 검토) |
| 인프라 | AWS 싱가포르 + Docker + ECS |
| 모바일 | Android Native + iOS Native + WatermelonDB |
| 프론트 | Next.js + TypeScript |

---

## STEP 7 — Salesforce 생태계 연동 (7월 이후)

> **현황 (2026-05-06)**: ISV 파트너 가입 ✅ | AppExchange 승인 ✅

### 7-1. MCP 서버 구현 (7~8월)
```
src/
└── integrations/
    └── salesforce/
        ├── mcp_server.py       ← MCP 프로토콜 서버
        ├── tools.py            ← get_farm_kpi / get_alerts / post_event
        ├── auth.py             ← Connected App OAuth 2.0
        └── schema.py           ← Pydantic 입출력 스키마
```

**구현 항목:**
- [ ] MCP 서버 엔드포인트 (`/mcp/v1/`) 구현
- [ ] Salesforce Connected App OAuth 2.0 인증 연동
- [ ] `get_farm_kpi` — PSY·MSY·NPD 현재값 + 벤치마크 반환
- [ ] `get_alerts` — 이상 감지 알림 목록 반환
- [ ] AgentExchange 등록을 위한 OpenAPI 스펙 작성

### 7-2. Agentforce Operations 연동 테스트 (2026년 5월 베타)
- [ ] Salesforce Sandbox 환경 구성
- [ ] Agentforce → PigOS MCP 서버 호출 E2E 테스트
- [ ] 번식 일정 알림 자동화 시나리오 검증

### 7-3. AgentExchange 등록 (8월)
- [ ] 앱 설명·카테고리 설정 (Agri-tech / Livestock Management)
- [ ] 보안 리뷰 대응 (Security Review)
- [ ] 가격 정책 설정 (무료 MCP 서버 + 데이터 API 유료)

---

## 관련 문서

- [db-schema-v2.sql](../specs/2026-04-15_db-schema-v2.sql)
- [schema-v1-to-v2-migration.md](../specs/2026-04-15_schema-v1-to-v2-migration.md)
- [PigOS_PlanUpdate_v2.3.md](2026-04-15_PigOS_PlanUpdate_v2.3.md) — v2.5 (Salesforce 파트너십 섹션 포함)
- [OpenAPI 스펙 v1](../api/) ← 미작성
