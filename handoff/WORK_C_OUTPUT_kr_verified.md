# 작업 C 완료 — KR verified 승격

> 기준: handoff/KPI_GOVERNANCE_v3.1.md §10(v3.2) / PROMPT_C_kr_verified_promotion.md
> 1차자료: 한돈팜스 전국 한돈농가 2025년 전산성적 (한돈연구소, 2026-05) — **내부 입수본, 메타+검증수치만 저장(PDF 원본 미저장)**
> 실행일 2026-06-25, dev DB head=`d7f9b2c4e6a1`. 운영 미배포(A·B·C 함께 배포 권장).

## 승격 (national_general, verified 7종)
| kpi_code | 값 | value_scale | 처리 |
|---|---|---|---|
| psy | 22.4 | n/a | provisional→verified UPDATE |
| msy | 18.9 | n/a | UPDATE |
| farrowing_rate | 85.7 | percent_0_100 | UPDATE |
| weaned_per_litter | 10.45 | n/a | UPDATE |
| sow_turnover | 2.14 | n/a | 신규 INSERT |
| prewean_survival | 89.1 | percent_0_100 | 신규 INSERT |
| postwean_survival | 84.3 | percent_0_100 | 신규 INSERT |

- comparison_status=`compatible`(상시모돈 분모 → EU/GB InterPIG 호환), mapping_status=`exact`, is_provisional=false.
- transformed_value=1차자료 전국 연간확정값. **알림 임계(warning/critical)는 NULL** — 1차자료는 평균만 제공, 임계 위조 안 함(별도 단계).
- 이전 provisional의 PigPlan median 임계는 verified 시 제거(다른 추출원이라 verified 행에 혼입 금지).

## 별도 obs_group (professional, normalized_verified 1종)
| kpi_code | 값 | population_scope | transform_formula | comparison |
|---|---|---|---|---|
| stillbirth_rate | 9.3% (1.27/13.62) | professional (229호) | 복당사산/복당총산*100 | normalized |
- 검증전제(메타 기록): **총산=실산+사산+미라 항등식 → 잔차(총산−생존)=사산+미라**. 복당생존=born alive(실산), 복당이유(11.03) 별도컬럼이므로 생존=이유전 실산. 라벨이 "복당사산"이어도 잔차구조상 미라 포함 → PigOS stillbirth_rate 정의 일치.

## 제외 / missing 유지
- **total_born(복당총산 11.73)**: kpi_definitions에 KPI 코드 없음(분모유형으로만 존재) → 시드 제외(orphan). 코드 신설은 별건.
- **market_age(출하일령 195)**: PigOS rule 28종·kpi_def 16종 모두 미등록 → 드롭.
- **npd**: 전국 일반사용자 표에 NPD 컬럼 없음 → missing 유지. **D-1과 무관**(데이터 부재).
- **전국 stillbirth_rate**: missing 유지 — 전문값 9.3%를 전국 슬롯에 채우지 않음(모집단 혼입 금지). national_general엔 사산 원자료 없음.

## STEP1 kpi_code 확인 결과
- §2 추정명 `preweaning_survival`/`postweaning_survival` → 실제 `prewean_survival`/`postwean_survival`로 대조·교정.
- 7종 전부 kpi_definitions 존재, direction(higher_better)·value_scale 일치(불일치 0). override 없음.

## STEP5 가드 무결성 (mutation 재발 점검)
- `if False/if True/and False/or True`·주석처리 raise: **0건**(benchmark_seed/thresholds). ★⑧ transform_formula 가드 생존 확인.
- **DB CHECK 실작동(파이썬 우회 raw INSERT)**: active-verified unique 중복→ERROR / 복합FK 오류→ERROR / ★⑦ verified+value NULL→ERROR. 전부 DB 레벨 차단 확인.

## 스키마 변경 (작업 C)
- `benchmarks.population_scope` 컬럼 신설(national_general/professional 구분).
- active-verified unique index에 population_scope 포함 → 같은 KPI라도 모집단 다르면 verified 공존(전국 22.4 / 전문 24.2), 같은 모집단 중복은 차단.
- ⚠️ PROMPT_C SQL의 `b.country`/`b.population_scope`는 예시 — 실제 컬럼은 `country_code` + 신설 `population_scope`로 매핑.

## 테스트 (STEP6)
- `test_kr_verified_promotion.py` 11종 PASS: 7종 value_scale 일치 / 전문 사산율 normalized 유효 / 전국 사산율 누수 차단 / national·professional 공존 / 같은 population 중복 차단(DB).
- 기존 test_15(active-verified)도 population_scope 포함 인덱스에 맞게 갱신.
- **전체 회귀: pytest 530 passed** (B 519 + C 11).

## 전국 stillbirth_rate missing 유지: ✓ 확인
## 미배포 여부: ✓ 운영 미반영 (A·B·C 함께 배포 권장)

## KR 최종 상태 (benchmarks)
verified 7 (national_general) / normalized_verified 1 (professional 사산율) / provisional 6 (culling_rate·fcr·npd·prewean_mortality·sow_mortality·wsi — 1차자료 미확보분) / missing 1 (전국 사산율) / orphan 16 (source_observations만).

## 다음 단계 (§10.7)
1. ✅ 작업 C (완료)
2. **Codex로 A·B·C 교차검증** (가드 무력화·DB CHECK 실작동) — US 적재 전 권장
3. US PigCHAMP 적재 (D-4 결정 후): 사산율 9.93% normalized / 분만율 83.81% verified / PWMFY→psy missing
4. EU/GB (D-3 후) / BR·VN·CN 1차자료 후 / TH·MX global_fallback
