# PIGOS_FEATURE_ENTITLEMENT_MATRIX v0.1
## 무료·트라이얼·유료 기능 매트릭스 (paywall 위치 SSOT)

> **상태**: DRAFT — 전 행 decision_status=PROPOSED. 본 문서 승인 = D-08(두수 무제한)·D-09(경영 P0)·D-10(R1/R2 경계) 일괄 승인.
> **승인자**: 대표 / **작성**: CTO
> **근거**: 2026-07-21 회의 (docs/meetings/MEETING_NOTES_2026-07-21.md §2) · COUNTRY_KPI_RULE_SPEC v0.3.1 §7
> **원칙**: "데이터 입력을 막지 않으면서 고부가가치 결과에 과금한다" — Capture 무료 / Insight 기본무료·고급유료 / Automation·Transaction 유료

---

## 0. 결정 요청 (승인 시 일괄 확정)

| ID | 내용 | 권고 |
|---|---|---|
| D-08 | 무료 Core 사육 두수 제한 | **무제한** (회의 제안: 데이터 생성 극대화 → PigSignal) |
| D-09 | 경영관리(운영비·손익) 제품 P0 + **무료** 배치 | 무료 (회의: "기본이 나올 수 있게 해줘야") |
| D-10 | R1(룰 경보) 무료 / R2(특화 예측) 유료 경계 | 본 매트릭스 layer·R-class 열 그대로 |

## 1. Layer 1 — Capture (입력: 전부 무료)

| feature_code | 기능 | R | 무료 | 구현 | 비고 |
|---|---|---|---|---|---|
| capture_breeding | 번식·분만·이유·폐사 기록 | — | O | 기존 | |
| capture_feed | 사료 주문·사용 입력 | — | O | 기존 | |
| capture_medicine | 약품·백신 사용 입력 | — | O | 미구현 | 해외 필수, 무료 확인 |
| capture_shipment | 출하 기록 | — | O | 부분 | 정산 연결 신설 |
| capture_finance | 비용·매출 입력 (경영관리) | — | O | 미구현 | D-09. 인건비·임대료 포함 |
| capture_task_log | 직원 작업 완료 기록 | — | O | 미구현 | 기록=무료 / 관리·배정=유료(auto_workforce) |
| capture_doc_upload | 명세서·사진 업로드(OCR) | — | O | 미구현 | B-08 해소 전 프로덕션 금지 |
| capture_voice | 음성 입력 | — | O | 미구현 | |
| capture_sensor | 센서 데이터 수신 | — | ⚠️TBD | 미구현 | 수신 무료 vs 연동 유료 경계 → OPEN-1 |

## 2. Layer 2 — Insight (기본 무료 / 고급 유료)

| feature_code | 기능 | R | 무료 | trial | 과금 | 구현 | 비고 |
|---|---|---|---|---|---|---|---|
| insight_basic_kpi | 기본 KPI 대시보드 (국가별 PRIMARY) | — | O | — | — | 기존 | resolved policy 기반 |
| insight_rule_alerts | 룰 기반 경보 (AI 무개입) | R1 | O | — | — | 기존 | 무료 핵심 가치 |
| insight_benchmark | 기본 벤치마크·유사농장 비교 | C1 | O | — | — | 부분 | verdict 금지. 콜드스타트 D-07 종속 |
| insight_cash_pnl | 기간 운영비·현금 기준 손익 | — | O | — | — | 미구현 | D-09. "생산비" 명명 금지 |
| insight_weather | 날씨 컨텍스트 (농장 좌표 기반) | — | O | — | — | 미구현 | 접속 위치 아닌 **농장 등록 좌표**. 소스 커버리지 → OPEN-2 |
| insight_weather_alerts | 날씨 결합 룰 경보 (혹서·급변) | R1 | O | — | — | 미구현 | GUARDRAIL driver |
| insight_weekly_ai | AI 주간 해석·요약 | R2 | — | 1주 | 크레딧/월 TBD | 미구현 | |
| insight_disease_predict | 질병 특화 예측 | R2 | — | 1주 | 크레딧 | 부분 | 명명 특화 필수 |
| insight_feed_intel | 사료효율·FCR 최적화 | R2 | — | 1주 | 월+사용량 TBD | 부분 | |
| insight_adv_finance | 업그레이드 경영분석 | R2 | — | 1주 | TBD | 미구현 | |
| insight_report_pro | 상세 진단 보고서 | R2 | — | TBD | 건별 TBD | 미구현 | ⚠️B-07 인사이트 중복 정리 후 |
| insight_talk | PigOS Talk (대화형) | R2 | — | 1주 | 크레딧 | 부분 | |

## 3. Layer 3 — Automation / Transaction (유료)

| feature_code | 기능 | R | 과금 | 구현 | 비고 |
|---|---|---|---|---|---|
| auto_agent | AI 에이전트 자동실행 | R2 | 크레딧 | 미구현 | |
| auto_workforce | 직원 배정·관리·리포트 | — | 월/농장 TBD | 미구현 | |
| paid_multifarm | 다농장 통합관리 | — | 조직/농장 TBD | 부분 | 기존 제공처 처리 → OPEN-3 |
| paid_integration | ERP·센서 연동 | — | 연결 단위 TBD | 미구현 | |
| paid_consulting | 전문 컨설팅 | — | 건별 | — | |
| txn_matching | 거래 연결 | — | 거래 수수료 | 미구현 | **DEFERRED**: 옵트인+규제 검토 선행 (T-R3) |

## 4. 공통 규칙
- trial: 1주 체험, 결제수단 등록만, 1주 내 해지 미결제, 이후 월 과금. 만료 후 기존 알림 = D-05.
- no_entitlement_behavior: R2 = 알림 **미생성**. 기타 유료 = 잠금+업셀.
- upsell_trigger: R1 경보 상세에서 연관 R2 노출. Safe Claim Matrix 준수 ("AI-assisted").
- country_availability: resolved policy 참조 — 본 문서에서 재정의 금지.
- 가격 전부 TBD — 근거 소스 확보 후 별도 승인.

## 5. OPEN
OPEN-1 센서 경계 / OPEN-2 기상 소스·라이선스 국가별 확인 / OPEN-3 다농장 기존 제공처 / OPEN-4 무료 티어 월 크레딧 소량 지급 / B-07 보고서·인사이트 중복.

## 변경 이력
| v0.1 | 2026-07-21 | 초안. 회의 무료/유료 전수, 3층 구조, D-08~10 결정 요청 |
