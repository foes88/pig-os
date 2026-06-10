"""Unit tests for cross-fostering validator (per-transfer cap)."""
import pytest

from app.validators.cross_fostering import validate_cross_fostering
from app.validators.base import ValidationError


class TestCrossFosteringValidator:
    def test_normal_transfer(self):
        validate_cross_fostering(transfer_count=4)

    def test_boundary_25(self):
        validate_cross_fostering(transfer_count=25)

    def test_over_25_rejected(self):
        with pytest.raises(ValidationError, match="cannot exceed 25 piglets per transfer"):
            validate_cross_fostering(transfer_count=26)
