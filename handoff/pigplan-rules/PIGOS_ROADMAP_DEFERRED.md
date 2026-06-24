# PigOS 보류/로드맵 백로그 — Phase D-heavy / E (2026-06-24)

> 136룰 본문 재검증 결과 중 **지금 데이터로 못 만드는 것**의 정리.
> 원칙: **위조 0** — 필요한 데이터/피드가 생기기 전엔 룰을 만들지 않는다. 만들 땐 PigOS 네이티브로 재해석(KR 내부구조 복제 금지).
> 현재 완료: Phase A(KR seed) · B(엔진 35종) · D-lite(손실4) · C(LLM Renderer). 이 문서는 그 다음.

---

## Phase D-heavy — 신규 데이터 입력기능 → 그 위 룰
각 항목 = **입력 UI + 모델 + 마이그레이션이 선행**, 그 다음 룰. 독립적이라 하나씩 진행.

| # | 입력기능 (선행) | 활성될 룰 | KR 근거 | 우선도 |
|---|---|---|---|---|
| D1 | **임신감정(pregnancy-check)** 이벤트 입력 | `conception.rate_low` + `abortion.rate_high` 분모 정밀화(risk-population) | PREG_ACCIDENT_DENOM | ★ 높음(번식 핵심) |
| D2 | **자돈 폐사 사유·일령** 코딩(piglet_events에 reason/age) | `piglet.crushing_rate`·`piglet.lbw_rate`·`piglet.death_age_skew`·`piglet.cause_trend` | PIGLET_DEATH_KPI_V1·AGE_DEATH_ANALYSIS·REASON_TREND | ★ 높음(PWMR 심화) |
| D3 | **MSY 산출**(출하↔모돈 연결 또는 스냅샷) | `msy.below_bep`(BEP 17.0) | MSY_BEP | 중 |
| D4 | **배치(AIAO) 16주+ 이력 집계** | `batch.aiao_detect`(요일집중·주기 fitness) | BATCH_MGMT·BATCH_CONCENTRATION·BATCH_CYCLE_CONFIG | 중 |
| D5 | **BCS·체중 입력** | (heat/BCS 룰) | BCS_THRESHOLD·HEAT_DETECTION_THRESHOLD | 낮음(seed는 이미 대기) |
| D6 | **치료이력(약품) 입력 활용** | `treatment.frequency_high` | TREATMENT_THRESHOLD | 낮음(health_events 존재, 집계만) |

> seed는 이미 system 기본으로 일부 대기(THI/BCS/TREATMENT/HEAT/MSY) — 입력·집계가 붙으면 즉시 작동.

---

## Phase E — Out-of-scope (PigOS 네이티브 피드 선행, 로드맵만)
KR 플랫폼 내부 메커니즘이라 복제 불가. 필요 시 재해석.

### E1. 전국 벤치마킹 / 산출농장 선정 (테넌트 전체 모집단 필요)
- KR룰: FARM_ELIGIBILITY·FARM_FILTER·BENCHMARK_FILTER·COMPARE_METHOD·INPUT_DELAY_NATIONAL·PEER_MATCH
- 필요: PigOS가 **다수 농장 익명 집계 파이프라인**을 구축해야(데이터 수익화 전략과 직결). 그때 "상위 25%·동류농가 매칭" 재해석.

### E2. 질병 크롤러 (외부 뉴스 수집)
- KR룰: DISEASE_VALIDATION·DISEASE_DISPLAY·DISEASE_CRAWLER_FILTER
- 현재 PigOS: `disease.endemic_risk`는 **수동/시드 prevalence** 기반. 크롤러 자체는 별도 인프라.
- 필요: PigOS 네이티브 질병 피드(공신력 소스 + 확진 필터). 국가별 소스 상이.

### E3. 예측(Forecast) 인프라
- KR룰: PROPHET_CONFIG·ALERT_THRESHOLD·SEASON_CONFIG·SHIP_FORECAST_PARAMS·(WEATHER_THRESHOLD)
- 필요: 시계열 예측 서비스(Prophet 등) + 기상 피드. 결정론 룰이 아니라 ML 트랙.

### E4. 도체/출하 등급 (carcass grade)
- KR룰: SHIP_AGE·SHIP_AGE_STANDARD·SHIPMENT_QUALITY·SHIPMENT_RANGE·SHIP_COMPARE·SHIPMENT_DIAGNOSIS·S3_GRADE
- 필요: **도체중·등지방·등급 데이터 입력**(도축장 연동 또는 수동). 국가별 등급체계 상이 → country scope.

### E5. KR 입력지연(input-delay) 지표
- KR룰: NPD_INPUT_DELAY_SEPARATION(데이터측)·INPUT_DELAY_DIAG·INPUT_DELAY_IMPACT·INPUT_DELAY_EMPHASIS·DAILY_LOG_THRESHOLD
- 사유: 작업일(WK_DT)↔등록일(LOG_INS_DT) 간극 = **KR 운영 데이터 품질 개념**. PigOS 오프라인 sync 모델과 달라 그대로 이식 부적합. 필요 시 sync 지연 지표로 재정의.

### E6. AI 모델 라우팅 / 시장가
- KR룰: AI_MODEL_STRATEGY·AI_CLASS_RULE(모델선택 half)·MARKET_PRICE_STD
- 사유: KR Gemini/Claude 라우팅 = PigOS Addon#1 LLM 설정으로 흡수(이미 llm_renderer). 경락가(057016)는 KR 도매시장 특화 → 국가별 가격피드로 재정의.

---

## 권장 순서
**D1(임신감정) → D2(자돈 폐사 사유/일령) → D3(MSY) → D4(배치)** 순으로 입력기능부터.
E는 각 항목이 별도 인프라(집계 파이프라인/크롤러/ML/도축연동)라 **제품 로드맵 결정 사항** — 엔진 작업과 분리.

> RENDERER(~45 KR 룰)는 Phase C(LLM Renderer)에서 가이드 증류로 일부 흡수 완료. 잔여는 Addon#1 프롬프트 점진 보강.
