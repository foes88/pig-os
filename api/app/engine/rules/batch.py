"""
Batch / all-in-all-out detection (base tier, D4) — 교배 요일집중도로 배치운영 추정.

경고가 아닌 **분류(INFO)**: 특정 요일 교배집중이 높으면 배치(AIAO) 운영으로 판단.
KR BATCH_MGMT(요일집중 50%↑). 표본 부족(<16)이면 빈 결과.
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity
from app.engine.rules._common import resolve


async def _batch_aiao_detect(ctx: RuleContext) -> list[Finding]:
    v = ctx.kpi.get("BATCH_DOW_CONCENTRATION")
    if v is None:
        return []
    # 임계 초과 시 "배치운영" 분류(INFO). warning/critical은 분류 경계로만 사용.
    threshold, _ = resolve(ctx, "batch.aiao_detect", "BATCH_DOW_CONCENTRATION", 50.0, 70.0)
    if v < threshold:
        return []
    return [Finding(
        rule_id="batch.aiao_detect",
        kpi="BATCH_DOW_CONCENTRATION",
        severity=Severity.INFO,
        current_value=round(v, 1),
        target_value=threshold,
        causes=["batch_managed_farm_detected"],
        recommended_actions=["interpret_weekly_kpis_with_batch_cycle_in_mind"],
        detail={"dow_concentration": round(v, 1)},
    )]


RuleRegistry.register(Rule("batch.aiao_detect", "batch", "Batch (AIAO) farm detected", _batch_aiao_detect))
