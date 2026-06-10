"""Unit tests for sow status-transition validator."""
import pytest

from app.validators.base import ValidationError
from app.validators.sow_state import ALLOWED_TRANSITIONS, validate_transition


class TestSowStateValid:
    def test_mating_from_gilt(self):
        validate_transition(event="mating", current_status="GILT")

    def test_mating_from_open(self):
        validate_transition(event="mating", current_status="OPEN")

    def test_mating_from_accident(self):
        validate_transition(event="mating", current_status="ACCIDENT")

    def test_farrowing_from_pregnant(self):
        validate_transition(event="farrowing", current_status="PREGNANT")

    def test_weaning_from_lactating(self):
        validate_transition(event="weaning", current_status="LACTATING")

    def test_rts_from_pregnant(self):
        validate_transition(event="rts", current_status="PREGNANT")

    @pytest.mark.parametrize("status", ALLOWED_TRANSITIONS["culling"])
    def test_culling_from_any_active(self, status):
        validate_transition(event="culling", current_status=status)


class TestSowStateInvalid:
    def test_mating_from_pregnant_rejected(self):
        with pytest.raises(ValidationError, match="Allowed statuses: GILT, OPEN, ACCIDENT"):
            validate_transition(event="mating", current_status="PREGNANT")

    def test_farrowing_from_open_rejected(self):
        with pytest.raises(ValidationError, match="Cannot record 'farrowing'"):
            validate_transition(event="farrowing", current_status="OPEN")

    def test_weaning_from_pregnant_rejected(self):
        with pytest.raises(ValidationError, match="Allowed statuses: LACTATING"):
            validate_transition(event="weaning", current_status="PREGNANT")

    def test_rts_from_lactating_rejected(self):
        with pytest.raises(ValidationError, match="Allowed statuses: PREGNANT"):
            validate_transition(event="rts", current_status="LACTATING")

    def test_culling_from_culled_rejected(self):
        with pytest.raises(ValidationError, match="Cannot record 'culling'"):
            validate_transition(event="culling", current_status="CULLED")

    def test_unknown_event_rejected(self):
        with pytest.raises(ValidationError, match="Unknown transition event"):
            validate_transition(event="teleport", current_status="OPEN")
