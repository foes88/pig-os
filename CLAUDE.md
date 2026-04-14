# PigOS

> Global Swine Farm Management SaaS + Data Monetization Platform
> 피그플랜 27년 양돈 노하우 기반 글로벌 버전

---

## 프로젝트 개요

- **제품**: PigOS — 해외 양돈 농장용 Farm Management SaaS
- **포지셔닝**: 벤더-중립 독립 데이터 플랫폼 + 오픈 연동 생태계
- **전략**: 무료 제공 → 데이터 수집 → 수익화 → 농가 배분
- **타겟**: 5개 시장 (US/CN/SEA/LatAm/KR)

---

## 기술 스택 (MVP)

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python) → Phase 2+ Spring Boot (Java 21) |
| Frontend | Next.js + TypeScript |
| Mobile | Android Native + iOS Native |
| DB | PostgreSQL 16+ (Schema-per-tenant) + TimescaleDB (IoT) |
| Cache | Redis 7+ |
| Infra | AWS (싱가포르 리전) + Docker + Kubernetes |
| Offline Sync | WatermelonDB (모바일 로컬 SQLite) |

---

## 폴더 구조

```
pig-os/
├── CLAUDE.md           ← 이 파일
├── docs/
│   ├── specs/          ← DB 스키마, KPI 계산식, API 스펙
│   ├── master-data/    ← 시드 데이터 (질병코드, 백신, 벤치마크)
│   └── api/            ← OpenAPI 스펙
├── src/                ← 소스 코드 (FastAPI)
└── tests/              ← 테스트
```

---

## 핵심 설계 원칙

1. **모듈형 구조**: 11개 모듈 독립 배포 가능 (49 테이블)
2. **지역 중립**: 단일 스키마로 5개 시장 커버 (country_configs)
3. **Schema-per-tenant**: 농장별 데이터 완전 격리
4. **월마감 잠금**: period_locks로 확정 데이터 수정 차단
5. **감사 추적**: 모든 CUD → audit_log
6. **오프라인 동기화**: sync_queue + WatermelonDB (Last-Write-Wins)
7. **Soft Delete**: deleted_at 패턴 (모든 핵심 테이블)

---

## 기획 문서 (biz-report-os 프로젝트)

심층분석 기획서 및 회의 자료는 별도 프로젝트에서 관리:
- `c:/dev/biz-report-os/projects/pig-os/docs/`
- GlobalStrategy.html (심층분석 16개 섹션)
- Meeting2_Prep.html (2차 회의 준비)
- 참고문서/ (지역별 관리포인트, 경쟁사 분석, 개발반영사항)

---

## 다음 할 일

- [ ] 마스터 데이터 시드 완성 (이벤트 48종, 질병, 백신, 항생제)
- [ ] KPI 계산 공식 확정 (PSY/NPD/FCR 엣지케이스)
- [ ] OpenAPI 3.1 스펙 v1
- [ ] MVP 스프린트 시작 (8주)
