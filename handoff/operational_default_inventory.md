# operational_default 인벤토리 (2.0) — 추출 전 검수표

> 코드에 흩어진 경고 기준값 전수. **값은 현재 코드 그대로(변경 0)**. 이 표 확인 후 레지스트리로 1:1 이전.
> 방향: 아래=낮을수록나쁨(값↓→경고) / 위=높을수록나쁨(값↑→경고) / 범위=양쪽.
> scope=global (국가 무관). 국가별 임계는 여전히 rule_configs 우선.

## A. 공용 resolve() 사용 (23개)
| rule_id | KPI | 경고 | 위험 | 방향 | value_scale | 출처 |
|---|---|---|---|---|---|---|
| batch.aiao_detect | BATCH_DOW_CONCENTRATION | 50 | 70 | 위(높을수록↓) | percent_0_100 | batch.py:16 |
| boar.farrow_rate_low | BOAR_FARROW_RATE | 65 | 55 | 아래 | percent_0_100 | boar.py:15 |
| fcr.high | FCR | 3.0 | 3.3 | 위 | n/a | grow_finish.py:21 |
| adg.low | ADG | 650 | 550 | 아래 | n/a | grow_finish.py:44 |
| finish_mortality.high | FINISH_MORTALITY | 5 | 8 | 위 | percent_0_100 | grow_finish.py:67 |
| stillborn.rate_high | STILLBORN_RATE | 8 | 12 | 위 | percent_0_100 | litter.py:33 |
| mummified.rate_high | MUMMIFIED_RATE | 2 | 4 | 위 | percent_0_100 | litter.py:53 |
| born_alive.low | BORN_ALIVE | 11 | 10 | 아래 | n/a | litter.py:73 |
| total_born.low | TOTAL_BORN | 12 | 11 | 아래 | n/a | litter.py:92 |
| weaned.low | WEANED_COUNT | 10 | 9 | 아래 | n/a | litter.py:109 |
| birth_weight.low | BIRTH_WEIGHT | 1.3 | 1.1 | 아래 | n/a | litter.py:128 |
| weaning_weight.low | WEANING_WEIGHT | 5.5 | 5.0 | 아래 | n/a | litter.py:147 |
| lactation.too_short | WEANING_AGE_LOW | 19 | 16 | 아래 | n/a | litter.py:164 |
| lactation.too_long | WEANING_AGE_HIGH | 28 | 35 | 위 | n/a | litter.py:180 |
| piglet.crushing_rate_high | CRUSHING_RATE | 6 | 10 | 위 | percent_0_100 | litter.py:197 |
| piglet.death_age_skew | DEATH_AGE_0_3_RATIO | 70 | 80 | 위 | percent_0_100 | litter.py:216 |
| culling.rate_high | CULLING_RATE | 45 | 55 | 위 ⚠️ | percent_0_100 | sow_herd.py:21 |
| sow_mortality.high | SOW_MORTALITY | 8 | 12 | 위 | percent_0_100 | sow_herd.py:44 |
| parity.high_ratio | HIGH_PARITY_RATIO | 20 | 30 | 위 | percent_0_100 | sow_herd.py:67 |
| replacement.rate_abnormal | REPLACEMENT_RATE | 50 | 60 | 위 ⚠️ | percent_0_100 | sow_herd.py:87 |
| parity.second_litter_slump | SECOND_LITTER_DROP | 1.5 | 2.5 | 위 | n/a | sow_herd.py:111 |
| accident.parity_skew | ACCIDENT_P1_RATIO | 40 | 55 | 위 | percent_0_100 | sow_herd.py:129 |
| msy.below_bep | MSY | 17 | 15 | 아래 | n/a | sow_herd.py:151 |

## B. reproduction.py 자체 상수 (6개)
| rule_id | KPI | 경고 | 위험 | 방향 | value_scale | 출처 |
|---|---|---|---|---|---|---|
| wsi.overdue | WSI | 10 | 14 | 위 | n/a | reproduction.py:16 |
| rts.rate_high | RTS_RATE | 15 | 25 | 위 | percent_0_100 | reproduction.py:17 |
| pwmr.high | PWMR | 15 | 20 | 위 | percent_0_100 | reproduction.py:18 |
| abortion.rate_high | ABORTION_RATE | 3 | 5 | 위 | percent_0_100 | reproduction.py:156 |
| seasonal.summer_infertility | SUMMER_FARROW_DROP | 6 | 10 | 위 | n/a (pp) | reproduction.py:190 |
| conception.rate_low | CONCEPTION_RATE | 85 | 80 | 아래 | percent_0_100 | reproduction.py:224 |

## C. base.py — 특수형 (단순 경고/위험 아님, 별도 취급)
| rule_id | KPI | 형태 | 출처 |
|---|---|---|---|
| npd.overdue | NPD | 기본 35일, "초과+7일"에서 발화 | base.py:73 |
| psy.below_target | PSY | **4등급 밴드**(≥28 OK / 24–28 / 20–24 / <20) — 단순 w/c 아님 | base.py PSY_GRADES |
| farrowing_rate (base) | FARROWING_RATE | bench.warning 기반 | base.py:160 |

## ⚠️ 추출 중 발견한 특이사항 (검수 필요)
1. **culling.rate_high**: 현재 룰은 "위(45 초과 경고)"만. governance는 culling_rate를 **range_target**(너무 낮아도 노령화)으로 정의 → 현재 룰은 하단을 안 봄. **추출은 현행대로 "위"만 보존**(동작 불변), governance range 정의와의 갭은 별도 후속.
2. **replacement.rate_abnormal**: "abnormal"=비정상(양쪽?)인데 코드는 hi_w/hi_c만 → 현재는 "위(상단)"만. 현행대로 보존.
3. **psy.below_target**: 4등급 밴드라 단일 warning/critical로 못 옮김. → operational_default에 PSY는 등급 경계(예: warning=24, critical=20)로 넣되 **현행 등급 발화와 1:1 일치 테스트로 검증**, 또는 PSY는 밴드 전용으로 레지스트리 예외 처리. **결정 필요.**

→ 1·2는 현행 보존(동작 불변)으로 진행, 3(PSY 밴드)만 어떻게 옮길지 확인 필요.
