# PigPlanCORE 변경 흐름 (Changelog)

> 프로젝트가 어떻게 발전해왔는지 단계별 기록

---

## Phase 0: 프로젝트 초기 설정
> 최초 기획 → 스펙 문서화

- DB 스키마 v1 (49 테이블, 11 모듈) + KPI 계산 명세
- API 스펙 v1 (30 엔드포인트)
- 마스터 데이터 시드 (이벤트 48종, 질병 30종, 백신 22종, 항생제 22종)
- 기획서/회의자료/참고문서를 레포로 통합
- 2차 미팅 자료 작성 (경쟁사 6권역 + 개발 스펙)

**이 시점의 방향: 6개 권역(KR/EU/US/BR/SEA/CN) 대상 양돈 관리 SaaS**

---

## Phase 1: MVP 프로토타입 제작
> UI를 눈에 보이게 만듦

### MVP 풀버전 (13페이지)
- index.html (대시보드)
- sows.html (모돈관리)
- sow-detail.html (모돈 상세)
- breeding.html (번식 파이프라인)
- record.html (이벤트 기록)
- kpi.html (KPI 대시보드)
- fattening.html (비육)
- feed.html (사료/원가)
- health.html (건강/방역)
- shipment.html (출하)
- ai-insights.html (AI 인사이트)
- reports.html (보고서)
- settings.html (설정)

### MVP Lite (미니멀 4페이지)
- index.html, sows.html, record.html, kpi.html
- Owner Dashboard (농장주 관점 질문 기반 UI)

### UI 컨셉 5종
- 엔터프라이즈 / 현장 운영 / AI / 돈군관리 / 번식 워크플로우

### UI 개선
- CSS 톤다운 (여백/색상/노이즈)
- 사이드바 메뉴 13페이지 전체 통일
- 깨진 링크 전부 수정
- 농장명: 안성 1농장 → Wiselake Farm

---

## Phase 2: 2차 미팅 자료 작성 + 발표 준비
> 미팅 보고서 + 발표 스크립트

- 2차 미팅 준비 보고서 (HTML)
- 발표 스크립트 (모바일 최적화 HTML)
- presentations/ 폴더 분리

---

## Phase 3: 미팅 자료 대규모 수정
> 피드백 반영 + 팩트 체크 + 현실화

### 제거한 것들
- "대표님" 관련 문구 전부 제거
- 피그플랜 기존 분석 로직 재사용 언급 제거
- 피그플랜 27년 개발 비용 회수 문구 제거
- Oracle MCP 분석 섹션 → DB 신규 설계로 교체
- Q&A/체크리스트 섹션 → 발표 스크립트로 이동
- 가격 대응 전략 섹션 제거 (근거 부족)
- "아시아어 차별화" 전부 제거 (Cloudfarms 24개 언어 지원 확인)
- 브라질/중국 기능 설명 제거 (근거 부족)
- P2 유료 → P2 출시 (유료 여부 미정)

### 변경한 것들
- 한국(KR) 시장 제거 → 5개 권역 (EU/US/BR/SEA/CN)
- 6개 권역 → 5개 권역
- FastAPI 권고 문구 비개발자 친화적으로 수정
- "AI 분석 민주화" → "AI 분석 — 대형 전용이 아닌 전 농장 제공"
- 역할별 권한 4단계 → 6단계 (업계 표준 반영)
- 질병 경보: SEA 전용 → 글로벌 전 지역
- 다사이트: Phase 2 → Phase 1
- 마스터 데이터 테이블에 출처 컬럼 추가
- 경쟁사 가격 테이블: 미국 5개사 → 글로벌 9개사
- Phase 1 필수 항목 배경색 강조

### 일정 변경 이력
1. 8주 MVP → 12~14주 웹 런칭
2. 12~14주 → 웹 8주 + 모바일 10주
3. 월 표기 제거 → 주 단위만
4. 검증 3주로 확대 (개발과 동일 비중)
5. Slack 피드백 체크포인트 3회 추가 (2주/5주/8주차)

---

## Phase 4: 전략 심층분석 + 미팅 피드백 반영
> Q1~Q3 답변 + 미팅 후 피드백

### Strategy Deep Dive 문서 생성
- Q1: API 아키텍처 (Schema-per-tenant + TimescaleDB + PowerSync)
- Q2: 수익 모델 (SaaS 구독 + B2B 데이터 API)
- Q3: 국가별 진입 → 투자 효율 기준 마케팅 집중도

### GTM 전략 진화
1. 초기: 순차 진입 (베트남 1순위)
2. 변경: 전 권역 동시 오픈 + 마케팅 집중도 구분
3. Partner-led 삭제 (파트너 없음)
4. 영문 약어 한글화 (Product-led → 제품 중심 확산)
5. 영업사원 방문 제거 → 온라인 전용
6. 최종: "제품이 영업 / 사용자가 퍼뜨림 / 콘텐츠가 신뢰"

### 타겟 시장 변경
1. 6개 권역 (KR/EU/US/BR/SEA/CN)
2. → 한국 제거, 5개 권역 (EU/US/BR/SEA/CN)
3. → EU 제거, 한국 추가: **미국/중국/동남아(VN·TH)/남미/한국**
4. 한국 = Reference 시장 (피그플랜 유사+추가개발)

### 미팅 피드백 반영
- 도체등급 연동 설명 보강 (국가별 등급 체계 상이)
- 다중농장: 내 농장=기본, 업체관리=추후 모듈+과금
- 구간별 과금 (200두↓무료 / 구간별 TBD / 5000+협상)
- 오프라인: Phase 1 → Phase 2
- 모바일: React Native → Android Native + iOS Native

### 조사 결과 추가
- Schema-per-tenant: 수천 농장 안정, 5000+ Citus 확장
- AWS vs Azure vs GCP: GCP $245/월 최저, 크레딧 $200K
- 결제: Stripe 한국법인 직접 사용 가능
- 경쟁사 테스트: PigCHAMP/PigKnows Free Trial 확인

---

## Phase 5: 문서 구조 재배치 + v2 분리
> 9섹션 → 6섹션 자연스러운 흐름

### 기존 (9섹션, 왔다갔다)
01 국가별 기능 → 02 경쟁사 가격 → 03 기술스택 → 04 DB설계 → 05 일정 → 06 경쟁사상세 → 07 5권역 → 08 개발스펙 → 09 타겟+수익

### 변경 (6섹션, 전략→실행)
01 타겟 시장 → 02 경쟁 환경 → 03 수익+GTM → 04 기술 → 05 스펙+일정 → 06 Summary

### 파일 분리
- 원본: `2026-03-23_CORE_Meeting2_Prep.html` (2차 미팅 그대로)
- v2: `2026-03-23_CORE_Meeting2_Prep_v2.html` (피드백 반영 최신)

---

## Phase 6: 컨셉 전환 — SaaS → AI 플랫폼
> 가장 큰 방향 전환

| 구분 | v1 (SaaS) | v2 (AI 플랫폼) |
|------|-----------|---------------|
| 제품 정의 | 양돈 관리 SaaS | 양돈 수익 최적화 AI 운영 시스템 |
| 기술 구조 | CRUD 기반 | Event-driven + Time-series + AI Agent |
| AI 역할 | 보조 (리포트/챗봇) | 핵심 (의사결정 + 실행) |
| 과금 | Per-seat 구독 | Platform 무료 → Usage → Outcome 기반 |
| 한 줄 | 기록하는 시스템 | **돈을 만들어주는 시스템** |

### 홈페이지 섹션 콘텐츠 제작
- i18n KO/EN 텍스트
- 이미지 AI 생성 프롬프트 4종 (섹션 배치용 16:9)
- 컴포넌트 배치 가이드

### 언어 확장
- 5개 → 7개 언어
- 추가: 브라질 포르투갈어(pt-BR) + LATAM 스페인어(es-419)
- 로케일 코드 정의
- 현지화 명세 테이블 7개국 분리

---

## 현재 상태 (Latest)

### 문서 목록
| 문서 | 위치 | 설명 |
|------|------|------|
| 2차 미팅 원본 | `docs/meeting-prep/...Prep.html` | 미팅 당시 그대로 |
| 글로벌 전략 v2 | `docs/meeting-prep/...Prep_v2.html` | 피드백 전부 반영 최신 |
| 발표 스크립트 | `docs/presentations/...Script.html` | 발표용 |
| Strategy Deep Dive | `docs/presentations/...Deep_Dive.html` | Q1~Q3 상세 |
| 조사 결과 | `docs/references/06_조사결과...html` | 인프라/결제/스키마 |
| 오프라인 수요 | `docs/references/05_오프라인수요...html` | 정량 분석 |
| 홈페이지 섹션 | `docs/homepage_pigplancore_section.md` | AI 컨셉 반영 |
| 프로젝트 오버뷰 | `docs/pigplancore_overview.md` | 상세 |
| 프로젝트 요약 | `docs/pigplancore_summary.md` | 홈페이지용 간략 |
| MVP 풀버전 | `mvp/` | 13페이지 프로토타입 |
| MVP Lite | `mvp-lite/` | 4페이지 미니멀 |
| UI 컨셉 | `concepts/` | 5종 디자인 |

### 다음 할 것 (v2 제작 필요)
- [ ] 기획서 v2 — SaaS→AI 플랫폼 전환 반영 기능정의서
- [ ] MVP 프로토타입 v2 — AI Agent 대시보드 중심 UI
- [ ] DB 스키마 v2 — Event-driven + AI Agent 구조
