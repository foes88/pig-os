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

### 1-5. 모바일 — Android 70% / iOS 60%

#### Android (github.com/wiselake/pigos-android)

| 항목 | 상태 | 내용 |
|------|------|------|
| 기술 스택 | ✅ | Kotlin + Jetpack Compose (Material 3) + Hilt + MVVM |
| 화면 구현 | ✅ | 9종 — 로그인·대시보드·모돈(목록/상세)·자돈·비육돈·기록·채팅·온보딩·설정 |
| 오프라인 동기화 | ✅ | Room → SyncQueue → WorkManager(SyncWorker) → POST /sync |
| 인증 | ✅ | JWT (DataStore) + AccessToken 자동 갱신 (TokenAuthenticator) |
| API 연동 | ✅ | Retrofit + OkHttp + AuthInterceptor |
| 양방향 동기화 | ✅ | Upload(변경분) + Download(server_changes) 완성 |
| CI/CD | ✅ | GitHub Actions (android.yml) |
| 테스트 | ✅ | JVM 유닛 36케이스 (ViewModel + Repository + Fake) |
| 남은 작업 | 🔜 | 비육돈/자돈 상세 화면, 날짜 피커 UI, Compose UI 테스트 |

#### iOS (github.com/wiselake/pigos-ios)

| 항목 | 상태 | 내용 |
|------|------|------|
| 기술 스택 | ✅ | Swift 5.9 + SwiftUI + SwiftData + 수동 DI (AppContainer) |
| 화면 구현 | ✅ | 8종 — 로그인·대시보드·모돈(목록/상세)·온보딩·채팅·기록(도폐사·임신사고)·모돈등록 |
| 오프라인 동기화 | ✅ | SwiftData 로컬 저장 → BGTaskScheduler 백그라운드 동기화 |
| 인증 | ✅ | JWT (Keychain) + 자동 refresh + 토큰 로테이션 |
| API 연동 | ✅ | URLSession + APIClient + DTO |
| 배포 대상 | ✅ | iOS 17.0+ / iPhone + iPad (XcodeGen) |
| 남은 작업 | 🔜 | Reports/More ViewModel, 동기화 다운로드 완성, UI 테스트 |

#### 모바일 공통 현황

| 지표 | Android | iOS |
|------|---------|-----|
| 진도 | **70%** | **60%** |
| 구현 화면 수 | 9종 | 8종 |
| 테스트 | 36케이스 | 초기 단계 |
| 오프라인 동기화 | Room + WorkManager | SwiftData + BGTask |
| CI/CD | GitHub Actions | 미설정 |

---

## 2. 수치 요약

| 지표 | 값 |
|------|-----|
| DB 테이블 | 40개 |
| API 엔드포인트 | 50+ |
| 통과 테스트 | 58개 (통합) + 43개 (unit) + 36개 (Android JVM) |
| 구현 화면 수 | 웹 22종 + Android 9종 + iOS 8종 = **39종** |
| 모바일 진도 | Android 70% / iOS 60% |
| 신규 문서 | 오프라인 sync 스펙, OpenAPI v1, Android 개발 가이드, 디자인 가이드 |
| 도메인 | pigos.io (2026-05-18 확보) |

---

## 3. 6월 진행 현황 (06-01 ~ 06-05)

| 항목 | 상태 | 완료일 |
|------|------|--------|
| UI Shell 통합 (Sidebar + Topbar + BottomNav + Drawer) | ✅ 완료 | 06-04 |
| /dashboard 실API 연동 (KPI + Alert) | ✅ 완료 | 06-04 |
| 조직 계층 구조 + 권한 시스템 (SUPER_ADMIN/VENDOR/DEALER 등 10개 롤) | ✅ 완료 | 06-05 |
| Rule Engine DB화 — 글로벌 5개국(KR/US/BR/CN/VN) 임계값 | ✅ 완료 | 06-05 |
| /record 이벤트 기록 Flow 레이아웃 (분만 스테퍼+자동계산+난이도) | ✅ 완료 | 06-05 |
| Essential 페이지 10종 (약관·인증·결제·공지·지원·점검·업데이트 등) | ✅ 완료 | 06-05 |
| Codex 코드 검증 (권한 시스템 + 마이그레이션) | ✅ 완료 | 06-05 |
| Unit 테스트 76개 전체 통과 | ✅ 완료 | 06-05 |

## 4. 남은 작업 (~ 7/1 출시)

| 항목 | 목표일 |
|------|--------|
| Supabase 마이그레이션 적용 | 06-25 |
| /farrowing·/reports 링크 처리 | 06-25 |
| **FastAPI 배포 (api.pigos.io)** | 06-28 |
| **Next.js 배포 (app.pigos.io)** | 06-28 |
| **7/1 MVP 공개 출시** | 07-01 |
