"""Unit tests for the LLM renderer fallback + quota (no external API calls)."""
import asyncio
from datetime import date
from uuid import uuid4

from app.engine.llm_renderer import (
    MONTHLY_LIMIT,
    build_system_prompt,
    render,
    within_quota,
)
from app.engine.renderer import render_text
from app.engine.rule_engine import Finding, Severity, StructuredResult


def make_result() -> StructuredResult:
    return StructuredResult(
        farm_id=uuid4(),
        intent="psy",
        severity=Severity.WARNING,
        findings=[
            Finding(
                rule_id="psy.below_target",
                kpi="PSY",
                severity=Severity.WARNING,
                current_value=22.0,
                target_value=24.0,
                causes=["low_litters_per_sow_per_year"],
                recommended_actions=["audit_weaning_to_mating_interval"],
                grade="Stable",
            )
        ],
        as_of=date(2026, 6, 10),
    )


class TestQuota:
    def test_within_quota(self):
        assert within_quota(0) is True
        assert within_quota(MONTHLY_LIMIT - 1) is True

    def test_quota_exhausted(self):
        assert within_quota(MONTHLY_LIMIT) is False
        assert within_quota(MONTHLY_LIMIT + 5) is False


class TestRenderFallback:
    def test_use_llm_false_returns_template(self):
        result = make_result()
        text, by = asyncio.run(render(result, locale="ko", use_llm=False))
        assert by == "template"
        assert text == render_text(result, "ko")

    def test_no_api_key_falls_back(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        result = make_result()
        text, by = asyncio.run(render(result, locale="en", use_llm=True))
        assert by == "template"
        assert text == render_text(result, "en")

    def test_quota_exhausted_falls_back(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        result = make_result()
        text, by = asyncio.run(
            render(result, locale="en", use_llm=True, usage_count=MONTHLY_LIMIT)
        )
        assert by == "template"


class TestSystemPrompt:
    def test_locale_language(self):
        assert "Korean" in build_system_prompt("ko")
        assert "English" in build_system_prompt("en")

    def test_explain_only_instruction(self):
        p = build_system_prompt("en")
        assert "explain" in p.lower()
        assert "do not" in p.lower() or "not" in p.lower()
