"""비육·자돈 성장 룰 (app/engine/rules/grow_finish.py) — 직접 테스트 없음.

FCR(높을수록나쁨)·ADG(낮을수록나쁨)·비육폐사율(높을수록나쁨) 코드기본 임계 발화.
governance OFF로 코드 기본값 사용, RuleContext 직접구성(DB 불필요).
"""
import uuid

import pytest

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules import grow_finish

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _governance_off(monkeypatch):
    monkeypatch.setattr("app.engine.threshold_resolver.settings.use_governance_benchmarks", False)


def _ctx(**kpi) -> RuleContext:
    return RuleContext(
        farm_id=uuid.UUID("00000000-0000-0000-0000-0000000000f2"),
        country="KR", kpi=kpi, benchmarks={}, sow_counts={}, extra={},
    )


async def test_fcr_high_bands():
    assert await grow_finish._fcr_high(_ctx(FCR=2.9)) == []                        # ≤3.0 정상
    assert (await grow_finish._fcr_high(_ctx(FCR=3.1)))[0].severity == Severity.WARNING   # >3.0
    assert (await grow_finish._fcr_high(_ctx(FCR=3.4)))[0].severity == Severity.CRITICAL  # >3.3


async def test_adg_low_bands_lower_is_worse():
    assert await grow_finish._adg_low(_ctx(ADG=700)) == []                          # ≥650 정상
    assert (await grow_finish._adg_low(_ctx(ADG=600)))[0].severity == Severity.WARNING   # <650
    assert (await grow_finish._adg_low(_ctx(ADG=500)))[0].severity == Severity.CRITICAL  # <550


async def test_finish_mortality_high_bands():
    assert await grow_finish._finish_mortality_high(_ctx(FINISH_MORTALITY=4)) == []                        # ≤5 정상
    assert (await grow_finish._finish_mortality_high(_ctx(FINISH_MORTALITY=6)))[0].severity == Severity.WARNING   # >5
    assert (await grow_finish._finish_mortality_high(_ctx(FINISH_MORTALITY=9)))[0].severity == Severity.CRITICAL  # >8


async def test_missing_kpi_returns_empty():
    empty = _ctx()
    assert await grow_finish._fcr_high(empty) == []
    assert await grow_finish._adg_low(empty) == []
    assert await grow_finish._finish_mortality_high(empty) == []
