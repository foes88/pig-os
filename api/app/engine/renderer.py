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
