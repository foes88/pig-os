"""Unit tests for reproductive farm-config resolution + validation."""
import pytest
from pydantic import ValidationError as PydValidationError

from app.schemas.farm import FarmReproConfigUpdate
from app.services.farm_service import resolve_repro_config


class TestResolveReproConfig:
    def test_all_defaults(self):
        assert resolve_repro_config({}) == {
            "gestation_days": 114, "lactation_days": 21, "wei_target_days": 7,
            "gilt_first_mating_age": 240, "slaughter_age": 180,
        }

    def test_overrides(self):
        cfg = {"GESTATION_DAYS": "116", "LACTATION_DAYS": "28", "SLAUGHTER_AGE": "175"}
        r = resolve_repro_config(cfg)
        assert r["gestation_days"] == 116
        assert r["lactation_days"] == 28
        assert r["slaughter_age"] == 175
        assert r["wei_target_days"] == 7  # default

    def test_bad_value_falls_back_to_default(self):
        assert resolve_repro_config({"GESTATION_DAYS": "abc"})["gestation_days"] == 114


class TestReproConfigUpdateValidation:
    def test_valid(self):
        FarmReproConfigUpdate(gestation_days=114, lactation_days=21, wei_target_days=7)

    def test_partial_ok(self):
        m = FarmReproConfigUpdate(gestation_days=115)
        assert m.lactation_days is None

    def test_gestation_out_of_range(self):
        with pytest.raises(PydValidationError):
            FarmReproConfigUpdate(gestation_days=99)
        with pytest.raises(PydValidationError):
            FarmReproConfigUpdate(gestation_days=131)

    def test_wsi_out_of_range(self):
        with pytest.raises(PydValidationError):
            FarmReproConfigUpdate(wei_target_days=0)

    def test_gilt_age_out_of_range(self):
        with pytest.raises(PydValidationError):
            FarmReproConfigUpdate(gilt_first_mating_age=500)
