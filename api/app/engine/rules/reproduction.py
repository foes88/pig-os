"""
Reproduction rules (base tier) — WSI, RTS rate, and pre-weaning mortality.

These use global clinical thresholds (not country benchmarks) by default, but a
``ctx.benchmarks[KPI]`` entry with ``warning``/``critical`` keys overrides them so
the values can still be tuned per farm/region via default_metric_values later.

Registered rules:
  wsi   → wsi.overdue
  rts   → rts.rate_high
  pwmr  → pwmr.high
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity

# Global default thresholds (overridable via ctx.benchmarks).
WSI_WARNING, WSI_CRITICAL = 10.0, 14.0       # days
RTS_WARNING, RTS_CRITICAL = 15.0, 25.0       # %
PWMR_WARNING, PWMR_CRITICAL = 15.0, 20.0     # %


def _severity_above(value: float, warning: float, critical: float) -> Severity | None:
    """Alert when value rises above a threshold (higher is worse)."""
    if value > critical:
        return Severity.CRITICAL
    if value > warning:
        return Severity.WARNING
    return None


def _thresholds(ctx: RuleContext, kpi: str, default_w: float, default_c: float) -> tuple[float, float]:
    bench = ctx.benchmarks.get(kpi, {})
    warning = bench.get("warning")
    critical = bench.get("critical")
    return (
        warning if warning is not None else default_w,
        critical if critical is not None else default_c,
    )


# ── WSI overdue ───────────────────────────────────────────────────────────────

async def _wsi_overdue(ctx: RuleContext) -> list[Finding]:
    wsi = ctx.kpi.get("WSI")
    if wsi is None:
        return []
    warning, critical = _thresholds(ctx, "WSI", WSI_WARNING, WSI_CRITICAL)
    severity = _severity_above(wsi, warning, critical)
    if severity is None:
        return []

    causes = ["prolonged_weaning_to_service_interval"]
    actions = ["review_lactation_feed_intake", "improve_post_weaning_heat_detection"]
    if severity == Severity.CRITICAL:
        causes.append("possible_anestrus_or_excessive_body_condition_loss")
        actions.append("assess_body_condition_and_consider_hormonal_intervention")

    return [Finding(
        rule_id="wsi.overdue",
        kpi="WSI",
        severity=severity,
        current_value=wsi,
        target_value=warning,
        causes=causes,
        recommended_actions=actions,
    )]


RuleRegistry.register(Rule("wsi.overdue", "wsi", "WSI above target", _wsi_overdue))


# ── RTS rate high ─────────────────────────────────────────────────────────────

async def _rts_rate_high(ctx: RuleContext) -> list[Finding]:
    rts = ctx.kpi.get("RTS_RATE")
    if rts is None:
        return []
    warning, critical = _thresholds(ctx, "RTS_RATE", RTS_WARNING, RTS_CRITICAL)
    severity = _severity_above(rts, warning, critical)
    if severity is None:
        return []

    causes = ["elevated_return_to_service_rate"]
    actions = ["audit_heat_detection_and_insemination_timing", "check_semen_handling_and_boar_fertility"]
    if severity == Severity.CRITICAL:
        causes.append("possible_reproductive_disease_or_seasonal_infertility")
        actions.append("consult_veterinarian_for_reproductive_disease_screening")

    return [Finding(
        rule_id="rts.rate_high",
        kpi="RTS_RATE",
        severity=severity,
        current_value=rts,
        target_value=warning,
        causes=causes,
        recommended_actions=actions,
    )]


RuleRegistry.register(Rule("rts.rate_high", "rts", "RTS rate high", _rts_rate_high))


# ── Pre-weaning mortality high ────────────────────────────────────────────────

def _compute_pwmr(ctx: RuleContext, method: str) -> float | None:
    """Resolve PWMR from ctx.kpi['PWMR'] or compute from ctx.extra components."""
    if ctx.kpi.get("PWMR") is not None:
        return ctx.kpi["PWMR"]
    e = ctx.extra
    if method == "A" and e.get("deaths") is not None and e.get("weaned") is not None:
        denom = e["weaned"] + e["deaths"]
        return (e["deaths"] / denom * 100) if denom else None
    if method == "B" and e.get("avg_tb") and e.get("avg_weaned") is not None:
        return (e["avg_tb"] - e["avg_weaned"]) / e["avg_tb"] * 100
    return None


async def _pwmr_high(ctx: RuleContext) -> list[Finding]:
    method = ctx.extra.get("pwmr_method", "A")
    pwmr = _compute_pwmr(ctx, method)
    if pwmr is None:
        return []
    warning, critical = _thresholds(ctx, "PWMR", PWMR_WARNING, PWMR_CRITICAL)
    severity = _severity_above(pwmr, warning, critical)
    if severity is None:
        return []

    causes = ["high_pre_weaning_piglet_mortality"]
    actions = ["review_crushing_prevention_and_creep_management", "improve_colostrum_intake_and_cross_fostering"]
    if severity == Severity.CRITICAL:
        causes.append("possible_lactation_failure_or_disease_in_litters")
        actions.append("investigate_sow_milk_yield_and_piglet_scour_pathogens")

    return [Finding(
        rule_id="pwmr.high",
        kpi="PWMR",
        severity=severity,
        current_value=round(pwmr, 1),
        target_value=warning,
        causes=causes,
        recommended_actions=actions,
        detail={"method": method},
    )]


RuleRegistry.register(Rule("pwmr.high", "pwmr", "Pre-weaning mortality high", _pwmr_high))
