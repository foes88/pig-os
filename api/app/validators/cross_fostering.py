"""
Cross-fostering (piglet transfer) validation.

Reference: docs/SCREEN_MENU_SPEC.md → Events / Cross-fostering tab.
    No. of piglets : max 25 per transfer
"""
from __future__ import annotations

from app.validators.base import ValidationError

MAX_TRANSFER_COUNT = 25


def validate_cross_fostering(*, transfer_count: int) -> None:
    """Raise :class:`ValidationError` (HTTP 422) if a transfer exceeds the per-transfer cap."""
    if transfer_count > MAX_TRANSFER_COUNT:
        raise ValidationError(
            f"Cross-fostering cannot exceed {MAX_TRANSFER_COUNT} piglets per transfer"
        )
