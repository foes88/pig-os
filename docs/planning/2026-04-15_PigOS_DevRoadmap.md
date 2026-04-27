# PigOS 백엔드 개발 STEP

> 2026-04-15 | 7월 1일 베이직 출시 기준
> 5개 시장 동시 출시: US / CN / SEA(VN·TH) / LatAm(BR) / KR

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

## STEP 2 — FastAPI 백엔드 MVP (5월, 8주)

### Week 1~2: 프로젝트 셋업 + 인증

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
│       └── dashboard.py
├── models/               ← SQLAlchemy ORM
├── schemas/              ← Pydantic v2 스키마
└── services/             ← 비즈니스 로직 분리
```

**산출물:**
- 회원가입 / 로그인 / 토큰 갱신
- 농장 생성 시 schema-per-tenant 자동 생성
- 권한 미들웨어 (7단계 role)

---

### Week 3~4: 마스터 데이터 + 온보딩

**마스터 데이터 API:**
- 이벤트 48종 코드 (`code_groups` / `code_values`)
- 질병 30종, 백신 22종, 항생제 22종 시드
- `default_metric_values` KR/NA/EU/SEA/SA 기준값

**온보딩 플로우 API:**
```
POST /onboarding/start
  body: { country_code, sow_count, farm_type }
  → IP 기반 region 감지 + scope_kpi_recommendations 조회
  → is_base KPI 자동 추천 반환
  → compliance_profiles 필수 KPI 강제 포함

POST /onboarding/complete
  → farm 생성 + tenant schema 초기화
  → default_metric_values 적용
```

---

### Week 5~6: 이벤트 입력 + KPI 계산

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

### Week 5~6 추가: 반응형·iPad·i18n
- 반응형 웹 (모바일·태블릿·iPad)
- 7개 언어 i18n 구축: en / ko / vi / th / pt / zh / da

### Week 7~8: 대시보드 + Rule Engine + Claude API

**대시보드 API (Layer 2 — Insight):**
- 농장 점수화 (KPI vs benchmark 비교)
- 이상 감지: `default_value` 기준 ±N% 이탈 시 알림
- `alerts` 테이블 → 푸시 알림 트리거

**Rule Engine:**
```python
# default_metric_values 기준값 이탈 감지
def check_kpi_alerts(farm_id, region_code, market_code):
    metrics = effective_metric_values(farm_id, region_code, market_code)
    current = get_current_kpi(farm_id)
    for m in metrics:
        deviation = (current[m.metric_code] - m.benchmark_avg) / m.benchmark_avg
        if abs(deviation) > ALERT_THRESHOLD:
            create_alert(farm_id, m.metric_code, deviation)

# compliance_profiles 규제 조건 검증
def validate_compliance(farm_id, profile_code):
    profile = get_compliance_profile(profile_code)
    if profile.min_wean_period:
        validate_wean_period(farm_id, profile.min_wean_period)
```

**Claude API 연동 — 두 가지 AI 상호작용 모드:**

**(1) Layer 2 Insight: 월간 AI 분석 리포트 (Push형)**
```python
# AI가 먼저 분석해서 리포트 생성 → 농장주에게 전달
prompt = build_farm_analysis_prompt(
    farm_kpi=current_kpi,
    metrics=effective_metrics,
    compliance=compliance_profile
)
response = anthropic.messages.create(
    model="claude-opus-4-7",
    messages=[{"role": "user", "content": prompt}]
)
```

**(2) Layer 3 Advisor: 자연어 Q&A (Pull형)**
```python
# 농장주가 직접 질문 → AI가 농장 데이터 기반으로 즉시 답변
# 예: "이번 달 PSY가 왜 낮아?" / "재발정 많은 이유가 뭐야?"
def chat_with_farm_data(farm_id: str, user_question: str):
    context = build_farm_context(
        farm_id=farm_id,
        kpi_snapshots=get_recent_kpi(farm_id, months=3),
        alerts=get_active_alerts(farm_id),
        benchmarks=effective_metric_values(farm_id)
    )
    response = anthropic.messages.create(
        model="claude-opus-4-7",
        system=FARM_ADVISOR_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"{context}\n\n질문: {user_question}"}
        ]
    )
    return response.content[0].text
```
> 경쟁사 PLD(Precision Livestock Diagnostics)가 이 방식으로 차별화 중.
> Claude API 추가 비용 없이 구현 가능. 7월 Base에 베타 포함 검토.

**Base vs Addon 경계:**
| 기능 | 층 | 포함 |
|------|----|------|
| 월간 AI 리포트 | Layer 2 | Base (무료) |
| 자연어 Q&A (기본 KPI 질문) | Layer 3 | Base 베타 (7월) |
| 자연어 Q&A (Addon 도메인 질문) | Layer 3 | 해당 Addon 포함 |

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

## STEP 5 — 애드온 순차 출시 (8~11월)

| 시점 | 애드온 | 내용 |
|------|--------|------|
| 8월 | #1 FCR 최적화 | 사료 입력 + FCR 계산 + 최적화 추천 |
| 9월 | #2 건강·방역 | 항생제 추적, RAG 구축 시작 |
| 10~11월 | #3 수익 분석 | 두당 수익, 출하 최적화, 시장가 연동 |
| 12월 | KPI 풀라인업 | 4종 완전 출시 + Gemma4 전환 검토 |

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

## 관련 문서

- [db-schema-v2.sql](../specs/2026-04-15_db-schema-v2.sql)
- [schema-v1-to-v2-migration.md](../specs/2026-04-15_schema-v1-to-v2-migration.md)
- [PigOS_PlanUpdate_v2.3.md](2026-04-15_PigOS_PlanUpdate_v2.3.md)
- [OpenAPI 스펙 v1](../api/) ← 미작성
