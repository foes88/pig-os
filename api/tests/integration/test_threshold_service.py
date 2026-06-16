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


class TestRegionPriority:
    """QA 야간검증(Q3): 농장>국가(region)>글로벌 3단 체인의 '국가' 티어 검증.
    test_farm.country == 'KR'."""

    async def test_region_beats_global(self, db, test_farm: Farm):
        # KR 국가 임계값 추가 → 글로벌보다 우선, source/scope가 region에서 나옴.
        db.add(DefaultMetricValue(
            scope_type="region", scope_code="KR", metric_code="STILLBORN_RATE",
            warning_threshold=7.0, critical_threshold=11.0, alert_direction="above",
            unit_code="%", confidence="high", source_ref="PigPlan/한돈팜스",
        ))
        await db.flush()
        rows = await threshold_service.list_effective(db, test_farm)
        sr = next(r for r in rows if r["metric_code"] == "STILLBORN_RATE")
        assert sr["scope"] == "country"
        assert sr["warning"] == 7.0
        assert sr["source"] == "PigPlan/한돈팜스"  # source는 선택된 scope(국가)에서
        assert sr["is_override"] is False

    async def test_farm_beats_region_then_clear_reverts_to_region(self, db, test_farm: Farm):
        # 3단: 농장 override > 국가 > 글로벌. clear 시 글로벌이 아니라 '국가'로 복귀해야 함.
        db.add(DefaultMetricValue(
            scope_type="region", scope_code="KR", metric_code="STILLBORN_RATE",
            warning_threshold=7.0, critical_threshold=11.0, alert_direction="above",
            unit_code="%", confidence="high", source_ref="PigPlan/한돈팜스",
        ))
        await db.flush()
        await threshold_service.set_override(db, test_farm, "STILLBORN_RATE", warning=5.0, critical=9.0)
        rows = await threshold_service.list_effective(db, test_farm)
        sr = next(r for r in rows if r["metric_code"] == "STILLBORN_RATE")
        assert sr["scope"] == "farm" and sr["warning"] == 5.0
        # clear → 국가(KR) 값으로 복귀 (글로벌 8.0 아님)
        await threshold_service.clear_override(db, test_farm, "STILLBORN_RATE")
        rows = await threshold_service.list_effective(db, test_farm)
        sr = next(r for r in rows if r["metric_code"] == "STILLBORN_RATE")
        assert sr["scope"] == "country" and sr["warning"] == 7.0
