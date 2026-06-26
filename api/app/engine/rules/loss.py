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


# ── NPD(비생산일) 손실 — WEI 기반(보수적) ───────────────────────────────────────
# 모돈일 손실 = PSY × 육성률 × 두당가 ÷ 365, × Σ지연일(WEI). (PigPlan S9_NPD §2)
async def _loss_npd(ctx: RuleContext) -> list[Finding]:
    li = _inputs(ctx)
    if not li:
        return []
    wei_days = li.get("wei_total_days") or 0.0
    psy = ctx.kpi.get("PSY")
    born_alive = ctx.kpi.get("BORN_ALIVE")
    weaned = ctx.kpi.get("WEANED_COUNT")
    if wei_days <= 0 or not psy or not born_alive or not weaned:
        return []
    weaning_rate = min(float(weaned) / float(born_alive), 1.0)  # 육성률
    per_sow_day = float(psy) * weaning_rate * li["price"] / 365.0
    lost_amount = round(wei_days * per_sow_day)
    if lost_amount <= 0:
        return []
    return [Finding(
        rule_id="loss.npd", kpi="NPD_LOSS", severity=Severity.INFO,
        current_value=round(wei_days, 0), target_value=None,
        causes=["npd_nonproductive_days_economic_loss"],
        recommended_actions=["reduce_weaning_to_service_interval_to_recover_loss"],
        detail={"loss": {"amount": lost_amount, "currency": li["currency"],
                         "basis": "wei_sow_days", "wei_days": round(wei_days, 0), "demo": li.get("demo", True)},
                "scope": "WEI_only_conservative"},
    )]


RuleRegistry.register(Rule("loss.npd", "loss", "NPD (non-productive days) loss", _loss_npd))


# ── 조기도태 손실 — 산차별 잔여가치(KR seed, region/KR 없으면 미발화) ────────────
def _residual(ctx: RuleContext, code: str) -> float | None:
    b = (ctx.benchmarks.get(code) if ctx.benchmarks else None) or {}
    return b.get("target")


async def _loss_sow_culling(ctx: RuleContext) -> list[Finding]:
    # D-7: SOW_RESIDUAL/SALVAGE는 KRW(한국 잔존가 모델 S2_SOW_RETIREMENT) 기반 → KR 전용.
    # 非KR 농장엔 원화 잔존가가 새지 않도록 게이트(출시 전 분리, 통화 일반화는 P2).
    if (ctx.country or "").upper() != "KR":
        return []
    li = (ctx.extra.get("loss_inputs") if ctx.extra else None) or {}
    rows = li.get("cull_by_parity") or []
    if not rows or _residual(ctx, "SOW_RESIDUAL_P0") is None:  # 잔여가치 seed 없으면 미발화
        return []
    salvage_cull = _residual(ctx, "SOW_SALVAGE_CULL") or 0.0
    salvage_death = _residual(ctx, "SOW_SALVAGE_DEATH") or 0.0
    total = 0.0
    head = 0
    for r in rows:
        parity = r.get("parity", 0)
        if parity >= 7:           # 적정 이상 도태 — 잔여가치 0(손실 아님)
            continue
        residual = _residual(ctx, f"SOW_RESIDUAL_P{parity}")
        if residual is None:
            continue
        salvage = salvage_cull if r.get("status") == "CULLED" else salvage_death
        loss_per = max(residual - salvage, 0.0)
        total += loss_per * r.get("count", 0)
        head += r.get("count", 0)
    if total <= 0:
        return []
    currency = (ctx.benchmarks.get("SOW_RESIDUAL_P0") or {}).get("unit", "KRW")
    return [Finding(
        rule_id="loss.sow_culling", kpi="SOW_CULL_LOSS", severity=Severity.INFO,
        current_value=head, target_value=None,
        causes=["premature_sow_culling_economic_loss"],
        recommended_actions=["reduce_early_culling_below_breakeven_parity"],
        detail={"loss": {"amount": round(total), "currency": currency or "KRW",
                         "basis": "residual_value_by_parity", "head": head, "demo": False}},
    )]


RuleRegistry.register(Rule("loss.sow_culling", "loss", "Premature sow culling loss", _loss_sow_culling))
