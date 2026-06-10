"""
Sow status-transition validation (state machine guard).

Reference: docs/SCREEN_MENU_SPEC.md → Sow Status Definitions + Status Transition Map.

An event is only allowed when the sow is currently in one of the eligible
statuses for that event. The map mirrors the breeding cycle:

    mating      : GILT / OPEN / ACCIDENT          → PREGNANT
    farrowing   : PREGNANT                         → LACTATING
    weaning     : LACTATING                        → OPEN
    rts         : PREGNANT                         → ACCIDENT
    culling     : any active status               → CULLED
"""
from __future__ import annotations

from app.validators.base import ValidationError

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "mating": ["GILT", "OPEN", "ACCIDENT"],
    "farrowing": ["PREGNANT"],
    "weaning": ["LACTATING"],
    "rts": ["PREGNANT"],
    "culling": ["GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT"],
}


def validate_transition(*, event: str, current_status: str) -> None:
    """Raise :class:`ValidationError` (HTTP 422) if ``event`` is not allowed from ``current_status``.

    Unknown ``event`` keys raise too (defensive — caller passed an unmapped event).
    """
    if event not in ALLOWED_TRANSITIONS:
        raise ValidationError(f"Unknown transition event '{event}'")
    allowed = ALLOWED_TRANSITIONS[event]
    if current_status not in allowed:
        raise ValidationError(
            f"Cannot record '{event}' while sow status is '{current_status}'. "
            f"Allowed statuses: {', '.join(allowed)}"
        )
