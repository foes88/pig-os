"""Unit tests for Phase 3 reproduction rules + PSY grade."""
import asyncio
from uuid import uuid4

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules.base import _psy_analysis, psy_grade
from app.engine.rules.reproduction import _pwmr_high, _rts_rate_high, _wsi_overdue


def make_ctx(kpi=None, benchmarks=None, extra=None) -> RuleContext:
    return RuleContext(
        farm_id=uuid4(),
        country="KR",
        kpi=kpi or {},
        benchmarks=benchmarks or {},
        sow_counts={"OPEN": 100},
        extra=extra or {},
    )


class TestWsiRule:
    def test_none_no_finding(self):
        assert asyncio.run(_wsi_overdue(make_ctx(kpi={"WSI": None}))) == []

    def test_boundary_10_ok(self):
        assert asyncio.run(_wsi_overdue(make_ctx(kpi={"WSI": 10.0}))) == []

    def test_11_warning(self):
        f = asyncio.run(_wsi_overdue(make_ctx(kpi={"WSI": 11.0})))
        assert f[0].severity == Severity.WARNING

    def test_boundary_14_warning(self):
        f = asyncio.run(_wsi_overdue(make_ctx(kpi={"WSI": 14.0})))
        assert f[0].severity == Severity.WARNING

    def test_15_critical(self):
        f = asyncio.run(_wsi_overdue(make_ctx(kpi={"WSI": 15.0})))
        assert f[0].severity == Severity.CRITICAL

    def test_benchmark_override(self):
        ctx = make_ctx(kpi={"WSI": 6.0}, benchmarks={"WSI": {"warning": 5.0, "critical": 8.0}})
        f = asyncio.run(_wsi_overdue(ctx))
        assert f[0].severity == Severity.WARNING


class TestRtsRule:
    def test_boundary_15_ok(self):
        assert asyncio.run(_rts_rate_high(make_ctx(kpi={"RTS_RATE": 15.0}))) == []

    def test_16_warning(self):
        f = asyncio.run(_rts_rate_high(make_ctx(kpi={"RTS_RATE": 16.0})))
        assert f[0].severity == Severity.WARNING

    def test_25_warning(self):
        f = asyncio.run(_rts_rate_high(make_ctx(kpi={"RTS_RATE": 25.0})))
        assert f[0].severity == Severity.WARNING

    def test_26_critical(self):
        f = asyncio.run(_rts_rate_high(make_ctx(kpi={"RTS_RATE": 26.0})))
        assert f[0].severity == Severity.CRITICAL


class TestPwmrRule:
    def test_from_kpi_warning(self):
        f = asyncio.run(_pwmr_high(make_ctx(kpi={"PWMR": 16.0})))
        assert f[0].severity == Severity.WARNING
        assert f[0].detail["method"] == "A"

    def test_critical(self):
        f = asyncio.run(_pwmr_high(make_ctx(kpi={"PWMR": 21.0})))
        assert f[0].severity == Severity.CRITICAL

    def test_method_a_computed(self):
        # deaths=3, weaned=12 → 3/15 = 20% → CRITICAL? 20 not >20 → WARNING boundary
        f = asyncio.run(_pwmr_high(make_ctx(extra={"deaths": 3, "weaned": 12, "pwmr_method": "A"})))
        assert f[0].severity == Severity.WARNING
        assert abs(f[0].current_value - 20.0) < 0.01

    def test_method_b_computed(self):
        # avg_tb=14, avg_weaned=11 → (3/14)*100 = 21.4% → CRITICAL
        f = asyncio.run(
            _pwmr_high(make_ctx(extra={"avg_tb": 14.0, "avg_weaned": 11.0, "pwmr_method": "B"}))
        )
        assert f[0].severity == Severity.CRITICAL
        assert f[0].detail["method"] == "B"

    def test_no_data_no_finding(self):
        assert asyncio.run(_pwmr_high(make_ctx())) == []


class TestPsyGrade:
    def test_grades(self):
        assert psy_grade(30) == "Excellence"
        assert psy_grade(28) == "Excellence"
        assert psy_grade(27.9) == "Advanced"
        assert psy_grade(24) == "Advanced"
        assert psy_grade(23.9) == "Stable"
        assert psy_grade(20) == "Stable"
        assert psy_grade(19.9) == "Developing"
        assert psy_grade(None) is None

    def test_grade_attached_to_finding(self):
        ctx = make_ctx(
            kpi={"PSY": 19.0},
            benchmarks={"PSY": {"warning": 24.0, "critical": 20.0, "direction": "below"}},
        )
        f = asyncio.run(_psy_analysis(ctx))
        assert f[0].grade == "Developing"
