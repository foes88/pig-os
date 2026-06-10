"""Unit tests for cross-event date-range validators."""
from datetime import date

import pytest

from app.validators.base import ValidationError
from app.validators.date_rules import (
    validate_event_within_sow_lifespan,
    validate_farrowing_after_mating,
    validate_mating_after_last_weaning,
    validate_weaning_after_farrowing,
)


class TestLifespan:
    def test_event_after_entry_ok(self):
        validate_event_within_sow_lifespan(
            event_date=date(2026, 2, 1), entry_date=date(2026, 1, 1)
        )

    def test_event_on_entry_ok(self):
        validate_event_within_sow_lifespan(
            event_date=date(2026, 1, 1), entry_date=date(2026, 1, 1)
        )

    def test_event_before_entry_rejected(self):
        with pytest.raises(ValidationError, match="entry date"):
            validate_event_within_sow_lifespan(
                event_date=date(2025, 12, 31), entry_date=date(2026, 1, 1)
            )

    def test_event_after_removal_rejected(self):
        with pytest.raises(ValidationError, match="removal date"):
            validate_event_within_sow_lifespan(
                event_date=date(2026, 6, 2),
                entry_date=date(2026, 1, 1),
                exit_date=date(2026, 6, 1),
            )

    def test_no_entry_date_is_noop(self):
        validate_event_within_sow_lifespan(event_date=date(2026, 1, 1), entry_date=None)


class TestEventOrdering:
    def test_mating_after_weaning_ok(self):
        validate_mating_after_last_weaning(
            mating_date=date(2026, 1, 10), last_weaning_date=date(2026, 1, 3)
        )

    def test_mating_before_weaning_rejected(self):
        with pytest.raises(ValidationError, match="last weaning date"):
            validate_mating_after_last_weaning(
                mating_date=date(2026, 1, 2), last_weaning_date=date(2026, 1, 3)
            )

    def test_mating_no_prior_weaning_is_noop(self):
        validate_mating_after_last_weaning(
            mating_date=date(2026, 1, 2), last_weaning_date=None
        )

    def test_farrowing_after_mating_ok(self):
        validate_farrowing_after_mating(
            farrowing_date=date(2026, 4, 25), mating_date=date(2026, 1, 1)
        )

    def test_farrowing_before_mating_rejected(self):
        with pytest.raises(ValidationError, match="mating date"):
            validate_farrowing_after_mating(
                farrowing_date=date(2025, 12, 31), mating_date=date(2026, 1, 1)
            )

    def test_weaning_after_farrowing_ok(self):
        validate_weaning_after_farrowing(
            weaning_date=date(2026, 5, 16), farrowing_date=date(2026, 4, 25)
        )

    def test_weaning_before_farrowing_rejected(self):
        with pytest.raises(ValidationError, match="farrowing date"):
            validate_weaning_after_farrowing(
                weaning_date=date(2026, 4, 24), farrowing_date=date(2026, 4, 25)
            )
