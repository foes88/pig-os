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


# detail 중 LLM이 설명에 쓸 수 있는 안전 키만 통과(룰엔진 계산값, raw DB 아님).
_DETAIL_WHITELIST = ("loss", "grade", "ear_tag", "weakest_kpi", "weakest_rule",
                     "method", "benchmark_avg", "accidents", "per_litter", "head", "matings")


def _safe_detail(detail: dict) -> dict:
    return {k: detail[k] for k in _DETAIL_WHITELIST if k in detail}


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
                "detail": _safe_detail(f.detail) if getattr(f, "detail", None) else {},
            }
            for f in result.findings
        ],
    }


# 7개 로케일(공개 6 + ko 관리자). 미지정은 English 폴백.
_LANG_NAME = {
    "ko": "Korean", "en": "English", "zh": "Chinese", "es": "Spanish",
    "vi": "Vietnamese", "th": "Thai", "pt": "Brazilian Portuguese", "ru": "Russian",
}


def build_system_prompt(locale: str) -> str:
    lang = _LANG_NAME.get(locale, "English")
    # PigPlan RENDERER 가이드 증류(출력규칙·금지·데이터신뢰) — 판단 금지 원칙은 유지.
    return (
        "You are a swine-farm analytics explainer. You receive a JSON object produced "
        "by a verified rule engine (the 'findings'). Your ONLY job is to explain that "
        f"result in fluent {lang}, in 2-4 short sentences.\n"
        "Rules:\n"
        "- Explain only. Do NOT add new judgments, numbers, diagnoses, or recommendations "
        "beyond what the JSON contains. Do not contradict or re-rank the findings.\n"
        "- Lead with the most severe finding (CRITICAL > WARNING > INFO).\n"
        "- For actions, use ONLY the items in recommended_actions; never invent specifics, "
        "and never name a drug, vaccine, or commercial product.\n"
        "- State a monetary amount ONLY if a finding's detail.loss.amount is present; if "
        "detail.loss.demo is true, present it as an approximate estimate.\n"
        "- If a value is 0 or 0%, treat it as possibly missing input rather than asserting "
        "perfect or zero performance.\n"
        "- Be concrete and practical; do not pad with generalities."
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
