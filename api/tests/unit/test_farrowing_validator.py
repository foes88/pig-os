"""Unit tests for farrowing validator — 5 valid + 7 invalid cases."""
import pytest

from app.validators.base import ValidationError
from app.validators.farrowing import validate_farrowing


class TestFarrowingValidatorValid:
    def test_typical_litter(self):
        validate_farrowing(
            total_born=14, born_alive=13, stillborn=1, mummified=0,
            avg_birth_weight_kg=1.4,
        )

    def test_total_born_boundary_35(self):
        validate_farrowing(total_born=35, born_alive=35)

    def test_stillborn_boundary_25(self):
        validate_farrowing(total_born=25, born_alive=0, stillborn=25)

    def test_avg_birth_weight_boundary_3_0(self):
        validate_farrowing(total_born=10, born_alive=10, avg_birth_weight_kg=3.0)

    def test_sexed_counts_match_born_alive(self):
        validate_farrowing(total_born=12, born_alive=12, male=6, female=6)


class TestFarrowingValidatorInvalid:
    def test_total_born_over_35(self):
        with pytest.raises(ValidationError, match="Total Born cannot exceed 35"):
            validate_farrowing(total_born=36, born_alive=36)

    def test_stillborn_over_25(self):
        with pytest.raises(ValidationError, match="Stillborn cannot exceed 25"):
            validate_farrowing(total_born=30, born_alive=4, stillborn=26)

    def test_mummified_over_25(self):
        with pytest.raises(ValidationError, match="Mummified cannot exceed 25"):
            validate_farrowing(total_born=30, born_alive=4, mummified=26)

    def test_born_alive_exceeds_total_born(self):
        with pytest.raises(ValidationError, match="cannot exceed Total Born"):
            validate_farrowing(total_born=14, born_alive=15)

    def test_sexed_counts_mismatch(self):
        with pytest.raises(ValidationError, match="must equal Male"):
            validate_farrowing(total_born=10, born_alive=10, male=4, female=5)

    def test_avg_birth_weight_over_3_0(self):
        with pytest.raises(ValidationError, match="Average birth weight"):
            validate_farrowing(total_born=10, born_alive=10, avg_birth_weight_kg=3.1)

    def test_avg_birth_weight_just_over_3_0(self):
        with pytest.raises(ValidationError, match="Average birth weight"):
            validate_farrowing(total_born=10, born_alive=10, avg_birth_weight_kg=3.01)
