"""Unit tests for mating validator (eligible status + sequential boar slots)."""
import pytest

from app.validators.base import ValidationError
from app.validators.mating import validate_mating


class TestMatingValidatorValid:
    def test_gilt_single_boar(self):
        validate_mating(sow_status="GILT", boar_1="b1")

    def test_open_no_boar(self):
        validate_mating(sow_status="OPEN")

    def test_accident_two_boars(self):
        validate_mating(sow_status="ACCIDENT", boar_1="b1", boar_2="b2")

    def test_three_boars_sequential(self):
        validate_mating(sow_status="OPEN", boar_1="b1", boar_2="b2", boar_3="b3")


class TestMatingValidatorInvalid:
    def test_pregnant_status_rejected(self):
        with pytest.raises(ValidationError, match="only allowed"):
            validate_mating(sow_status="PREGNANT", boar_1="b1")

    def test_lactating_status_rejected(self):
        with pytest.raises(ValidationError, match="only allowed"):
            validate_mating(sow_status="LACTATING")

    def test_culled_status_rejected(self):
        with pytest.raises(ValidationError, match="only allowed"):
            validate_mating(sow_status="CULLED")

    def test_boar2_without_boar1(self):
        with pytest.raises(ValidationError, match="Boar 1 required before Boar 2"):
            validate_mating(sow_status="GILT", boar_2="b2")

    def test_boar3_without_boar2(self):
        with pytest.raises(ValidationError, match="Boar 2 required before Boar 3"):
            validate_mating(sow_status="GILT", boar_1="b1", boar_3="b3")
