"""
Mating event validation.

Reference: docs/SCREEN_MENU_SPEC.md → Events / Mating tab + Sow Status Definitions.
    Eligible sow status : GILT / OPEN / ACCIDENT
    Boar slots          : sequential — Boar 2 requires Boar 1, Boar 3 requires Boar 2

Kept in sync with ``event_service.MATABLE_STATUSES``.
"""
from __future__ import annotations

from typing import Any

from app.validators.base import ValidationError

MATABLE_STATUSES = ("GILT", "OPEN", "ACCIDENT")


def validate_mating(
    *,
    sow_status: str,
    boar_1: Any | None = None,
    boar_2: Any | None = None,
    boar_3: Any | None = None,
) -> None:
    """Raise :class:`ValidationError` (HTTP 422) on an invalid mating record."""
    if sow_status not in MATABLE_STATUSES:
        raise ValidationError(
            f"Sow status is '{sow_status}'. Mating is only allowed when status is "
            f"one of {', '.join(MATABLE_STATUSES)}"
        )
    if boar_2 is not None and boar_1 is None:
        raise ValidationError("Boar 1 required before Boar 2")
    if boar_3 is not None and boar_2 is None:
        raise ValidationError("Boar 2 required before Boar 3")
