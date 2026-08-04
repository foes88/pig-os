"""약관 문서 렌더러 (TERMS_DISPLAY §1·§2·§5) — 순수 조립기, 기존 테스트 없음.

문서세트 = 마스터 + 글로벌 방침 + (해당국) 부속 1개. EU/GB 부속 분리 확인.
문구 자체(변호사 확정 전 placeholder)는 검증 대상 아님 — 조합·버전·언어우선만.
"""
from app.services.terms_renderer import build_document_set, language_for


def _ids(group):
    ds = build_document_set(jurisdiction_code=group, group=group)
    return [d.doc_id for d in ds.docs], ds


def test_eu_set_appends_eu_addendum():
    ids, ds = _ids("EU")
    assert ids == ["MASTER_TERMS", "GLOBAL_PRIVACY_NOTICE", "ADDENDUM_EU"]
    assert ds.lang == "en"


def test_gb_addendum_is_split_from_eu():
    gb_ids, _ = _ids("GB")
    assert gb_ids[-1] == "ADDENDUM_GB"       # EU와 다른 부속
    assert "ADDENDUM_EU" not in gb_ids


def test_us_set_appends_us_addendum():
    us_ids, _ = _ids("US")
    assert us_ids[-1] == "ADDENDUM_US"


def test_kr_has_no_addendum():
    kr_ids, _ = _ids("KR")
    assert kr_ids == ["MASTER_TERMS", "GLOBAL_PRIVACY_NOTICE"]   # 부속 없음


def test_notice_version_is_deterministic_join():
    _, ds = _ids("EU")
    assert ds.notice_version == "+".join(f"{d.doc_id}@{d.version}" for d in ds.docs)
    assert "@" in ds.notice_version and ds.notice_version.count("+") == 2


def test_draft_placeholders_flag_any_draft():
    _, ds = _ids("EU")
    assert ds.any_draft is True   # 전부 변호사확정전 DRAFT → 게시불가 신호
    assert all(d.body for d in ds.docs)  # 본문 비어있지 않음


def test_language_for_group_priority():
    assert language_for("KR") == "ko"
    assert language_for("EU") == "en"
    assert language_for("BR") == "pt"
    assert language_for("UNKNOWN_GROUP") == "en"   # 폴백
