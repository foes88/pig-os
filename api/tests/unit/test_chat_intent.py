"""intent 분류 + 미분류(unknown) 응답 구조 검증.

회귀 대상 2건 (prod 라이브에서 확인):
  1) 키워드 사전이 en/ko 뿐이라 zh/es/vi/th/pt 질문은 무엇을 묻든 "dashboard" 로 떨어졌다.
  2) 매칭 실패 시에도 "dashboard" 를 반환해, "오늘 서울 날씨 알려줘" 에 KPI 4건을 덤프했다.
"""
from datetime import date
from uuid import uuid4

import pytest

from app.engine.i18n import INTENT_KEYWORDS, INTENT_LABELS, SUPPORTED_LOCALES, UNKNOWN_INTENT, ui
from app.engine.renderer import render_text
from app.engine.rule_engine import Finding, Severity, StructuredResult
from app.services.chat_service import classify_intent


def make_result(intent: str, findings: list[Finding] | None = None) -> StructuredResult:
    return StructuredResult(
        farm_id=uuid4(),
        intent=intent,
        severity=Severity.INFO,
        findings=findings or [],
        as_of=date(2026, 8, 25),
    )


def a_finding() -> Finding:
    return Finding(
        rule_id="psy.below_target", kpi="PSY", severity=Severity.WARNING,
        current_value=22.0, target_value=24.0,
        causes=["low_litters_per_sow_per_year"],
        recommended_actions=["audit_weaning_to_mating_interval"],
    )


class TestClassifier:
    @pytest.mark.parametrize("question,expected", [
        # en / ko — 기존에도 동작하던 경로
        ("Why is PSY low?", "psy"),
        ("이유두수가 왜 낮아?", "psy"),
        ("How is the farrowing rate?", "farrowing"),
        ("분만율 어때?", "farrowing"),
        # 기존에 전부 dashboard 로 떨어지던 5개 언어
        ("为什么分娩率这么低？", "farrowing"),
        ("¿Por qué es baja la tasa de partos?", "farrowing"),
        ("Tại sao tỷ lệ đẻ thấp?", "farrowing"),
        ("อัตราการคลอดต่ำเพราะอะไร", "farrowing"),
        ("Por que a taxa de parto está baixa?", "farrowing"),
        ("料肉比高吗？", "fcr"),
        ("¿Cómo va la conversión alimenticia?", "fcr"),
        ("Số nái hiện tại là bao nhiêu?", "inventory"),
        ("จำนวนแม่สุกรตอนนี้เท่าไร", "inventory"),
        ("Quantas matrizes tem o plantel?", "inventory"),
    ])
    def test_domain_questions_classify_across_languages(self, question, expected):
        assert classify_intent(question) == expected

    @pytest.mark.parametrize("question", [
        "우리 농장 이번 달 상태 어때?",
        "How is my farm overall?",
        "猪场整体状况如何？",
        "¿Cuál es el estado general de la granja?",
        "Tình hình trại thế nào?",
        "ภาพรวมของฟาร์มเป็นอย่างไร",
        "Qual é a situação geral da granja?",
    ])
    def test_general_status_questions_still_map_to_dashboard(self, question):
        assert classify_intent(question) == "dashboard"

    @pytest.mark.parametrize("question", [
        "오늘 서울 날씨 알려줘",
        "What is the capital of France?",
        "点一份披萨",
    ])
    def test_off_topic_questions_are_unknown_not_dashboard(self, question):
        assert classify_intent(question) == UNKNOWN_INTENT

    def test_dashboard_is_matched_last(self):
        """포괄 키워드가 도메인 키워드를 가로채면 안 된다('농장 상태'+'분만율' 동시 포함)."""
        assert classify_intent("우리 농장 상태 중에 분만율 어때?") == "farrowing"
        assert list(INTENT_KEYWORDS)[-1] == "dashboard"


class TestUnknownIntentRendering:
    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_notice_is_prepended_and_localized(self, locale):
        text = render_text(make_result(UNKNOWN_INTENT, [a_finding()]), locale)
        assert text.startswith(ui("unknown_intent", locale))

    def test_findings_still_rendered_after_notice(self):
        """못 알아들었다고만 하고 끝내지 않는다 — 전체 요약은 그대로 이어진다."""
        text = render_text(make_result(UNKNOWN_INTENT, [a_finding()]), "ko")
        assert "[PSY]" in text

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_notice_shown_even_when_no_findings(self, locale):
        text = render_text(make_result(UNKNOWN_INTENT), locale)
        assert ui("unknown_intent", locale) in text
        assert ui("all_normal", locale) in text


class TestIntentScopedNormalMessage:
    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_specific_intent_names_the_metric(self, locale):
        """'모든 KPI 정상'으로 뭉개지 말고 무엇을 물었는지 밝힌다."""
        text = render_text(make_result("farrowing"), locale)
        assert INTENT_LABELS["farrowing"][locale] in text
        assert text != ui("all_normal", locale)

    @pytest.mark.parametrize("intent", sorted(INTENT_LABELS))
    def test_every_intent_has_a_scoped_message(self, intent):
        text = render_text(make_result(intent), "ko")
        assert INTENT_LABELS[intent]["ko"] in text

    def test_dashboard_keeps_the_blanket_message(self):
        assert render_text(make_result("dashboard"), "ko") == ui("all_normal", "ko")
