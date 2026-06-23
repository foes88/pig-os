"""
Composite rules (base tier, domain='composite') — 다른 룰의 findings를 롤업.

엔진이 2-pass로 실행: 일반 룰 먼저 → ctx.extra["_prior_findings"]에 결과 주입 → composite 실행.
위조 0: 실제 발생한 finding의 severity만 집계.

Registered:
  farm.health_class  — 농가 종합등급 RED/YELLOW/GREEN
  farm.weakest_kpi   — 가장 시급한 KPI(최고 severity + 최대 gap) 선정
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity

_RANK = {Severity.OK: 0, Severity.INFO: 1, Severity.WARNING: 2, Severity.CRITICAL: 3}


def _prior(ctx: RuleContext) -> list[Finding]:
    return (ctx.extra.get("_prior_findings", []) if ctx.extra else []) or []


# ── 농가 종합등급 (RED/YELLOW/GREEN) ─────────────────────────────────────────────
async def _farm_health_class(ctx: RuleContext) -> list[Finding]:
    prior = _prior(ctx)
    crit = sum(1 for f in prior if f.severity == Severity.CRITICAL)
    warn = sum(1 for f in prior if f.severity == Severity.WARNING)
    # RED: critical 1건+ 또는 warning 3건+ / YELLOW: warning 1건+ / GREEN: 그 외
    if crit >= 1 or warn >= 3:
        grade, sev = "RED", Severity.CRITICAL
    elif warn >= 1:
        grade, sev = "YELLOW", Severity.WARNING
    else:
        grade, sev = "GREEN", Severity.INFO
    return [Finding(
        rule_id="farm.health_class", kpi="FARM_HEALTH_CLASS", severity=sev,
        current_value=None, target_value=None,
        causes=[f"farm_grade_{grade.lower()}"],
        recommended_actions=[],
        grade=grade,
        detail={"grade": grade, "critical": crit, "warning": warn},
    )]


RuleRegistry.register(Rule("farm.health_class", "composite", "Farm health class (RYG)", _farm_health_class))


# ── 가장 시급한 KPI ──────────────────────────────────────────────────────────────
async def _farm_weakest_kpi(ctx: RuleContext) -> list[Finding]:
    prior = [f for f in _prior(ctx) if f.severity in (Severity.WARNING, Severity.CRITICAL)]
    if not prior:
        return []
    # 최고 severity → 최대 normalized_gap 순으로 가장 시급한 것 선정
    worst = max(prior, key=lambda f: (_RANK[f.severity], f.detail.get("normalized_gap") or 0))
    return [Finding(
        rule_id="farm.weakest_kpi", kpi="WEAKEST_KPI", severity=Severity.INFO,
        current_value=worst.current_value, target_value=worst.target_value,
        causes=["weakest_kpi_priority"],
        recommended_actions=worst.recommended_actions[:2],
        detail={"weakest_rule": worst.rule_id, "weakest_kpi": worst.kpi,
                "severity": worst.severity.value},
    )]


RuleRegistry.register(Rule("farm.weakest_kpi", "composite", "Weakest KPI (priority)", _farm_weakest_kpi))
