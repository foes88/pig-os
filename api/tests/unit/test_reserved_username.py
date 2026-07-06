"""예약어/사칭 아이디 차단 — RegisterRequest·OnboardingCompleteRequest username validator."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import OnboardingCompleteRequest, RegisterRequest


def _reg(username: str) -> dict:
    return dict(
        name="Test User", username=username, email="a@b.com",
        password="password1", org_name="Org", country="US",
    )


@pytest.mark.parametrize("bad", [
    "admin", "Admin", "ADMIN", "administrator", "Administrator",
    "adm1n", "4dmin", "admin1", "admin_kr", "root", "superuser",
    "superadmin", "super_admin", "system", "support", "pigos",
    "pigos_support", "wiselake", "PigOS",
])
def test_reserved_usernames_rejected(bad: str):
    with pytest.raises(ValidationError):
        RegisterRequest(**_reg(bad))


@pytest.mark.parametrize("ok", [
    "zdravko2706", "john_farm", "maria.silva", "farmer99",
    "nguyen_van", "kim_pig", "a1b2c3",
])
def test_normal_usernames_allowed(ok: str):
    # 실사용자(예: Zdravko) 아이디는 통과해야 함 — 오탐 방지
    assert RegisterRequest(**_reg(ok)).username == ok


def test_onboarding_request_also_blocks_reserved():
    with pytest.raises(ValidationError):
        OnboardingCompleteRequest(
            org_name="O", country="US", name="N", username="administrator",
            email="a@b.com", password="password1", farm_name="F",
        )
