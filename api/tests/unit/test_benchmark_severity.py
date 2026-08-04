"""벤치마크 발화/심각도 결정 로직 (app/engine/benchmark_thresholds.py) 순수 매트릭스.

통합테스트는 실제 KPI 데이터 경로만 밟음 — 여기선 방향×경계×임계우선 전체 매트릭스와
발화 침묵(100배 오류·미검증 기준 방지) 경계를 직접 고정.
"""
import pytest

from app.engine.benchmark_thresholds import (
    CRITICAL,
    OK,
    WARNING,
    can_fire,
    severity_for,
    should_generate_insight,
)


class TestSeverityHigherBetter:
    def test_ok_above_warning(self):
        assert severity_for("higher_better", 30, warning_min=24, critical_min=20) == OK

    def test_boundary_equal_warning_is_ok(self):
        # value == warning_min 은 '< warning_min' 아님 → OK(경계 포함 정상)
        assert severity_for("higher_better", 24, warning_min=24, critical_min=20) == OK

    def test_warning_band(self):
        assert severity_for("higher_better", 23, warning_min=24, critical_min=20) == WARNING

    def test_boundary_equal_critical_is_warning(self):
        assert severity_for("higher_better", 20, warning_min=24, critical_min=20) == WARNING

    def test_critical_takes_precedence(self):
        # 둘 다 초과해도 critical 우선
        assert severity_for("higher_better", 15, warning_min=24, critical_min=20) == CRITICAL

    def test_none_thresholds_always_ok(self):
        assert severity_for("higher_better", 0) == OK


class TestSeverityLowerBetter:
    def test_ok_below_warning(self):
        assert severity_for("lower_better", 40, warning_max=50, critical_max=60) == OK

    def test_boundary_equal_warning_is_ok(self):
        assert severity_for("lower_better", 50, warning_max=50, critical_max=60) == OK

    def test_warning_band(self):
        assert severity_for("lower_better", 51, warning_max=50, critical_max=60) == WARNING

    def test_critical_over_max(self):
        assert severity_for("lower_better", 61, warning_max=50, critical_max=60) == CRITICAL


class TestSeverityRangeTarget:
    KW = dict(warning_min=10, warning_max=20, critical_min=5, critical_max=25)

    def test_ok_in_range(self):
        assert severity_for("range_target", 15, **self.KW) == OK

    def test_warning_below_and_above(self):
        assert severity_for("range_target", 8, **self.KW) == WARNING
        assert severity_for("range_target", 22, **self.KW) == WARNING

    def test_critical_below_and_above(self):
        assert severity_for("range_target", 4, **self.KW) == CRITICAL
        assert severity_for("range_target", 26, **self.KW) == CRITICAL


def test_unknown_direction_raises():
    with pytest.raises(ValueError):
        severity_for("sideways", 10, warning_min=1)


class TestCanFireSilence:
    def test_all_good_fires(self):
        assert can_fire("verified", "exact", "per_litter") is True

    def test_missing_value_scale_silences(self):
        # value_scale 없으면 비교 금지(100배 오류 방지)
        assert can_fire("verified", "exact", None) is False

    def test_unfireable_status_silences(self):
        assert can_fire("missing", "exact", "per_litter") is False

    def test_incompatible_comparison_silences(self):
        assert can_fire("verified", "incompatible", "per_litter") is False


def test_should_generate_insight_mirrors_firing_guards():
    assert should_generate_insight("exact", "verified") is True
    assert should_generate_insight("unknown", "verified") is False
    assert should_generate_insight("exact", "missing") is False
