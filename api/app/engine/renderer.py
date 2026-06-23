"""
Template Renderer — Base tier response builder.

Converts StructuredResult → human-readable text using static templates.
Addon tier swaps this for an LLM call; the Rule Engine is not touched.

Locales supported: "en", "ko"
"""
from app.engine.rule_engine import Severity, StructuredResult

# ── Cause label translations ──────────────────────────────────────────────────
_CAUSE_EN: dict[str, str] = {
    "high_weaning_to_mating_interval":               "High weaning-to-mating interval",
    "extended_return_to_estrus":                     "Extended return to estrus",
    "repeat_breeding_failures_extending_cycle":      "Repeat breeding failures extending cycle",
    "low_litters_per_sow_per_year":                  "Low litters per sow per year",
    "critically_low_litter_size_or_survivability":   "Critically low litter size or survivability",
    "high_non_productive_days_extending_inter_litter_interval": "High NPD extending inter-litter interval",
    "repeat_breeding_failures":                      "Repeat breeding failures",
    "possible_disease_causing_early_embryo_loss_or_abortion": "Possible disease causing embryo loss/abortion",
    "insufficient_weaning_records":                  "Insufficient weaning records",
    "no_active_sows_registered_in_system":           "No active sows registered",
    "feed_intake_increased":                         "Increased feed intake with no gain improvement",
    "daily_gain_decreased":                          "Decreased daily weight gain",
    "mortality_increased":                           "Elevated mortality in finishing groups",
}

_CAUSE_KO: dict[str, str] = {
    "high_weaning_to_mating_interval":               "이유~교배 간격 과다",
    "extended_return_to_estrus":                     "발정 재귀 지연",
    "repeat_breeding_failures_extending_cycle":      "반복 교배 실패로 사이클 연장",
    "low_litters_per_sow_per_year":                  "연간 복수 부족",
    "critically_low_litter_size_or_survivability":   "복당 두수 또는 생존율 심각 저하",
    "high_non_productive_days_extending_inter_litter_interval": "NPD 과다로 분만간격 연장",
    "repeat_breeding_failures":                      "반복 교배 실패",
    "possible_disease_causing_early_embryo_loss_or_abortion": "질병으로 인한 수정란 손실/유산 의심",
    "insufficient_weaning_records":                  "이유 기록 부족",
    "no_active_sows_registered_in_system":           "시스템에 활성 모돈 없음",
    "feed_intake_increased":                         "사료 섭취량 증가 (증체 미개선)",
    "daily_gain_decreased":                          "일당 증체량 감소",
    "mortality_increased":                           "비육돈 폐사율 상승",
}

# ── Action label translations ─────────────────────────────────────────────────
_ACTION_EN: dict[str, str] = {
    "audit_sow_body_condition_score":                          "Audit sow body condition scores",
    "improve_transition_feed_intake":                          "Improve feed intake during transition",
    "verify_boar_exposure_protocol":                           "Verify boar exposure protocol",
    "review_heat_detection_frequency":                         "Review heat detection frequency",
    "audit_weaning_to_mating_interval":                        "Audit weaning-to-mating intervals",
    "review_sow_nutrition_and_genetic_merit":                  "Review sow nutrition and genetic merit",
    "reduce_npd_to_shorten_cycle_and_improve_psy":             "Reduce NPD to shorten inter-litter interval",
    "review_heat_detection_accuracy":                          "Review heat detection accuracy",
    "check_boar_libido_and_semen_quality":                     "Check boar libido and semen quality",
    "consult_veterinarian_for_reproductive_disease_screening": "Consult vet for reproductive disease screening",
    "complete_weaning_data_entry_for_current_year":            "Complete weaning data entry",
    "complete_sow_inventory_entry_via_onboarding":             "Complete sow inventory via onboarding",
    "check_feed_waste":                                        "Inspect feeders for waste",
    "review_group_health":                                     "Review group health records",
}

_ACTION_KO: dict[str, str] = {
    "audit_sow_body_condition_score":                          "모돈 체형 점수 확인",
    "improve_transition_feed_intake":                          "이행기 사료 섭취량 개선",
    "verify_boar_exposure_protocol":                           "웅돈 접촉 프로토콜 점검",
    "review_heat_detection_frequency":                         "발정 탐지 빈도 검토",
    "audit_weaning_to_mating_interval":                        "이유~교배 간격 점검",
    "review_sow_nutrition_and_genetic_merit":                  "모돈 영양 및 유전 능력 검토",
    "reduce_npd_to_shorten_cycle_and_improve_psy":             "NPD 감소로 분만간격 단축",
    "review_heat_detection_accuracy":                          "발정 탐지 정확도 검토",
    "check_boar_libido_and_semen_quality":                     "웅돈 성욕 및 정액 품질 확인",
    "consult_veterinarian_for_reproductive_disease_screening": "번식 질환 수의사 상담",
    "complete_weaning_data_entry_for_current_year":            "이유 데이터 입력 완성",
    "complete_sow_inventory_entry_via_onboarding":             "온보딩으로 모돈 재고 입력",
    "check_feed_waste":                                        "급이기 사료 낭비 점검",
    "review_group_health":                                     "그룹 건강 기록 검토",
}


# ── 확장 규칙 라벨 (litter / grow-finish / abortion) ───────────────────────────
_CAUSE_EN.update({
    "high_stillbirth_rate":                                   "High stillbirth rate",
    "possible_prolonged_farrowing_or_late_gestation_disease": "Possible prolonged farrowing or late-gestation disease",
    "high_mummified_rate":                                    "High mummified-fetus rate",
    "possible_in_utero_viral_infection":                      "Possible in-utero viral infection (PPV/PRRS)",
    "low_born_alive_per_litter":                              "Low born-alive per litter",
    "possible_high_embryonic_loss":                           "Possible high embryonic loss",
    "low_piglets_weaned_per_litter":                          "Low piglets weaned per litter",
    "high_pre_weaning_piglet_mortality":                      "High pre-weaning piglet mortality",
    "low_average_birth_weight":                               "Low average birth weight",
    "possible_large_litter_or_poor_late_gestation_feeding":   "Possible large litter or poor late-gestation feeding",
    "low_weaning_weight":                                     "Low weaning weight",
    "lactation_length_too_short":                             "Lactation length too short",
    "lactation_length_too_long":                              "Lactation length too long",
    "elevated_abortion_rate":                                 "Elevated abortion rate",
    "possible_abortive_disease":                              "Possible abortive disease (lepto/parvo/PRRS)",
    "high_feed_conversion_ratio":                             "High feed conversion ratio",
    "possible_subclinical_disease_depressing_efficiency":     "Possible subclinical disease depressing efficiency",
    "low_average_daily_gain":                                 "Low average daily gain",
    "possible_subclinical_disease_depressing_growth":         "Possible subclinical disease depressing growth",
    "high_finishing_mortality":                              "High finishing mortality",
    "possible_disease_outbreak_in_finishing":               "Possible disease outbreak in finishing",
    "low_total_born_per_litter":                             "Low total-born per litter",
    "high_sow_culling_rate":                                 "High sow culling rate",
    "possible_involuntary_culling_from_reproductive_failure": "Possible involuntary culling from reproductive failure",
    "high_sow_mortality":                                    "High sow mortality",
    "possible_disease_or_management_failure":                "Possible disease or management failure",
    "aging_sow_herd_high_parity_share":                     "Aging herd — high share of parity 7+",
    "excessive_sow_replacement":                            "Excessive sow replacement rate",
    "insufficient_sow_replacement":                         "Insufficient sow replacement rate",
    "second_litter_slump":                                  "Second-litter slump (P2 born-alive drop vs P1)",
    "pregnancy_accidents_concentrated_in_p1":               "Pregnancy accidents concentrated in parity 1",
    "possible_reproductive_disease_in_gilts":               "Possible reproductive disease in gilts",
    "seasonal_summer_infertility":                          "Seasonal summer infertility (farrowing-rate drop)",
    "severe_heat_stress_depressing_conception":             "Severe heat stress depressing conception",
})
_CAUSE_KO.update({
    "high_stillbirth_rate":                                   "사산율 과다",
    "possible_prolonged_farrowing_or_late_gestation_disease": "난산 또는 임신후기 질병 의심",
    "high_mummified_rate":                                    "미라변성태 과다",
    "possible_in_utero_viral_infection":                      "자궁 내 바이러스 감염 의심(PPV/PRRS)",
    "low_born_alive_per_litter":                              "복당 실산자 부족",
    "possible_high_embryonic_loss":                           "수정란 손실 과다 의심",
    "low_piglets_weaned_per_litter":                          "복당 이유두수 부족",
    "high_pre_weaning_piglet_mortality":                      "포유자돈 폐사 과다",
    "low_average_birth_weight":                               "평균 출생체중 저하",
    "possible_large_litter_or_poor_late_gestation_feeding":   "과다 복수 또는 임신후기 급이 부족 의심",
    "low_weaning_weight":                                     "이유체중 저하",
    "lactation_length_too_short":                             "포유기간 과소(조기이유)",
    "lactation_length_too_long":                              "포유기간 과다",
    "elevated_abortion_rate":                                 "유산율 상승",
    "possible_abortive_disease":                              "유산성 질병 의심(렙토/파보/PRRS)",
    "high_feed_conversion_ratio":                             "사료요구율(FCR) 과다",
    "possible_subclinical_disease_depressing_efficiency":     "준임상 질병으로 사료효율 저하 의심",
    "low_average_daily_gain":                                 "일당증체(ADG) 저조",
    "possible_subclinical_disease_depressing_growth":         "준임상 질병으로 증체 저하 의심",
    "high_finishing_mortality":                              "비육 폐사율 과다",
    "possible_disease_outbreak_in_finishing":               "비육돈 질병 발생 의심",
    "low_total_born_per_litter":                             "복당 총산자 부족",
    "high_sow_culling_rate":                                 "모돈 도태율 과다",
    "possible_involuntary_culling_from_reproductive_failure": "번식장애로 인한 비자발 도태 의심",
    "high_sow_mortality":                                    "모돈 폐사율 과다",
    "possible_disease_or_management_failure":                "질병 또는 관리 실패 의심",
    "aging_sow_herd_high_parity_share":                     "노산돈(7산 이상) 비율 과다",
    "excessive_sow_replacement":                            "모돈 갱신율 과다",
    "insufficient_sow_replacement":                         "모돈 갱신율 과소",
    "second_litter_slump":                                  "2산차 슬럼프(P2 실산 감소)",
    "pregnancy_accidents_concentrated_in_p1":               "임신사고 1산차 편중",
    "possible_reproductive_disease_in_gilts":               "후보돈 번식질환 의심",
    "seasonal_summer_infertility":                          "여름철 계절성 불임(분만율 하락)",
    "severe_heat_stress_depressing_conception":             "고온스트레스로 수태 저하",
})
_ACTION_EN.update({
    "review_farrowing_supervision":                 "Increase farrowing attendance/supervision",
    "check_sow_parity_and_gestation_length":        "Check sow parity profile and gestation length",
    "consult_veterinarian_for_perinatal_loss":      "Consult vet for perinatal loss",
    "review_gestation_biosecurity_and_vaccination": "Review gestation biosecurity and vaccination",
    "screen_for_abortive_pathogens":                "Screen for abortive pathogens",
    "audit_insemination_timing":                    "Audit insemination timing",
    "review_gilt_development_and_sow_nutrition":     "Review gilt development and sow nutrition",
    "improve_colostrum_and_cross_fostering":         "Improve colostrum intake and cross-fostering",
    "improve_lactation_feed_and_creep":             "Improve lactation feed and creep management",
    "review_sow_milk_yield":                         "Review sow milk yield/udder health",
    "adjust_weaning_age_to_target":                 "Adjust weaning age toward target",
    "review_early_weaning_protocol":                "Review early-weaning protocol",
    "review_sow_throughput_and_npd":                "Review sow throughput and NPD",
    "audit_feed_quality_and_wastage":               "Audit feed quality and wastage",
    "review_finishing_diet_and_stocking_density":   "Review finishing diet and stocking density",
    "investigate_finishing_health_and_environment": "Investigate finishing health and environment",
    "check_water_and_feeder_access":                "Check water and feeder access",
    "consult_veterinarian_for_finishing_mortality": "Consult vet for finishing mortality",
    "audit_feed_quality_and_mycotoxins":            "Audit feed quality and mycotoxins",
    "review_culling_policy_and_reasons":            "Review culling policy and reasons",
    "review_gilt_replacement_plan":                 "Review gilt replacement plan",
    "audit_reproductive_failure_and_lameness":      "Audit reproductive failure and lameness",
    "audit_lameness_and_prolapse":                  "Audit lameness and prolapse",
    "review_heat_stress_and_body_condition":        "Review heat stress and body condition",
    "consult_veterinarian_for_sow_mortality":       "Consult vet for sow mortality",
    "review_parity_structure_and_replacement":      "Review parity structure and replacement",
    "plan_gilt_introduction_cadence":               "Plan gilt introduction cadence",
    "review_involuntary_culling_drivers":           "Review involuntary-culling drivers",
    "review_gilt_intake_plan":                      "Review gilt intake plan",
    "improve_p1_lactation_feed_and_bcs":            "Improve P1 lactation feed and body condition",
    "shorten_p1_wean_to_service_interval":          "Shorten P1 wean-to-service interval",
    "review_gilt_acclimation_and_vaccination":      "Review gilt acclimation and vaccination",
    "audit_gilt_breeding_management":               "Audit gilt breeding management",
    "improve_summer_cooling_and_ventilation":       "Improve summer cooling and ventilation",
    "review_summer_feed_intake_and_boar_exposure":  "Review summer feed intake and boar exposure",
    "audit_heat_abatement_and_insemination_timing": "Audit heat abatement and insemination timing",
})
_ACTION_KO.update({
    "review_farrowing_supervision":                 "분만 입회·관리 강화",
    "check_sow_parity_and_gestation_length":        "모돈 산차 분포·임신기간 점검",
    "consult_veterinarian_for_perinatal_loss":      "주산기 손실 수의사 상담",
    "review_gestation_biosecurity_and_vaccination": "임신사 방역·백신 프로그램 점검",
    "screen_for_abortive_pathogens":                "유산성 병원체 검사",
    "audit_insemination_timing":                    "수정 적기 점검",
    "review_gilt_development_and_sow_nutrition":     "후보돈 육성·모돈 영양 검토",
    "improve_colostrum_and_cross_fostering":         "초유 급여·양자 개선",
    "improve_lactation_feed_and_creep":             "포유사료·보조사료(크립) 관리 개선",
    "review_sow_milk_yield":                         "모돈 비유량·유방 건강 점검",
    "adjust_weaning_age_to_target":                 "이유일령 목표 조정",
    "review_early_weaning_protocol":                "조기이유 프로토콜 검토",
    "review_sow_throughput_and_npd":                "모돈 회전율·NPD 검토",
    "audit_feed_quality_and_wastage":               "사료 품질·손실 점검",
    "review_finishing_diet_and_stocking_density":   "비육 사료·사육밀도 검토",
    "investigate_finishing_health_and_environment": "비육 건강·환경 조사",
    "check_water_and_feeder_access":                "급수·급이 접근성 점검",
    "consult_veterinarian_for_finishing_mortality": "비육 폐사 수의사 상담",
    "audit_feed_quality_and_mycotoxins":            "사료 품질·곰팡이독소 점검",
    "review_culling_policy_and_reasons":            "도태 기준·사유 검토",
    "review_gilt_replacement_plan":                 "후보돈 보충 계획 검토",
    "audit_reproductive_failure_and_lameness":      "번식장애·지제(파행) 점검",
    "audit_lameness_and_prolapse":                  "지제(파행)·탈출증 점검",
    "review_heat_stress_and_body_condition":        "고온스트레스·체형 관리 검토",
    "consult_veterinarian_for_sow_mortality":       "모돈 폐사 수의사 상담",
    "review_parity_structure_and_replacement":      "산차 구조·보충 검토",
    "plan_gilt_introduction_cadence":               "후보돈 도입 주기 계획",
    "review_involuntary_culling_drivers":           "비자발 도태 원인 검토",
    "review_gilt_intake_plan":                      "후보돈 도입 계획 검토",
    "improve_p1_lactation_feed_and_bcs":            "1산차 포유사료·체형 개선",
    "shorten_p1_wean_to_service_interval":          "1산차 이유~교배 간격 단축",
    "review_gilt_acclimation_and_vaccination":      "후보돈 순화·백신 검토",
    "audit_gilt_breeding_management":               "후보돈 교배 관리 점검",
    "improve_summer_cooling_and_ventilation":       "여름 냉방·환기 개선",
    "review_summer_feed_intake_and_boar_exposure":  "여름 사료섭취·웅돈접촉 검토",
    "audit_heat_abatement_and_insemination_timing": "고온대책·수정적기 점검",
})


def _label(mapping: dict[str, str], code: str) -> str:
    return mapping.get(code, code.replace("_", " ").title())


def _severity_prefix(sev: Severity, locale: str) -> str:
    if locale == "ko":
        return {"OK": "✓", "INFO": "ℹ", "WARNING": "⚠ 경고", "CRITICAL": "🔴 위험"}.get(sev, sev)
    return {"OK": "✓", "INFO": "ℹ", "WARNING": "⚠ Warning", "CRITICAL": "🔴 Critical"}.get(sev, sev)


def render_text(result: StructuredResult, locale: str = "en") -> str:
    """
    Convert StructuredResult to plain-text report.
    Override with LLM renderer in Addon tier — this function signature is the contract.
    """
    cause_map  = _CAUSE_KO  if locale == "ko" else _CAUSE_EN
    action_map = _ACTION_KO if locale == "ko" else _ACTION_EN

    critical_findings = [f for f in result.findings if f.severity == Severity.CRITICAL]
    warning_findings  = [f for f in result.findings if f.severity == Severity.WARNING]
    info_findings     = [f for f in result.findings if f.severity == Severity.INFO]

    if not result.findings:
        return (
            "모든 KPI가 정상 범위입니다." if locale == "ko"
            else "All KPIs are within normal range."
        )

    lines: list[str] = []

    for f in critical_findings + warning_findings + info_findings:
        prefix = _severity_prefix(f.severity, locale)
        if f.current_value is not None and f.target_value is not None:
            header = f"{prefix} [{f.kpi}] {f.current_value} (target: {f.target_value})"
        elif f.current_value is not None:
            header = f"{prefix} [{f.kpi}] {f.current_value}"
        else:
            header = f"{prefix} [{f.kpi}]"
        lines.append(header)

        if f.causes:
            label = "원인" if locale == "ko" else "Causes"
            cause_text = ", ".join(_label(cause_map, c) for c in f.causes)
            lines.append(f"  {label}: {cause_text}")

        if f.recommended_actions:
            label = "조치" if locale == "ko" else "Actions"
            action_text = ", ".join(_label(action_map, a) for a in f.recommended_actions)
            lines.append(f"  {label}: {action_text}")

        lines.append("")

    return "\n".join(lines).strip()
