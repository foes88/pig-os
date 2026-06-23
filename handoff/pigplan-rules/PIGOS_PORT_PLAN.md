# PigPlan 136룰 → PigOS 이식 — 확정 매핑 + Phase 계획 (제안)

> 본문(`pigplan_ai_rules_reference.md` 4962줄) 전수 대조로 자동초안(coverage.md)을 재검증한 결과.
> **합의 후 구현.** 작성: 2026-06-23. 대조 기준 = PigOS 현재 **24개 엔진룰**(초안의 "9개"는 낡음).

---

## 1. 자동초안 분류는 신뢰 불가 — 레이어 재정의

초안의 `✅있음 45 / ⚠️seed 44 / 🆕신규 47`은 **키워드 자동매칭**이라 레이어가 뒤섞임. PigOS 아키텍처(엔진=결정론 Finding / Renderer=LLM Addon / seed=임계데이터)에 맞춰 재분류:

| 레이어 | 의미 | 재검증 건수 | 초안 대비 |
|---|---|---|---|
| **ENGINE-HAVE** | 24룰이 이미 탐지 (seed로 임계만 보강) | ~22 (룰을 *튜닝*) | 초안 "✅45"는 과장 — 대부분 탐지가 아니라 seed/renderer |
| **ENGINE-NEW** | 신규 결정론 룰로 만들 가치 | ~18 | |
| **SEED** | 임계/파라미터 → default_metric_values (코드無) | ~46 | |
| **RENDERER/LLM** | AI 프롬프트·출력형식·진단서술 → Addon#1 | ~45 | **초안이 엔진/신규로 대거 오분류** |
| **OUT-OF-SCOPE** | KR 플랫폼 내부(크롤러·전국집계·예측·도체·입력지연) | ~20 | |

**가장 큰 발견**: KR 136룰 중 **약 45개는 엔진이 아니라 LLM Renderer(Addon#1) 프롬프트**(OUTPUT_STYLE 10 + DIAGNOSIS 12 + ANALYSIS 7 + 서술형 다수). 엔진룰로 만들면 안 됨. **약 20개는 OUT-OF-SCOPE**(전국 벤치마킹·질병 크롤러·Prophet 예측·도체등급·KR 입력지연).

### 자동초안 오분류 12건 (대표)
1. `GRADE_WEIGHTS_V1` → "✅wsi.overdue" ❌ → 실제 **월간 종합등급 가중치**(WSI 무관). SEED(composite).
2. OUTPUT_STYLE 10건 "🆕신규" ❌ → 전부 **RENDERER**.
3. DIAGNOSIS 12건(`PSY_DRILLDOWN`·`MULTI_AXIS_GUIDE`·`NPD_BREAKDOWN`…) → **RENDERER** 서술, 탐지 아님.
4. CRAWLING 3건 "✅disease" ❌ → **OUT-OF-SCOPE** 크롤러 정책.
5. `FARM_SIZE_GROUP`/`FARM_SIZE_CLASS` "✅inventory.zero" ❌ → 규모 구간, **SEED**.
6. 전국집계 필터(`FARM_ELIGIBILITY`·`FARM_FILTER`·`COMPARE_METHOD`·`PEER_MATCH`…) "⚠️seed" ❌ → **OUT-OF-SCOPE**.
7. LOSS_CALC `S1/S_PW/S9` "✅" ❌ → **ENGINE-NEW 손실계산기**(탐지≠비용산출).
8. `SEASONAL_INFERTILITY` "✅farrowing" ❌ → **ENGINE-NEW**(Q3-Q1 하락 탐지, 절대임계와 다름).
9. NURSING_PIGLET 5건 전부 "✅pwmr" ❌ → 2건 RENDERER, 3건 ENGINE-NEW(사유/일령 데이터 필요).
10. `PREG_LOSS/PARITY_DIST`·`PARITY/SLUMP_GUIDE` → **ENGINE-NEW**(결정론 패턴).
11. `LOSS_PRESENTATION` "✅npd" ❌ → **RENDERER**.
12. `AI_MODEL_STRATEGY`·`AI_CLASS_RULE` 모델라우팅 → **OUT-OF-SCOPE**(Addon#1 LLM 설정).

---

## 2. Phase별 작업목록 (제안)

### Phase A — SEED 주입 (코드無·최고 ROI·최저 리스크) ⭐먼저
~46개 임계세트를 `default_metric_values`(system/region/farm scope)에 주입 → **기존 24룰이 PigPlan 실측 임계로 작동**. 국가차이 = scope로 흡수(`if country==` 금지).
- 룰별 그룹: psy/npd/farrowing/wsi/rts·abortion/pwmr·stillborn·weaned/fcr·adg·finish_mort/culling·sow_mort/parity/disease/inventory (서브에이전트 §4 전체 목록)
- KR 7등급(KPI_7GRADE)·벤치(NPD_BENCHMARK·FARM_SIZE_BENCHMARK)·cohort 파라미터·SYSTEM_DEFAULTS·VALID_RANGES 가드
- 산출물: alembic seed 마이그레이션 1~2개 + benchmark 화면 노출
- **미보유 데이터 임계는 "future-capture seed"로 표시만**(THI/BCS/TREATMENT/HEAT/MSY) — 활성 안 함

### Phase B — ENGINE-NEW Tier A (지금 데이터로 가능) 
| # | rule_id | 내용 | 데이터 |
|---|---|---|---|
| B1 | `loss.npd` | NPD 손실액(생리지연만) | reproductive_events+PSY+farm_config |
| B1 | `loss.preweaning_mortality` | 포유폐사 손실액 | piglet_events+단가 |
| B1 | `loss.pregnancy_accident` | 임신사고 손실액 | reproductive_events+PSY |
| B1 | `loss.sow_culling` | 도태 잔여가치 손실 | sows(parity,exit)+잔존가 seed |
| B2 | `seasonal.summer_infertility` | 여름 분만율 하락(SID) | matings/farrowings 월별 |
| B2 | `replacement.rate_abnormal` | 모돈 갱신율 과다/과소 | sows |
| B2 | `parity.second_litter_slump` | 2산차 슬럼프 | farrowings by parity |
| B2 | `accident.parity_skew` | 임신사고 산차편중(감염의심) | reproductive_events+sows.parity |
| B3 | `farm.health_class` | 농가 RED/YEL/GRN 종합등급 | 기존 룰 severity 롤업 |
| B3 | `farm.weakest_kpi` | 가장 시급한 KPI 자동선정 | KPI 스냅샷 |
| B4 | `boar.farrow_rate_low` | 웅돈별 분만율 저조 | matings.boar+farrowings |

### Phase C — RENDERER/LLM (Addon#1) ~45건
KR 진단서술·출력형식·코멘트규칙 → **Phase 14 LLM Renderer 프롬프트**로 이식. 엔진 무관, Addon#1 활성 때 가치. (별도 트랙)

### Phase D — Tier B: 신규 데이터 캡처 필요 (입력기능 먼저)
- 포유자돈 **폐사 사유·일령** 코딩 → `piglet.crushing_rate`/`death_age_skew`/`cause_trend`
- **임신감정(preg-check)** 이벤트 → abortion 분모 정밀화·conception
- **MSY** 산출 → `msy.below_bep`
- **배치(AIAO)** 16주+ 이력 → `batch.aiao_detect`
→ 각각 "데이터 입력기능 추가"가 선행. 룰은 그 다음.

### Phase E — OUT-OF-SCOPE (PigOS 네이티브 피드 선행, 로드맵만)
전국 벤치마킹·질병 크롤러·Prophet 예측·도체등급·KR 입력지연. 복제 금지, 필요 시 재해석.

---

## 3. 권장 실행 순서
**A(seed) → B(엔진신규 Tier A) → C(Renderer, Addon#1 때) / D(데이터캡처 후) / E(로드맵).**
A·B만으로 KR 결정론 탐지 가치의 대부분을 PigOS 네이티브로 흡수. C는 Addon#1, D·E는 후속.
