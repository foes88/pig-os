"""동의 정책 매트릭스 (CONSENT_SPEC §2·§3) — policy_for 순수 조회, 기존 테스트 없음.

목적×법역그룹 → (법적근거·UI종류·상태태그). CN 차단·EU/GB 정당한이익·VN 미노출 등
정책 결정을 회귀 고정. 문안 아님 — 정책 벡터만.
"""
from app.policy.consent_matrix import (
    GROUP_BR,
    GROUP_CN,
    GROUP_EU,
    GROUP_GB,
    GROUP_KR,
    GROUP_OTHER,
    GROUP_TH,
    GROUP_US,
    GROUP_VN,
    OPT_IN_PURPOSES,
    SIGNUP_PURPOSE_ORDER,
    policy_for,
)

ALL_GROUPS = [GROUP_KR, GROUP_US, GROUP_EU, GROUP_GB, GROUP_BR, GROUP_TH, GROUP_VN, GROUP_CN, GROUP_OTHER]


def test_policy_for_never_raises_for_any_signup_purpose_group():
    # 모든 (목적×그룹) 조합이 KeyError 없이 정책을 반환(GROUP_OTHER 폴백 포함)
    for code in SIGNUP_PURPOSE_ORDER:
        for g in ALL_GROUPS:
            p = policy_for(code, g)
            assert p.purpose_code == code


def test_unknown_group_falls_back_to_other():
    assert policy_for("AI_MODEL_TRAINING", "ZZ") == policy_for("AI_MODEL_TRAINING", GROUP_OTHER)


def test_service_operation_contract_everywhere_notice_except_cn():
    for g in ALL_GROUPS:
        p = policy_for("SERVICE_OPERATION", g)
        assert p.lawful_basis == "CONTRACT"          # 계약이행 근거는 전 그룹 공통
        # CN은 전체 HOLD(D-07)라 서비스운영조차 BLOCKED, 나머지는 고지형
        assert p.ui_kind == ("BLOCKED" if g == GROUP_CN else "NOTICE")
    assert policy_for("SERVICE_OPERATION", GROUP_CN).status_tag == "HOLD_D07"


def test_cn_sensitive_purposes_blocked_hold_d07():
    for code in ("AI_MODEL_TRAINING", "NAMED_RESEARCH", "TRANSACTION_MATCHING"):
        p = policy_for(code, GROUP_CN)
        assert p.ui_kind == "BLOCKED"
        assert p.status_tag == "HOLD_D07"


def test_eu_gb_anon_is_legitimate_interest():
    for g in (GROUP_EU, GROUP_GB):
        p = policy_for("ANON_AGG_STATS", g)
        assert p.lawful_basis == "LEGITIMATE_INTEREST"
        assert p.ui_kind == "LI_OBJECT"


def test_vn_transaction_matching_hidden():
    assert policy_for("TRANSACTION_MATCHING", GROUP_VN).ui_kind == "HIDDEN"


def test_opt_in_purposes_require_evidence():
    for code in OPT_IN_PURPOSES:
        p = policy_for(code, GROUP_KR)
        assert p.lawful_basis == "CONSENT"
        assert p.requires_evidence is True
