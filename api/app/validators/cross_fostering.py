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


def validate_cross_foster_distinct(source_sow_id, dest_sow_id) -> None:
    """B6: 동일 모돈 양자 차단 — 자기 자신에게 전입/전출 불가(두수 꼬임 방지)."""
    if source_sow_id == dest_sow_id:
        raise ValidationError(
            "Cross-foster source and destination must be different sows (cannot transfer to self)"
        )
