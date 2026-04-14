# PigOS — Roadmap Infographic Data

> 인포그래픽 제작용 구조화 데이터
> 추출 기준: 월간보고서 + 기능정의서 + 글로벌전략기획서

---

## 1. Timeline (월별)

### 2026년 3월 — 기획/설계 완료

- DB 스키마 v1 설계 (49 테이블)
- KPI 계산 명세 (PSY/NPD/FCR/MSY/분만율)
- API 스펙 v1 초안
- 마스터 데이터 시드 초안
- DB 스키마 리뷰 + ERD + 데이터 무결성 스펙
- 글로벌 전략 보고서 (심층분석 16개 섹션)
- 타겟 시장 확정 (US/CN/SEA/LatAm/KR)
- GTM 전략 수립
- 경쟁사 분석 (글로벌 9개사)
- 사업계획서 v2
- MVP 프로토타입 3종 (14페이지 + Lite + AI)
- 컨셉 디자인 5종
- PigPlanCORE → PigOS 리브랜딩 (초기 기획 단계 명칭 CORE에서 변경)
- 7개 언어 현지화 명세
- Next.js 프론트엔드 초기 셋업

### 2026년 4월 — 설계 검증 + 백엔드 착수

- DB 스키마 v1 검증 (정합성, 엣지케이스, 실데이터 매핑)
- Schema-per-tenant 멀티테넌시 구조 검증
- 백엔드 아키텍처 설계 (API 레이어, DB 접근 패턴, tenant 라우팅)
- Phase 1 MVP OpenAPI 3.1 스펙 문서화
- FastAPI 백엔드 MVP 개발 착수
- 마스터 데이터 시드 완성 (이벤트 48종, 질병, 백신, 항생제)
- 모바일 앱 설계 (API 개발과 병행)

### 2026년 5~6월 — Phase 1 MVP 개발 (8주 스프린트)

- 모돈 교배/분만/이유 기록 API + UI
- 모돈 목록/개체 상세/등록/도태 기능
- PSY/NPD 기본 KPI 대시보드
- 기본 알림 (분만/이유 예정)
- 사용자 권한 (농장주/작업자 2단계)
- Android 오프라인 앱 (자동 동기화)
- 한국어/영어/베트남어 UI
- AWS 배포 환경 구축 (EC2/Docker/K8s)

### 2026년 7~9월 — Phase 1.5 (MVP 이후 3~4개월)

- 포유 관리 상세
- 비육돈 배치 관리 기본
- 사료 급여 기록 + 사료빈 재고
- 투약 기록
- 월별 추이 차트
- 일일 종합 일보 / 생산 성적 보고서 / 모돈 대장 보고서

### 2026년 10월~ — Phase 2 (6개월 후)

- 멀티사이트/조직 관리
- 전체 권한 매트릭스
- 건강/방역 전체 모듈
- 출하 관리 전체
- 항생제 보고서
- 멀티사이트 KPI + 벤치마크 비교
- SMS/카카오 알림
- Feed Mill 연동 (북미)
- ERP 연동 (SAP/Oracle)
- iOS 앱

### Phase 3 — 장기 (시점 미정)

- ESG 대시보드
- Genetics/Pedigree 모듈
- 벤치마킹 DB (글로벌)
- IoT 센서 통합 연동
- AI 예측 분석 (사망률, 출하 시기)
- Enterprise 계약 기반 확장

---

## 2. Categorized Tasks

### Development

- DB 스키마 설계/검증 (49 테이블, Schema-per-tenant)
- FastAPI 백엔드 MVP (Python)
- Next.js + TypeScript 프론트엔드
- Android Native 오프라인 앱 (WatermelonDB)
- iOS Native 앱 (Phase 2)
- OpenAPI 3.1 스펙
- PostgreSQL + TimescaleDB + Redis
- AWS 인프라 (Docker + K8s)
- Phase 2: Spring Boot (Java 21) 전환

### Data

- 마스터 데이터 시드 (이벤트 48종, 질병, 백신, 항생제)
- KPI 계산 로직 (PSY/NPD/FCR/MSY/분만율)
- 데이터 무결성 스펙
- 오프라인 동기화 (sync_queue + Last-Write-Wins)
- 월마감 잠금 (period_locks)
- 감사 추적 (audit_log)

### Marketing

- GTM 전략: 영업 없이 퍼지는 구조 (Phase 1 전면 무료)
- 5개 시장 동시 침투 (US/CN/SEA/LatAm/KR)
- 경쟁사 이탈 고객 흡수 (PigKnows/Valstone 인수 반사이익)
- 오픈 연동 생태계 포지셔닝 (vs Valstone 폐쇄형)
- 7개 언어 현지화 (KO/EN/VI/TH/ZH/PT/ES)

### Research

- 글로벌 전략 심층분석 (16개 섹션)
- 경쟁사 기능/가격 분석 (9개사)
- 타겟 시장별 규제/요구사항 조사
- 오프라인 동기화 기술 검증 (WatermelonDB vs SQLite)

---

## 3. Key Milestones

| 마일스톤 | 예상 시점 | 의미 |
|----------|-----------|------|
| 기획/설계 완료 | 2026.03 (완료) | DB + API + 전략 기반 확보 |
| 설계 검증 완료 | 2026.04 | 백엔드 개발 시작 가능 상태 |
| MVP 웹 런칭 (Phase 1) | 2026.06 | 8주 스프린트 완료, SEA 농장주 첫 사용 |
| Android 앱 출시 | 2026.06 | 오프라인 모바일 — SEA 필수 |
| Phase 1.5 출시 | 2026.09 | 사료/비육/보고서 추가 |
| Phase 2 출시 | 2026.12~ | 멀티사이트 + 유료 전환 |
| 임계 농가 수 도달 | 미정 | 유료 전환 트리거 |

---

## 4. Target Markets / Countries

| 시장 | 주요 국가 | 진입 전략 | 가격 민감도 |
|------|-----------|-----------|-------------|
| SEA | 베트남, 태국, 필리핀, 인도네시아 | 전면 무료 → 오프라인 모바일 + 다국어 | 매우 높음 |
| US | 미국, 캐나다 | 무료로 PigKnows 이탈 고객 흡수 | 중간 |
| CN | 중국 | 무료 침투 | 높음 |
| LatAm | 브라질 등 | 무료 침투 | 높음 |
| KR | 한국 | 피그플랜 기존 고객 기반 | 중간 |

- Phase 1: 전 지역 무료 동시 오픈
- Phase 2: 지역별 차등 유료 전환

---

## 5. Core Features vs Additional Features

### Core (Phase 1 MVP — 8주)

- 모돈 교배/분만/이유 기록
- 모돈 목록/개체 상세/등록/도태
- PSY/NPD 기본 KPI 대시보드
- 기본 알림 (분만/이유 예정)
- 사용자 권한 (농장주/작업자)
- Android 오프라인 앱
- 한국어/영어/베트남어 UI
- 단일 농장 관리

### Additional (Phase 1.5+)

- 비육돈 배치 관리
- 사료 급여/재고/FCR 분석
- 투약 기록
- 일일 종합 일보 / 생산 성적 보고서

### Advanced (Phase 2+)

- 멀티사이트 통합 관리
- 건강/방역 전체
- 출하 관리 전체
- 항생제 보고서
- 벤치마크 비교
- Feed Mill 연동
- ERP 연동 (SAP/Oracle)
- iOS 앱

### Long-term (Phase 3)

- ESG 대시보드
- Genetics/Pedigree 모듈
- 글로벌 벤치마킹 DB
- AI 예측 분석
- IoT 센서 통합 연동

---

## 6. Data Sources

### Internal

- 피그플랜 27년 운영 데이터 (1.52억 건) — KPI 검증/시드 데이터용
- 전국 모돈 32% 실시간 관리 점유율 데이터
- PSY 14두(2010) → 22두(2023) 생산성 향상 레퍼런스

### External

- IoT 센서 (온도/습도/환기)
- 전자식 급이기 (ESF)
- 도축장 도체 등급 연동
- ERP 시스템 (SAP/Oracle) — Phase 2
- Feed Mill 시스템 — Phase 2
- pig333.com (글로벌 양돈 벤치마크 통계)
- Verified Market Reports / Capstone Partners (시장 규모 데이터)
