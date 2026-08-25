"""렌더 결과가 요청 로케일로 실제 현지화되는지 (7개 언어 전부) 검증.

회귀 대상: renderer 가 ``_CAUSE_KO if locale == "ko" else _CAUSE_EN`` 이진 분기였던 시절,
zh/es/vi/th/pt 로 물어도 응답이 전부 영어로 나갔다 (prod 라이브에서 확인된 버그).
"""
from datetime import date
from uuid import uuid4

import pytest

from app.engine.i18n import ACTION_LABELS, CAUSE_LABELS, SUPPORTED_LOCALES, ui
from app.engine.renderer import render_text
from app.engine.rule_engine import Finding, Severity, StructuredResult

CAUSE = "low_litters_per_sow_per_year"
ACTION = "audit_weaning_to_mating_interval"


def make_result(findings: list[Finding] | None = None) -> StructuredResult:
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
                causes=[CAUSE],
                recommended_actions=[ACTION],
            )
        ] if findings is None else findings,
        as_of=date(2026, 6, 10),
    )


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_cause_and_action_rendered_in_requested_locale(locale):
    text = render_text(make_result(), locale)
    assert CAUSE_LABELS[CAUSE][locale] in text
    assert ACTION_LABELS[ACTION][locale] in text
    assert ui("causes", locale) in text
    assert ui("actions", locale) in text


@pytest.mark.parametrize("locale", [loc for loc in SUPPORTED_LOCALES if loc != "en"])
def test_non_english_locales_do_not_leak_english_labels(locale):
    """영어 라벨이 그대로 새어나오지 않아야 한다(문구가 en과 동일한 언어는 없음)."""
    text = render_text(make_result(), locale)
    assert CAUSE_LABELS[CAUSE]["en"] not in text
    assert ACTION_LABELS[ACTION]["en"] not in text


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_empty_findings_message_is_localized(locale):
    text = render_text(make_result(findings=[]), locale)
    assert text == ui("all_normal", locale)


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_severity_prefix_and_target_label_localized(locale):
    text = render_text(make_result(), locale)
    assert ui("severity_warning", locale) in text
    assert f"{ui('target', locale)}: 24.0" in text


def test_locale_variants_are_folded():
    """pt-BR / zh_Hans 같은 클라이언트 변형도 현지화돼야 한다."""
    assert CAUSE_LABELS[CAUSE]["pt"] in render_text(make_result(), "pt-BR")
    assert CAUSE_LABELS[CAUSE]["zh"] in render_text(make_result(), "zh_Hans")


def test_unsupported_locale_falls_back_to_english():
    text = render_text(make_result(), "ru")
    assert CAUSE_LABELS[CAUSE]["en"] in text


def test_unknown_cause_code_is_humanized_not_raw_snake_case():
    result = make_result(findings=[
        Finding(
            rule_id="x.y", kpi="PSY", severity=Severity.INFO,
            current_value=None, target_value=None,
            causes=["some_brand_new_cause"], recommended_actions=[],
        )
    ])
    text = render_text(result, "ko")
    assert "Some Brand New Cause" in text
    assert "some_brand_new_cause" not in text
