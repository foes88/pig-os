"""
이벤트 입력 즉시 분석 (insight_service) 통합 테스트 — pigos_test (Docker).
임계값은 default_metric_values 시드(system/global)에서 읽음.
"""
from datetime import date

import pytest

from app.db.models.config import DefaultMetricValue
from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.services import insight_service


async def _persist_farrowing(db, farm, sow, ba):
    """Mating→Farrowing 체인 persist (mating_id NOT NULL). 반환: Farrowing."""
    m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2026, 2, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=sow.id, mating_id=m.id,
                  farrowing_date=date(2026, 6, 1), total_born=ba + 1,
                  born_alive=ba, stillborn=1, mummified=0)
    db.add(f)
    await db.flush()
    return f

# 시드 (system/global) — conftest는 create_all만 하므로 테스트에서 직접 삽입
_SEED = [
    ("STILLBORN_RATE", "above", 8.0, 12.0, "%"),
    ("BORN_ALIVE", "below", 13.0, 11.5, "두/복"),
    ("PRE_WEANING_MORTALITY", "above", 13.0, 18.0, "%"),
    ("WEANED_COUNT", "below", 11.0, 9.5, "두/복"),
    ("WSI", "above", 7.0, 10.0, "일"),
    ("WEANING_AGE_LOW", "below", 18.0, 14.0, "일"),
    ("WEANING_AGE_HIGH", "above", 28.0, 32.0, "일"),
]


@pytest.fixture(autouse=True)
async def _seed_thresholds(db):
    for code, direction, warn, crit, unit in _SEED:
        db.add(DefaultMetricValue(
            scope_type="system", scope_code="SYSTEM", metric_code=code,
            warning_threshold=warn, critical_threshold=crit,
            alert_direction=direction, unit_code=unit,
        ))
    await db.flush()


def _farrowing(farm_id, sow_id, tb, ba, sb, mum):
    return Farrowing(
        farm_id=farm_id, sow_id=sow_id, farrowing_date=date(2026, 6, 1),
        total_born=tb, born_alive=ba, stillborn=sb, mummified=mum,
    )


class TestFarrowingInsight:
    async def test_high_stillborn_critical(self, db, test_farm: Farm, test_sow):
        # 사산율 = (4+2)/14 = 42.9% → critical(>12)
        f = _farrowing(test_farm.id, test_sow.id, tb=14, ba=8, sb=4, mum=2)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        codes = {i.metric_code: i for i in insights}
        assert "STILLBORN_RATE" in codes
        sr = codes["STILLBORN_RATE"]
        assert sr.severity == "CRITICAL"
        assert sr.direction == "above"
        # 메인 선정용 필드(백엔드 계산): normalized_gap = (42.9-12)/12 ≈ 2.57, priority 존재
        assert sr.normalized_gap is not None and sr.normalized_gap > 2.0
        assert sr.priority == 20  # STILLBORN_RATE 우선순위

    async def test_normal_farrowing_no_stillborn_alert(self, db, test_farm: Farm, test_sow):
        # 사산율 = 1/15 = 6.7% → 정상(<8), born_alive 14 정상(>13)
        f = _farrowing(test_farm.id, test_sow.id, tb=15, ba=14, sb=1, mum=0)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        assert all(i.metric_code != "STILLBORN_RATE" for i in insights)

    async def test_low_born_alive_warning(self, db, test_farm: Farm, test_sow):
        # born_alive 12 → warning(<13), critical(<11.5)면 critical
        f = _farrowing(test_farm.id, test_sow.id, tb=13, ba=12, sb=1, mum=0)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        ba = next((i for i in insights if i.metric_code == "BORN_ALIVE"), None)
        assert ba is not None
        assert ba.severity == "WARNING"


class TestWeaningInsight:
    async def test_weaning_age_too_early(self, db, test_farm: Farm, test_sow):
        # 이유일령 15일(<18 warning, <14 critical → warning)
        f = await _persist_farrowing(db, test_farm, test_sow, ba=12)
        w = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                    weaning_date=date(2026, 6, 16), weaned_count=11, weaning_age_days=15)
        insights = await insight_service.analyze_weaning(db, test_farm, w)
        low = next((i for i in insights if i.metric_code == "WEANING_AGE_LOW"), None)
        assert low is not None
        assert low.severity == "WARNING"

    async def test_high_pre_weaning_mortality(self, db, test_farm: Farm, test_sow):
        # 생존 12 → 이유 8 : PWM = (12-8)/12 = 33% → critical(>18)
        f = await _persist_farrowing(db, test_farm, test_sow, ba=12)
        w = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                    weaning_date=date(2026, 6, 22), weaned_count=8, weaning_age_days=21)
        insights = await insight_service.analyze_weaning(db, test_farm, w)
        pwm = next((i for i in insights if i.metric_code == "PRE_WEANING_MORTALITY"), None)
        assert pwm is not None
        assert pwm.severity == "CRITICAL"


class TestNullSkip:
    async def test_no_threshold_metric_skipped(self, db, test_farm: Farm, test_sow):
        # RTS_RATE 등 시드 안 된 메트릭은 행 없음 → None(skip), 예외 없음
        f = _farrowing(test_farm.id, test_sow.id, tb=15, ba=15, sb=0, mum=0)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        # 정상 분만 → insight 없음 (예외 없이 빈 리스트)
        assert isinstance(insights, list)
