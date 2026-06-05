# 월간 보고서 — 2026년 5월

> 작성: 2026-06-05 | 기간: 2026-05-01 ~ 2026-05-31

---

## 1. 5월 실적

### 1-1. 백엔드 — FastAPI 전체 구현

| 항목 | 상태 | 날짜 |
|------|------|------|
| FastAPI 백엔드 전체 구조 구현 (스키마/서비스/라우터/엔진) | ✅ 완료 | 05-중 |
| Alembic 마이그레이션 생성 + Docker PostgreSQL 40테이블 적용 | ✅ 완료 | 05-중 |
| Rule Engine 구축 — RuleRegistry + NPD/PSY/분만율/재고 base rules | ✅ 완료 | 05-중 |
| Rule-grounded Q&A API (`POST /api/v1/farms/{farm_id}/chat/query`) | ✅ 완료 | 05-중 |
| KPI Snapshot 백그라운드 잡 (ARQ) — daily/weekly/monthly cron | ✅ 완료 | 05-중 |
| 오프라인 동기화 프로토콜 설계 + 구현 (`POST /api/v1/farms/{farm_id}/sync`) | ✅ 완료 | 05-19 |
| OpenAPI 3.1 스펙 v1 (`docs/api/openapi-v1.yaml`) | ✅ 완료 | 05-19 |
| 마스터 데이터 시드 완성 (질병코드/백신/벤치마크) | ✅ 완료 | 05-19 |
| Docker Compose 로컬 개발환경 (postgres + redis + api) | ✅ 완료 | 05-중 |
| TDD 인프라 구축 + 교배/분만/이유 서비스 로직 검증 | ✅ 완료 | 05-중 |
| 통합 테스트 58개 전체 통과 | ✅ 완료 | 05-중 |

### 1-2. 프론트엔드 — Next.js 기반 + 핵심 페이지

| 항목 | 상태 | 날짜 |
|------|------|------|
| Next.js 15 프론트엔드 기반 — Zustand + TanStack Query + axios + next-intl | ✅ 완료 | 05-중 |
| /login 페이지 + JWT 인증 플로우 | ✅ 완료 | 05-중 |
| 온보딩 3단계 플로우 (농장 기본정보 → 규모 → 완료) | ✅ 완료 | 05-중 |
| 핵심 페이지 3종 구현 — 모돈 목록/상세, 이벤트 기록, KPI 대시보드 | ✅ 완료 | 05-중 |
| API Contract 검증 + 수정 (프론트-백 계약 7종 수정, 버그 8종 수정) | ✅ 완료 | 05-말 |
| Unit 테스트 43/43 pass | ✅ 완료 | 05-말 |

### 1-3. 기술 스택 결정

| 항목 | 결정 내용 | 날짜 |
|------|----------|------|
| 모바일: React Native → **Native (Kotlin/Swift)** 전환 결정 | 현장 작업자 + 오프라인 + 저사양 기기 환경에서 Native가 구조적으로 유리 | 05-중 |
| Android 개발 가이드 신규 생성 | Kotlin + Jetpack Compose + Room + WorkManager + Retrofit | 05-중 |
| 오프라인 동기화: Room (Android) / Core Data (iOS) — LWW 방식 | sync protocol 스펙 문서화 | 05-19 |
| pigos.io 도메인 구매 확정 | 2026-05-18 | 05-18 |

### 1-4. 설계 확정

| 항목 | 내용 |
|------|------|
| Q&A 아키텍처 확정 | Rule-grounded 방식 — LLM은 판단 금지, Rule Engine 결과를 자연어 변환만 |
| KPI 계산 전략 확정 | 대시보드: kpi_snapshots 조회 / 실시간: 개별 이벤트 상세 계산 |
| Multi-tenant 전략 | Shared Schema + farm_id row-level filtering |

---

## 2. 수치 요약

| 지표 | 값 |
|------|-----|
| 생성된 DB 테이블 | 40개 |
| API 엔드포인트 | 50+ |
| 통과 테스트 | 58개 (통합) + 43개 (unit) |
| 커밋 수 | 10+ |
| 신규 문서 | 오프라인 sync 스펙, OpenAPI v1, Android 개발 가이드 |

---

## 3. 6월 계획

| 항목 | 목표일 |
|------|--------|
| UI Shell 통합 (Sidebar + Topbar + BottomNav + Drawer) | 06-10 |
| /dashboard 실API 연동 (KPI + Alert) | 06-10 |
| 조직 계층 구조 + 권한 시스템 구축 | 06-15 |
| Rule Engine DB화 + 글로벌 5개국 임계값 | 06-15 |
| /record 이벤트 기록 Flow 레이아웃 | 06-20 |
| Essential 페이지 10종 (법적 필수 + 운영 필수) | 06-20 |
| Supabase 마이그레이션 적용 | 06-25 |
| **7/1 MVP 배포 (api.pigos.io + app.pigos.io)** | 07-01 |
