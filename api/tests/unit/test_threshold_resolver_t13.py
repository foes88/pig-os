"""
T1-3 Threshold Resolver 테스트 (A-하이브리드 게이트1).
flag ON: rule_config → operational_defaults → code default. flag OFF: 기존 경로(동작 0 변화).
operational_defaults 값은 코드 default와 동일하므로 flag ON 발화 == 코드 발화(1:1).
"""
from uuid import uuid4

import pytest

from app.core import config
from app.db.operational_defaults_seed import OPERATIONAL_DEFAULTS
from app.engine.rule_engine import RuleContext
from app.engine.rules._common import resolve
from app.engine.threshold_resolver import gov_resolve_thresholds


def _ctx(*, rule_configs=None, operational_defaults=None, benchmarks=None) -> RuleContext:
    return RuleContext(
        farm_id=uuid4(), country="ZZ", kpi={}, benchmarks=benchmarks or {}, sow_counts={},
        extra={"rule_configs": rule_configs or {}, "operational_defaults": operational_defaults or {}},
    )


def test_gov_rule_config_priority():
    ctx = _ctx(rule_configs={"r": {"warning": 99, "critical": 88}},
              operational_defaults={"r": {"warning": 50, "critical": 70}})
    w, c, src = gov_resolve_thresholds(ctx, "r", 10, 5)
    assert (w, c, src) == (99, 88, "rule_config")


def test_gov_operational_default_fallback():
    ctx = _ctx(operational_defaults={"r": {"warning": 50, "critical": 70}})
    w, c, src = gov_resolve_thresholds(ctx, "r", 10, 5)
    assert (w, c, src) == (50, 70, "operational_default")


def test_gov_code_default_fallback():
    ctx = _ctx()
    w, c, src = gov_resolve_thresholds(ctx, "r", 10, 5)
    assert (w, c, src) == (10, 5, "code_default")


def test_gov_no_default_metric_values_used():
    """flag ON 경로는 ctx.benchmarks(옛 default_metric_values)를 보지 않는다(§14.6)."""
    ctx = _ctx(benchmarks={"KPI": {"warning": 1, "critical": 2}})
    w, c, src = gov_resolve_thresholds(ctx, "r", 10, 5)
    assert (w, c) == (10, 5) and src == "code_default"  # benchmark 무시


@pytest.mark.parametrize("d", OPERATIONAL_DEFAULTS, ids=[d["rule_id"] for d in OPERATIONAL_DEFAULTS])
def test_1to1_operational_default_equals_code(d):
    """flag ON: operational_defaults 값이 코드 default와 1:1 (발화 불변 근거)."""
    opd = {d["rule_id"]: {"warning": d["warning"], "critical": d["critical"]}}
    ctx = _ctx(operational_defaults=opd)
    # 코드 default를 일부러 다르게 줘도 operational_default가 우선 → 레지스트리 값이 나와야
    w, c, src = gov_resolve_thresholds(ctx, d["rule_id"], -1, -1)
    assert (w, c, src) == (d["warning"], d["critical"], "operational_default")


def test_flag_off_uses_legacy_benchmark(monkeypatch):
    """flag OFF: _common.resolve는 기존(rule_config→benchmark→code) — operational_defaults 무시."""
    monkeypatch.setattr(config.settings, "use_governance_benchmarks", False)
    ctx = _ctx(benchmarks={"KPI": {"warning": 7, "critical": 3}},
               operational_defaults={"r": {"warning": 50, "critical": 70}})
    w, c = resolve(ctx, "r", "KPI", 10, 5)
    assert (w, c) == (7, 3)  # benchmark 사용(legacy), operational_defaults 아님


def test_flag_on_resolve_uses_operational(monkeypatch):
    """flag ON: _common.resolve가 operational_defaults 사용, benchmark 무시."""
    monkeypatch.setattr(config.settings, "use_governance_benchmarks", True)
    ctx = _ctx(benchmarks={"KPI": {"warning": 7, "critical": 3}},
               operational_defaults={"r": {"warning": 50, "critical": 70}})
    w, c = resolve(ctx, "r", "KPI", 10, 5)
    assert (w, c) == (50, 70)  # operational_default 사용, benchmark(7/3) 무시
