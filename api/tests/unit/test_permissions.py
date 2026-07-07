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
    # E(QA 보안 L1): 미인식/공란은 fail-open(FARM_OWNER write)이 아닌 fail-closed(VIEWER 읽기전용).
    assert effective_system_role(_user("", "")) == "VIEWER"


def test_effective_system_role_rejects_unknown_system_role():
    # Unrecognized system_role must fail-CLOSED to VIEWER, not pass through nor grant write.
    assert effective_system_role(_user("FARM_OWNER", "UNKNOWN_ROLE")) == "VIEWER"


def test_effective_system_role_rejects_unknown_legacy_role():
    # Unrecognized legacy role with no system_role must also fail-closed to VIEWER.
    assert effective_system_role(_user("MYSTERY_ROLE", "")) == "VIEWER"
