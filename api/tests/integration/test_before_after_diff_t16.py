"""
T1-6 before/after diff (A-하이브리드 게이트4, §10 관문).

고정 fixture set으로 발화 결과를 측정:
- flag OFF (배선 후 = 현행 경로) vs flag ON (operational_defaults 경로)
- operational_defaults 값 == 코드 default이므로 country override 없는 fixture에선 **발화 1:1 동일**해야.
- 차이 = 회귀. 0이면 §10.2 "발화 ≈ 유지" 합격.

ctx.benchmarks={}(국가 override 없음)으로 둬 flag OFF(code default)와 flag ON(operational_defaults=code)을
동일 조건에서 비교. (KR default_metric_values override는 flag ON 실배포 결정사항 — 본 게이트 범위 밖.)
"""
from uuid import uuid4

import pytest

from app.core import config
from app.db.operational_defaults_seed import OPERATIONAL_DEFAULTS
from app.engine.rule_engine import RuleContext, RuleEngine
from app.services import kpi_service as _kpi  # noqa: F401  (룰 등록 부작용)

pytestmark = pytest.mark.anyio

# 여러 도메인 룰을 발화시키는 고정 KPI 입력 (3개 가상 농장)
FIXTURES = {
    "KRfarm": dict(country="KR", kpi={
        "PSY": 15.0, "NPD": 55.0, "FARROWING_RATE": 70.0, "FCR": 3.5, "STILLBORN_RATE": 13.0,
        "MUMMIFIED_RATE": 5.0, "WEANED_COUNT": 8.0, "BORN_ALIVE": 9.0, "WSI": 15.0, "RTS_RATE": 26.0,
        "ABORTION_RATE": 6.0, "CONCEPTION_RATE": 79.0, "MSY": 14.0, "CULLING_RATE": 56.0,
        "SOW_MORTALITY": 13.0, "FINISH_MORTALITY": 9.0, "ADG": 540.0, "CRUSHING_RATE": 11.0}),
    "USfarm": dict(country="US", kpi={
        "PSY": 24.0, "FCR": 2.6, "STILLBORN_RATE": 7.0, "WSI": 6.0, "MSY": 20.0,
        "FARROWING_RATE": 86.0, "WEANED_COUNT": 11.0, "SOW_MORTALITY": 6.0}),
    "GLOBALfarm": dict(country="ZZ", kpi={
        "FCR": 3.05, "WSI": 11.0, "STILLBORN_RATE": 9.0, "CULLING_RATE": 47.0, "CONCEPTION_RATE": 84.0}),
}

_OPD_MAP = {d["rule_id"]: {"warning": d["warning"], "critical": d["critical"]} for d in OPERATIONAL_DEFAULTS}


def _ctx(country, kpi, *, with_opd: bool) -> RuleContext:
    extra = {"rule_configs": {}}
    if with_opd:
        extra["operational_defaults"] = _OPD_MAP
    return RuleContext(farm_id=uuid4(), country=country, kpi=kpi, benchmarks={}, sow_counts={}, extra=extra)


async def _fire(ctx) -> set[tuple[str, str]]:
    res = await RuleEngine.evaluate(ctx, intent="dashboard")
    return {(f.rule_id, f.severity.name) for f in res.findings}


async def test_before_after_firing_identical(monkeypatch):
    """배선 후 flag OFF == flag ON 발화 (operational_defaults=code default → 0 diff)."""
    report = {}
    for name, fx in FIXTURES.items():
        monkeypatch.setattr(config.settings, "use_governance_benchmarks", False)
        before = await _fire(_ctx(fx["country"], fx["kpi"], with_opd=False))
        monkeypatch.setattr(config.settings, "use_governance_benchmarks", True)
        after = await _fire(_ctx(fx["country"], fx["kpi"], with_opd=True))
        only_before = before - after
        only_after = after - before
        report[name] = (len(before), len(after), only_before, only_after)
        assert only_before == set(), f"{name} flag ON에서 사라진 발화: {only_before}"
        assert only_after == set(), f"{name} flag ON에서 새로 생긴 발화: {only_after}"
    # 진단 출력(로그용)
    for name, (b, a, ob, oa) in report.items():
        print(f"[diff] {name}: before={b} after={a} lost={len(ob)} gained={len(oa)}")
    # 최소 한 fixture는 실제로 여러 발화가 있어야(빈 비교로 통과하는 것 방지)
    assert report["KRfarm"][0] >= 8


async def test_flag_on_uses_operational_value(monkeypatch):
    """flag ON에서 operational_defaults 임계로 발화하는지(경로 실작동 확인)."""
    monkeypatch.setattr(config.settings, "use_governance_benchmarks", True)
    # FCR 3.5 > critical 3.3 → fcr.high critical 발화
    fired = await _fire(_ctx("ZZ", {"FCR": 3.5}, with_opd=True))
    assert ("fcr.high", "CRITICAL") in fired
