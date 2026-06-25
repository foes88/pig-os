# 작업 B 출력 — KR 27 재검증/확정 판정

> 기준: handoff/KPI_GOVERNANCE_v3.1.md / PROMPT_B_kr27_reverification.md
> 선행: 작업 A(head c5e7a9b1d3f0, 커밋 bcf75fb). 실행일 2026-06-25, dev DB 실측.
> 결론: **1차자료(한돈팜스 PDF) 미확보 → KR verified 0 확정 불가(D-6). 전부 provisional 유지 + missing 1.** A 결과는 안전하며 데이터 손실/역발화/근거없는 승격 없음.

---

## 1. §3 조회 결과 (DB 실측)

- **provisional 10**: psy, msy, farrowing_rate, weaned_per_litter, npd, sow_mortality, wsi, fcr, prewean_mortality, culling_rate
- **missing 1**: stillbirth_rate
- **orphan 16** (benchmarks 없는 KR source_observations): ABORTION_RATE, BORN_ALIVE, HIGH_PARITY_RATIO, MARKET_PRICE_HEAD, RTS_RATE, SOW_RESIDUAL_P0~P6(7), SOW_SALVAGE_CULL, SOW_SALVAGE_DEATH, WEANING_AGE_LOW, WEANING_WEIGHT
- 개수: 10+1+16 = 27 ✓ / default_metric_values KR 원본 27 삭제 0 ✓

## 2. orphan 16 분류 (★ 최우선)

**§2 kpi_definitions 16종 중 KR 미커버 5종** = sow_turnover, prewean_survival, postwean_survival, mummy_rate, postwean_mortality.
**orphan 16종 ∩ 미커버 5종 = ∅** → orphan 중 §2에 매핑 가능한 것 **0건**.

| orphan | 성격 | 분류 | 근거 |
|---|---|---|---|
| ABORTION_RATE | 유산율 | 정상 미매핑 | §2 KPI 없음 |
| BORN_ALIVE | 복당생존산자 | 정상 미매핑 | §2에 born-alive KPI 없음(weaned_per_litter≠) |
| HIGH_PARITY_RATIO | 고산차비율 | 정상 미매핑 | §2 KPI 없음 |
| MARKET_PRICE_HEAD | 두당경락가(KRW) | 정상 미매핑 | 가격(비KPI) |
| RTS_RATE | 재발정율 | 정상 미매핑 | §2 KPI 없음 |
| SOW_RESIDUAL_P0~P6 | 산차별 잔존가(KRW) | 정상 미매핑 | 경제값(비KPI) |
| SOW_SALVAGE_CULL/DEATH | 도태/폐사 잔존가(KRW) | 정상 미매핑 | 경제값(비KPI) |
| WEANING_AGE_LOW | 이유일령 | 정상 미매핑 | §2 KPI 없음 |
| WEANING_WEIGHT | 이유체중 | 정상 미매핑 | §2 KPI 없음 |

**결론: 16종 전부 "정상 미매핑". 누락(복구대상) orphan 0건.** A의 매핑 누락 없음.
**"16정의 = 16orphan"은 우연** (16정의 → KR매핑 11 + 미커버 5 / 16orphan → 전부 KR고유·경제값). 통째 매핑실패 신호 아님.

## 3. provisional 10 — §6 9조건 게이트

| 조건 | 결과 | 비고 |
|---|---|---|
| 1 source name/year/url | **FAIL** | 출처가 내부 ref("PigPlan:…"), 한돈팜스 공식 PDF/URL 미확인(D-6) |
| 2 모집단 확인 | **FAIL** | population_scope='unknown' (전국/조합/전문/상위1% 미구분) |
| 3 kpi 매핑 | PASS | 11종 매핑 명확 |
| 4 분자/분모/기간 일치 | PARTIAL | 분모 일치, 기간(period) 미확인 |
| 5 direction 일치 | PASS | kpi_def와 일치 |
| 6 denominator_type 일치 | PASS | |
| 7 period/population 또는 comparison∈{exact,compatible,normalized} | PASS | comparison_status='compatible'로 OR 충족 |
| 8 value_scale 명시 | PASS | percent_0_100 / n/a |
| 9 방향·스케일 테스트 존재 | PASS | severity_for·value_scale 테스트 |

→ **조건 1·2 미충족 → verified 금지 → 10종 provisional 잔류.** (1차자료 확보 시 1·2·4 해소되면 verified 승격 가능.)

## 4. 최종 판정표

| KPI | 최종상태 | 변경 | 사유 |
|---|---|---|---|
| psy/msy/farrowing_rate/weaned_per_litter/npd/sow_mortality/wsi/fcr/prewean_mortality/culling_rate | **provisional** | 유지 | 9조건 1·2 미충족(1차자료·모집단), D-6 |
| stillbirth_rate | **missing** | 유지 | 아래 §5 |
| (orphan 16) | 미매핑 | 유지 | §2 KPI 없음, benchmarks 비대상 |

**verified 0 / normalized_verified 0 / provisional 10 / missing 1 / 미매핑 16.**

## 5. 고위험 4항목 점검

- **사산율(stillbirth_rate)**: A "재정규화불가" 근거 = **'원자료 자체 없음'**. KR STILLBORN_RATE는 default_metric_values에 **임계값만**(warn 8/crit 12/target 5) 존재하고 사산·미라·총산 **원수치(raw_fields) 없음** → (사산+미라)/총산 재계산 불가 → **missing 정당**. (게다가 KR 임계 8%는 사산-only 관행치로 추정돼 PigOS 미라포함 정의와 직접 비교도 부적합.) → 한돈팜스 원문에 사산/미라 분리수치 확보 시에만 normalized_verified 검토.
- **NPD**: lower_better, warning_max=35/critical_max=50로 정배치(역발화 없음). gilt_entry_included 미결(D-1) → verified 금지 사유에 포함.
- **lower_better 그룹**(npd/sow_mortality/wsi/fcr/prewean_mortality): 전부 warning_max/critical_max에 적재(=값↑→severity↑). **역발화 없음 확인**(테스트 고정).
- **population_scope**: 현재 DB엔 PigPlan median 단일치만, 부경27.3/전문24.2/상위1% 값은 **미적재** → 혼입 없음. 단 단일치도 모집단 'unknown' → provisional.

## 6. D-6 / D-7

### D-6 (1차자료 필요) — verified 불가 사유
1차 발표자료(한돈팜스 공식 PDF) 확보 필요 KR 수치: **psy/msy/farrowing_rate** 등 전 provisional 10종의 모집단·기간(연간확정 vs 분기 vs 1~9월 잠정 = 22.3/22.4/22.5 구분) 미확정. period_start/end/publication_date 전부 NULL. → **확보 전 전부 provisional.**

### D-7 (KR전용 지표 발화룰 여부) — 코드확인 결과 + 질문
orphan(KR출신) 중 **글로벌 Rule Engine이 발화 참조**하는 것 확인:

| metric | 발화 룰 위치 | 성격 | 누수 위험 |
|---|---|---|---|
| SOW_RESIDUAL_P0 | `loss.py` (sow_cull_loss) | **KRW 경제값** | ★ 높음 — 非KR 사용자에 한국 원화 잔존가 |
| SOW_SALVAGE_CULL/DEATH | `loss.py` | **KRW 경제값** | ★ 높음 |
| MARKET_PRICE_HEAD | (발화 0) | 가격 데이터 | 낮음(룰 없음) |
| ABORTION_RATE | `reproduction.py` (abortion.rate_high) | 보편 KPI | 낮음(전세계 통용) |
| RTS_RATE | `reproduction.py` (rts.rate_high) | 보편 KPI | 낮음 |
| HIGH_PARITY_RATIO | `sow_herd.py` | 보편 KPI | 낮음 |
| BORN_ALIVE / WEANING_AGE_LOW / WEANING_WEIGHT | `litter.py`,`loss.py` | 보편 KPI | 낮음 |

→ **질문(코드 임의판정 금지)**: 경제값 3종(SOW_RESIDUAL/SOW_SALVAGE)이 KRW 가정으로 글로벌 발화 시 非KR 농장에 한국 잔존가가 노출됨. **이를 (a) KR 전용으로 분리할지 (b) 국가별 통화/잔존가 시드로 일반화할지** 결정 필요. **실행은 보류**(분리/삭제 안 함) — 표시만. ("KR전용 6종" 후보 = SOW_RESIDUAL_P0, SOW_SALVAGE_CULL, SOW_SALVAGE_DEATH, MARKET_PRICE_HEAD + HIGH_PARITY_RATIO + RTS_RATE 중 어디까지를 'KR전용'으로 볼지도 D-7 확정 필요.)

## 7. 테스트 (작업 B)
`api/tests/integration/test_kr27_reverification.py` — 15종 PASS:
- KR lower_better 5종 역발화 없음 / PSY higher_better 방향 / 1차자료 미확인→verified 차단(★⑦) / 사산율 근거없는 normalized·verified 승격 차단(★⑧) / orphan 5종 정의없음→승격불가 / 정상 provisional 통과.
- 전체 회귀: **pytest 519 passed** (단, §9 validator 무력화 이슈 별도 — 아래).

## 8. 다음 단계 (B 이후)
- **US PigCHAMP 적재**(§4.3): 사산율 normalized_verified(9.93%, formula 기록) / 분만율 verified(83.81%) / PWMFY → psy missing.
- EU/GB provisional(D-3 production_system 결정 후) / TH·MX global_fallback / BR·VN·CN 1차자료 확보 전 시드 금지.
- D-6 한돈팜스 PDF 확보 시 KR provisional → period별 verified.
- D-7 경제값 분리/일반화 결정.

## 9. validator 가드 무력화 발견 → 복원 완료 (mutation 검증 통과)
작업 중 `api/app/db/benchmark_seed.py` ★⑧ 1조건이 `if False and not b.get("transform_formula")`로 무력화된 것을 발견. **test_06이 이를 RED로 잡음**(DID NOT RAISE) = 테스트가 그 규칙을 진짜 강제함을 입증(Codex 프롬프트 mutation 검증 그대로). 사용자 승인하에 `if not b.get("transform_formula")`로 **복원** → 전체 519 green 재확인. ★⑧("transform_formula 없으면 normalized_verified 금지") seed validator·DB CHECK 양쪽 강제 정상.
