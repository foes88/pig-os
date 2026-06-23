"""Unit tests for the LLM renderer fallback + quota (no external API calls)."""
import asyncio
from datetime import date
from uuid import uuid4

from app.engine.llm_renderer import (
    MONTHLY_LIMIT,
    _result_to_payload,
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

    def test_seven_locales(self):
        # 7개 로케일 모두 언어명이 프롬프트에 들어감
        for loc, name in [("zh", "Chinese"), ("es", "Spanish"), ("vi", "Vietnamese"),
                          ("th", "Thai"), ("pt", "Brazilian Portuguese")]:
            assert name in build_system_prompt(loc)
        assert "English" in build_system_prompt("xx")  # 미지정 → 폴백

    def test_explain_only_instruction(self):
        p = build_system_prompt("en").lower()
        assert "explain" in p
        assert "not" in p
        assert "drug" in p          # 약품명 금지(PROHIBIT_LIST 증류)


class TestPayloadDetail:
    def test_loss_amount_in_payload(self):
        result = StructuredResult(
            farm_id=uuid4(), intent="dashboard", severity=Severity.INFO,
            findings=[Finding(rule_id="loss.preweaning_mortality", kpi="PREWEAN_LOSS",
                              severity=Severity.INFO, current_value=40, target_value=None,
                              causes=["preweaning_mortality_economic_loss"], recommended_actions=[],
                              detail={"loss": {"amount": 12000000, "currency": "KRW", "demo": False},
                                      "_secret": "drop me"})],
            as_of=date(2026, 6, 24))
        payload = _result_to_payload(result)
        d = payload["findings"][0]["detail"]
        assert d["loss"]["amount"] == 12000000
        assert "_secret" not in d   # 화이트리스트 외 제거

    def test_template_renders_loss(self):
        result = StructuredResult(
            farm_id=uuid4(), intent="dashboard", severity=Severity.INFO,
            findings=[Finding(rule_id="loss.sow_culling", kpi="SOW_CULL_LOSS",
                              severity=Severity.INFO, current_value=3, target_value=None,
                              causes=["premature_sow_culling_economic_loss"], recommended_actions=[],
                              detail={"loss": {"amount": 16500000, "currency": "KRW", "demo": False}})],
            as_of=date(2026, 6, 24))
        txt = render_text(result, "ko")
        assert "16,500,000" in txt and "손실" in txt
