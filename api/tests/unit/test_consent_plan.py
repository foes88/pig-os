"""동의 인프라 — 법역별 가입 플랜 규칙 (CONSENT_SPEC §2, TERMS_DISPLAY §3·§4).

DB 불필요(순수 정책·렌더러). record/withdraw 원장 테스트는 integration 참조.
"""
from app.services.consent_service import build_signup_plan


def _plan(sel, fc=None, st=None):
    return build_signup_plan(selected_country=sel, farm_country=fc, farm_state=st,
                             lang=None, include_body=False)


def _kind(plan, code):
    return next(p.ui_kind for p in plan.purposes if p.purpose_code == code)


def _visible(plan, code):
    return next(p.visible for p in plan.purposes if p.purpose_code == code)


def test_kr_anon_is_notice_not_toggle():
    p = _plan("KR")
    assert _kind(p, "ANON_AGG_STATS") == "NOTICE_EXCLUSION"
    assert not next(x.is_toggle for x in p.purposes if x.purpose_code == "ANON_AGG_STATS")
    assert p.gate.signup_blocked is False


def test_eu_anon_is_li_object_and_release_hold():
    p = _plan("DE")
    assert p.jurisdiction.group == "EU"
    assert _kind(p, "ANON_AGG_STATS") == "LI_OBJECT"
    assert p.gate.release_hold is True


def test_optin_purposes_default_off_everywhere():
    for c in ("KR", "US", "DE", "BR", "TH"):
        p = _plan(c)
        for code in ("AI_MODEL_TRAINING", "NAMED_RESEARCH"):
            pp = next(x for x in p.purposes if x.purpose_code == code)
            assert pp.is_toggle and pp.default_on is False


def test_us_ne_written_opt_in_for_anon_and_research():
    p = _plan("US", "US", "NE")
    assert p.jurisdiction.code == "US-NE"
    assert _kind(p, "ANON_AGG_STATS") == "WRITTEN_OPT_IN"
    assert _kind(p, "NAMED_RESEARCH") == "WRITTEN_OPT_IN"
    assert p.state_flags.written_opt_in_required is True


def test_us_ca_do_not_sell_and_uoom():
    p = _plan("US", "US", "CA")
    assert p.state_flags.do_not_sell_link is True
    tm = next(x for x in p.purposes if x.purpose_code == "TRANSACTION_MATCHING")
    assert tm.auto_off_if_uoom is True  # CA honors UOOM


def test_vn_hides_transaction_matching_and_gates_paid():
    p = _plan("VN")
    assert _visible(p, "TRANSACTION_MATCHING") is False
    assert _kind(p, "EXTERNAL_AI_PROCESSING") == "TRANSFER_CONSENT"
    assert p.gate.paid_blocked is True
    assert p.lang_gate is True  # vi 미비


def test_cn_signup_blocked_no_visible_purposes():
    p = _plan("CN")
    assert p.gate.signup_blocked is True
    assert all(not x.visible for x in p.purposes)


def test_country_mismatch_triggers_counsel_and_conservative():
    # 선택 US, 농장 DE → 더 엄격한 EU 채택 + counsel
    p = _plan("US", "DE", None)
    assert p.jurisdiction.counsel_review is True
    assert p.jurisdiction.group == "EU"


def test_notice_version_is_deterministic_and_includes_addendum():
    p = _plan("US", "US", "NE")
    assert p.notice_version == _plan("US", "US", "NE").notice_version
    assert "ADDENDUM_US" in p.notice_version
    assert p.any_draft is True  # placeholder 문서 → 게시 불가 신호
