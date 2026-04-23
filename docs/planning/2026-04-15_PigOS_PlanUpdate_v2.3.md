# PigOS 기획서 Update v2.3

> 2026-04-15 | 회의 반영 + 보완 항목 통합
> 대상 섹션: 브랜딩 / 일정 / 패키징 / KPI 설계 / 제품 구조 / 해자
> 하위 문서:
>   - DB Schema v2 — [2026-04-15_db-schema-v2.sql](../specs/2026-04-15_db-schema-v2.sql)
>   - Migration — [2026-04-15_schema-v1-to-v2-migration.md](../specs/2026-04-15_schema-v1-to-v2-migration.md)

---

## 0. 이번 업데이트 요약

| # | 항목 | 결정 | 비고 |
|---|------|------|------|
| 1 | 제품명 | **PigOS** 단일 통일 | PigOS AI / PigOps AI 접미사 제거 |
| 2 | MVP 일정 | 5월 말 완성 → 6월 코드리뷰 → **7월 1일 베이직 출시** | 기존 6월 오픈 취소 |
| 3 | 모바일 | Android + iOS **7월 1일 베이직과 동시 출시** | 기존 iOS 별도 계획 폐기 |
| 4 | 패키징 | 베이직(무료) / 애드온(유료) / 프리미엄(자동화) 3단 | 세부 과금 트리거는 5월 내 확정 |
| 5 | KPI 설계 | Base KPI (PSY·MSY·NPD) 지역 공통 + Addon KPI (FCR 등) 지역별 | `scope_kpi_recommendations` |
| 6 | AI 플랫폼 | Claude API (7월 출시) → **Gemma4 로컬 전환 (12월 검토)** | 21만+ 토큰 컨텍스트 |
| 7 | 연간 로드맵 | 7월 베이직 → 8~11월 애드온 #1~3 순차 → 12월 KPI 풀라인업 | |
| 8 | DB 구조 | `country_configs` → `market_defaults` + `region_defaults` 2단계 | 스키마 v2 |

---

## 0. 핵심 제품 컨셉

```
FarmOS (Base, 무료)          AI Addon (유료)
─────────────────────        ──────────────────────────────
이벤트 입력                  Addon #1 — FCR AI 분석
KPI 자동 산출 (PSY·MSY·NPD)  Addon #2 — 건강·방역 AI 분석
기본 대시보드                 Addon #3 — 원가·재무 AI 분석
이상 감지 알림               Addon #4 — 시장연동 AI 분석
```

**차별화 전략:**
- 경쟁사 (PigCHAMP, MetaFarms 등): FarmOS 기능 자체에 과금 ($500+/yr)
- PigOS: FarmOS 무료 → 데이터 축적 → AI 분석으로 수익화
- "데이터는 무료로, AI 의사결정은 유료로"

---

## 1. 제품 아키텍처 (4-Layer)

> 기존 문서에 산발적이던 컨셉을 프레임워크로 통합.

```
🟢 Layer 1 — Data         수집·기록·KPI 시각화          (베이직 무료)
🟡 Layer 2 — Insight      이상감지·기본예측·농장점수     (베이직)
🟠 Layer 3 — Advisor      What-if·수익영향·액션추천     (애드온 유료)
🔴 Layer 4 — Autopilot    사료자동추천·번식스케줄       (프리미엄)
```

**패키지 ↔ Layer 매핑:**

| Layer | 패키지 | 대표 기능 | 과금 |
|-------|--------|----------|------|
| 1 Data | 베이직 | 이벤트 입력, KPI 대시보드, 기록 관리 | 무료 |
| 2 Insight | 베이직 | 기준값 이탈 경보, 농장 점수화 | 무료 |
| 3 Advisor | 애드온 #1~3 | FCR 최적화, 번식 What-if, 수익 시뮬 | 월 과금 |
| 4 Autopilot | 프리미엄 | 사료 자동 발주, 번식 스케줄링, 알림 실행 | 연 계약 |

---

## 2. AI 성숙도 레벨 (5단계)

| Level | 기능 | PigOS 시점 | 관련 Layer |
|-------|------|-----------|-----------|
| L1 | 데이터 시각화 | 7월 베이직 ✅ | Data |
| L2 | 이상 감지 | 7월 베이직 ✅ | Insight |
| L3 | 예측 | 8~10월 애드온 #1~2 | Insight/Advisor |
| L4 | 추천 (What-if) | 11월 애드온 #3 | Advisor |
| L5 | 자동화 (Autopilot) | 2027+ 프리미엄 | Autopilot |

---

## 3. Before vs After

> 투자자/영업용 1페이지 카드 슬라이드화 가능.

| 영역 | Before (현재 관행) | After (PigOS) |
|------|---|---|
| 의사결정 | 농장주 경험·감 | 데이터 + AI 추천 |
| 문제 대응 | 발생 후 사후 대응 | 예측 기반 사전 예방 |
| 운영 기록 | 수기 장부 + Excel | 자동 수집 + 실시간 대시보드 |
| 사료 관리 | 고정 급이 | FCR 기반 최적화 |
| 질병 관리 | 수의사 재방문 | 조기 경보 + 격리 가이드 |
| 수익 분석 | 월말 정산 | 두당 실시간 수익 추적 |

---

## 4. 개발 일정 (갱신)

| 항목 | 기존 | 변경 |
|------|------|------|
| MVP 완료 | 5월 29일 | **5월 말 완성** |
| 코드 리뷰 | 없음 | **6월 전체 (1개월)** |
| 정식 출시 | 6월 오픈 | **7월 1일 베이직 출시** |
| iOS | 9월 별도 | **Android + iOS 7월 1일 베이직과 동시 출시** |

**연간 로드맵:**

```
5월    — MVP 개발 완료
6월    — 코드 리뷰 / QA / 내부 안정화
7월 1일 — 베이직 출시 (L1·L2, PSY·MSY·NPD)
8월    — 애드온 #1 출시 (FCR 최적화)
9월    — 애드온 #2 출시 (건강·방역 + 항생제 추적)
10~11월 — 애드온 #3 출시 (수익 시뮬)
12월   — KPI 4종 풀 라인업 + Gemma4 로컬 전환 검토
```

---

## 5. 제품 패키징 구조

> 여전히 세부 과금 트리거는 TBD. 구조만 확정.

### 5-1. FarmOS — Base (무료)
- **기능**: 이벤트 입력 (교배·분만·이유·도폐사) + PSY·MSY·NPD 자동 산출 + 기본 대시보드 + 이상 감지 알림
- **리포트**: 월간 KPI 요약 / 농장 점수 vs 국가 평균 / 이벤트 현황 / AI 자연어 분석 리포트 (Claude API) + **PDF 내보내기 포함**
- **목적**: 농가 유입 + 데이터 축적 (경쟁사 대비 무료가 핵심 무기)

### 5-2. AI Addon (월 과금)
> 각 Addon = 특정 기능 영역 전체 (데이터 입력 + AI 분석) 패키지

| Addon | 기능 영역 | AI 적용 |
|-------|----------|---------|
| #1 (8월) | FCR · 사료 입출고 | 사료효율 최적화, 급이 패턴 분석 |
| #2 (9월) | 건강·방역 · 항생제 추적 | 질병 예측, 이상 패턴 감지 |
| #3 (10월) | 원가·재무 · 생산원가 | 두당 수익 시뮬레이션, 비용 최적화 |
| #4 (11월) | 시장연동 · 출하 관리 | 시세 기반 출하 타이밍 AI 추천 |
- **과금 트리거 후보**:
  1. 등록 두수 증가 (100두 / 500두 / 1000두 구간)
  2. 애드온 선택 (모듈별 개별 과금)
  3. 사용량 (AI 호출 / 리포트 생성)

### 5-3. 프리미엄 (연 계약)
- **기능**: Layer 4 Autopilot
- **대상**: 대형 농장, 통합 기업 (1000두 이상)
- **포함**: 전담 컨설팅, 전용 모델 fine-tuning

### 5-4. 미결정 (5월 내 확정)
- [ ] 베이직 무료 한도 기준 (모돈 수? 기록 수? 기간?)
- [ ] 애드온 월 과금액
- [ ] 과금 트리거 1~3개 중 메인 선택
- [ ] 베이직 내 soft paywall 포함 여부 (리포트 export 등)

---

## 6. KPI 설계 원칙

### 6-1. 지역 중립 Base + 지역별 Addon
- **Base (지역 공통)**: PSY, MSY, NPD
- **Addon (지역별)**:
  - NA: FCR (Base 후보), COST
  - EU: ANTIBIOTIC_USE, WELFARE_SCORE (규제로 Base)
  - SEA/SA: 지역 적응형

### 6-2. 4개 기준값 분리
| 컬럼 | 용도 |
|------|------|
| `default_value` | 신규 농장 자동 입력값 |
| `benchmark_avg` | 국가/권역 평균 |
| `benchmark_top25` | 상위 25% |
| `target_value` | 제품 권장 목표 |

### 6-3. 우선순위 조회
```
farm_config > region_defaults > market_defaults > system_defaults
```

DB View: [`effective_metric_values()`](../specs/2026-04-15_db-schema-v2.sql)

### 6-4. 지역 IP 기반 온보딩 추천 UX
```
① IP 감지 → region pre-select (수정 가능)
② 농장 규모·형태 입력
③ scope_kpi_recommendations 조회 → is_base KPI 자동 추천
④ compliance_profiles.requires_* → 규제 필수 KPI 강제 포함
⑤ Addon 안내 (30일 무료 체험)
⑥ 대시보드 진입
```

---

## 7. AI 엔진 아키텍처

```
PigOS DB (농장 데이터)
    ↓
[1] Rule Engine
    default_metric_values 기준값 이탈 감지
    compliance_profiles 규제 조건 검증
    ↓
[2] RAG (pgvector)
    관련 양돈 전문 문서 검색
    ↓
[3] AI API (Claude → Gemma4)
    데이터 + 기준값 4종 + RAG 문서 → 자연어 분석
    ↓
분석 결과 → PigOS 화면 출력
```

**Phase:**

| Phase | 기간 | 내용 |
|-------|------|------|
| 1 | 4~6월 | Rule Engine + v2 스키마 구축 + 양돈 Rule 문서화 |
| 2 | 7월 출시 | Claude API 연동, 자연어 분석 리포트 |
| 3 | 9~11월 | RAG 구축 (pgvector), 양돈 전문 문서 적재 |
| 4 | 12월~ | Gemma4 로컬 전환 검토, 농장별 fine-tuning |

---

## 8. 데이터 락인(Moat) 전략

| 단계 | 기간 | 메커니즘 | 이탈 비용 |
|------|------|---------|-----------|
| 온보딩 | 0~3M | 이벤트 수집 시작 | 낮음 |
| 성장 | 3~12M | 개인화 벤치마크 캘리브레이션 | 중간 |
| 고착 | 1~3Y | 농장별 AI fine-tuning | 높음 |
| 종속 | 3Y+ | 유전·환경·의사결정 전이력 | 매우 높음 |

**3대 락인 축:**
1. **Historical KPI lock** — 27년 PigPlan 벤치마크 + 농장 자체 궤적
2. **Personalized AI lock** — 개별 농장 파인튜닝 모델 = 이전 불가
3. **Ecosystem lock** — Feed mill / 수의사 / 출하 파트너 API 연동

---

## 9. 개발 전 확인 필요 (양돈 Rule 문서화)

> **양돈 전문가 확인 필요 항목**

- [ ] 권역·국가별 PSY·MSY·NPD 평균·상위25%·목표값
- [ ] 이유 후 발정 재귀일수 정상 범위
- [ ] 폐사율 경보 기준 (자돈·육성·비육 구간별)
- [ ] FCR 정상 범위 (구간별)
- [ ] EU 항생제 최대 처치 횟수 규정
- [ ] 번식 장애 원인별 진단 기준
- [ ] 계절별 생산성 변동 패턴
- [ ] 질병(ASF·PRRS·PED) 대응 가이드
- [ ] 농장 규모별 벤치마크 (100두 미만 / 100~500 / 500두 이상)

---

## 10. 미결 의사결정 종합

| 항목 | 내용 | 시점 |
|------|------|------|
| 무료 한도 기준 | 모돈 수 몇 두까지 무료? | 5월 내 |
| Addon 가격 | KPI별 월 과금액 | 6월 내 |
| 과금 트리거 선택 | 두수/애드온/사용량 중 메인 1개 | 5월 내 |
| AI API 선택 | Claude vs GPT-4o vs Gemini | 5월 내 |
| MVP 출시 국가 | **미국·중국·동남아(VN·TH)·남미·한국 — 5개 시장 동시 출시** ✅ | 확정 |
| RAG 문서 범위 | 어떤 문서를 지식 DB에 넣을지 | 7월 전 |
| Gemma4 전환 기준 | API 호출량 임계치 | 12월 검토 |
| 시세 갱신 주기 | `market_price_reference` 일별/주별 | 개발 전 |
| CN 권역 | NEA vs 독립 | DB v2 확정 전 |
| feed_price 분리 | price_reference 통합 vs 별도 | DB v2 확정 전 |
| farms.market_code | 중복 저장 vs region 조인 | DB v2 확정 전 |

---

## 11. 관련 문서

- [db-schema-v2.sql](../specs/2026-04-15_db-schema-v2.sql) — v2.3 DB DDL
- [schema-v1-to-v2-migration.md](../specs/2026-04-15_schema-v1-to-v2-migration.md) — 마이그레이션 가이드
- [db-schema-review-v1.md](../specs/2026-03-31_db-schema-review-v1.md) — v1 검증 리포트 (7건 issue)
- [GlobalStrategy_Content.md](2026-03-18_PigOS_GlobalStrategy_Content.md) — 글로벌 전략 본문
- [2026_roadmap-infographic-data.md](2026_roadmap-infographic-data.md) — 연간 로드맵 데이터
