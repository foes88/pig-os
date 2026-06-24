# PigOS 보류/로드맵 백로그 — Phase D-heavy / E (2026-06-24)

> 136룰 본문 재검증 결과 중 **지금 데이터로 못 만드는 것**의 정리.
> 원칙: **위조 0** — 필요한 데이터/피드가 생기기 전엔 룰을 만들지 않는다. 만들 땐 PigOS 네이티브로 재해석(KR 내부구조 복제 금지).
> 현재 완료: Phase A(KR seed) · B(엔진 35종) · D-lite(손실4) · C(LLM Renderer). 이 문서는 그 다음.

---

## Phase D-heavy — 신규 데이터 입력기능 → 그 위 룰
각 항목 = **입력 UI + 모델 + 마이그레이션이 선행**, 그 다음 룰. 독립적이라 하나씩 진행.

| # | 입력기능 (선행) | 활성될 룰 | KR 근거 | 상태 |
|---|---|---|---|---|
| D1 | **임신감정(pregnancy-check)** 이벤트 입력 | `conception.rate_low` | PREG_ACCIDENT_DENOM | ✅ 완료(백+프론트+모바일) |
| D2 | **자돈 폐사 사유·일령**(이미 캡처: reason+age_days 자동) | `piglet.crushing_rate_high`·`piglet.death_age_skew` (+ mortality 리포트 사유분해) | PIGLET_DEATH_KPI_V1·AGE_DEATH | ✅ 완료(룰+리포트) |
| D3 | **MSY 산출**(비육 head_out/활성모돈) | `msy.below_bep`(BEP 17.0) | MSY_BEP | ✅ 완료 |
| D4 | **배치(AIAO) 교배 요일집중** | `batch.aiao_detect`(INFO 분류) | BATCH_MGMT·BATCH_CONCENTRATION | ✅ 완료(단순판 — 주기 fitness는 후속) |
| D5 | **BCS·체중 입력** ⬜ **인프라 0(새 테이블 필요)** | (BCS 룰) | BCS_THRESHOLD·HEAT_DETECTION | ⬜ 미착수 — 입력기능 설계 필요 |
| D6 | **치료이력(약품) 입력 플로우** ⬜ **health_events 비어있음** | `treatment.frequency_high` | TREATMENT_THRESHOLD | ⬜ 미착수 — 입력 플로우 정의 필요 |

> **현재 결정론 룰엔진 = 40종**(D1~D4 반영). 데이터가 실제로 캡처되는 탐지는 사실상 전부 구현.
> D5/D6는 **룰 추가가 아니라 신규 입력기능 프로젝트** — 데이터 없이 룰만 만들면 위조라 미착수. 입력기능부터 설계 후 진행.
> 후속 미세룰: `piglet.cause_trend`(주간 연속1위 streak — 시계열 윈도잉), 배치 주기 fitness, abortion 분모 risk-population 정밀화.

### D5/D6 재개용 KR 임계값(본문 추출 완료 — 재추출 불필요)
- **BCS_THRESHOLD**(등지방 mm 분포): target_range [17,20], low_max 13, high_min 22 / target_good 60%·warn 40% / low·high warn 15%·danger 30% / window 180일, min_events 50, min_pigs 10.
- **TREATMENT_THRESHOLD**: 반복치료율 repeat_warn 20%·repeat_red 30% / window 180일, min_events 20, min_pigs 5.
- **HEAT_DETECTION_THRESHOLD**: 정상 1→2차 간격 [18,24]일, BCS(등지방) 정상 [17,20]mm / good 80%·warn 60% / window 180, min_heads 10, min_cycles 5.
> 주의: KR은 **등지방(mm)** 기준(BCS 1~5 척도 아님). PigOS는 BCS 척도 vs 등지방 중 입력 방식 결정 필요(설계 항목).

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
