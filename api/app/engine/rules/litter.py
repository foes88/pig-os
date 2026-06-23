"""
Litter / piglet quality rules (base tier) — 자돈 복 성적 탐지.

모두 herd 집계(build_herd_kpis)가 ctx.kpi에 넣은 실데이터를 읽는다. 값 없으면 빈 결과(날조 0).
임계는 rule_configs(운영자) → benchmarks(국가) → 코드 기본값 순. (_common.resolve)

Registered rules:
  stillborn   → stillborn.rate_high
  mummified   → mummified.rate_high
  born_alive  → born_alive.low
  weaned      → weaned.low
  birth_weight→ birth_weight.low
  wean_weight → weaning_weight.low
  lactation   → lactation.too_short, lactation.too_long
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity
from app.engine.rules._common import resolve, sev_above, sev_below


def _finding(rule_id, kpi, sev, value, target, causes, actions) -> Finding:
    return Finding(
        rule_id=rule_id, kpi=kpi, severity=sev,
        current_value=round(value, 2), target_value=target,
        causes=causes, recommended_actions=actions,
    )


# ── 사산율 ──────────────────────────────────────────────────────────────────────
async def _stillborn_high(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("STILLBORN_RATE")
    if v is None:
        return []
    w, c = resolve(ctx, "stillborn.rate_high", "STILLBORN_RATE", 8.0, 12.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["high_stillbirth_rate"]
    actions = ["review_farrowing_supervision", "check_sow_parity_and_gestation_length"]
    if sev == Severity.CRITICAL:
        causes.append("possible_prolonged_farrowing_or_late_gestation_disease")
        actions.append("consult_veterinarian_for_perinatal_loss")
    return [_finding("stillborn.rate_high", "STILLBORN_RATE", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("stillborn.rate_high", "stillborn", "Stillborn rate high", _stillborn_high))


# ── 미라변성태 ──────────────────────────────────────────────────────────────────
async def _mummified_high(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("MUMMIFIED_RATE")
    if v is None:
        return []
    w, c = resolve(ctx, "mummified.rate_high", "MUMMIFIED_RATE", 2.0, 4.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["high_mummified_rate"]
    actions = ["review_gestation_biosecurity_and_vaccination"]
    if sev == Severity.CRITICAL:
        causes.append("possible_in_utero_viral_infection")
        actions.append("screen_for_abortive_pathogens")
    return [_finding("mummified.rate_high", "MUMMIFIED_RATE", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("mummified.rate_high", "mummified", "Mummified rate high", _mummified_high))


# ── 복당 실산자 ──────────────────────────────────────────────────────────────────
async def _born_alive_low(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("AVG_BORN_ALIVE")
    if v is None:
        return []
    w, c = resolve(ctx, "born_alive.low", "AVG_BORN_ALIVE", 11.0, 10.0)
    sev = sev_below(v, w, c)
    if sev is None:
        return []
    causes = ["low_born_alive_per_litter"]
    actions = ["review_gilt_development_and_sow_nutrition", "audit_insemination_timing"]
    if sev == Severity.CRITICAL:
        causes.append("possible_high_embryonic_loss")
    return [_finding("born_alive.low", "AVG_BORN_ALIVE", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("born_alive.low", "born_alive", "Born-alive per litter low", _born_alive_low))


# ── 복당 이유두수 ────────────────────────────────────────────────────────────────
async def _weaned_low(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("AVG_WEANED")
    if v is None:
        return []
    w, c = resolve(ctx, "weaned.low", "AVG_WEANED", 10.0, 9.0)
    sev = sev_below(v, w, c)
    if sev is None:
        return []
    causes = ["low_piglets_weaned_per_litter"]
    actions = ["improve_colostrum_and_cross_fostering", "improve_lactation_feed_and_creep"]
    if sev == Severity.CRITICAL:
        causes.append("high_pre_weaning_piglet_mortality")
    return [_finding("weaned.low", "AVG_WEANED", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("weaned.low", "weaned", "Weaned per litter low", _weaned_low))


# ── 평균 출생체중 ────────────────────────────────────────────────────────────────
async def _birth_weight_low(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("AVG_BIRTH_WEIGHT")
    if v is None:
        return []
    w, c = resolve(ctx, "birth_weight.low", "AVG_BIRTH_WEIGHT", 1.3, 1.1)
    sev = sev_below(v, w, c)
    if sev is None:
        return []
    causes = ["low_average_birth_weight"]
    actions = ["review_gilt_development_and_sow_nutrition"]
    if sev == Severity.CRITICAL:
        causes.append("possible_large_litter_or_poor_late_gestation_feeding")
    return [_finding("birth_weight.low", "AVG_BIRTH_WEIGHT", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("birth_weight.low", "birth_weight", "Avg birth weight low", _birth_weight_low))


# ── 평균 이유체중 ────────────────────────────────────────────────────────────────
async def _weaning_weight_low(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("AVG_WEANING_WEIGHT")
    if v is None:
        return []
    w, c = resolve(ctx, "weaning_weight.low", "AVG_WEANING_WEIGHT", 5.5, 5.0)
    sev = sev_below(v, w, c)
    if sev is None:
        return []
    causes = ["low_weaning_weight"]
    actions = ["improve_lactation_feed_and_creep", "review_sow_milk_yield"]
    return [_finding("weaning_weight.low", "AVG_WEANING_WEIGHT", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("weaning_weight.low", "wean_weight", "Avg weaning weight low", _weaning_weight_low))


# ── 포유일령(너무 짧음 / 너무 김) ────────────────────────────────────────────────
async def _lactation_short(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("AVG_WEANING_AGE")
    if v is None:
        return []
    w, c = resolve(ctx, "lactation.too_short", "AVG_WEANING_AGE", 19.0, 16.0)
    sev = sev_below(v, w, c)
    if sev is None:
        return []
    causes = ["lactation_length_too_short"]
    actions = ["adjust_weaning_age_to_target", "review_early_weaning_protocol"]
    return [_finding("lactation.too_short", "AVG_WEANING_AGE", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("lactation.too_short", "lactation", "Lactation too short", _lactation_short))


async def _lactation_long(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("AVG_WEANING_AGE")
    if v is None:
        return []
    w, c = resolve(ctx, "lactation.too_long", "AVG_WEANING_AGE", 28.0, 35.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["lactation_length_too_long"]
    actions = ["adjust_weaning_age_to_target", "review_sow_throughput_and_npd"]
    return [_finding("lactation.too_long", "AVG_WEANING_AGE", sev, v, w, causes, actions)]


RuleRegistry.register(Rule("lactation.too_long", "lactation", "Lactation too long", _lactation_long))
