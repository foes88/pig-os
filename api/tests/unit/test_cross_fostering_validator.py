"""Unit tests for cross-fostering validator (per-transfer cap + distinct sows)."""
from uuid import uuid4

import pytest

from app.validators.base import ValidationError
from app.validators.cross_fostering import (
    validate_cross_foster_distinct,
    validate_cross_fostering,
)


class TestCrossFosterDistinct:
    """B6: 동일 모돈 양자 차단."""

    def test_distinct_sows_pass(self):
        validate_cross_foster_distinct(uuid4(), uuid4())

    def test_same_sow_rejected(self):
        sid = uuid4()
        with pytest.raises(ValidationError, match="different sows"):
            validate_cross_foster_distinct(sid, sid)


class TestCrossFosteringValidator:
    def test_normal_transfer(self):
        validate_cross_fostering(transfer_count=4)

    def test_boundary_25(self):
        validate_cross_fostering(transfer_count=25)

    def test_over_25_rejected(self):
        with pytest.raises(ValidationError, match="cannot exceed 25 piglets per transfer"):
            validate_cross_fostering(transfer_count=26)
