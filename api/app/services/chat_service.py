"""
Q&A Chat Service — Base tier (Rule Engine + Template Renderer).

Flow:
  question → classify_intent() → build_rule_context() → RuleEngine.evaluate()
           → renderer.render_text() → ChatResponse

Addon upgrade path:
  - Swap render_text() call with llm_renderer.render()
  - Rule Engine and context-building stay identical
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform import Farm
from app.engine import RuleEngine, RuleContext
from app.engine.renderer import render_text
from app.engine.rules import base as _base_rules  # noqa: F401  ensure registration
from app.schemas.chat import ChatQuery, ChatResponse, FindingOut
from app.services.kpi_service import build_rule_context

# ── Intent classifier ─────────────────────────────────────────────────────────
# Keyword-based for Base tier. Replace with embedding classifier in Addon.
_INTENT_KEYWORDS: dict[str, list[str]] = {
    "psy":       ["psy", "piglets per sow", "생산성", "이유두수", "productivity"],
    "npd":       ["npd", "non-productive", "비생산일", "이유 간격", "idle", "weaning interval"],
    "farrowing": ["farrowing rate", "분만율", "farrowing", "conception"],
    "inventory": ["sow count", "모돈 수", "inventory", "재고"],
    # "fcr"      → requires Addon; classifier returns "fcr" but RuleEngine will
    #              produce no findings at base tier (no fcr rules registered yet).
    "fcr":       ["fcr", "feed conversion", "사료효율", "feed efficiency"],
}


def classify_intent(question: str) -> str:
    q = question.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return intent
    return "dashboard"  # default: run all base rules


async def handle_query(
    db: AsyncSession,
    farm: Farm,
    query: ChatQuery,  # farm_id resolved by router via get_farm_context
) -> ChatResponse:
    intent = classify_intent(query.question)

    ctx: RuleContext = await build_rule_context(db, farm)

    # Base tier only; pass active addon codes here when Addon subscriptions are checked
    result = await RuleEngine.evaluate(ctx, intent=intent, tiers=["base"])

    answer = render_text(result, locale=query.locale)

    findings_out = [
        FindingOut(
            rule_id=f.rule_id,
            kpi=f.kpi,
            severity=f.severity,
            current_value=f.current_value,
            target_value=f.target_value,
            causes=f.causes,
            recommended_actions=f.recommended_actions,
        )
        for f in result.findings
    ]

    return ChatResponse(
        intent=result.intent,
        severity=result.severity,
        answer=answer,
        findings=findings_out,
        farm_id=farm.id,
        as_of=str(result.as_of),
        renderer="template",
    )
