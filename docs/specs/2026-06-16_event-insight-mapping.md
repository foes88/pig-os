# 이벤트 → 즉시 분석(Insight) 매핑 스펙

> 목적: 사용자가 교배/분만/이유 등을 입력하는 **순간** 그 이벤트를 분석해 농장주에게 경고/인사이트를 표시.
> 원칙: **추측 금지** — 분석은 ① 기존 RuleEngine 규칙(집계 KPI) + ② KPI spec 공식 기반 이벤트 단위 체크만.
> 출처: `app/engine/rules/`(base·reproduction), `docs/specs/2026-03-19_kpi-calculation-specs.md`.
> 미정 임계값은 **[확인필요]** 표기 — 합의 전 구현 안 함.

---

## 두 층 구조
- **A. 집계 인사이트** = 기존 RuleEngine 규칙 재사용(농장 KPI). 이미 검증됨 → 그대로 호출.
- **B. 이벤트 인사이트** = 방금 입력한 그 레코드 자체의 분석(이 분만의 사산율 등). 신규 규칙(spec 공식 기반).

severity: `INFO`(참고) / `WARNING`(점검) / `CRITICAL`(즉시조치). B는 입력값 + farm_config/benchmark 기준.

---

## 1. 교배(Mating) 입력 시
| 분석 | 층 | 기준/공식 | severity | 예시 메시지 |
|------|----|-----------|----------|-------------|
| WSI 초과 | A | `wsi.overdue` 규칙(>10 WARNING, >14 CRITICAL) | W/C | "이유~교배 간격 12일 — 목표 7일 초과" |
| RTS율 높음 | A | `rts.rate_high`(>15% W, >25% C) | W/C | "최근 재발율 18% (경고)" |
| **연속 재발 누적** | B | 이 모돈 RTS 연속 ≥3회 → 도태검토 (alert_service cull 기준과 동일) | WARNING | "이 모돈 재발 3회째 — 도태 검토 권고" |

## 2. 분만(Farrowing) 입력 시
| 분석 | 층 | 기준/공식 | severity | 예시 메시지 |
|------|----|-----------|----------|-------------|
| PSY 미달 | A | `psy.below_target`(benchmark 기반) | I/W/C | "PSY 22.4 — 국가목표 24 미달" |
| NPD 초과 | A | `npd.overdue` | W/C | "NPD 45일 — 목표 초과" |
| **사산+미라 비율 높음** | B | `(stillborn+mummified)/total_born`; **[확인필요] 임계 >10% W, >15% C** | W/C | "이번 분만 사산율 18% — 평균 대비 높음" |
| **생존산자 적음** | B | `born_alive`; **[확인필요] benchmark 대비 또는 절대 <8두 INFO** | INFO | "생존 7두 — 산차 평균 대비 낮음" |
> 물리적 상한(TB>35, 사산>25 등)은 이미 **validator가 422로 차단**. B는 그 안에서 "경고 수준" 판정.

## 3. 이유(Weaning) 입력 시
| 분석 | 층 | 기준/공식 | severity | 예시 메시지 |
|------|----|-----------|----------|-------------|
| 포유폐사율 높음(농장) | A | `pwmr.high`(>15% W, >20% C) | W/C | "포유폐사율 17% (경고)" |
| **이 사이클 포유폐사** | B | `(born_alive - weaned)/born_alive`(spec §6) — 연결된 분만 기준 | I/W/C | "이 모돈 포유 중 4두 폐사(폐사율 22%)" |
| **이유두수 적음** | B | `weaned_count`; **[확인필요] benchmark/산차 대비 또는 <9두 INFO** | INFO | "이유두수 7두 — 목표 대비 낮음" |
| **이유일령 벗어남** | B | `weaning_age` vs farm_config.lactation_days; ±N일 | INFO | "이유일령 17일 — 설정 21일과 차이" |

## 4. 임신사고/RTS(Reproductive) 입력 시
| 분석 | 층 | 기준 | severity | 예시 |
|------|----|------|----------|------|
| RTS율 | A | `rts.rate_high` | W/C | — |
| 연속 재발 도태검토 | B | 교배와 동일(≥3회) | WARNING | "재발 누적 — 도태 검토" |

## 5. 도폐사(Cull) — 분석 대상 아님(이미 종료 처리). 알림 생략.

---

## 표시 경로 (농장주에게 어떻게 보이나)
1. **즉시 인라인**: 이벤트 POST 응답에 `insights: [{code, severity, title, message, recommended_actions}]` 동봉 → 입력 패널에 배너로 표시.
2. **알림 적재**: `WARNING` 이상 insight는 notification(IN_APP)으로도 적재 → 나중에 /notifications에서 재확인 + (G1 활성 시) 푸시.
3. **표현 등급**: 무료=템플릿 문장(renderer), AI Insight addon 농장=LLM 자연어(llm_renderer) — 기존 분기 재사용.

## 확정 임계값 (리서치 반영 2026-06-16 — 출처기반, default_metric_values 시드용)
> 산출규칙: target=권장/상위25%, **warning=해당국 평균선**, **critical=하위10~25%분위 또는 경제손실 구간**.
> 국가 데이터 없으면 글로벌/유전회사/SEA 프록시(저신뢰=⚠). 정의: STILLBORN=사산+미라(미라 포함!).
> 교차검증: PigOS deep-research 결과와 대조 예정. KR은 27년 노하우 최종 검수 권장.

### metric_code별 시드 (warning / critical / direction) — country: KR/US/BR/CN/VN
| metric_code | dir | KR | US | BR | CN | VN | 단위 |
|---|---|---|---|---|---|---|---|
| STILLBORN_RATE | above | 8 / 12 ⚠ | 8 / 12 | 8.4 / 10 | 8 / 12 ⚠ | 8 / 12 ⚠ | % |
| BORN_ALIVE | below | 10.5 / 9.5 ⚠ | 13.2 / 12 | 13 / 12 | 11 / 10 ⚠ | 11 / 10 ⚠ | 두/복 |
| PRE_WEANING_MORTALITY | above | 10 / 14 | 14 / 18 | 12 / 16 | 10 / 14 | 13.6 / 19 | % |
| WEANED_COUNT | below | 10 / 9 | 11 / 10 | 11 / 10 | 10.5 / 9 | 10 / 9 ⚠ | 두/복 |
| WSI | above | 7 / 10 | 7 / 10 | 7 / 10 | 7 / 10 | 7 / 10 | 일 (글로벌 공통) |
| RTS_RATE | above | 10 / 15 ⚠ | 10 / 15 | 10 / 15 ⚠ | 10 / 15 ⚠ | 10 / 15 ⚠ | % |
| PSY | below | 22 / 18 | 26 / 23 | 28 / 25 | 24 / 20 | 22 / 18 ⚠ | 두/모돈/년 |
| NPD | above | 50 / 70 | 50 / 70 | 50 / 70 | 50 / 70 | 50 / 70 | 일 |
| FARROWING_RATE | below | 82 / 78 | 82 / 78 | 82 / 78 | 82 / 78 | 82 / 78 | % |
| SOW_MORTALITY | above | 12 / 15 | 12 / 15 | 12 / 15 | 12 / 15 | 12 / 15 | %/년 |

### WEANING_AGE — 양방향(밴드) → 단일 direction 불가 → 2개 메트릭으로 분리
| metric_code | dir | 기준 | 비고 |
|---|---|---|---|
| WEANING_AGE_LOW | below | warning <18, critical <16(무항생제국 <14 US) | 너무 이른 이유 → WSI연장·장건강 |
| WEANING_AGE_HIGH | above | warning >28, critical >30 | 너무 늦은 이유 → 모돈회전율↓ |
> EU 진출 시 별도 룰셋: 이유일령 28일 **법정 최소**.

⚠ = 저신뢰(프록시/역산) — 운영 데이터 쌓이면 재캘리브레이션. 출처/근거는 리서치 원문 §1~9 참조.

## 리서치 반영 — 구현 시 필수 설계 함의
1. **STILLBORN 정의 = 사산+미라**. 화면/메시지에 "미라 포함" 명시(클레임 방지).
2. **WEANING_AGE는 밴드** → `WEANING_AGE_LOW`(below)+`WEANING_AGE_HIGH`(above) 2 메트릭으로 판정.
3. **국가 디폴트 + 글로벌 폴백 2계층**: effective_metric_values의 scope 체인(farm>region>market>system)이 이미 처리.
   국가 행 없으면 system(글로벌) 자동 적용 → 인사이트에 "글로벌 기준" 플래그 노출 권장.
4. **산차·계절 보정(v2)**: 사산율은 P1/P6+에서 +2~4%p, 여름철 WSI↑·분만율↓ → 전체평균 임계 그대로 쓰면 오경보.
   v1은 평균 임계로 출시하되, v2에서 parity 가중치 + 6~9월 "계절 경고" 태깅 추가(스펙에 backlog).
5. **다산복 PWM 동적조정(v2)**: 생존산자 13두↑ 복은 PWM 임계를 산자수 연동.
6. **재캘리브레이션(future)**: 외부 벤치마크는 시드일 뿐, 누적 데이터로 농장군 분위 기반 재학습.

## 구현 메모
- `insight_service.analyze_event(db, farm, event_type, event)` → `list[EventInsight]` (A는 RuleEngine.evaluate 재사용, B는 신규 체크)
- **B 체크는 임계값을 effective_metric_values()에서 읽음 → 코드에 숫자 하드코딩 0.** 위 표는 default_metric_values 시드로만 투입.
- event_service.record_* 커밋 후 호출. 분석 실패가 입력 자체를 막지 않게 격리(try/except, savepoint).
- 코드(엔진)는 숫자와 분리 → 시드값은 deep-research 교차검증 후 확정해도 무방.
