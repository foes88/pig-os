# PigOS Rule Engine 카탈로그 (2026-06-23)

> AI 알림(탐지) 규칙 전수. **로직은 국가 중립 1벌, 임계(수치)만 국가별 조정.**
> 운영자는 `/admin/rules`(SUPER_ADMIN)에서 각 규칙의 **활성/임계(주의·긴급)를 배포 없이** 조정.
> 임계 우선순위: `rule_configs`(운영자) → `benchmarks`(국가) → 코드 기본값.
> 구현: `api/app/engine/rules/*.py` + `api/app/services/kpi_service.py:build_herd_kpis` (실데이터 집계, 날조 0).

## 데이터 흐름
```
build_herd_kpis(롤링 365일 집계)  →  RuleContext.kpi
        +  benchmarks(국가)  +  rule_configs(운영자)
        →  RuleEngine.evaluate(intent="dashboard")
        →  Finding[]  →  대시보드 알림 / 챗 응답 / 모바일 insights 배너
```

## 규칙 36종

> Phase B(ENGINE-NEW Tier A) 추가분 — 아래 표 뒤 "Phase B 신규" 섹션 참조.

### 번식 (Reproduction)
| rule_id | KPI | 방향 | 코드 기본 임계(주의/긴급) |
|---|---|---|---|
| psy.below_target | PSY | 낮을수록↓ | 국가 benchmark |
| npd.overdue | NPD | 높을수록↑ | 국가 benchmark |
| farrowing.low_rate | FARROWING_RATE | ↓ | 85 / 80 % |
| wsi.overdue | WSI | ↑ | 10 / 14 일 |
| rts.rate_high | RTS_RATE | ↑ | 15 / 25 % |
| abortion.rate_high | ABORTION_RATE | ↑ | 3 / 5 % |
| conception.rate_low | CONCEPTION_RATE | ↓ | 85 / 80 % (임신감정 양성/(양성+음성), 표본≥5) |

### 자돈/복 성적 (Litter)
| rule_id | KPI | 방향 | 코드 기본 임계 |
|---|---|---|---|
| pwmr.high | PWMR(포유폐사율) | ↑ | 15 / 20 % |
| stillborn.rate_high | STILLBORN_RATE | ↑ | 8 / 12 % |
| mummified.rate_high | MUMMIFIED_RATE | ↑ | 2 / 4 % |
| total_born.low | TOTAL_BORN | ↓ | 12 / 11 두 |
| born_alive.low | BORN_ALIVE | ↓ | 11 / 10 두 |
| weaned.low | WEANED_COUNT | ↓ | 10 / 9 두 |
| birth_weight.low | BIRTH_WEIGHT | ↓ | 1.3 / 1.1 kg |
| weaning_weight.low | WEANING_WEIGHT | ↓ | 5.5 / 5.0 kg |
| lactation.too_short | WEANING_AGE (LOW 벤치) | ↓ | 19 / 16 일 |
| lactation.too_long | WEANING_AGE (HIGH 벤치) | ↑ | 28 / 35 일 |

### 비육 (Grow-finish)
| rule_id | KPI | 방향 | 코드 기본 임계 |
|---|---|---|---|
| fcr.high | FCR | ↑ | 3.0 / 3.3 |
| adg.low | ADG | ↓ | 650 / 550 g/day |
| finish_mortality.high | FINISH_MORTALITY | ↑ | 5 / 8 % |

### 모돈군 구조 (Sow herd, 롤링 365일=연간 근사)
| rule_id | KPI | 방향 | 코드 기본 임계 |
|---|---|---|---|
| culling.rate_high | CULLING_RATE | ↑ | 45 / 55 % |
| sow_mortality.high | SOW_MORTALITY | ↑ | 8 / 12 % |
| parity.high_ratio | HIGH_PARITY_RATIO(7산+) | ↑ | 20 / 30 % |

### 건강/재고 (Health / Inventory)
| rule_id | KPI | 내용 |
|---|---|---|
| disease.endemic_risk | DISEASE | 최근 법정전염병 발생 감지 |
| inventory.zero | SOW_COUNT | 활성 모돈 0 |

### Phase B 신규 (ENGINE-NEW Tier A, 9종)
| rule_id | KPI | 방향 | 기본 임계 | 데이터 |
|---|---|---|---|---|
| seasonal.summer_infertility | SUMMER_FARROW_DROP | ↑ | 6 / 10 pp | 여름(6~8월) 교배 cohort 분만율 하락(farrowings.mating_id→교배월) |
| replacement.rate_abnormal | REPLACEMENT_RATE | 양방향 | >50/60, <30 | gilt 도입/활성herd |
| parity.second_litter_slump | SECOND_LITTER_DROP | ↑ | 1.5 / 2.5 두 | P1−P2 실산(breeding_cycles.parity) |
| accident.parity_skew | ACCIDENT_P1_RATIO | ↑ | 40 / 55 % | 임신사고 1산 편중(감염의심) |
| boar.farrow_rate_low | BOAR_FARROW_RATE | ↓ | 65 / 55 % | 웅돈별 분만율(멀티개체, 표본≥10) |
| loss.preweaning_mortality | PREWEAN_LOSS | 금액 | — | 포유폐사 두수×출하두당가(가격 없으면 미발화) |
| loss.pregnancy_accident | ACCIDENT_LOSS | 금액 | — | 사고건수×복당이유두수×단가 |
| loss.npd | NPD_LOSS | 금액 | — | WEI 기반: PSY×육성률×두당가/365 × Σwei_days (S9_NPD §2) |
| loss.sow_culling | SOW_CULL_LOSS | 금액 | — | 산차별 잔여가치 seed(KR)−salvage, 7산+ 제외 (S2_SOW_RETIREMENT) |
| farm.health_class | FARM_HEALTH_CLASS | 종합 | RED/YEL/GREEN | 전 룰 severity 롤업(2-pass finalizer) |
| farm.weakest_kpi | WEAKEST_KPI | 종합 | — | 최고 severity+최대 gap KPI 선정 |

> **D-lite 완료(2026-06-24)**: `loss.npd`(WEI 기반)·`loss.sow_culling`(KR 잔여가치 seed) 활성. 타국은 잔여가치 seed 행 추가 시 자동 작동.

> **국가별 조정 예**: KR PSY 목표 24, US/BR은 다른 목표 → `benchmarks` 행만 다르면 동일 규칙이 자동으로 각국 기준 적용. 운영자가 특정 농장군에 더 엄격히 하려면 `/admin/rules`에서 임계 오버라이드. Phase A에서 KR 실측 8종 주입 완료(STILLBORN/ABORTION/FCR/CULLING/SOW_MORTALITY/HIGH_PARITY/WEANING_WEIGHT/WEANING_AGE_LOW).

## 신규 규칙 추가 절차
1. `build_herd_kpis`(또는 build_rule_context)에 KPI 계산 추가 — **실데이터만**(없으면 None → 규칙 빈 결과).
2. `engine/rules/<domain>.py`에 규칙 함수 + `RuleRegistry.register(...)`.
3. `engine/rules/__init__.py`(+admin/rules.py) 임포트 → `/admin/rules` 자동 노출.
4. `renderer.py`에 cause/action 라벨(en/ko) 추가(미지정 시 .title() 폴백).
5. `tests/unit/test_rule_engine_expanded.py`에 경계값 테스트.

## 렌더링 (다국어)
- Finding의 causes/actions = i18n 키 → `renderer.py`(en/ko) 또는 프론트 `src/lib/alerts/meta.ts`에서 문구화.
- 미번역 키는 영어 `.title()` 폴백 → raw 키 노출/크래시 0.
- 손실 금액 등 미보유 데이터 **위조 금지** — 실 룰엔진 근거만.
