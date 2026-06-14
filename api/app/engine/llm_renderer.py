"""
LLM Renderer — Addon #1 (AI Insight).

Same interface as the Template Renderer, but turns a StructuredResult into a
natural-language explanation via an LLM. The LLM is told to **explain only, never
judge** — all decisions already come from the verified Rule Engine.

Safety / cost controls:
  * Falls back to the Template Renderer when no API key is configured, when
    ``use_llm`` is False, or when the farm's monthly quota is exhausted.
  * Vendor-agnostic: swap the call in ``_call_llm`` without touching chat_service.

This module never imports the vendor SDK at module load (lazy import inside the
call) so the Base tier has zero extra dependencies.
"""
from __future__ import annotations

import json
import os

from app.engine.renderer import render_text
from app.engine.rule_engine import StructuredResult

MONTHLY_LIMIT = 100
LLM_MODEL = "claude-haiku-4-5-20251001"


def has_api_key() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))


def within_quota(used: int, limit: int = MONTHLY_LIMIT) -> bool:
    return used < limit


def _result_to_payload(result: StructuredResult) -> dict:
    """Compact, vendor-neutral JSON the LLM is allowed to see (no raw DB rows)."""
    return {
        "intent": result.intent,
        "severity": result.severity.value,
        "as_of": str(result.as_of),
        "findings": [
            {
                "rule_id": f.rule_id,
                "kpi": f.kpi,
                "severity": f.severity.value,
                "current_value": f.current_value,
                "target_value": f.target_value,
                "grade": getattr(f, "grade", None),
                "causes": f.causes,
                "recommended_actions": f.recommended_actions,
            }
            for f in result.findings
        ],
    }


def build_system_prompt(locale: str) -> str:
    lang = {"ko": "Korean", "en": "English", "zh": "Chinese", "es": "Spanish", "vi": "Vietnamese"}.get(locale, "English")
    return (
        "You are a swine-farm analytics explainer. You will receive a JSON object "
        "produced by a verified rule engine. Your ONLY job is to explain that result "
        f"in fluent {lang}, in 2-4 short sentences. "
        "Do NOT add new judgments, numbers, diagnoses, or recommendations beyond what "
        "the JSON contains. Do not contradict or re-rank the findings."
    )


async def _call_llm(result: StructuredResult, locale: str) -> str:
    """Vendor call. Lazy-imports the SDK; raises on any failure (caller falls back)."""
    import anthropic  # lazy

    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = await client.messages.create(
        model=LLM_MODEL,
        max_tokens=400,
        system=build_system_prompt(locale),
        messages=[{"role": "user", "content": json.dumps(_result_to_payload(result), ensure_ascii=False)}],
    )
    return msg.content[0].text.strip()


async def render(
    result: StructuredResult,
    locale: str = "en",
    *,
    use_llm: bool = False,
    usage_count: int = 0,
) -> tuple[str, str]:
    """Return ``(text, rendered_by)`` where rendered_by is "llm" or "template".

    Falls back to the template renderer whenever the LLM path is unavailable or
    disallowed, so callers always get a valid answer.
    """
    if not use_llm or not has_api_key() or not within_quota(usage_count):
        return render_text(result, locale), "template"
    try:
        return await _call_llm(result, locale), "llm"
    except Exception:
        return render_text(result, locale), "template"
