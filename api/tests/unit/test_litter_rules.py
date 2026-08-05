"""산자·포유 룰 (app/engine/rules/litter.py) — 직접 임계 테스트 없음.

대표 룰의 코드기본 임계 발화(sev_above·sev_below 양방향) + 동일 KPI 양방향
(이유일 너무짧음/너무김) + 부분데이터 견고성. governance OFF, RuleContext 직접구성(DB 불필요).
"""
import uuid

import pytest

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules import litter

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _governance_off(monkeypatch):
    monkeypatch.setattr("app.engine.threshold_resolver.settings.use_governance_benchmarks", False)


def _ctx(**kpi) -> RuleContext:
    return RuleContext(
        farm_id=uuid.UUID("00000000-0000-0000-0000-0000000000f3"),
        country="KR", kpi=kpi, benchmarks={}, sow_counts={}, extra={},
    )


async def test_stillborn_high_above():
    assert await litter._stillborn_high(_ctx(STILLBORN_RATE=5)) == []                        # ≤8 정상
    assert (await litter._stillborn_high(_ctx(STILLBORN_RATE=10)))[0].severity == Severity.WARNING   # >8
    assert (await litter._stillborn_high(_ctx(STILLBORN_RATE=13)))[0].severity == Severity.CRITICAL  # >12


async def test_born_alive_low_below():
    assert await litter._born_alive_low(_ctx(BORN_ALIVE=12)) == []                            # ≥11 정상
    assert (await litter._born_alive_low(_ctx(BORN_ALIVE=10.5)))[0].severity == Severity.WARNING   # <11
    assert (await litter._born_alive_low(_ctx(BORN_ALIVE=9)))[0].severity == Severity.CRITICAL      # <10


async def test_lactation_short_and_long_same_kpi_both_directions():
    # WEANING_AGE 하나로 너무짧음(sev_below 19/16)·너무김(sev_above 28/35) 양방향
    assert await litter._lactation_short(_ctx(WEANING_AGE=21)) == []
    assert (await litter._lactation_short(_ctx(WEANING_AGE=18)))[0].severity == Severity.WARNING   # <19
    assert (await litter._lactation_short(_ctx(WEANING_AGE=15)))[0].severity == Severity.CRITICAL  # <16
    assert await litter._lactation_long(_ctx(WEANING_AGE=25)) == []
    assert (await litter._lactation_long(_ctx(WEANING_AGE=30)))[0].severity == Severity.WARNING    # >28
    assert (await litter._lactation_long(_ctx(WEANING_AGE=36)))[0].severity == Severity.CRITICAL   # >35


async def test_crushing_rate_high_above():
    assert await litter._crushing_rate_high(_ctx(CRUSHING_RATE=5)) == []
    assert (await litter._crushing_rate_high(_ctx(CRUSHING_RATE=8)))[0].severity == Severity.WARNING   # >6
    assert (await litter._crushing_rate_high(_ctx(CRUSHING_RATE=11)))[0].severity == Severity.CRITICAL  # >10


async def test_missing_kpi_returns_empty():
    empty = _ctx()
    assert await litter._stillborn_high(empty) == []
    assert await litter._born_alive_low(empty) == []
    assert await litter._lactation_short(empty) == []
    assert await litter._crushing_rate_high(empty) == []
