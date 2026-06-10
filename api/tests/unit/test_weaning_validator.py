"""Unit tests for weaning validator (head-count identity)."""
import pytest

from app.validators.weaning import validate_weaning
from app.validators.base import ValidationError


class TestWeaningValidatorValid:
    def test_simple_no_adjustments(self):
        validate_weaning(weaned=11, nursing_head=11)

    def test_with_deaths(self):
        # 13 nursing - 2 deaths = 11 weaned
        validate_weaning(weaned=11, nursing_head=13, deaths=2)

    def test_with_transfers_in_and_out(self):
        # 10 + 3 in - 1 out = 12
        validate_weaning(weaned=12, nursing_head=10, transfers_in=3, transfers_out=1)

    def test_all_adjustments(self):
        # 14 - (2 deaths + 1 out - 2 in) = 13
        validate_weaning(
            weaned=13, nursing_head=14, deaths=2, transfers_out=1, transfers_in=2
        )


class TestWeaningValidatorInvalid:
    def test_weaned_too_high(self):
        with pytest.raises(ValidationError, match="Weaned count must equal"):
            validate_weaning(weaned=13, nursing_head=13, deaths=2)

    def test_weaned_too_low(self):
        with pytest.raises(ValidationError, match="Weaned count must equal"):
            validate_weaning(weaned=9, nursing_head=11)

    def test_ignores_transfers_when_mismatched(self):
        with pytest.raises(ValidationError, match="= 11, but got 12"):
            validate_weaning(weaned=12, nursing_head=13, deaths=2)
