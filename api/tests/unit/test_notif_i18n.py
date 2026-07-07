"""알림 body i18n 회귀 — 수신자 언어로 연결어·단위 현지화, 한국어 하드코딩 leak 방지.

과거 버그: persist_insights가 body를 f"...{unit} (기준 {t}{unit})"로 구워
unit=한국어("두/복")·연결어="기준"이 비한국어 사용자에게도 노출됐다.
"""
import re

from app.schemas.insight import EventInsight
from app.services.insight_service import _fmt_num, _notif_texts

HANGUL = re.compile(r"[가-힣]")


def _mk(metric="BORN_ALIVE", sev="WARNING", value=10.0, threshold=10.5, unit="piglets/litter"):
    return EventInsight(
        metric_code=metric, severity=sev, value=value, threshold=threshold,
        unit=unit, direction="below",
    )


def test_en_body_has_no_korean():
    title, body = _notif_texts(_mk(), "en")
    assert not HANGUL.search(body), body
    assert not HANGUL.search(title), title
    assert "threshold" in body
    assert "/litter" in body
    # metric_code·severity는 코드 유지
    assert body.startswith("BORN_ALIVE WARNING:")


def test_ko_body_localized_korean():
    _, body = _notif_texts(_mk(), "ko")
    assert "기준" in body
    assert "두/복" in body


def test_zh_and_pt_localized_no_korean():
    for lang, word in (("zh", "阈值"), ("pt", "limite"), ("es", "umbral"),
                       ("vi", "ngưỡng"), ("th", "เกณฑ์")):
        _, body = _notif_texts(_mk(), lang)
        assert word in body, (lang, body)
        assert not HANGUL.search(body), (lang, body)


def test_days_unit_localized():
    _, en = _notif_texts(_mk(metric="WEANING_AGE_HIGH", value=52, threshold=32, unit="days"), "en")
    assert "52d" in en and "32d" in en
    _, ko = _notif_texts(_mk(metric="WEANING_AGE_HIGH", value=52, threshold=32, unit="days"), "ko")
    assert "52일" in ko


def test_unknown_lang_falls_back_to_en():
    _, body = _notif_texts(_mk(), "de")
    assert "threshold" in body
    assert not HANGUL.search(body)


def test_symbol_units_passthrough():
    _, body = _notif_texts(_mk(metric="STILLBORN_RATE", value=18, threshold=12, unit="%"), "en")
    assert "18%" in body and "12%" in body


def test_fmt_num_integer_and_decimal():
    assert _fmt_num(10.0) == "10"
    assert _fmt_num(10.5) == "10.5"
    assert _fmt_num(52) == "52"
    assert _fmt_num(None) == ""


def test_unknown_unit_token_passthrough_not_crash():
    _, body = _notif_texts(_mk(unit="g/day", value=800, threshold=750), "ko")
    assert "800g/day" in body
