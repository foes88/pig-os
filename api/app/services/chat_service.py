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

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform import AddonSubscription, Farm
from app.engine import RuleContext, RuleEngine
from app.engine.i18n import INTENT_KEYWORDS, UNKNOWN_INTENT
from app.engine.llm_renderer import render as llm_render
from app.engine.rules import base as _base_rules  # noqa: F401  ensure registration
from app.schemas.chat import ChatQuery, ChatResponse, FindingOut
from app.services import llm_usage_service
from app.services.kpi_service import build_rule_context

# Addon #1 (AI Insight) — LLM 자연어 렌더러를 켜는 구독 코드
AI_INSIGHT_ADDON_CODE = "ADDON_AI_INSIGHT"


async def _has_ai_insight(db: AsyncSession, farm_id: UUID) -> bool:
    """농장이 AI Insight Addon을 활성 구독 중인지 확인."""
    row = await db.scalar(
        select(AddonSubscription).where(
            AddonSubscription.farm_id == farm_id,
            AddonSubscription.addon_code == AI_INSIGHT_ADDON_CODE,
            AddonSubscription.is_active.is_(True),
        )
    )
    return row is not None

# ── Intent classifier ─────────────────────────────────────────────────────────
# Keyword-based for Base tier. Replace with embedding classifier in Addon.
# 키워드 사전은 app/engine/i18n.py 가 SSOT (7개 언어). 예전엔 여기에 en/ko 만 있어서
# 비영어·비한국어 질문은 무엇을 묻든 전부 "dashboard"로 떨어졌다.


def classify_intent(question: str) -> str:
    """매칭 실패 시 "unknown". 예전엔 "dashboard"로 뭉개서 '오늘 날씨' 같은 질문에도
    KPI를 덤프했다. 호출측이 unknown을 보고 못 알아들었음을 밝힌 뒤 요약으로 이어간다."""
    q = question.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return intent
    return UNKNOWN_INTENT


async def handle_query(
    db: AsyncSession,
    farm: Farm,
    query: ChatQuery,  # farm_id resolved by router via get_farm_context
    use_llm: bool | None = None,   # None → AI Insight 구독 여부로 자동 판정 (테스트는 명시 override)
    usage_count: int | None = None,  # None → 이번달 호출 수 자동 조회 (쿼터 폴백용)
) -> ChatResponse:
    intent = classify_intent(query.question)

    # Addon #1 구독·사용량 자동 배선 (명시 인자가 없을 때만)
    if use_llm is None:
        use_llm = await _has_ai_insight(db, farm.id)
    if usage_count is None:
        usage_count = await llm_usage_service.monthly_count(db, farm.id) if use_llm else 0

    ctx: RuleContext = await build_rule_context(db, farm)

    # Base tier only; pass active addon codes here when Addon subscriptions are checked
    # unknown 은 도메인 룰이 없으므로 dashboard 룰로 평가하되, intent 는 unknown 으로 유지한다
    # (렌더러가 "못 알아들었다" 안내를 붙일 수 있도록).
    eval_intent = "dashboard" if intent == UNKNOWN_INTENT else intent
    result = await RuleEngine.evaluate(ctx, intent=eval_intent, tiers=["base"])
    result.intent = intent

    from app.core.config import settings
    if settings.use_governance_benchmarks:  # flag ON: 비교 맥락 + §7 trace 첨부
        from app.services.benchmark_service import enrich_findings_with_governance
        await enrich_findings_with_governance(db, farm.country or "default", result.findings)

    answer, used_renderer = await llm_render(
        result, locale=query.locale, use_llm=use_llm, usage_count=usage_count
    )

    # LLM이 실제로 사용된 경우에만 사용량 로그 기록 (쿼터 폴백 시엔 template라 기록 안 함)
    if used_renderer == "llm":
        await llm_usage_service.record_call(db, farm.id, intent=result.intent)
        await db.commit()

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
        renderer=used_renderer,
    )
