"""
이벤트 입력 즉시 분석 (insight_service) 통합 테스트 — pigos_test (Docker).
임계값은 default_metric_values 시드(system/global)에서 읽음.
"""
from datetime import date

import pytest
from sqlalchemy import delete, select

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
_PRICE = ("MARKET_PRICE_HEAD", 450000.0, "KRW")
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
    # 출하 두당가격(손실 계산용, system scope=글로벌 → demo=True)
    db.add(DefaultMetricValue(
        scope_type="system", scope_code="SYSTEM", metric_code=_PRICE[0],
        default_value=_PRICE[1], unit_code=_PRICE[2], alert_direction="below",
    ))
    await db.flush()
    # BORN_ALIVE에 상대판정용 top25 baseline 추가
    row = await db.scalar(select(DefaultMetricValue).where(
        DefaultMetricValue.metric_code == "BORN_ALIVE", DefaultMetricValue.scope_type == "system"))
    row.benchmark_top25 = 15.0
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
        # 손실액(LOSS_CALC): 사산4+미라2=6두 × 450000 = 2,700,000, system가격이라 demo=True
        assert sr.loss is not None
        assert sr.loss["amount"] == 6 * 450000
        assert sr.loss["lost_pigs"] == 6
        assert sr.loss["demo"] is True

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
        # 상대판정 슬롯(#3): top25=15 baseline → 생존12는 3두 미달
        assert ba.relative is not None
        assert ba.relative["top25"] == 15.0
        assert ba.relative["gap"] == 3.0  # below: 15-12=3 미달
        assert ba.relative["better"] is False


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


class TestEdgeCases:
    """QA 야간검증(Q2): 분모 0 / 음수 폐사 / 가격·top25 없음 / 글로벌 폴백 / 진입점 격리."""

    async def test_total_born_zero_no_crash(self, db, test_farm: Farm, test_sow):
        # total_born=0 → 사산율 분모 0. 가드(tb>0)로 STILLBORN_RATE skip, 예외 없음.
        f = _farrowing(test_farm.id, test_sow.id, tb=0, ba=0, sb=0, mum=0)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        assert isinstance(insights, list)
        assert all(i.metric_code != "STILLBORN_RATE" for i in insights)

    async def test_born_alive_zero_pwm_skipped(self, db, test_farm: Farm, test_sow):
        # born_alive=0 → 포유폐사율 분모 0. 가드(born_alive>0)로 PWM skip, 예외 없음.
        f = await _persist_farrowing(db, test_farm, test_sow, ba=0)
        w = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                    weaning_date=date(2026, 6, 22), weaned_count=0, weaning_age_days=21)
        insights = await insight_service.analyze_weaning(db, test_farm, w)
        assert isinstance(insights, list)
        assert all(i.metric_code != "PRE_WEANING_MORTALITY" for i in insights)

    async def test_weaned_exceeds_born_alive_no_false_mortality(self, db, test_farm: Farm, test_sow):
        # 이유두수 > 생존산자(포유자 입양 등) → dead 음수 → 거짓 폐사경보·손실 없음.
        f = await _persist_farrowing(db, test_farm, test_sow, ba=10)
        w = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                    weaning_date=date(2026, 6, 22), weaned_count=12, weaning_age_days=21)
        insights = await insight_service.analyze_weaning(db, test_farm, w)
        pwm = next((i for i in insights if i.metric_code == "PRE_WEANING_MORTALITY"), None)
        assert pwm is None  # 음수 폐사는 경보 아님

    async def test_no_price_hides_loss(self, db, test_farm: Farm, test_sow):
        # MARKET_PRICE_HEAD 없으면 손실 슬롯 None(금액 표시 금지).
        await db.execute(delete(DefaultMetricValue).where(
            DefaultMetricValue.metric_code == "MARKET_PRICE_HEAD"))
        await db.flush()
        f = _farrowing(test_farm.id, test_sow.id, tb=14, ba=8, sb=4, mum=2)  # 사산율 42.9% critical
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        sr = next((i for i in insights if i.metric_code == "STILLBORN_RATE"), None)
        assert sr is not None and sr.severity == "CRITICAL"
        assert sr.loss is None  # 가격 없음 → 손실 숨김

    async def test_no_top25_hides_relative(self, db, test_farm: Farm, test_sow):
        # top25 baseline 없는 메트릭(STILLBORN_RATE)은 상대판정 슬롯 None.
        f = _farrowing(test_farm.id, test_sow.id, tb=14, ba=8, sb=4, mum=2)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        sr = next((i for i in insights if i.metric_code == "STILLBORN_RATE"), None)
        assert sr is not None
        assert sr.relative is None  # baseline 없음 → 상대 숨김

    async def test_global_fallback_flag_when_system_scope(self, db, test_farm: Farm, test_sow):
        # 국가/농장 행 없이 system(글로벌)만 시드 → is_global_fallback=True.
        f = _farrowing(test_farm.id, test_sow.id, tb=14, ba=8, sb=4, mum=2)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        sr = next((i for i in insights if i.metric_code == "STILLBORN_RATE"), None)
        assert sr is not None
        assert sr.is_global_fallback is True

    async def test_analyze_event_unknown_type_returns_empty(self, db, test_farm: Farm, test_sow):
        # 알 수 없는 이벤트 타입 → 빈 리스트(진입점 안전).
        result = await insight_service.analyze_event(db, test_farm, "unknown_type", object())
        assert result == []


class TestRelativeSlotAbove:
    """QA 야간검증(Q4): 상대판정 슬롯 'above' 방향 gap 부호 검증.
    above(사산율 등 높을수록 나쁨)에서 top25는 낮은 값 → value-top25 부호."""

    async def test_above_direction_worse_than_top25(self, db, test_farm: Farm, test_sow):
        # STILLBORN_RATE에 top25=5.7 baseline 주입 (above 방향).
        row = await db.scalar(select(DefaultMetricValue).where(
            DefaultMetricValue.metric_code == "STILLBORN_RATE",
            DefaultMetricValue.scope_type == "system"))
        row.benchmark_top25 = 5.7
        await db.flush()
        # 사산율 = 6/14 = 42.9% → critical, top25(5.7)보다 훨씬 나쁨.
        f = _farrowing(test_farm.id, test_sow.id, tb=14, ba=8, sb=4, mum=2)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        sr = next(i for i in insights if i.metric_code == "STILLBORN_RATE")
        assert sr.relative is not None
        assert sr.relative["top25"] == 5.7
        assert sr.relative["gap"] > 0          # above: value-top25 > 0 = top25보다 나쁨
        assert sr.relative["better"] is False


class TestPersistIdempotency:
    """QA 야간검증 2회차(C2-Q2): persist_insights 멱등 — 동일 이벤트 재분석/재적재 시
    미읽음 중복 알림 0."""

    async def test_persist_insights_no_duplicate_on_second_call(self, db, test_farm: Farm, test_user, test_sow):
        from sqlalchemy import func

        from app.db.models.ops import Notification
        from app.db.models.platform import UserFarm
        from app.services import notification_service  # noqa: F401  (멱등 경로 사용)

        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        await db.flush()

        f = _farrowing(test_farm.id, test_sow.id, tb=14, ba=8, sb=4, mum=2)
        insights = await insight_service.analyze_farrowing(db, test_farm, f)
        serious = [i for i in insights if i.severity in ("WARNING", "CRITICAL")]
        assert serious

        async def _count():
            return int(await db.scalar(
                select(func.count()).select_from(Notification).where(
                    Notification.user_id == test_user.id,
                    Notification.related_entity_id == test_sow.id,
                    Notification.type == "IN_APP",
                )
            ) or 0)

        await insight_service.persist_insights(db, test_farm, test_sow.id, insights)
        n1 = await _count()
        assert n1 >= 1
        # 2회차 — 미읽음 동일 알림 재생성 금지
        await insight_service.persist_insights(db, test_farm, test_sow.id, insights)
        n2 = await _count()
        assert n2 == n1
