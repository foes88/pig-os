"""
Cross-event date-range validation.

Reference: docs/SCREEN_MENU_SPEC.md → Screen → URL → Status Transition Map and the
per-event "must be after last recorded event" notes.

Rules enforced
--------------
* An event cannot predate the sow's ``entry_date``.
* An event cannot postdate the sow's removal (cull/death/sale) date.
* Mating must come after the previous weaning (re-service).
* Farrowing must come after its mating.
* Weaning must come after its farrowing.

All functions are no-ops when a reference date is unknown (``None``).
"""
from __future__ import annotations

from datetime import date

from app.validators.base import (
    ValidationError,
    validate_date_after,
    validate_date_not_before,
)


def validate_event_within_sow_lifespan(
    *,
    event_date: date,
    entry_date: date | None,
    exit_date: date | None = None,
    event_name: str = "Event",
) -> None:
    """Event must fall on/after entry and on/before removal date."""
    validate_date_not_before(event_date, entry_date, f"{event_name} date", "the sow's entry date")
    if exit_date is not None and event_date is not None and event_date > exit_date:
        raise ValidationError(
            f"{event_name} date ({event_date.isoformat()}) cannot be after "
            f"the sow's removal date ({exit_date.isoformat()})"
        )


def validate_mating_after_last_weaning(
    *, mating_date: date, last_weaning_date: date | None
) -> None:
    """Re-service mating must be after the previous weaning."""
    validate_date_after(mating_date, last_weaning_date, "Mating date", "the last weaning date")


def validate_farrowing_after_mating(
    *, farrowing_date: date, mating_date: date | None
) -> None:
    """Farrowing must be after the mating that produced it."""
    validate_date_after(farrowing_date, mating_date, "Farrowing date", "the mating date")


def validate_weaning_after_farrowing(
    *, weaning_date: date, farrowing_date: date | None
) -> None:
    """Weaning must be after the farrowing it ends."""
    validate_date_after(weaning_date, farrowing_date, "Weaning date", "the farrowing date")
