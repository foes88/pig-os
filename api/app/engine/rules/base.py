"""
Base tier rules — active for every farm regardless of subscriptions.

Thresholds (warning/critical) and benchmarks are loaded from default_metric_values
via effective_metric_values() DB function. No hardcoded per-country values here.

Registered rules:
  npd       → npd.overdue
  psy       → psy.below_target, psy.no_data
  farrowing → farrowing.low_rate
  inventory → inventory.zero
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity


# ── helpers ───────────────────────────────────────────────────────────────────

def _severity_from_bench(value: float, bench: dict, direction: str) -> Severity | None:
    """
    Return the appropriate Severity given a value and benchmark thresholds.
    Returns None when no alert should fire (value within acceptable range).
    direction='below': alert when value falls below threshold (PSY, FR)
    direction='above': alert when value rises above threshold (NPD)
    """
    warning  = bench.get("warning")
    critical = bench.get("critical")

    if direction == "above":
        if warning is None or value <= warning:
            return None
        if critical is not None and value > critical:
            return Severity.CRITICAL
        return Severity.WARNING
    else:  # below
        if warning is None or value >= warning:
            return None
        if critical is not None and value < critical:
            return Severity.CRITICAL
        return Severity.WARNING


# ── NPD overdue ───────────────────────────────────────────────────────────────

async def _npd_overdue(ctx: RuleContext) -> list[Finding]:
    npd = ctx.kpi.get("NPD")
    if npd is None:
        return []

    bench = ctx.benchmarks.get("NPD", {})
    direction = bench.get("direction", "above")
    severity = _severity_from_bench(npd, bench, direction)
    if severity is None:
        return []

    warning = bench.get("warning") or 35.0
    causes  = ["high_weaning_to_mating_interval"]
    actions = ["audit_sow_body_condition_score", "improve_transition_feed_intake"]

    # Dynamic additions based on severity level
    if severity == Severity.CRITICAL:
        causes.append("extended_return_to_estrus")
        actions.append("verify_boar_exposure_protocol")
    if bench.get("warning") and npd > warning + 7:
        causes.append("repeat_breeding_failures_extending_cycle")
        actions.append("review_heat_detection_frequency")

    return [Finding(
        rule_id="npd.overdue",
        kpi="NPD",
        severity=severity,
        current_value=npd,
        target_value=bench.get("warning"),
        causes=causes,
        recommended_actions=actions,
        detail={"benchmark_avg": bench.get("avg")},
    )]


RuleRegistry.register(Rule("npd.overdue", "npd", "NPD above target", _npd_overdue))


# ── PSY below target ──────────────────────────────────────────────────────────

async def _psy_analysis(ctx: RuleContext) -> list[Finding]:
    psy   = ctx.kpi.get("PSY")
    bench = ctx.benchmarks.get("PSY", {})

    if psy is None:
        return [Finding(
            rule_id="psy.no_data",
            kpi="PSY",
            severity=Severity.INFO,
            current_value=None,
            target_value=bench.get("warning"),
            causes=["insufficient_weaning_records"],
            recommended_actions=["complete_weaning_data_entry_for_current_year"],
        )]

    direction = bench.get("direction", "below")
    severity = _severity_from_bench(psy, bench, direction)
    if severity is None:
        return []

    causes  = ["low_litters_per_sow_per_year"]
    actions = ["audit_weaning_to_mating_interval"]

    if severity == Severity.CRITICAL:
        causes.append("critically_low_litter_size_or_survivability")
        actions.append("review_sow_nutrition_and_genetic_merit")

    # Cross-KPI: high NPD explains low PSY
    npd = ctx.kpi.get("NPD")
    npd_bench = ctx.benchmarks.get("NPD", {})
    npd_warning = npd_bench.get("warning") or 35.0
    if npd and npd > npd_warning:
        causes.append("high_non_productive_days_extending_inter_litter_interval")
        actions.append("reduce_npd_to_shorten_cycle_and_improve_psy")

    return [Finding(
        rule_id="psy.below_target",
        kpi="PSY",
        severity=severity,
        current_value=psy,
        target_value=bench.get("warning"),
        causes=causes,
        recommended_actions=actions,
        detail={"benchmark_avg": bench.get("avg")},
    )]


RuleRegistry.register(Rule("psy.below_target", "psy", "PSY below target", _psy_analysis))


# ── Farrowing rate low ────────────────────────────────────────────────────────

async def _farrowing_rate_low(ctx: RuleContext) -> list[Finding]:
    fr = ctx.kpi.get("FARROWING_RATE")
    if fr is None:
        return []

    bench = ctx.benchmarks.get("FARROWING_RATE", {})
    direction = bench.get("direction", "below")
    severity = _severity_from_bench(fr, bench, direction)
    if severity is None:
        return []

    causes  = ["repeat_breeding_failures"]
    actions = ["review_heat_detection_accuracy", "check_boar_libido_and_semen_quality"]

    if severity == Severity.CRITICAL:
        causes.append("possible_disease_causing_early_embryo_loss_or_abortion")
        actions.append("consult_veterinarian_for_reproductive_disease_screening")

    return [Finding(
        rule_id="farrowing.low_rate",
        kpi="FARROWING_RATE",
        severity=severity,
        current_value=fr,
        target_value=bench.get("warning"),
        causes=causes,
        recommended_actions=actions,
        detail={"benchmark_avg": bench.get("avg")},
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
