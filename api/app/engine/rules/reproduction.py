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


def _cfg_default(ctx: RuleContext, rule_id: str, default_w: float, default_c: float) -> tuple[float, float]:
    """운영자 규칙 설정(ctx.extra["rule_configs"])의 임계값을 코드 기본값 대신 사용. 없으면 기본값."""
    cfg = (ctx.extra.get("rule_configs", {}) if ctx.extra else {}).get(rule_id) or {}
    w, c = cfg.get("warning"), cfg.get("critical")
    return (w if w is not None else default_w, c if c is not None else default_c)


# ── WSI overdue ───────────────────────────────────────────────────────────────

async def _wsi_overdue(ctx: RuleContext) -> list[Finding]:
    wsi = ctx.kpi.get("WSI")
    if wsi is None:
        return []
    warning, critical = _thresholds(ctx, "WSI", *_cfg_default(ctx, "wsi.overdue", WSI_WARNING, WSI_CRITICAL))
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
    warning, critical = _thresholds(ctx, "RTS_RATE", *_cfg_default(ctx, "rts.rate_high", RTS_WARNING, RTS_CRITICAL))
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
    warning, critical = _thresholds(ctx, "PWMR", *_cfg_default(ctx, "pwmr.high", PWMR_WARNING, PWMR_CRITICAL))
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


# ── Abortion rate high ────────────────────────────────────────────────────────
ABORTION_WARNING, ABORTION_CRITICAL = 3.0, 5.0       # % of services

async def _abortion_rate_high(ctx: RuleContext) -> list[Finding]:
    rate = ctx.kpi.get("ABORTION_RATE")
    if rate is None:
        return []
    warning, critical = _thresholds(
        ctx, "ABORTION_RATE", *_cfg_default(ctx, "abortion.rate_high", ABORTION_WARNING, ABORTION_CRITICAL)
    )
    severity = _severity_above(rate, warning, critical)
    if severity is None:
        return []

    causes = ["elevated_abortion_rate"]
    actions = ["review_gestation_biosecurity_and_vaccination", "audit_feed_quality_and_mycotoxins"]
    if severity == Severity.CRITICAL:
        causes.append("possible_abortive_disease")
        actions.append("screen_for_abortive_pathogens")

    return [Finding(
        rule_id="abortion.rate_high",
        kpi="ABORTION_RATE",
        severity=severity,
        current_value=rate,
        target_value=warning,
        causes=causes,
        recommended_actions=actions,
    )]


RuleRegistry.register(Rule("abortion.rate_high", "abortion", "Abortion rate high", _abortion_rate_high))


# ── Seasonal summer infertility ───────────────────────────────────────────────
SID_WARNING, SID_CRITICAL = 6.0, 10.0       # 분만율 하락 pp (여름 cohort)

async def _summer_infertility(ctx: RuleContext) -> list[Finding]:
    drop = ctx.kpi.get("SUMMER_FARROW_DROP")
    if drop is None:
        return []
    warning, critical = _thresholds(
        ctx, "SUMMER_FARROW_DROP", *_cfg_default(ctx, "seasonal.summer_infertility", SID_WARNING, SID_CRITICAL)
    )
    severity = _severity_above(drop, warning, critical)
    if severity is None:
        return []

    causes = ["seasonal_summer_infertility"]
    actions = ["improve_summer_cooling_and_ventilation", "review_summer_feed_intake_and_boar_exposure"]
    if severity == Severity.CRITICAL:
        causes.append("severe_heat_stress_depressing_conception")
        actions.append("audit_heat_abatement_and_insemination_timing")

    return [Finding(
        rule_id="seasonal.summer_infertility",
        kpi="SUMMER_FARROW_DROP",
        severity=severity,
        current_value=drop,
        target_value=warning,
        causes=causes,
        recommended_actions=actions,
    )]


RuleRegistry.register(Rule("seasonal.summer_infertility", "seasonal", "Summer infertility (SID)", _summer_infertility))
