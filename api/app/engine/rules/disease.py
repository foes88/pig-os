"""
Disease-prevalence-aware rules.
Elevates or suppresses alert severity based on regional_prevalence of notifiable diseases.

Registered rules:
  disease.endemic_risk  → CRITICAL if notifiable + ENDEMIC in farm's country (last 30 days)
  disease.free_region   → INFO if disease is officially FREE in farm's country
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity

# Prevalence levels that trigger elevated alert
_CRITICAL_STATUSES = {"ENDEMIC", "EPIDEMIC"}
_WARNING_STATUSES = {"MODERATE", "SPORADIC"}
_FREE_STATUSES = {"FREE", "ABSENT"}


async def _disease_endemic_risk(ctx: RuleContext) -> list[Finding]:
    """
    Fires when a notifiable disease with recent health events is ENDEMIC in this farm's country.
    Data injected via ctx.extra["recent_notifiable_diseases"]:
      [{"disease_code": str, "label_en": str, "prevalence": {"KR":"ENDEMIC",...}, "event_count": int}]
    """
    events = ctx.extra.get("recent_notifiable_diseases", [])
    if not events:
        return []

    country = ctx.country.upper()
    findings: list[Finding] = []

    for ev in events:
        prevalence: dict = ev.get("prevalence") or {}
        status = (prevalence.get(country) or "UNKNOWN").upper()
        disease_code = ev.get("disease_code", "UNKNOWN")
        label = ev.get("label_en", disease_code)
        count = ev.get("event_count", 1)

        if status in _CRITICAL_STATUSES:
            severity = Severity.CRITICAL
            causes = [f"notifiable_disease_{disease_code}_is_endemic_in_{country}"]
            actions = [
                "isolate_affected_animals_immediately",
                "notify_veterinary_authority",
                "implement_biosecurity_level_3_protocol",
            ]
        elif status in _WARNING_STATUSES:
            severity = Severity.WARNING
            causes = [f"notifiable_disease_{disease_code}_has_regional_presence_in_{country}"]
            actions = [
                "increase_biosecurity_monitoring",
                "consult_veterinarian_for_disease_screening",
            ]
        elif status in _FREE_STATUSES:
            # Disease is officially FREE in this country — demote to INFO (possible import case)
            severity = Severity.INFO
            causes = [f"notifiable_disease_{disease_code}_is_officially_free_in_{country}_possible_import"]
            actions = [
                "verify_animal_origin_and_import_health_certificates",
                "report_to_national_veterinary_authority",
            ]
        else:
            continue  # UNKNOWN / no data — skip

        findings.append(Finding(
            rule_id=f"disease.{disease_code.lower()}.{status.lower()}",
            kpi="DISEASE",
            severity=severity,
            current_value=float(count),
            target_value=0,
            causes=causes,
            recommended_actions=actions,
            detail={"disease_code": disease_code, "label": label, "prevalence_status": status, "country": country},
        ))

    return findings


RuleRegistry.register(
    Rule("disease.endemic_risk", "disease", "Disease risk adjusted by regional prevalence", _disease_endemic_risk)
)
