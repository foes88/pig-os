# 월간 보고서 — 2026년 4월

> 작성: 2026-04-29 | 기간: 2026-04-01 ~ 2026-04-30

---

## 1. 4월 실적

### 1-1. 브랜딩 / 구조

| 항목 | 상태 | 날짜 |
|------|------|------|
| PigOS AI / PigOps AI → **PigOS** 단일 브랜드 통일 (76개 파일) | ✅ 완료 | 04-14 |
| GitHub repo `pig-os-ai` → `pig-os` rename | ✅ 완료 | 04-14 |
| 핵심 컨셉 확정: **FarmOS(무료) + AI Addon(유료)** | ✅ 완료 | 04-15 |
| Addon 4개 구조 확정 (#1 FCR / #2 건강·방역 / #3 원가·재무 / #4 시장연동AI) | ✅ 완료 | 04-15 |

### 1-2. 기획 문서

| 항목 | 상태 | 날짜 |
|------|------|------|
| 기획서 v2.3 → v2.4 작성 (4-Layer 구조, AI 5단계, Before/After, 데이터 락인) | ✅ 완료 | 04-15 |
| 백엔드 개발 STEP 로드맵 (STEP 1~6, 7월 1일 출시 기준) | ✅ 완료 | 04-15 |
| 마케팅 로드맵 (4~12월 월별 계획) | ✅ 완료 | 04-15 |
| 경쟁사 인텔리전스 문서 (CloudFarms / PLD / PigFlow 분석) | ✅ 완료 | 04-27 |
| PigSignal 영업전략: A2A(메인) + H2A(보조) 동시 운영 | ✅ 완료 | 04-27 |
| 온보딩 UX 수정: IP = 힌트, 농장 소재 국가 직접 선택 필수화 | ✅ 완료 | 04-27 |
| Layer 3 자연어 Q&A (Pull형) DevRoadmap 반영 | ✅ 완료 | 04-27 |

### 1-3. 일정 / 출시 범위 확정

| 항목 | 이전 | 변경 후 | 날짜 |
|------|------|---------|------|
| 모바일 출시 | iOS 9월 별도 | Android + iOS **7월 1일 동시 출시** | 04-15 |
| 출시 국가 | 미확정 | **US / CN / SEA(VN·TH) / BR / KR 5개 시장 동시** | 04-15 |
| Addon 수 | 3개 | **4개** (#4 시장연동AI 추가) | 04-15 |
| 7개 언어 i18n + 반응형·iPad | 누락 | **7월 1일 출시 범위 포함** | 04-15 |
| Base 리포트 + PDF | 유료 검토 | **무료 확정** | 04-15 |

### 1-4. DB 스키마

| 항목 | 상태 | 날짜 |
|------|------|------|
| DB 스키마 v2 DDL — 설정 계층 5개 테이블 + effective_metric_values() | ✅ 완료 | 04-15 |
| 마이그레이션 가이드 v1→v2 (M1~M6) | ✅ 완료 | 04-15 |
| CRITICAL 이슈 7건 반영 (C-01~C-07): 신규 테이블 4개 + 트리거 10종 + CHECK 전수 | ✅ 완료 | 04-27 |
| MAJOR P1 반영 (M-01/M-03/M-06/M-07): 상태전이 트리거, NPD/PSY 뷰 수정 | ✅ 완료 | 04-27 |

### 1-5. 개발 환경

| 항목 | 상태 | 날짜 |
|------|------|------|
| Docker PostgreSQL 검증 환경 구축 (docker-compose + init 스크립트 3종) | ✅ 완료 | 04-27 |
| 검증 시나리오 10종 SQL (상태전이·두수정합·제약위반·뷰·함수) | ✅ 완료 | 04-27 |
| PigPlan Oracle → PostgreSQL 임포트 가이드 | ✅ 완료 | 04-27 |

---

## 2. 4월 주요 의사결정

| 결정 | 내용 | 이유 |
|------|------|------|
| FarmOS 무료 + AI Addon 유료 | 경쟁사(PigCHAMP 등)는 기본 기능도 과금. PigOS는 FarmOS 무료로 농가 유입 → AI로 수익화 | 차별화 |
| 모바일 7월 1일 동시 출시 | roadmap.html 기준 확인. 기존 9월 기재는 오류 | 일정 수정 |
| Addon = 데이터입력+AI분석+AI리포트+PDF 완결 패키지 | Addon별로 해당 도메인 전체를 묶어야 가치 명확 | 패키징 |
| Layer 3 자연어 Q&A 7월 Base 베타 포함 | PLD 경쟁 대응. Claude API 추가 비용 없이 구현 가능 | 경쟁 대응 |
| 온보딩 농장 소재 국가 직접 선택 필수화 | 해외 거주 농장주가 접속 시 IP ≠ 실제 농장 위치 케이스 대응 | UX 정확성 |
| DB CRITICAL 7건 전부 반영 (개발 전) | 개발 착수 후 스키마 변경 시 리팩토링 비용 큼 | 설계 완결성 |

---

## 3. 5월 계획

### 블로킹 이슈 (개발 착수 전 해결 필요)

| 항목 | 담당 | 기한 |
|------|------|------|
| DB 스키마 PostgreSQL 실제 적용 검증 (Docker 환경 완비) | Claude + 개발자 | 5월 1주 |
| **과금 구조 확정** — 무료 한도 기준, 과금 트리거 메인 1개 선택 | 의사결정 필요 | 5월 1주 |
| **AI API 선택** — Claude vs GPT-4o vs Gemini | 의사결정 필요 | 5월 1주 |
| OpenAPI 3.1 스펙 v1 작성 | Claude | 5월 1~2주 |

### 개발 착수 (5월 MVP 8주 스프린트)

| 항목 | 기간 |
|------|------|
| FastAPI 프로젝트 셋업 + 인증 (JWT + refresh token) | 5월 1~2주 |
| 마스터 데이터 API + 온보딩 API | 5월 3~4주 |
| 이벤트 입력 API + KPI 계산 엔진 | 5월 5~6주 |
| 대시보드 API + Rule Engine + Claude API 연동 | 5월 7~8주 |

### 추가 설계 작업

| 항목 | 기간 |
|------|------|
| INSPIG Rule → 국가별 default_metric_values SQL 시드 (KR 완성 + US/EU 추가) | 5월 1주 |
| 양돈 Rule 문서화 9개 항목 (전문가 확인) | 5월 중 |
| CN 권역 결정 (NEA vs 독립) | 5월 중 |

---

## 4. 미결 의사결정 (5월 내 확정 필요)

| 항목 | 옵션 | 기한 |
|------|------|------|
| 무료 한도 기준 | 모돈 수 기준? 기록 수? 기간 제한? | 5월 1주 |
| 과금 트리거 메인 | ① 두수 구간 / ② Addon 선택 / ③ 사용량 | 5월 1주 |
| AI API | Claude (현재 계획) / GPT-4o / Gemini | 5월 1주 |
| CN 권역 코드 | NEA 포함 vs 독립 시장 | 5월 중 |
| farms.market_code | 컬럼 추가 vs region 조인으로 대체 | 개발 전 |

---

## 5. 현재 블로커

| 블로커 | 현황 |
|--------|------|
| Docker Desktop 미실행 | DB 검증 대기 중. Docker Desktop 켜면 즉시 실행 가능 |
| 과금 구조 미확정 | subscription 테이블 설계에 영향. 개발 착수 전 결정 필요 |
| 양돈 Rule 전문가 확인 | 기준값 초안 있음 (INSPIG 데이터). 전문가 검토 필요 |

---

## 6. 산출물 목록 (4월 생성 파일)

| 파일 | 설명 |
|------|------|
| [docs/planning/2026-04-15_PigOS_PlanUpdate_v2.4.md](../2026-04-15_PigOS_PlanUpdate_v2.3.md) | 기획서 v2.4 |
| [docs/planning/2026-04-15_PigOS_DevRoadmap.md](../2026-04-15_PigOS_DevRoadmap.md) | 백엔드 개발 STEP 로드맵 |
| [docs/planning/2026-04-15_PigOS_MarketingRoadmap.md](../2026-04-15_PigOS_MarketingRoadmap.md) | 마케팅 로드맵 |
| [docs/planning/2026-04-27_PigOS_CompetitorIntel.md](../2026-04-27_PigOS_CompetitorIntel.md) | 경쟁사 인텔리전스 |
| [docs/specs/2026-04-15_db-schema-v2.sql](../../specs/2026-04-15_db-schema-v2.sql) | DB 스키마 v2 DDL |
| [docs/specs/2026-04-15_schema-v1-to-v2-migration.md](../../specs/2026-04-15_schema-v1-to-v2-migration.md) | 마이그레이션 가이드 |
| [tests/db/](../../../tests/db/) | Docker PostgreSQL 검증 환경 |
