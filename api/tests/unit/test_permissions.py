from types import SimpleNamespace

from app.core.permissions import effective_system_role


def _user(role: str, system_role: str | None = None):
    return SimpleNamespace(role=role, system_role=system_role)


def test_effective_system_role_uses_explicit_system_role():
    assert effective_system_role(_user("FARM_OWNER", "VENDOR_ADMIN")) == "VENDOR_ADMIN"


def test_effective_system_role_maps_legacy_admin():
    assert effective_system_role(_user("ADMIN", None)) == "SUPER_ADMIN"


def test_effective_system_role_maps_legacy_company():
    assert effective_system_role(_user("COMPANY", "")) == "VENDOR_ADMIN"


def test_effective_system_role_falls_back_for_blank_values():
    assert effective_system_role(_user("", "")) == "FARM_OWNER"


def test_effective_system_role_rejects_unknown_system_role():
    # Unrecognized system_role must fail-safe to FARM_OWNER, not pass through.
    assert effective_system_role(_user("FARM_OWNER", "UNKNOWN_ROLE")) == "FARM_OWNER"


def test_effective_system_role_rejects_unknown_legacy_role():
    # Unrecognized legacy role with no system_role must also fail-safe.
    assert effective_system_role(_user("MYSTERY_ROLE", "")) == "FARM_OWNER"
