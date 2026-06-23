# KR 룰 ↔ PigOS 커버리지 매핑표

> 입력: `ruleengine3.json`(136 KR 룰) × PigOS `api/app/engine/rules/*.py`(base·reproduction·disease)
> ⚠️ 본 분류는 **키워드 기반 자동 1차 초안** — PigOS 세션이 룰 본문 보고 확정할 것.

## PigOS 현재 엔진 (대조 기준)
- **기존 룰 9개**: psy.below_target / npd.overdue / farrowing.low_rate / inventory.zero / wsi.overdue / rts.rate_high / pwmr.high / abortion.rate_high / disease.endemic_risk
- **임계값 조정 인프라**: `ctx.benchmarks`(default_metric_values, 농가/국가 scope) + `ctx.extra["rule_configs"]`(운영자 룰별 임계값) → **코드수정 없이 조정 가능**
- **국가 인지**: `ctx.country` (disease.py가 국가별 prevalence로 심각도 조정)

## 분류 요약

| 분류 | 의미 | 건수 |
|---|---|---|
| ✅ 있음 | PigOS에 대응 룰 존재 → 재사용/보강 | 45 |
| ⚠️ seed | 임계값/파라미터 → `default_metric_values`·`rule_configs` 주입(코드無) | 44 |
| 🆕 신규 | PigOS에 없음 → 신규 구현 또는 지식 참고 판단 | 47 |
| **합계** | | **136** |

---

## DOMAIN (25)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `BATCH_MGMT` | 일괄작업(올인올아웃) 원칙 | MD | 🆕 신규 |  |
| `PWSL_BENCHMARK` | 모돈 생애 이유두수(PWSL) 벤치마크 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `PARITY_DISTRIBUTION` | 모돈 산차구성 목표 분포 (herd 5-band) | JSON | 🆕 신규 |  |
| `WSI_P1_BENCHMARK` | P1 초산 재귀발정일(WSI) 5구간 분포 | JSON | ✅ 있음 | wsi.overdue |
| `SOW_LONGEVITY` | 모돈 도태산차·수명 기준 (국내외) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `SHIP_AGE_STANDARD` | 출하일령 표준·평가 정책 (도체중 동반) | JSON | 🆕 신규 |  |
| `SEASON_SUMMER` | 여름 고온 스트레스 + 시차 효과 | MD | 🆕 신규 |  |
| `SEASON_WINTER` | 겨울 한랭 스트레스 + PED | MD | ✅ 있음 | disease.endemic_risk |
| `SEASON_TRANSITION` | 환절기 관리 (3~5월, 9~11월) | MD | 🆕 신규 |  |
| `REPRODUCTION` | 번식 관리 원칙 | MD | 🆕 신규 |  |
| `DISEASE_ASF` | ASF(아프리카돼지열병) 질병 규칙 | MD | ✅ 있음 | disease.endemic_risk |
| `SHIPMENT_GRADE` | 출하 등급 관리 | MD | 🆕 신규 |  |
| `DISEASE_PED_PRRS` | PED/PRRS 질병 규칙 (통합) | MD | ✅ 있음 | disease.endemic_risk |
| `FARM_SIZE` ⛔ | 농장 규모별 코멘트 조정 | MD | 🆕 신규 |  |
| `COMMON_MISTAKES` | AI 분석 흔한 실수 방지 | MD | 🆕 신규 |  |
| `PROHIBIT_LIST` | AI 절대 금지 규칙 | MD | 🆕 신규 |  |
| `FARM_ELIGIBILITY` | 전국 집계 산출농장 선정 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `FARM_SIZE_BENCHMARK` | 농장 규모별 조정 + 벤치마크 기준값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `PSY_IMPROVEMENT` | PSY 개선 경로 (AI 진단용) | MD | ✅ 있음 | psy.below_target |
| `NPD_DEFINITION` | NPD 용어 정의 및 국제 기준 | MD | ✅ 있음 | npd.overdue |
| `NPD_INPUT_DELAY_SEPARATION` | NPD와 입력지연 완전 분리 원칙 (AI 혼동 방지) | MD | ✅ 있음 | npd.overdue |
| `SHIP_AGE` | 출하일령×도체중 판정행렬 룰 | JSON | 🆕 신규 |  |
| `FCR_FINISHING` | 비육 FCR 해석기준 룰 (준비중) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `SHIP_FORECAST_PARAMS` | 출하 전망 cohort 투영 파라미터 룰 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `PARITY_BENCHMARK` | 산차별 보유모돈 구성 벤치마크 | JSON | ⚠️ seed | default_metric_values / rule_configs |

## INTERPRET (29)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `PARITY_BENCHMARK` | 평균 산차 벤치마크(경제산차) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `BOAR_BENCHMARK` | 웅돈 성적 벤치마크(분만율·WSI) | JSON | ✅ 있음 | farrowing.low_rate |
| `REPLACEMENT_BENCHMARK` | 모돈 교체(갱신/도폐사) 벤치마크 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `KPI_CLASSIFY` ⛔ | KPI 해석 + RED/YELLOW/GREEN 분류 | MD | 🆕 신규 |  |
| `RED_YELLOW_GREEN` | 농가분류 RED/YELLOW/GREEN 조건 | JSON | 🆕 신규 |  |
| `SHIPMENT_QUALITY` | 출하 품질 해석 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `KPI_7GRADE` | KPI 7등급 해석 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `PARITY_RETIREMENT` | 산차별 도태 기준 해석 | MD | 🆕 신규 |  |
| `DISEASE_CALENDAR` | 월별 질병 위험 카렌다 | JSON | ✅ 있음 | disease.endemic_risk |
| `CLASSIFY_EXCLUDE_RANGES` | 분류 제외 범위 (유효성 가드) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `NPD_BENCHMARK` ⛔ | NPD 국내외 벤치마크 | JSON | ✅ 있음 | npd.overdue |
| `KPI_COLOR_THRESHOLD` | KPI 카드 색상 임계값 (리포트 UI) | JSON | ✅ 있음 | psy.below_target |
| `PIGLET_THRESHOLD` | 포유자돈 폐사/생존 색상 임계값 | JSON | ✅ 있음 | pwmr.high |
| `ACCIDENT_BENCHMARK` | 임신사고 벤치마크 임계값 | JSON | ✅ 있음 | abortion.rate_high |
| `THI_THRESHOLD` | THI 열 스트레스 지수 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `KEY_MONITOR_KPI` | 핵심 모니터링 지표 (농장주 관심 26개) | MD | 🆕 신규 |  |
| `SHIPMENT_RANGE` | 출하 도체중/등지방 적정 범위 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `CULLING_BENCHMARK` | 도태/폐사 벤치마크 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `DATA_QUALITY_GUARD` | 데이터 극단값 가드 (분류 제외 범위) | JSON | ✅ 있음 | psy.below_target |
| `SYSTEM_DEFAULTS` | 시스템 기본값 (TC_FARM_CONFIG 미설정 시 fallback) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `SEASONAL_BENCHMARK` | 계절 보정 기대치 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `PARITY_STRUCTURE` | 산차분포 자동진단 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `DISEASE_RADIUS` | 인근 질병 경보 반경 룰 | JSON | ✅ 있음 | disease.endemic_risk |
| `BATCH_CONCENTRATION` | 배치 집중도(HHI) 판정 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `BATCH_CYCLE_CONFIG` | 배치 주기 감지 설정 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `FARM_DIFFERENTIATION` | 농장 차등화 분석 기준 | MD | ✅ 있음 | disease.endemic_risk |
| `DISEASE_ALERT_LEVEL` | 주변 질병 3단계 경보 판정 기준 | JSON | ✅ 있음 | disease.endemic_risk |
| `AI_COMMENT_THRESHOLDS` | AI 코멘트 통합 임계값 (5 탭 산발 하드코딩 통합) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `MARKET_PRICE_STD` | 경락가격 표준 산출 기준 | MD | 🆕 신규 |  |

## DIAGNOSIS (12)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `PSY_DRILLDOWN` | PSY 진단 + 손실 원인 추론 경로 | MD | ✅ 있음 | psy.below_target |
| `SHIPMENT_DIAGNOSIS` | 출하 품질 진단 경로 | MD | 🆕 신규 |  |
| `SEASONAL_DIAGNOSIS` | 계절성 진단 경로 | MD | 🆕 신규 |  |
| `INPUT_DELAY_DIAG` | 입력지연 + 예정달성율 + 산차도태 진단 | MD | 🆕 신규 |  |
| `LOSS_DIAGNOSIS` | 손실 원인 진단 경로 | MD | 🆕 신규 |  |
| `CORE_PRESCRIPTION_PRESERVE` | 핵심 처방 보존 룰 (회귀 차단) | MD | 🆕 신규 |  |
| `KPI_DRIVER_MAP` | 경영진단 KPI 인과 매핑 + 리포트 가이드 | JSON | 🆕 신규 |  |
| `MULTI_AXIS_GUIDE` | 다축 경영진단 분석 지침 | MD | ✅ 있음 | disease.endemic_risk |
| `NPD_BREAKDOWN` | NPD 분해 분석 룰 (cause별) | PROMPT | ✅ 있음 | npd.overdue |
| `PEER_MATCH` | 동류 농가 매칭 룰 (3차 분류) | PROMPT | 🆕 신규 |  |
| `BATCH_CYCLE_ANALYSIS` | 배치 주기 농장 분석 지침 (올인올아웃) | MD | 🆕 신규 |  |
| `INPUT_DELAY_IMPACT` | 입력 지연 ↔ KPI 상관분석 및 개선 시뮬레이션 | MD | 🆕 신규 |  |

## GRADING (2)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `AI_CLASS_RULE` | AI_CLASS(RED/YELLOW/GREEN) 연계 조건 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `BENCHMARK_FILTER` | 산출농장 선정 기준 (7개 필터) | JSON | ⚠️ seed | default_metric_values / rule_configs |

## BENCHMARK (14)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `FARM_FILTER` | 산출농장 선정 필터 (F1-F2, Q1-Q7) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `VALID_RANGES` | 데이터 허용 범위 (이상치 판정) | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `FARM_SIZE_GROUP` | 농장 규모별 분류 기준 (상시모돈수) | JSON | ✅ 있음 | inventory.zero |
| `TAB_THRESHOLDS` | 리포트 탭/배치 매직넘버 SSOT | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `COMPARE_METHOD` | 전국비교 기준 정의 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `SHIP_COMPARE` | 출하탭 비교 분석 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `DISEASE_IMPACT` | 질병별 영향도 파라미터 (반경·경보일·KPI 영향) | JSON | ✅ 있음 | disease.endemic_risk |
| `HEAT_DETECTION_THRESHOLD` | 발정 감지 카드 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `KPI_TIMEFRAME` | KPI 시간 단위 매핑 룰 (WY 1주 + 13주 롤링) | PROMPT | 🆕 신규 |  |
| `TREATMENT_THRESHOLD` | 치료 이력 카드 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `BCS_THRESHOLD` | 모돈 BCS·체중 카드 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `DAILY_LOG_THRESHOLD` | 작업일보 카드 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `FARM_SIZE_CLASS` | 농장 규모 경계값 | JSON | ✅ 있음 | inventory.zero |
| `INPUT_DELAY_NATIONAL` | 전국 입력 지연 기준값 및 과거 5년 트렌드 | JSON | ⚠️ seed | default_metric_values / rule_configs |

## LOSS_CALC (7)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `S1_PREGNANCY` | 임신사고 손실 계산식 | MD | ✅ 있음 | abortion.rate_high |
| `S_PW_PIGLET` | 포유자돈 폐사 손실 계산식 | MD | ✅ 있음 | pwmr.high |
| `S3_GRADE` | 출하 등급 손실 계산식 | JSON | 🆕 신규 |  |
| `S9_NPD` | NPD 손실 산출 (순수 생리학적 지연만) | MD | ✅ 있음 | npd.overdue |
| `S2_SOW_CULL` | 모돈 도태/폐사 잔여가치 손실 | MD | 🆕 신규 |  |
| `S2_SOW_RETIREMENT` | 모돈 도태/폐사 손실 계산식 | JSON | 🆕 신규 |  |
| `IMPROVEMENT_SIM` | 개선 시뮬레이션 산출 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |

## FORECAST (5)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `PROPHET_CONFIG` | Prophet 시계열 예측 모델 설정 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `ALERT_THRESHOLD` | 예측 vs 실적 차이 경고 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `WEATHER_THRESHOLD` | 기상 경보 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `SEASON_CONFIG` | 계절 패턴 분석 설정 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `AI_MODEL_STRATEGY` | AI 모델 전략 (1차/2차 자동 전환) | JSON | ⚠️ seed | default_metric_values / rule_configs |

## OUTPUT_STYLE (10)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `COMMENT_FORMAT` | 지난주 핵심 (comment) 작성 규칙 | MD | 🆕 신규 |  |
| `WEEK_DEFINITION` | 주차 정의 (절대 혼동 금지) | MD | 🆕 신규 |  |
| `ANNUAL_KPI_RULE` | 연간 환산 지표(WY) 표기 규칙 | MD | 🆕 신규 |  |
| `DATA_TRUST_RULE` | 데이터 신뢰성 규칙 | MD | 🆕 신규 |  |
| `SECTION_RULE` | 섹션별 작성 규칙 (loss/plan/forecast/summary) | MD | 🆕 신규 |  |
| `SECTION_BOUNDARY` | 섹션 경계 규칙 (혼용 금지) | MD | 🆕 신규 |  |
| `STEP6_COLOR_RULES` | STEP 6 진단 카드 공통 색상 분기 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `OUTPUT_FORMAT` | 출력 JSON 형식 규칙 | MD | 🆕 신규 |  |
| `INPUT_DELAY_EMPHASIS` | v9 진단탭 입력 지연 강조 노출 원칙 | MD | 🆕 신규 |  |
| `LOSS_PRESENTATION` | 손실탭 NPD/입력지연 분리 표시 + 숨은 손실 카드 원칙 | MD | ✅ 있음 | npd.overdue |

## ANALYSIS (7)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `PERIOD_DISTINCTION` | W/WY/M/MY 기간 구분 규칙 | MD | 🆕 신규 |  |
| `GAP_TREND` | 전국 대비 격차 추이 분석 규칙 | JSON | 🆕 신규 |  |
| `GAP_TREND_GUIDE` | 격차 추이 AI 분석 지침 | MD | 🆕 신규 |  |
| `WEAKNESS_GUIDE` | 취약점 분석 AI 지침 (10년 추이) | MD | 🆕 신규 |  |
| `CAUSAL_ANALYSIS` | 선행지표 인과분석 AI 지침 | MD | ✅ 있음 | psy.below_target |
| `SIMILAR_FARM` | 유사농장 벤치마킹 AI 지침 | MD | 🆕 신규 |  |
| `PRESCRIPTION_GUIDE` | 구체적 처방 작성 지침 (Phase 8-4) | MD | 🆕 신규 |  |

## MONTHLY (11)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `WEAKEST_PRIORITY` | 월간 리포트 가장 시급한 KPI 자동 결정 룰 | JSON | 🆕 신규 |  |
| `SEASONAL_INFERTILITY` | 계절성 불임 — 여름 분만율 저하(SID) | JSON | ✅ 있음 | farrowing.low_rate |
| `MSY_BEP` | MSY 손익분기점(BEP) | JSON | 🆕 신규 |  |
| `SOW_REPLACEMENT` | 모돈 갱신율 국내 권장 기준 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `PREG_ACCIDENT_DENOM` | 임신사고 분모(risk-population) 정책 | JSON | ✅ 있음 | abortion.rate_high |
| `COHORT_WSI` | 재귀일(WSI) cohort 매칭 정책 | JSON | ✅ 있음 | wsi.overdue |
| `COHORT_PWM` | 이유전폐사율(PWM) cohort 매칭 정책 | JSON | ✅ 있음 | pwmr.high |
| `COHORT_MATING_FARROW` | 분만율 보정 cohort 매칭 정책 | JSON | ✅ 있음 | farrowing.low_rate |
| `COHORT_FARROW_WEAN` | 이유율 cohort 매칭 정책 (옵션1 이유도래) | JSON | ✅ 있음 | farrowing.low_rate |
| `GRADE_WEIGHTS_V1` | 월간 종합등급 KPI 가중치·7밴드 룰 | JSON | ✅ 있음 | wsi.overdue |
| `CAUSAL_CHAIN_MAP` | 월간 리포트 약점 KPI 인과체인·시각카드 매핑 | JSON | 🆕 신규 |  |

## BATCH_CYCLE (1)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `OFF_WEEK_THRESHOLD` | 오프위크 신뢰도 임계값 | JSON | ⚠️ seed | default_metric_values / rule_configs |

## CRAWLING (3)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `DISEASE_VALIDATION` | 질병 크롤링 검증 규칙 (확진만 허용, 검사·예측·정책·학술 제외) | JSON | ✅ 있음 | disease.endemic_risk |
| `DISEASE_DISPLAY` | 질병 리포트 표시 설정 (초기 4건 · 더보기 최대 6건 · 질병별 탭) | JSON | ✅ 있음 | disease.endemic_risk |
| `DISEASE_CRAWLER_FILTER` | 질병 크롤러 필터·중복방지·소스 티어 정책 | JSON | ✅ 있음 | disease.endemic_risk |

## NURSING_PIGLET (5)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `REASON_CONTEXT` ⛔ | 포유자돈 폐사 사유별 원인·조치 컨텍스트 | JSON | ✅ 있음 | pwmr.high |
| `PIGLET_DEATH_KPI_V1` | 포유자돈 폐사 7개 핵심 KPI v1 (산식·임계값·근거) | JSON | ✅ 있음 | pwmr.high |
| `REASON_CONTEXT_V2` | 포유자돈 폐사 23사유 통합 컨텍스트 v2 (TC_CODE_JOHAP PCODE=032 전수) | JSON | ✅ 있음 | pwmr.high |
| `AGE_DEATH_ANALYSIS` | 포유자돈 일령별 폐사 분포 자동 진단 룰 | JSON | ✅ 있음 | pwmr.high |
| `REASON_TREND_ANALYSIS` | 포유자돈 사유별 추세 분석 룰 (연속1위·변동·급증) | JSON | ✅ 있음 | pwmr.high |

## PARITY (2)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `SLUMP_GUIDE` | 2산차 슬럼프 가이드 | JSON | ⚠️ seed | default_metric_values / rule_configs |
| `DIST_GUIDE` | 산차 분포 그룹 경계·권장 | JSON | ⚠️ seed | default_metric_values / rule_configs |

## PREG_ACCIDENT (1)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `REASON_CONTEXT` | 임신사고 사유별 처방 컨텍스트 (TB_SAGO 050 4유형) | JSON | ✅ 있음 | abortion.rate_high |

## PREG_LOSS (1)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `PARITY_DIST` | 임신사고 산차분포 진단 | MD | ✅ 있음 | abortion.rate_high |

## SOW_OUT (1)

| code | 이름 | type | 분류 | PigOS 대상/비고 |
|---|---|---|---|---|
| `REASON_CONTEXT` | 모돈 도태 사유별 처방 컨텍스트 (TC_CODE_JOHAP PCODE=031 26사유) | JSON | 🆕 신규 |  |

