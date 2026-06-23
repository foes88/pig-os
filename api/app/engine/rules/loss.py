"""
Loss calculators (base tier) — 경제적 손실 금액(₩) Finding.

원칙: **위조 0.** 실 폐사/사고 두수 × 출하두당가(있을 때만). 가격 없으면 미발화.
가격이 글로벌/프록시면 detail.loss.demo=True로 명시. (insight_service LOSS_CALC와 동일 규약)

ctx.extra["loss_inputs"] = {price, currency, demo, pw_deaths, accident_count}
ctx.kpi["WEANED_COUNT"] = 복당 평균 이유두수(임신사고 손실의 복당 환산용)

활성: loss.preweaning_mortality, loss.pregnancy_accident (실 count×단가)
미발화(별도 seed 필요): loss.npd(NPD 일당 기회비용), loss.sow_culling(산차별 잔존가) —
  rule_config 파라미터(cost_per_day / residual_value) 주입 전까지 빈 결과(위조 방지).
"""
from app.engine.rule_engine import Finding, Rule, RuleContext, RuleRegistry, Severity


def _loss_detail(lost: float, li: dict) -> dict:
    return {"amount": round(lost * li["price"]), "currency": li["currency"],
            "lost_pigs": round(lost, 1), "basis": "lost_market_pigs", "demo": li.get("demo", True)}


def _inputs(ctx: RuleContext) -> dict | None:
    li = (ctx.extra.get("loss_inputs") if ctx.extra else None) or None
    if not li or li.get("price") in (None, 0):
        return None
    return li


# ── 포유자돈 폐사 손실 ───────────────────────────────────────────────────────────
async def _loss_preweaning(ctx: RuleContext) -> list[Finding]:
    li = _inputs(ctx)
    if not li:
        return []
    lost = li.get("pw_deaths") or 0.0
    if lost <= 0:
        return []
    return [Finding(
        rule_id="loss.preweaning_mortality", kpi="PREWEAN_LOSS", severity=Severity.INFO,
        current_value=round(lost, 0), target_value=None,
        causes=["preweaning_mortality_economic_loss"],
        recommended_actions=["reduce_preweaning_mortality_to_recover_loss"],
        detail={"loss": _loss_detail(lost, li)},
    )]


RuleRegistry.register(Rule("loss.preweaning_mortality", "loss", "Pre-weaning mortality loss", _loss_preweaning))


# ── 임신사고 손실 ────────────────────────────────────────────────────────────────
async def _loss_pregnancy_accident(ctx: RuleContext) -> list[Finding]:
    li = _inputs(ctx)
    if not li:
        return []
    accidents = li.get("accident_count") or 0.0
    per_litter = ctx.kpi.get("WEANED_COUNT")  # 복당 환산: 사고 1건 = 1복 손실 ≈ 평균 이유두수
    if accidents <= 0 or not per_litter:
        return []
    lost = accidents * float(per_litter)
    return [Finding(
        rule_id="loss.pregnancy_accident", kpi="ACCIDENT_LOSS", severity=Severity.INFO,
        current_value=round(lost, 0), target_value=None,
        causes=["pregnancy_accident_economic_loss"],
        recommended_actions=["reduce_pregnancy_accidents_to_recover_loss"],
        detail={"loss": _loss_detail(lost, li), "accidents": round(accidents, 0),
                "per_litter": round(float(per_litter), 1)},
    )]


RuleRegistry.register(Rule("loss.pregnancy_accident", "loss", "Pregnancy accident loss", _loss_pregnancy_accident))
