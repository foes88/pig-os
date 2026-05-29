"""
Base tier rules — active for every farm regardless of subscriptions.

Registered rules (domain → rule_id):
  npd       → npd.overdue
  psy       → psy.below_target, psy.no_data
  farrowing → farrowing.low_rate
  inventory → inventory.zero
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity

# Regional farrowing rate benchmarks and targets (%)
_FR_BENCHMARK = {"KR": 82.0, "US": 78.3, "BR": 80.0, "CN": 78.0, "default": 80.0}
_FR_TARGET    = {"KR": 88.0, "US": 90.2, "BR": 85.0, "CN": 85.0, "default": 85.0}


# ── NPD overdue ───────────────────────────────────────────────────────────────

async def _npd_overdue(ctx: RuleContext) -> list[Finding]:
    npd = ctx.kpi.get("NPD")
    if npd is None:
        return []
    bench  = ctx.benchmarks.get("NPD", {})
    target = bench.get("target")
    avg    = bench.get("avg")
    if target is None or npd <= target:
        return []

    severity = Severity.CRITICAL if (avg and npd > avg) else Severity.WARNING
    causes  = ["high_weaning_to_mating_interval"]
    actions = ["audit_sow_body_condition_score", "improve_transition_feed_intake"]

    if npd > 50:
        causes.append("extended_return_to_estrus")
        actions.append("verify_boar_exposure_protocol")
    if target and npd > target + 7:
        causes.append("repeat_breeding_failures_extending_cycle")
        actions.append("review_heat_detection_frequency")

    return [Finding(
        rule_id="npd.overdue",
        kpi="NPD",
        severity=severity,
        current_value=npd,
        target_value=target,
        causes=causes,
        recommended_actions=actions,
        detail={"benchmark_avg": avg},
    )]


RuleRegistry.register(Rule("npd.overdue", "npd", "NPD above target", _npd_overdue))


# ── PSY below target ──────────────────────────────────────────────────────────

async def _psy_analysis(ctx: RuleContext) -> list[Finding]:
    psy   = ctx.kpi.get("PSY")
    bench = ctx.benchmarks.get("PSY", {})
    target = bench.get("target")
    avg    = bench.get("avg")

    if psy is None:
        return [Finding(
            rule_id="psy.no_data",
            kpi="PSY",
            severity=Severity.INFO,
            current_value=None,
            target_value=target,
            causes=["insufficient_weaning_records"],
            recommended_actions=["complete_weaning_data_entry_for_current_year"],
        )]

    if target is None or psy >= target:
        return []

    severity = Severity.CRITICAL if (avg and psy < avg * 0.9) else Severity.WARNING
    causes  = ["low_litters_per_sow_per_year"]
    actions = ["audit_weaning_to_mating_interval"]

    if psy < 20:
        causes.append("critically_low_litter_size_or_survivability")
        actions.append("review_sow_nutrition_and_genetic_merit")

    # Cross-KPI: high NPD explains low PSY cycle length
    npd = ctx.kpi.get("NPD")
    if npd and npd > 40:
        causes.append("high_non_productive_days_extending_inter_litter_interval")
        actions.append("reduce_npd_to_shorten_cycle_and_improve_psy")

    return [Finding(
        rule_id="psy.below_target",
        kpi="PSY",
        severity=severity,
        current_value=psy,
        target_value=target,
        causes=causes,
        recommended_actions=actions,
        detail={"benchmark_avg": avg},
    )]


RuleRegistry.register(Rule("psy.below_target", "psy", "PSY below target", _psy_analysis))


# ── Farrowing rate low ────────────────────────────────────────────────────────

async def _farrowing_rate_low(ctx: RuleContext) -> list[Finding]:
    fr = ctx.kpi.get("FARROWING_RATE")
    if fr is None:
        return []

    country = ctx.country
    avg    = _FR_BENCHMARK.get(country, _FR_BENCHMARK["default"])
    target = _FR_TARGET.get(country, _FR_TARGET["default"])

    if fr >= target:
        return []

    severity = Severity.CRITICAL if fr < avg * 0.9 else Severity.WARNING
    causes  = ["repeat_breeding_failures"]
    actions = ["review_heat_detection_accuracy", "check_boar_libido_and_semen_quality"]

    if fr < 75:
        causes.append("possible_disease_causing_early_embryo_loss_or_abortion")
        actions.append("consult_veterinarian_for_reproductive_disease_screening")

    return [Finding(
        rule_id="farrowing.low_rate",
        kpi="FARROWING_RATE",
        severity=severity,
        current_value=fr,
        target_value=target,
        causes=causes,
        recommended_actions=actions,
        detail={"benchmark_avg": avg, "country": country},
    )]


RuleRegistry.register(Rule("farrowing.low_rate", "farrowing", "Low farrowing rate", _farrowing_rate_low))


# ── Inventory zero ────────────────────────────────────────────────────────────

async def _inventory_zero(ctx: RuleContext) -> list[Finding]:
    active = sum(
        ctx.sow_counts.get(s, 0)
        for s in ("ACTIVE", "GESTATING", "LACTATING", "WEANED", "DRY")
    )
    if active > 0:
        return []
    return [Finding(
        rule_id="inventory.zero",
        kpi="SOW_COUNT",
        severity=Severity.CRITICAL,
        current_value=0,
        target_value=None,
        causes=["no_active_sows_registered_in_system"],
        recommended_actions=["complete_sow_inventory_entry_via_onboarding"],
    )]


RuleRegistry.register(Rule("inventory.zero", "inventory", "No active sows", _inventory_zero))
