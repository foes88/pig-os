"""
AI 탐지 라운드트립 — 실데이터 → herd 집계 → Rule Engine 탐지 → Finding/알림.
"데이터가 임계 넘으면 탐지된다 + 정상이면 오발화 0"을 엔드투엔드 보장. (pigos_test, Docker)
뷰(v_farm_psy 등)는 테스트 스키마에 없어 build_herd_kpis(테이블 집계)로 검증.
"""
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.engine import RuleContext, RuleEngine, Severity
from app.services.kpi_service import _sow_counts, build_herd_kpis


async def _seed_bad_farrowings(db: AsyncSession, farm: Farm, sow: Sow, n: int = 4):
    """고사산(50%)·저실산(6두) 분만 n건 — STILLBORN_RATE·BORN_ALIVE 임계 초과 유발."""
    today = date.today()
    for i in range(n):
        d = today - timedelta(days=30 + i * 10)
        m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=d - timedelta(days=114),
                   mating_type="AI")
        db.add(m)
        await db.flush()
        db.add(Farrowing(
            farm_id=farm.id, sow_id=sow.id, mating_id=m.id, farrowing_date=d,
            total_born=12, born_alive=6, stillborn=6, mummified=0,
        ))
    await db.flush()


async def _ctx(db: AsyncSession, farm: Farm, kpi: dict) -> RuleContext:
    # benchmarks 비움 → 규칙이 코드 기본 임계로 판정(뷰/함수 의존 0). sow_counts는 실 집계.
    counts = await _sow_counts(db, farm.id)
    return RuleContext(farm_id=farm.id, country=farm.country or "default",
                       kpi=kpi, benchmarks={}, sow_counts=counts, extra={"rule_configs": {}})


class TestRuleDetectionPipeline:
    async def test_bad_data_detected_and_surfaced(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow
    ):
        await _seed_bad_farrowings(db, test_farm, test_sow)

        # 1) 집계가 실데이터로 임계 초과 계산(날조 0 — 실제 50%·6두)
        herd = await build_herd_kpis(db, test_farm)
        assert herd["STILLBORN_RATE"] == 50.0
        assert herd["BORN_ALIVE"] == 6.0

        # 2) 엔진 탐지 → Finding
        result = await RuleEngine.evaluate(await _ctx(db, test_farm, herd), intent="dashboard")
        fired = {f.rule_id: f for f in result.findings}
        assert "stillborn.rate_high" in fired
        assert "born_alive.low" in fired

        # 3) viewing/알림에 필요한 필드(심각도·현재값) 채워짐
        sb = fired["stillborn.rate_high"]
        assert sb.severity == Severity.CRITICAL and sb.current_value >= 12

        # 4) 종합등급 롤업(critical 존재 → RED)
        assert fired["farm.health_class"].grade == "RED"
        # 전체 severity = CRITICAL (알림 배지)
        assert result.severity == Severity.CRITICAL

    async def test_clean_farm_no_false_alerts(
        self, db: AsyncSession, test_farm: Farm, test_sow: Sow
    ):
        # 데이터 없는 농장 → 임계 초과 탐지 0 (오발화 없음, 위조 0)
        herd = await build_herd_kpis(db, test_farm)
        result = await RuleEngine.evaluate(await _ctx(db, test_farm, herd), intent="dashboard")
        fired = {f.rule_id for f in result.findings}
        # 자돈 성적 데이터 없음 → 고사산/저실산 오발화 0 (위조 0)
        assert "stillborn.rate_high" not in fired
        assert "born_alive.low" not in fired
        # critical(RED) 아님 — 데이터 없는 농장이 위험으로 뜨지 않음
        assert result.severity != Severity.CRITICAL
        health = next((f for f in result.findings if f.rule_id == "farm.health_class"), None)
        assert health is not None and health.grade != "RED"
