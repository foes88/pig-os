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

## 규칙 24종

### 번식 (Reproduction)
| rule_id | KPI | 방향 | 코드 기본 임계(주의/긴급) |
|---|---|---|---|
| psy.below_target | PSY | 낮을수록↓ | 국가 benchmark |
| npd.overdue | NPD | 높을수록↑ | 국가 benchmark |
| farrowing.low_rate | FARROWING_RATE | ↓ | 85 / 80 % |
| wsi.overdue | WSI | ↑ | 10 / 14 일 |
| rts.rate_high | RTS_RATE | ↑ | 15 / 25 % |
| abortion.rate_high | ABORTION_RATE | ↑ | 3 / 5 % |

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

> **국가별 조정 예**: KR PSY 목표 24, US/BR은 다른 목표 → `benchmarks` 행만 다르면 동일 규칙이 자동으로 각국 기준 적용. 운영자가 특정 농장군에 더 엄격히 하려면 `/admin/rules`에서 임계 오버라이드.

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
