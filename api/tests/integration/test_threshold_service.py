"""임계값 관리 (#4) 통합 테스트 — pigos_test (Docker)."""
import pytest
from sqlalchemy import select

from app.db.models.config import DefaultMetricValue
from app.db.models.platform import Farm
from app.services import threshold_service


@pytest.fixture(autouse=True)
async def _seed(db):
    db.add(DefaultMetricValue(
        scope_type="system", scope_code="SYSTEM", metric_code="STILLBORN_RATE",
        warning_threshold=8.0, critical_threshold=12.0, alert_direction="above", unit_code="%",
        confidence="medium", source_ref="global",
    ))
    await db.flush()


class TestList:
    async def test_lists_global_scope(self, db, test_farm: Farm):
        rows = await threshold_service.list_effective(db, test_farm)
        sr = next((r for r in rows if r["metric_code"] == "STILLBORN_RATE"), None)
        assert sr is not None
        assert sr["scope"] == "global"
        assert sr["is_override"] is False
        assert sr["warning"] == 8.0


class TestOverride:
    async def test_set_override_takes_priority(self, db, test_farm: Farm):
        row = await threshold_service.set_override(db, test_farm, "STILLBORN_RATE", warning=6.0, critical=10.0)
        assert row["scope"] == "farm"
        assert row["is_override"] is True
        assert row["warning"] == 6.0
        # 재조회 시 농장값 우선
        rows = await threshold_service.list_effective(db, test_farm)
        sr = next(r for r in rows if r["metric_code"] == "STILLBORN_RATE")
        assert sr["warning"] == 6.0 and sr["scope"] == "farm"

    async def test_clear_override_reverts(self, db, test_farm: Farm):
        await threshold_service.set_override(db, test_farm, "STILLBORN_RATE", warning=6.0, critical=10.0)
        removed = await threshold_service.clear_override(db, test_farm, "STILLBORN_RATE")
        assert removed == 1
        rows = await threshold_service.list_effective(db, test_farm)
        sr = next(r for r in rows if r["metric_code"] == "STILLBORN_RATE")
        assert sr["scope"] == "global" and sr["warning"] == 8.0
        # farm 행 삭제 확인
        farm_row = await db.scalar(select(DefaultMetricValue).where(
            DefaultMetricValue.scope_type == "farm",
            DefaultMetricValue.metric_code == "STILLBORN_RATE",
        ))
        assert farm_row is None
