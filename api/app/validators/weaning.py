"""
Weaning event validation.

Reference: docs/SCREEN_MENU_SPEC.md → Events / Weaning tab.
    Weaned (head) = Nursing head − (Deaths + Transfers out − Transfers in)

This is the head-count identity that must hold exactly. ``event_service`` also
enforces ``weaned <= effective litter`` using persisted foster/death events; this
validator covers the direct user-entered identity for the weaning form.
"""
from __future__ import annotations

from app.validators.base import ValidationError


def validate_weaning(
    *,
    weaned: int,
    nursing_head: int,
    deaths: int = 0,
    transfers_out: int = 0,
    transfers_in: int = 0,
) -> None:
    """Raise :class:`ValidationError` (HTTP 422) if the weaned head-count identity fails."""
    expected = nursing_head - (deaths + transfers_out - transfers_in)
    if weaned != expected:
        raise ValidationError(
            "Weaned count must equal: nursing_head - (deaths + out - in) "
            f"= {nursing_head} - ({deaths} + {transfers_out} - {transfers_in}) "
            f"= {expected}, but got {weaned}"
        )
