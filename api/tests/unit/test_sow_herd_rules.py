"""모돈군 구조 룰 (app/engine/rules/sow_herd.py) — 직접 테스트 없음.

7개 룰의 코드 기본 임계 발화를 고정. governance OFF로 두면 resolve 가
rule_configs→benchmarks(둘 다 비움)→코드 기본값을 쓰므로 결정적.
sev_above: >warning→WARNING, >critical→CRITICAL (임계 '초과' strict).
"""
import uuid

import pytest

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules import sow_herd

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _governance_off(monkeypatch):
    # 코드 기본 임계를 쓰도록 거버넌스 벤치마크 해제(운영자/국가 오버라이드 배제)
    monkeypatch.setattr("app.engine.threshold_resolver.settings.use_governance_benchmarks", False)


def _ctx(**kpi) -> RuleContext:
    return RuleContext(
        farm_id=uuid.UUID("00000000-0000-0000-0000-0000000000e1"),
        country="KR", kpi=kpi, benchmarks={}, sow_counts={}, extra={},
    )


async def test_culling_rate_bands():
    assert await sow_herd._culling_rate_high(_ctx(CULLING_RATE=40)) == []          # <45 정상
    assert (await sow_herd._culling_rate_high(_ctx(CULLING_RATE=50)))[0].severity == Severity.WARNING
    assert (await sow_herd._culling_rate_high(_ctx(CULLING_RATE=60)))[0].severity == Severity.CRITICAL


async def test_sow_mortality_bands():
    assert (await sow_herd._sow_mortality_high(_ctx(SOW_MORTALITY=10)))[0].severity == Severity.WARNING
    assert (await sow_herd._sow_mortality_high(_ctx(SOW_MORTALITY=13)))[0].severity == Severity.CRITICAL


async def test_high_parity_ratio_warning():
    r = await sow_herd._parity_high_ratio(_ctx(HIGH_PARITY_RATIO=25))
    assert r[0].severity == Severity.WARNING and r[0].kpi == "HIGH_PARITY_RATIO"


async def test_replacement_abnormal_both_directions():
    assert (await sow_herd._replacement_rate_abnormal(_ctx(REPLACEMENT_RATE=55)))[0].severity == Severity.WARNING
    assert (await sow_herd._replacement_rate_abnormal(_ctx(REPLACEMENT_RATE=65)))[0].severity == Severity.CRITICAL
    # 과소 갱신(<30)도 경고
    assert (await sow_herd._replacement_rate_abnormal(_ctx(REPLACEMENT_RATE=25)))[0].severity == Severity.WARNING
    # 정상 밴드
    assert await sow_herd._replacement_rate_abnormal(_ctx(REPLACEMENT_RATE=40)) == []


async def test_msy_below_bep_lower_is_worse():
    assert await sow_herd._msy_below_bep(_ctx(MSY=18)) == []                       # >=17 정상
    assert (await sow_herd._msy_below_bep(_ctx(MSY=16)))[0].severity == Severity.WARNING   # 15~17
    assert (await sow_herd._msy_below_bep(_ctx(MSY=14)))[0].severity == Severity.CRITICAL  # <15


async def test_missing_kpi_returns_empty():
    # 관련 KPI 없으면 각 룰 빈 결과(부분 데이터 견고성)
    empty = _ctx()
    assert await sow_herd._culling_rate_high(empty) == []
    assert await sow_herd._sow_mortality_high(empty) == []
    assert await sow_herd._msy_below_bep(empty) == []
    assert await sow_herd._second_litter_slump(empty) == []
    assert await sow_herd._accident_parity_skew(empty) == []
