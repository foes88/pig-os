"""
N4 통합 테스트 — analytics_service.prrs_by_genetics.

품종별 PRRS 발생률 집계. DB 필요(pigos_test).
"""
from datetime import UTC, date, datetime

import pytest

from app.db.models.health import HealthEvent
from app.db.models.sow import Sow
from app.services import analytics_service

pytestmark = pytest.mark.asyncio


async def test_prrs_by_genetics(db, test_farm):
    s1 = Sow(farm_id=test_farm.id, ear_tag="PRRS-A1", parity=1, status="OPEN",
             entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT",
             breed="Yorkshire", genetics_id="Y-100")
    s2 = Sow(farm_id=test_farm.id, ear_tag="PRRS-A2", parity=1, status="OPEN",
             entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT",
             breed="Landrace", genetics_id="L-200")
    db.add_all([s1, s2])
    await db.flush()

    # Yorkshire 한 마리에 PRRS, 그리고 비-PRRS 질병 1건(집계 제외 확인)
    db.add(HealthEvent(farm_id=test_farm.id, sow_id=s1.id, event_date=date(2026, 5, 1),
                       event_type="DISEASE", disease_code="PRRS_2"))
    db.add(HealthEvent(farm_id=test_farm.id, sow_id=s2.id, event_date=date(2026, 5, 2),
                       event_type="DISEASE", disease_code="FMD"))
    await db.flush()

    res = await analytics_service.prrs_by_genetics(db, test_farm.id)
    assert res["total_sows"] == 2
    assert res["total_affected"] == 1
    assert res["total_events"] == 1  # PRRS만, FMD 제외

    by_breed = {r["breed"]: r for r in res["rows"]}
    assert by_breed["Yorkshire"]["affected_sows"] == 1
    assert by_breed["Yorkshire"]["incidence_rate"] == 100.0
    assert by_breed["Landrace"]["affected_sows"] == 0
    assert by_breed["Landrace"]["incidence_rate"] == 0.0
