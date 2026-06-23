"""
Grow-finish rules (base tier) — 비육 성적 탐지 (FCR / ADG / 폐사율).

herd 집계(build_herd_kpis)가 ctx.kpi에 넣은 비육 KPI를 읽는다. 값 없으면 빈 결과(날조 0).
임계는 rule_configs(운영자) → benchmarks(국가) → 코드 기본값 순.

Registered rules:
  fcr        → fcr.high
  adg        → adg.low
  finish_mortality → finish_mortality.high
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity
from app.engine.rules._common import resolve, sev_above, sev_below


# ── 사료요구율(FCR) ─────────────────────────────────────────────────────────────
async def _fcr_high(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("FCR")
    if v is None:
        return []
    w, c = resolve(ctx, "fcr.high", "FCR", 3.0, 3.3)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["high_feed_conversion_ratio"]
    actions = ["audit_feed_quality_and_wastage", "review_finishing_diet_and_stocking_density"]
    if sev == Severity.CRITICAL:
        causes.append("possible_subclinical_disease_depressing_efficiency")
        actions.append("investigate_finishing_health_and_environment")
    return [Finding(
        rule_id="fcr.high", kpi="FCR", severity=sev,
        current_value=round(v, 3), target_value=w, causes=causes, recommended_actions=actions,
    )]


RuleRegistry.register(Rule("fcr.high", "fcr", "Feed conversion ratio high", _fcr_high))


# ── 일당증체(ADG) ───────────────────────────────────────────────────────────────
async def _adg_low(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("ADG")
    if v is None:
        return []
    w, c = resolve(ctx, "adg.low", "ADG", 650.0, 550.0)
    sev = sev_below(v, w, c)
    if sev is None:
        return []
    causes = ["low_average_daily_gain"]
    actions = ["review_finishing_diet_and_stocking_density", "check_water_and_feeder_access"]
    if sev == Severity.CRITICAL:
        causes.append("possible_subclinical_disease_depressing_growth")
        actions.append("investigate_finishing_health_and_environment")
    return [Finding(
        rule_id="adg.low", kpi="ADG", severity=sev,
        current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions,
    )]


RuleRegistry.register(Rule("adg.low", "adg", "Average daily gain low", _adg_low))


# ── 비육 폐사율 ─────────────────────────────────────────────────────────────────
async def _finish_mortality_high(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("FINISH_MORTALITY")
    if v is None:
        return []
    w, c = resolve(ctx, "finish_mortality.high", "FINISH_MORTALITY", 5.0, 8.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["high_finishing_mortality"]
    actions = ["investigate_finishing_health_and_environment", "review_finishing_diet_and_stocking_density"]
    if sev == Severity.CRITICAL:
        causes.append("possible_disease_outbreak_in_finishing")
        actions.append("consult_veterinarian_for_finishing_mortality")
    return [Finding(
        rule_id="finish_mortality.high", kpi="FINISH_MORTALITY", severity=sev,
        current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions,
    )]


RuleRegistry.register(Rule("finish_mortality.high", "mortality", "Finishing mortality high", _finish_mortality_high))
