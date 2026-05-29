# PigOS Addon 서비스 스펙

> 작성: 2026-05-13 | Claude + GPT 3차 토론 최종 합의안
> 출처: pigos_final_full.html / pigos_final_summary.html
> **도메인**: pigos.io (2026-05-18 구매 확정)

---

## 전체 구조

```
FarmOS Base (무료)
├── 이벤트 입력 + KPI 자동 산출 (PSY·MSY·NPD)
├── 기본 대시보드 + Rule Engine 이상 감지 알림
├── Base CLI Q&A (기본 KPI 도메인, 기능 제한)
├── 월간 리포트 + PDF
└── #4 소농 시세 보기·출하 알림 (무료)

    ↓ Addon 구독 시 추가 (각 도메인 특화 CLI Q&A 포함)

Addon #1 FCR Optimizer AI            2026.08 GA   $15~50/월
Addon #2 Health & Mortality AI        2026.09 GA   $20~60/월
Addon #3 Cost/Profit Impact Layer     2026.10 통합  $0 (ROI Layer)
Addon #4 Market-linked Profit Advisor 2026.11 베타  소농 무료 / B2B $2k~10k/월
Addon #5 Breeding & Farrowing AI      2026.10 베타  $15~100/월
Addon #6 Biosecurity & Compliance AI  2026.10 베타  $10~60/월

    ↓ 별도 (농가 Addon 아님)

PigSignal API #1 Benchmark Intelligence   2027.Q1 GA
PigSignal API #2 Market/Cost/Supply       2026.11 베타
PigSignal API #3 Disease Radar            2027 외부 출시
PigSignal API #4 Risk Readiness           2027 이후

Enterprise: Multi-farm Command Center     2026 Q4 베타 / 2027 Q1 GA
```

---

## Addon 공통 구조

각 Addon = **데이터 입력 + Rule Engine 분석 + AI 리포트 + PDF + 도메인 특화 CLI Q&A**

```
CLI Q&A 구조:
┌──────────────────────────────────────────────────────────┐
│ Base CLI     │ 기본 KPI 질문/응답 (PSY·MSY·NPD 등)       │ 무료, 기능 제한
├──────────────────────────────────────────────────────────┤
│ Addon #1 CLI │ FCR·사료 특화  ("왜 FCR이 높아?")         │ #1 구독 시
│ Addon #2 CLI │ 건강·방역 특화 ("PRRS 위험 돈방은?")      │ #2 구독 시
│ Addon #4 CLI │ 시장연동 특화  ("지금 출하가 유리해?")    │ #4 구독 시
│ Addon #5 CLI │ 번식 특화      ("재교배 필요한 모돈은?")  │ #5 구독 시 (90일 단계)
│ Addon #6 CLI │ 방역 특화      ("방역 취약점이 어디야?")  │ #6 구독 시
└──────────────────────────────────────────────────────────┘
```

**API 엔드포인트 패턴:**
```
/addons/{addon_id}/data         ← 데이터 입력
/addons/{addon_id}/analysis     ← Rule Engine 분석 결과
/addons/{addon_id}/report       ← 리포트 생성
/addons/{addon_id}/chat         ← 특화 CLI Q&A
```

---

## Addon #1 — FCR Optimizer AI

> 출시: **2026년 8월 GA** | 전 시장 공통 | 총판 30초 데모 가능

**왜 1순위인가**
사료비 = 생산비 60~70%. FCR 0.1 개선 = 두당 수천원. 모든 농장에 즉각 적용, 입력 데이터가 급이 기록뿐이라 진입 장벽이 낮다.

**과금:** $15~50/월 (모돈 수 Tier)

**MVP 범위**
- 사료 급이량 + 체중 → FCR 자동 계산
- Rule Engine: 기준값 이탈 감지
- LLM: "왜 FCR이 올랐는지" 원인 설명
- 개선 액션 3개 추천
- 월간 FCR 추세 + 손실액 카드 (#3 ROI Layer)

**특화 CLI 예시:** "이번 달 FCR이 높은 이유가 뭐야?" / "어느 돈방 FCR이 제일 나빠?"

**Kill Criteria:** 60일 FCR 입력률 <50% → UX 재설계, CSV import 추가

**API:**
```
/addons/fcr/feed-records    ← 사료 입출고 입력
/addons/fcr/weight-records  ← 체중 측정 입력
/addons/fcr/analysis        ← FCR 계산 + 기준값 비교
/addons/fcr/chat            ← FCR 특화 CLI Q&A
```

---

## Addon #2 — Health & Mortality AI

> 출시: **2026년 9월 GA** | 전 시장 공통 | SEA ASF 경보

**범위 수정 내용**
폐사·치료·임상 기록이 핵심. EU 항생제 보고는 별도 Compliance Module (EU 전용 SKU). 방역 감사는 #6으로 분리. Disease Radar는 2026 내부 집계, 2027 PigSignal API.

**과금:** $20~60/월 (모돈 수 Tier)

**MVP 범위**
- 폐사 기록 + 원인 분류 → 군집 감지
- 치료 이력 + 약품 기록
- SEA: ASF/PRRS 조기 경보 (지역 이상 신호)
- 폐사 손실액 카드 (#3 ROI Layer)
- 수의사 알림 + 월간 Health 리포트

**특화 CLI 예시:** "PRRS 위험 징후 보이는 돈방은?" / "이번 달 항생제 사용량이 많은 이유는?"

**Kill Criteria:** 폐사 원인 "기타/미상" >35% → 원인 선택 UX 간소화

**API:**
```
/addons/health/mortality-records    ← 폐사 기록
/addons/health/treatment-records    ← 치료·약품 기록
/addons/health/analysis             ← 건강·방역 분석
/addons/health/chat                 ← 건강·방역 특화 CLI Q&A
```

---

## Addon #3 — Cost / Profit Impact Layer

> 출시: **2026년 10월 통합** | Base + Addon ROI 엔진 | **독립 과금 없음**

**포지션 재정의**
복잡한 회계 입력 없음. 이벤트 데이터에서 자동 파생. 모든 유료 Addon의 ROI 증명 도구로 활용해 구매 전환 유도.

**과금:** $0 (각 Addon에 포함)

**Addon별 ROI 카드 구성**
| Addon | ROI 카드 내용 |
|-------|--------------|
| #1 FCR | 사료비 손실액 자동 계산 |
| #2 Health | 폐사 손실액 계산 |
| #5 Breeding | NPD 손실액 = "이번 달 ₩XXX 누수 중" |
| #6 Biosecurity | 질병 발생 리스크 비용 추정 |

> 데이터 품질 낮으면 손실액 카드 숨김 처리. 오해 유발 수치 표시 금지.

---

## Addon #4 — Market-linked Profit Advisor

> 출시: **2026년 11월 B2B 베타** | PigSignal 연동 | AgentExchange Market Signal

**3단 구조**
| 대상 | 기능 | 과금 |
|------|------|------|
| 소농 (Base) | 시세 보기, 단순 출하 알림 | 무료 |
| 대형·출하권 보유 농장 (Lite) | 출하 타이밍, 예상 수익, 조기/지연 시뮬레이션 | Addon 또는 Enterprise 포함 |
| B2B (PigSignal API) | 사료사·도축장·보험사 공급 전망·원가 지수 | $2k~10k/월 |

**데이터 소스 (PigSignal 연동)**
| 국가 | 소스 | 주기 |
|------|------|------|
| 한국 | KAMIS | 일별 |
| 미국 | USDA AMS + CME 선물 | 일별 |
| 중국 | 농업농촌부 (MOA) | 일별 |
| 브라질 | CEPEA | 일별 |
| EU | EC DG AGRI | 주별 |
| 베트남·태국 | 각국 농업부 | 주별 |

**특화 CLI 예시:** "지금 출하하면 얼마 벌어?" / "이번 주 돈가 오를까 내릴까?"

**Kill Criteria:** 6개월 B2B LOI 2건 미만 → API 개발 중단, 소농 Base 기능만 유지

**API:**
```
/addons/market/prices           ← 각국 일별 돈가 (PigSignal 연동)
/addons/market/slaughter-plan   ← 출하 계획 입력
/addons/market/recommendation   ← 출하 타이밍 추천
/addons/market/chat             ← 시장연동 특화 CLI Q&A
```

---

## Addon #5 — Breeding & Farrowing AI ★ 신규

> 출시: **2026년 10월 베타 / 12월 GA** | 모돈 Lock-in 최강

**왜 해야 하는가**
NPD 1일 = ₩8,500 손실. 300두 농장 기준 월 150~250만원이 NPD로 누수 중. Base 이유·교배·분만 이벤트 데이터 그대로 재활용. 피그플랜 시드 데이터로 콜드스타트 없음.

**과금:** $15~100/월 (100두 기준 $35)

**MVP 범위 (단계별)**
| 단계 | 기능 |
|------|------|
| 30일 | NPD 계산 + 재교배 알림 + 아하 모먼트 화면 |
| 60일 | 분만 예정/지연 알림, 산차별 성적 비교, PDF 리포트 |
| 90일 | 도태 후보 리스트, 반복 문제 모돈 탐지, CLI Q&A |

**절대 제외:** 카메라 발정 감지, 자동 교배 스케줄, 유전 예측

**특화 CLI 예시 (90일 단계):** "재교배 필요한 모돈은?" / "NPD가 높은 모돈 원인은?"

**Kill Criteria:** 베타 15농가 유료전환 <5곳 → 독립 Addon 범위 축소

**API:**
```
/addons/breeding/events         ← 교배·분만·이유 이벤트 (Base 데이터 재활용)
/addons/breeding/npd            ← NPD 계산 + 누수 손실액
/addons/breeding/alerts         ← 재교배·분만 예정 알림
/addons/breeding/analysis       ← 산차별 성적 비교
/addons/breeding/chat           ← 번식 특화 CLI Q&A (90일 단계)
```

---

## Addon #6 — Biosecurity & Compliance Audit AI ★ 신규

> 출시: **2026년 10월 베타 / 12월 GA** | Insurance 2027 분리

**#2와의 차이**
- #2: "이미 문제가 생겼나?" → 폐사·치료·임상
- #6: "문제가 생길 가능성이 높은가?" → 출입·소독·격리·SOP

**영업 메시지:** "질병 들어오기 전에 구멍을 막습니다"

**과금:** $10~60/월 (수의사 계정 별도)

**MVP 범위 (단계별)**
| 단계 | 기능 |
|------|------|
| 30일 | 방역 체크리스트 + 방역 점수 + 취약 항목 Top 5 |
| 60일 | 차량·방문자·격리·소독 기록 + 월간 PDF 리포트 |
| 90일 | #2 Health 데이터 결합 리스크 신호 + 수의사 공유 |

**절대 제외:** 보험사 자동 전송, 개별 underwriting, 지역 질병 지도 공개

**특화 CLI 예시:** "방역 취약점이 어디야?" / "이번 달 소독 기록이 부족한 구역은?"

**Kill Criteria:** 체크리스트 월 1회 완료 <50% → UX 간소화

**API:**
```
/addons/biosecurity/checklist   ← 방역 체크리스트
/addons/biosecurity/records     ← 차량·방문자·소독 기록
/addons/biosecurity/score       ← 방역 점수 + 취약점 Top 5
/addons/biosecurity/report      ← PDF 리포트
/addons/biosecurity/chat        ← 방역 특화 CLI Q&A
```

---

## 과금 구조 확정 (2026-05-15)

### 핵심 원칙 2가지

**1. 무료 한도 기준 → 도메인 접근 차단**

질문 횟수 제한은 하지 않는다. 농장주 입장에서 불편하고 측정 기준도 모호하다.
대신 "어떤 도메인 질문인가"로 차단한다.

```
Base (무료) 접근 가능 도메인:
- PSY·MSY·NPD 기본 KPI 조회 및 질문
- 번식 기본 이벤트 입력 (교배·분만·이유)
- 이상 감지 알림 확인
- #4 소농 돈가 시세 보기

Addon 구독 필요 도메인:
- FCR·사료 분석 → Addon #1
- 건강·폐사·방역 진단 → Addon #2
- 출하 타이밍·수익 시뮬레이션 → Addon #4 Lite
- 번식 AI·NPD 최적화·도태 후보 → Addon #5
- 방역 감사·리스크 점수 → Addon #6
```

**2. 과금 트리거 → 기능(Addon) 선택, 도메인 기반 접근 제어**

모돈 수 기준은 농장주가 실제보다 낮게 입력하는 어뷰징이 발생한다.
사용량 기반(API 호출 수 등)은 농장주가 비용 예측을 못해 구매를 꺼린다.
**"이 기능 쓰려면 FCR Addon 구독"** 구조가 가장 단순하고 영업 메시지도 명확하다.

→ 구독 = Addon 기능 잠금해제. 구독 취소 = 해당 도메인 즉시 차단.

### 가격 책정 방식 → 모돈 수 Tier 제거, 플랫 월정액

모돈 수 Tier는 어뷰징 우려로 제거. 단순 플랫 월정액으로 전환.
(Enterprise Multi-farm은 별도 계약)

| Addon | 과금 방식 | 확정 가격 |
|-------|-----------|-----------|
| #1 FCR Optimizer | 플랫 월정액 | **$29/월** |
| #2 Health & Mortality | 플랫 월정액 | **$39/월** |
| #3 Cost Layer | 무료 (ROI 엔진) | $0 |
| #4 Market Advisor Lite | 플랫 월정액 | **$19/월** (소농 Base 무료) |
| #4 Market B2B API | B2B 계약 | $2k~10k/월 |
| #5 Breeding AI | 플랫 월정액 | **$35/월** |
| #6 Biosecurity Audit | 플랫 월정액 | **$25/월** |

**번들 예시 (플랫 기준)**
- 중형 농장 All-in: #1 + #2 + #5 = $103 → **번들 $79/월** (23% 할인)
- 방역 민감 농장: #2 + #6 = $64 → **번들 $49/월** (24% 할인)
- 스타터 패키지: #1 + #5 = $64 → **번들 $49/월** (24% 할인)

---

## PigSignal B2B API (Addon 아님)

> 농가가 앱에서 직접 구매하는 Addon이 아닌 B2B API 상품

| API | 대상 | 출시 | 가격 |
|-----|------|------|------|
| #1 Benchmark Intelligence | 사료사·연구기관·AgentExchange | 2027.Q1 GA | $300~5,000/월 |
| #2 Market/Cost/Supply Signal | 사료사·도축장·보험사 | 2026.11 베타 | $2k~10k/월 |
| #3 Disease Radar | 수의 네트워크·지자체 | 2027 외부 출시 | TBD |
| #4 Risk Readiness | 보험사·금융기관 | 2027 이후 | TBD |

---

## 로드맵

| 시점 | 내용 |
|------|------|
| 2026.05~06 | Scope Freeze — Addon 6개 + PigSignal API 확정 |
| 2026.07~08 | Farm OS 출시 + #1 FCR GA |
| 2026.09 | #2 Health GA + SEA ASF 경보 베타 |
| 2026.10 | #5 Breeding + #6 Biosecurity 동시 베타 |
| 2026.11 | #4 Market B2B 베타 + PigSignal Benchmark API 베타 |
| 2026.12 | #5/#6 GA 여부 Kill Criteria 평가 |
| 2027.Q1 | Enterprise Multi-farm GA + AgentExchange 등록 |

---

## 2026년 절대 금지 목록

- Carbon/ESG AI 독립 상품화
- Genetic Performance AI 판매
- Sensor full integration
- Autopilot Scheduling 전체 자동화
- Insurance API 개별 underwriting
- Benchmark를 Addon으로 포장
- "Insurance Readiness"라는 이름 사용

---

## 미결 사항

| 항목 | 상태 | 비고 |
|------|------|------|
| Base CLI 제한 기준 | **확정** | 도메인 접근 차단 (2026-05-15) |
| Addon 과금 트리거 | **확정** | 기능 선택 기반, 플랫 월정액 (2026-05-15) |
| EU Compliance Module | 미결 | #2 범위 수정 후 별도 SKU 설계 |
| Benchmark API 법적 검토 | 미결 | k-anonymity, opt-out, cohort N≥30 |
| #6 수의사 계정 체크리스트 검토 | 미결 | 수의사 2명 검토 필요 |
| #4 Lite 가격 검증 | 미결 | $19/월 → 시장 테스트 후 조정 가능 |
