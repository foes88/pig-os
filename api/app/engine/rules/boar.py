"""
Boar performance rule (base tier) — 웅돈별 분만율 저조 탐지(멀티개체).

ctx.extra["boar_stats"] = [{boar_id, ear_tag, matings, fr}] (build_boar_stats, 표본 ≥10).
저조 웅돈마다 Finding 1건. 임계는 rule_configs → benchmarks(BOAR_FARROW_RATE) → 코드 기본값.
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry
from app.engine.rules._common import resolve, sev_below


async def _boar_farrow_rate_low(ctx: RuleContext) -> list[Finding]:
    boars = (ctx.extra.get("boar_stats", []) if ctx.extra else []) or []
    if not boars:
        return []
    w, c = resolve(ctx, "boar.farrow_rate_low", "BOAR_FARROW_RATE", 65.0, 55.0)
    out: list[Finding] = []
    for b in boars:
        fr = b.get("fr")
        if fr is None:
            continue
        sev = sev_below(fr, w, c)
        if sev is None:
            continue
        out.append(Finding(
            rule_id="boar.farrow_rate_low",
            kpi="BOAR_FARROW_RATE",
            severity=sev,
            current_value=fr,
            target_value=w,
            causes=["low_boar_farrowing_rate"],
            recommended_actions=["check_semen_quality_and_storage", "review_boar_usage_and_libido"],
            detail={"boar_id": b.get("boar_id"), "ear_tag": b.get("ear_tag"), "matings": b.get("matings")},
        ))
    return out


RuleRegistry.register(Rule("boar.farrow_rate_low", "boar", "Boar farrowing rate low", _boar_farrow_rate_low))
