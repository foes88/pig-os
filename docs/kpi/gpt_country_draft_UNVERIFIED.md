# GPT 국가별 KPI 초안 — UNVERIFIED_DRAFT
> ⚠️ **미검증 초안. 어떤 항목도 검증된 사실이 아님.** GPT(교차 리뷰 모델)가 2026-07-21 생성. 인용된 기관·프로그램명(Pork Checkoff, Agriness, Embrapa, AHDB, SEGES, IFIP/GTTT/GTE, Teagasc, DanBred 등)은 **원문 대조된 바 없음.** source_year/cohort/denominator 전부 부재.
> 용도: 런 C(evidence 스텁)의 UNVERIFIED_DRAFT 격리 수록 입력 전용. 실사(웹 원문 대조) 없이 REVIEWED_DIRECTION 이상 승격 금지.

## 구조 제안 (채택 확정분 — 검증 불요, v0.4에 반영)
- 국가 × farm_type × production_stage 차원 / priority_class 6분류(NORTH_STAR|DRIVER|GUARDRAIL|FINANCIAL|QUALITY|CONTEXT) / evidence_status·decision_status 분리 / EU 단일 프로필 폐기 / G-C1~C8 승인 게이트 / 출처 우선순위 5단계

## 국가별 KPI 후보 (전부 UNVERIFIED_DRAFT)

### US
- BREEDING PRIMARY 후보: pigs_weaned_per_mated_female_year, preweaning_mortality, farrowing_rate, sow_mortality, born_alive_per_litter / SECONDARY: NPD, repeat_service, gilt_utilization, weaning_weight
- NURSERY/GROW_FINISH PRIMARY 후보: mortality_or_survival, adg, fcr, days_on_feed, market_weight
- FARROW_TO_FINISH PRIMARY 후보: msy, total_survival_to_market, whole_herd_feed_efficiency, cost_per_marketed_pig, margin_per_pig
- 주장 근거(미검증): Pork Checkoff 벤치마크가 sow/nursery/grow-finish/wean-to-finish 별도 집단 분석

### BR
- BREEDING/PIGLET PRIMARY 후보: pigs_weaned_per_sow_year, NPD, farrowings_per_sow_year, weaned_per_litter, born_alive_per_litter (미검증 근거: Agriness 평가 순서)
- FARROW_TO_FINISH PRIMARY 후보: finished_pigs_per_sow_year, mortality, fcr, adg, live_or_carcass_weight_sold, operating_cost_per_kg, cash_margin_per_pig (미검증 근거: Embrapa 기술관리 항목)

### GB
- INDOOR/OUTDOOR 시스템 분리 필수
- PRIMARY 후보: operating_cost_per_deadweight_kg, margin_per_kg_or_head, fcr, daily_liveweight_gain, mortality, pigs_weaned_per_sow_year — **재무 KPI 최상단** (미검증 근거: AHDB)

### DK
- BREEDING PRIMARY 후보: pigs_weaned_per_sow_year, total_piglet_mortality, born_alive, weaning_weight_or_uniformity, sow_mortality — 초다산 계통 특성상 이유두수+자돈 생존+FCR 동시 전면화 (미검증 근거: SEGES/DanBred)
- WEANER/FINISHER PRIMARY 후보: feed_conversion, mortality, adg, days_to_target_weight, carcass_weight_or_lean_value

### FR
- BREEDING PRIMARY 후보: piglets_weaned_per_productive_sow_year, born_alive_per_litter, preweaning_loss, farrowing_interval, first_service_conception, replacement_rate
- FARROW_TO_FINISH PRIMARY 후보: pigs_produced_per_sow_year, live_kg_per_sow_year, global_fcr, adg, postweaning_loss, margin_over_feed_and_replacement (미검증 근거: IFIP GTTT/GTE 이원 체계)

### IE
- PRIMARY 후보: pigs_produced_per_sow_year, piglet/weaner/finisher_mortality, adg_weaning_to_sale, feed_conversion_efficiency, live_or_carcass_output, feed_per_kg_carcass / SECONDARY: empty_days, born_alive, litters_per_sow_year, sow_mortality_culling (미검증 근거: Teagasc Profit Monitor)

### CN
- BREEDING PRIMARY 후보: psy, gilt_utilization, age_at_first_service, sow_gilt_mortality, culling_rate, born_alive, weaned_per_litter, farrowing_rate
- GROW_FINISH PRIMARY 후보: adg, fcr, survival_rate, mortality, feeding_days, market_weight, piglet_source_consistency
- 질병·biosecurity·PRRS 안정화 = HEALTH_GUARDRAIL 분리

### VN
- BREEDING/PIGLET PRIMARY 후보: born_alive, weaned_per_litter, preweaning_mortality, weaning_weight, piglet_adg, diarrhoea_incidence, farrowing_interval
- GROW_FINISH PRIMARY 후보: mortality, adg, fcr, days_to_sale, feed_cost_per_kg_gain
- Guardrail 별도: sudden_mortality, diarrhoea, medication_usage, biosecurity_compliance, data_freshness (ASF 회복 맥락)
- benchmark_exposure=NONE, 수치 임계 금지 (국가 대표 벤치마크 부재)

### TH
- 잠정 후보: adg, fcr, mortality, days_to_target_weight, backfat_lean_pct, preweaning_mortality, weaned_per_sow_year
- 근거가 오래됐거나 시험농장 중심 → evidence_status=INSUFFICIENT 또는 REVIEWED_DIRECTION, seed 금지, 인테그레이터 데이터 우선

### JP
- FINISHER/F2F PRIMARY 후보: carcass_weight, grade_compliance, backfat_lean_spec, margin_over_feed_cost_per_pig, fcr, days_to_market, meat_quality_brand_spec — 출하규격·도체가치 전면 (미검증 근거: 2023 도체거래 규격 변경 연구)
- STANDARD_COMMERCIAL / BRANDED_SPECIALTY 프로필 분리 옵션 (→ B-06 결정 자료)

### KR
- 기존 PigPlan SSOT 유지: PSY, MSY, NPD, farrowing_rate, preweaning_mortality, sow_mortality_culling, FCR, 기간 운영비·현금 손익. A-rule·Asset Policy 차단 유지.
