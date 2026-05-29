# PigOS 기획서 Update v2.4

> 2026-05-06 | v2.4 → v2.5 업데이트
> 대상 섹션: Salesforce 파트너십 현황 반영 / AgentExchange MCP 전략 추가
> **도메인**: pigos.io (2026-05-18 구매 확정)
> 하위 문서:
>   - DB Schema v2 — [2026-04-15_db-schema-v2.sql](../specs/2026-04-15_db-schema-v2.sql)
>   - Migration — [2026-04-15_schema-v1-to-v2-migration.md](../specs/2026-04-15_schema-v1-to-v2-migration.md)
>   - 경쟁사 인텔리전스 — [2026-04-27_PigOS_CompetitorIntel.md](2026-04-27_PigOS_CompetitorIntel.md)

---

## 0. 이번 업데이트 요약

### v2.3 (2026-04-15)
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

### v2.4 (2026-04-27)
| # | 항목 | 변경 전 | 변경 후 |
|---|------|---------|---------|
| 1 | 온보딩 UX | IP 감지 → region pre-select (수정 가능) | IP = 힌트(참고용), **농장 소재 국가 직접 선택 필수** |
| 2 | PigSignal 전략 | A2A 보류 | **A2A + H2A 동시 운영** (A2A 메인, H2A 보조) |
| 3 | 이메일 캠페인 | 일반 마케팅 목적 | **H2A 수요처(사료사·도축장·보험·연구기관) 직접 영업** 목적으로 명확화 |
| 4 | Layer 3 AI | 월간 리포트 생성(Push)만 | **자연어 Q&A(Pull) 추가** — 7월 Base 베타 포함 검토 |

### v2.5 (2026-05-06)
| # | 항목 | 내용 |
|---|------|------|
| 1 | Salesforce 파트너십 | **ISV 파트너 가입 완료 + AppExchange 승인 완료** |
| 2 | 데이터 유통 채널 | AgentExchange에 PigOS 데이터 API를 **MCP 서버**로 등록 — Agentforce 생태계에서 PigOS 데이터 직접 접근 가능 |
| 3 | Agentforce 연동 | Agentforce Operations (백오피스 자동화) 연동 계획 추가 — 2026년 5월 베타 진입 타이밍에 맞춰 테스트 |
| 4 | ISV GTM | AppExchange 비공개 제안·자동 프로비저닝 활용 → PigOS 구독 판매 채널 확장 |

---

## 0. 핵심 제품 컨셉

```
FarmOS (Base, 무료)               AI Addon (유료)
──────────────────────────        ──────────────────────────────────────
이벤트 입력                       Addon #1 — FCR Optimizer AI       $15~50/월
KPI 자동 산출 (PSY·MSY·NPD)       Addon #2 — Health & Mortality AI  $20~60/월
기본 대시보드                      Addon #3 — Cost/Profit Layer      $0 (ROI 엔진)
이상 감지 알림                     Addon #4 — Market Advisor         소농 무료/B2B
Base CLI Q&A (기본 KPI, 제한)      Addon #5 — Breeding & Farrowing   $15~100/월
#4 소농 시세 알림 (무료)           Addon #6 — Biosecurity Audit AI   $10~60/월
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
| 3 Advisor | 애드온 #1·#2·#4·#5·#6 | FCR 최적화, 건강·방역, 번식, 시장연동, 방역 감사 | 월 과금 |
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
- **리포트**: 월간 KPI 요약 / 농장 점수 vs 국가 평균 / 이벤트 현황 / AI 자연어 분석 리포트 + **PDF 내보내기 포함**
- **CLI Q&A (무료 포함, 기능 제한)**: 자연어로 AI에 질문/응답 가능. Base는 기본 KPI 도메인으로 제한. Addon 도메인 Q&A는 해당 Addon 구독 시 해제. (제한 기준 TBD — 질문 횟수 or 도메인)
- **목적**: 농가 유입 + 데이터 축적. CLI Q&A는 현재 업계 트렌드 대응 (SwineWeb Q1 2026 확인)

### 5-2. AI Addon (이용 시 과금)
> Addon 6개 확정 (2026-05-13, Claude + GPT 3차 토론 최종 합의)
> 상세 스펙: [2026-05_PigOS_AddonSpec.md](2026-05_PigOS_AddonSpec.md)

각 Addon = **데이터 입력 + Rule Engine 분석 + AI 리포트 + PDF + 도메인 특화 CLI Q&A** 완결 패키지

```
CLI Q&A 구조:
┌──────────────────────────────────────────────────────────┐
│ Base CLI     │ 기본 KPI 질문/응답 (PSY·MSY·NPD 등)       │ 무료, 기능 제한
├──────────────────────────────────────────────────────────┤
│ Addon #1 CLI │ FCR·사료 특화  ("왜 FCR이 높아?")         │ #1 구독 시
│ Addon #2 CLI │ 건강·방역 특화 ("PRRS 위험 돈방은?")      │ #2 구독 시
│ Addon #4 CLI │ 시장연동 특화  ("지금 출하가 유리해?")    │ #4 구독 시
│ Addon #5 CLI │ 번식 특화      ("재교배 필요한 모돈은?")  │ #5 구독 시
│ Addon #6 CLI │ 방역 특화      ("방역 취약점이 어디야?")  │ #6 구독 시
└──────────────────────────────────────────────────────────┘
```

| Addon | 기능 영역 | 과금 | 출시 |
|-------|----------|------|------|
| #1 FCR Optimizer AI | FCR·사료 입출고 | $15~50/월 | 2026.08 GA |
| #2 Health & Mortality AI | 건강·폐사·치료 | $20~60/월 | 2026.09 GA |
| #3 Cost/Profit Layer | 원가·손실 가시화 | $0 (ROI 엔진) | 2026.10 통합 |
| #4 Market Advisor | 시장연동·각국 일별 돈가 | 소농 무료 / B2B $2k~10k | 2026.11 베타 |
| #5 Breeding & Farrowing AI ★ | 번식·분만·모돈 최적화 | $15~100/월 | 2026.10 베타 |
| #6 Biosecurity Audit AI ★ | 방역 감사·점수화 | $10~60/월 | 2026.10 베타 |
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

### 6-4. 온보딩 추천 UX (v2.4 수정)

> **핵심 원칙**: IP는 편의 힌트, KPI 기준값은 항상 **농장 소재 국가** 기준

```
① IP 감지 → "미국으로 감지됐어요" (참고용 표시, 강제 아님)
② "농장이 위치한 국가를 선택해주세요" ← 필수 확인 단계
   - IP 감지 국가 pre-select (변경 가능)
   - 반드시 사용자 직접 확인/변경 후 다음 진행
   - 이유: 미국 거주자가 한국에서 접속 시 IP ≠ 농장 위치
③ 농장 규모·형태 입력 (모돈 수, 일관/번식/비육)
④ scope_kpi_recommendations 조회 (선택한 농장 국가 기준)
   → compliance_profiles.requires_* → 규제 필수 KPI 강제 포함
⑤ Addon 안내 → 대시보드 진입
```

| 구분 | 용도 | 강제 여부 |
|------|------|----------|
| IP 감지 국가 | 국가 선택 pre-select 힌트 | ❌ 참고용 |
| 농장 소재 국가 | KPI 추천·기준값 적용 기준 | ✅ 필수 선택 |

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

## 8. PigSignal 영업 전략 (v2.4 신규)

### 8-1. A2A + H2A 동시 운영

```
PigSignal API
    ├── A2A (Agent to Agent) ← 메인
    │   → AgentExchange 입점 → AI 에이전트가 자동 발견·호출
    │   → Salesforce AI, 기타 AgTech AI들이 자동 연결
    │   → 별도 영업 액션 불필요, 노출 = 영업
    │
    └── H2A (Human to Agent/API) ← 보조
        → 사료회사·도축장·보험사·연구기관 직접 영업
        → 이메일 캠페인으로 수요처 인지도 확보
        → 담당자가 직접 구매·활용
```

### 8-2. 채널별 역할

| 채널 | 주요 수요처 | 영업 방식 | 특징 |
|------|------------|----------|------|
| A2A | AgTech AI, Salesforce 에코시스템 | 입점 = 영업 완료 | 자동화, 확장성 |
| H2A | 사료·도축·보험·연구기관 | 이메일·직접 영업 | 고단가, 관계 기반 |

### 8-3. H2A 이메일 캠페인 방향

- 주 1회 정기 발송, 트렌드·계절 요인 반영 타겟 조정
- Radar Desk 기반 수요처 리스트 지속 업데이트
- **목적**: 일반 마케팅이 아닌 **H2A 수요처 직접 계약 유도**

---

## 9. Salesforce 파트너십 전략 (v2.5 신규)

### 9-0. 현황 (2026-05-06 기준)
| 항목 | 상태 |
|------|------|
| Salesforce ISV 파트너 가입 | ✅ 완료 |
| AppExchange 앱 등록 승인 | ✅ 완료 |
| AgentExchange MCP 서버 등록 | 🔲 예정 |
| Agentforce Operations 연동 테스트 | 🔲 예정 (2026년 5월 베타) |

### 9-1. 왜 Salesforce 생태계인가
- **AgentExchange**: 2026 TDX 발표 — AppExchange + Slack 마켓플레이스 + Agentforce를 단일 스토어로 통합. 현재 13,600개 앱·에이전트·MCP 서버 등록. **키워드가 아닌 비즈니스 의도 기반 검색** → PigOS 발견 가능성 향상.
- **Agentforce Operations**: 재고 관리·온보딩·컴플라이언스 체크 등 백오피스 자동화 지원 (2026년 5월 베타). 양돈 농장 운영 자동화와 직접 연결.
- **ISV GTM 앱**: 비공개 제안·통합 결제·자동 프로비저닝 → PigOS 구독 판매 채널 확장.

### 9-2. PigOS ↔ Salesforce 연동 구조
```
Salesforce CRM (고객 농장)
    ↓  Connected App (OAuth 2.0)
PigOS FastAPI
    ↓  MCP 서버 프로토콜
AgentExchange 에이전트
    ↓
Agentforce Operations
  → 사료 발주 자동화
  → 번식 일정 알림
  → 컴플라이언스 체크
```

### 9-3. MCP 서버 구현 범위 (개발 추가 항목)
| API | 설명 | 우선순위 |
|-----|------|---------|
| `get_farm_kpi` | PSY·MSY·NPD 현재값 + 벤치마크 | P1 (7월) |
| `get_alerts` | 이상 감지 알림 목록 | P1 (7월) |
| `get_sow_status` | 모돈별 현재 상태 (임신·분만·이유) | P2 (8월) |
| `post_event` | 이벤트 입력 (교배/분만/이유) | P2 (8월) |
| `get_benchmark` | 국가별 KPI 기준값 조회 | P3 (9월) |

### 9-4. 수익 연결
- **데이터 API 판매 채널**: AgentExchange를 통해 Salesforce 생태계 내 수요처(사료사·보험·연구기관)에 PigOS 집계 데이터 API 직접 유통 가능 → **PigSignal A2A 수익화** 가속
- **$50M Builders Initiative**: Salesforce AgentExchange Builders Initiative 신청 검토 (MCP 서버·에이전트 개발자 대상 지원금)

---

## 10. 하드웨어 중립 오픈 API 전략 (v2.5 신규)

> Eco-Pork·Big Dutchman·Fancom 등 하드웨어 번들 플레이어가 동남아 시장 동시 진입 중 → PigOS 포지션 명문화

PigOS는 특정 하드웨어에 종속되지 않는 오픈 API 생태계를 지향한다. Eco-Pork 바이오센싱 카메라·Big Dutchman IoT·Fancom 환경센서 등 외부 하드웨어 데이터를 PigOS로 연동 가능하도록 설계하며, 하드웨어 벤더를 경쟁자가 아닌 파트너 에코시스템으로 흡수하는 것을 차별화 전략의 핵심으로 삼는다.

| 하드웨어 벤더 | 데이터 유형 | PigOS 연동 포인트 |
|---|---|---|
| Eco-Pork | 카메라 영상 → 발정·분만 감지 | Breeding AI Addon 또는 Layer 2 이상 감지 |
| Big Dutchman | 급이·환기·온도 IoT | `environment_readings` + `feed_records` |
| Fancom | 온도·습도·CO₂ 센서 | `environment_readings` (TimescaleDB) |

**경쟁 구도 재정의**: 하드웨어 벤더는 PigOS의 데이터 수집 파트너, PigOS는 분석·AI 레이어 → Win-Win

---

## 11. 데이터 락인(Moat) 전략

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

## 10. 개발 전 확인 필요 (양돈 Rule 문서화)

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

## 12. 미결 의사결정 종합

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

## 13. 관련 문서

- [db-schema-v2.sql](../specs/2026-04-15_db-schema-v2.sql) — v2.3 DB DDL
- [schema-v1-to-v2-migration.md](../specs/2026-04-15_schema-v1-to-v2-migration.md) — 마이그레이션 가이드
- [db-schema-review-v1.md](../specs/2026-03-31_db-schema-review-v1.md) — v1 검증 리포트 (7건 issue)
- [GlobalStrategy_Content.md](2026-03-18_PigOS_GlobalStrategy_Content.md) — 글로벌 전략 본문
- [2026_roadmap-infographic-data.md](2026_roadmap-infographic-data.md) — 연간 로드맵 데이터
