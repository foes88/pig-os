"""
Event input validators — business-rule guards.

Design notes
------------
* Each validator is a **pure function** taking primitives/value-objects (no DB
  session, no ORM rows) so it unit-tests without Postgres and composes cleanly
  inside ``event_service`` after the rows have been loaded.
* Failures raise :class:`app.core.exceptions.ValidationError`, which the global
  exception handler already maps to **HTTP 422**. We deliberately reuse that
  exception instead of defining a new one so the API surface stays consistent.

This module holds the shared exception re-export and date helpers used by the
per-event validator modules (farrowing/weaning/mating/cross_fostering/date_rules).
"""
from __future__ import annotations

from datetime import date

from app.core.exceptions import ValidationError

__all__ = ["ValidationError", "validate_date_after", "validate_date_not_before"]


def validate_date_after(
    value: date | None,
    reference: date | None,
    field_name: str,
    reference_name: str = "the reference date",
) -> None:
    """Raise 422 if ``value`` is not strictly after ``reference``.

    No-op when either date is ``None`` (the field is optional / not yet known).
    """
    if value is None or reference is None:
        return
    if value <= reference:
        raise ValidationError(
            f"{field_name} ({value.isoformat()}) must be after "
            f"{reference_name} ({reference.isoformat()})"
        )


def validate_date_not_before(
    value: date | None,
    reference: date | None,
    field_name: str,
    reference_name: str = "the reference date",
) -> None:
    """Raise 422 if ``value`` is earlier than ``reference`` (equal is allowed).

    No-op when either date is ``None``.
    """
    if value is None or reference is None:
        return
    if value < reference:
        raise ValidationError(
            f"{field_name} ({value.isoformat()}) cannot be before "
            f"{reference_name} ({reference.isoformat()})"
        )
