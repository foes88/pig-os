"""
Sow herd structure rules (base tier) — 모돈군 구조/회전 탐지.

herd 집계(build_herd_kpis, 롤링 365일)가 ctx.kpi에 넣은 실데이터를 읽는다. 값 없으면 빈 결과.
임계는 rule_configs(운영자) → benchmarks(국가) → 코드 기본값 순.

Registered rules:
  culling  → culling.rate_high
  sow_mort → sow_mortality.high
  parity   → parity.high_ratio
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity
from app.engine.rules._common import resolve, sev_above


# ── 모돈 도태율(연간 근사) ───────────────────────────────────────────────────────
async def _culling_rate_high(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("CULLING_RATE")
    if v is None:
        return []
    w, c = resolve(ctx, "culling.rate_high", "CULLING_RATE", 45.0, 55.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["high_sow_culling_rate"]
    actions = ["review_culling_policy_and_reasons", "review_gilt_replacement_plan"]
    if sev == Severity.CRITICAL:
        causes.append("possible_involuntary_culling_from_reproductive_failure")
        actions.append("audit_reproductive_failure_and_lameness")
    return [Finding(
        rule_id="culling.rate_high", kpi="CULLING_RATE", severity=sev,
        current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions,
    )]


RuleRegistry.register(Rule("culling.rate_high", "culling", "Sow culling rate high", _culling_rate_high))


# ── 모돈 폐사율(연간 근사) ───────────────────────────────────────────────────────
async def _sow_mortality_high(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("SOW_MORTALITY")
    if v is None:
        return []
    w, c = resolve(ctx, "sow_mortality.high", "SOW_MORTALITY", 8.0, 12.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["high_sow_mortality"]
    actions = ["audit_lameness_and_prolapse", "review_heat_stress_and_body_condition"]
    if sev == Severity.CRITICAL:
        causes.append("possible_disease_or_management_failure")
        actions.append("consult_veterinarian_for_sow_mortality")
    return [Finding(
        rule_id="sow_mortality.high", kpi="SOW_MORTALITY", severity=sev,
        current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions,
    )]


RuleRegistry.register(Rule("sow_mortality.high", "sow_mort", "Sow mortality high", _sow_mortality_high))


# ── 노산돈 비율(parity ≥ 7) ──────────────────────────────────────────────────────
async def _parity_high_ratio(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("HIGH_PARITY_RATIO")
    if v is None:
        return []
    w, c = resolve(ctx, "parity.high_ratio", "HIGH_PARITY_RATIO", 20.0, 30.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["aging_sow_herd_high_parity_share"]
    actions = ["review_parity_structure_and_replacement", "plan_gilt_introduction_cadence"]
    return [Finding(
        rule_id="parity.high_ratio", kpi="HIGH_PARITY_RATIO", severity=sev,
        current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions,
    )]


RuleRegistry.register(Rule("parity.high_ratio", "parity", "Aging herd (high parity)", _parity_high_ratio))


# ── 모돈 갱신율 비정상(과다/과소 양방향) ─────────────────────────────────────────
async def _replacement_rate_abnormal(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("REPLACEMENT_RATE")
    if v is None:
        return []
    hi_w, hi_c = resolve(ctx, "replacement.rate_abnormal", "REPLACEMENT_RATE", 50.0, 60.0)
    lo = 30.0  # 과소 갱신 경고선(KR SOW_REPLACEMENT low band)
    if v > hi_w:
        sev = Severity.CRITICAL if v > hi_c else Severity.WARNING
        causes = ["excessive_sow_replacement"]
        actions = ["review_involuntary_culling_drivers", "review_gilt_intake_plan"]
        return [Finding(rule_id="replacement.rate_abnormal", kpi="REPLACEMENT_RATE", severity=sev,
                        current_value=round(v, 1), target_value=hi_w, causes=causes, recommended_actions=actions)]
    if v < lo:
        causes = ["insufficient_sow_replacement"]
        actions = ["plan_gilt_introduction_cadence", "review_parity_structure_and_replacement"]
        return [Finding(rule_id="replacement.rate_abnormal", kpi="REPLACEMENT_RATE", severity=Severity.WARNING,
                        current_value=round(v, 1), target_value=lo, causes=causes, recommended_actions=actions)]
    return []


RuleRegistry.register(Rule("replacement.rate_abnormal", "replacement", "Sow replacement rate abnormal", _replacement_rate_abnormal))


# ── 2산차 슬럼프(P1 대비 P2 실산 감소) ───────────────────────────────────────────
async def _second_litter_slump(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("SECOND_LITTER_DROP")
    if v is None:
        return []
    w, c = resolve(ctx, "parity.second_litter_slump", "SECOND_LITTER_DROP", 1.5, 2.5)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["second_litter_slump"]
    actions = ["improve_p1_lactation_feed_and_bcs", "shorten_p1_wean_to_service_interval"]
    return [Finding(rule_id="parity.second_litter_slump", kpi="SECOND_LITTER_DROP", severity=sev,
                    current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions)]


RuleRegistry.register(Rule("parity.second_litter_slump", "parity", "Second-litter slump", _second_litter_slump))


# ── 임신사고 P1 편중(감염 의심) ──────────────────────────────────────────────────
async def _accident_parity_skew(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("ACCIDENT_P1_RATIO")
    if v is None:
        return []
    w, c = resolve(ctx, "accident.parity_skew", "ACCIDENT_P1_RATIO", 40.0, 55.0)
    sev = sev_above(v, w, c)
    if sev is None:
        return []
    causes = ["pregnancy_accidents_concentrated_in_p1"]
    actions = ["review_gilt_acclimation_and_vaccination", "audit_gilt_breeding_management"]
    if sev == Severity.CRITICAL:
        causes.append("possible_reproductive_disease_in_gilts")
        actions.append("screen_for_abortive_pathogens")
    return [Finding(rule_id="accident.parity_skew", kpi="ACCIDENT_P1_RATIO", severity=sev,
                    current_value=round(v, 1), target_value=w, causes=causes, recommended_actions=actions)]


RuleRegistry.register(Rule("accident.parity_skew", "accident", "Accident parity skew (P1)", _accident_parity_skew))
