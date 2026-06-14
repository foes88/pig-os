"""Unit tests for event-delete status rollback (pure)."""
import pytest

from app.core.exceptions import ValidationError
from app.services.event_service import (
    ROLLBACK_STATUS_ON_DELETE,
    rollback_status_on_delete,
)


class TestRollback:
    def test_mating(self):
        assert rollback_status_on_delete("mating") == "OPEN"

    def test_farrowing(self):
        assert rollback_status_on_delete("farrowing") == "PREGNANT"

    def test_weaning(self):
        assert rollback_status_on_delete("weaning") == "LACTATING"

    def test_map_complete(self):
        assert set(ROLLBACK_STATUS_ON_DELETE) == {"mating", "farrowing", "weaning"}

    def test_unknown_raises(self):
        with pytest.raises(ValidationError, match="Cannot roll back unknown"):
            rollback_status_on_delete("teleport")
