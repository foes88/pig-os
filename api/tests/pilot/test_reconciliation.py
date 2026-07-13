"""PigPlan pilot reconciliation regression.

This test intentionally targets the configured live pilot database, not the isolated
integration-test database. If the pilot DB/CSV is unavailable it skips; when pilot
farms are loaded it enforces the same scorecard as scripts.verify_pilot.
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import SQLAlchemyError

from scripts.verify_pilot import build_scorecards

pytestmark = pytest.mark.anyio


async def test_pigplan_pilot_reconciliation_scorecard():
    try:
        scorecards = await build_scorecards()
    except (OSError, SQLAlchemyError) as exc:
        pytest.skip(f"pilot DB/CSV unavailable: {exc}")

    loaded = [card for card in scorecards if card.loaded_sows > 0]
    if not loaded:
        pytest.skip("pilot data is not loaded; run import_pigplan before this test")

    failures = [reason for card in scorecards for reason in card.failure_reasons()]
    assert not failures, "\n".join(failures)
