"""소형 엔진 룰 3모듈 (boar·batch·composite) — 직접 테스트 없음.

- boar.farrow_rate_low: ctx.extra['boar_stats'] 개체별 sev_below(65/55)
- batch.aiao_detect: ctx.kpi 요일집중도 임계(≥50) 시 배치운영 INFO
- composite: 2-pass — ctx.extra['_prior_findings']로 농가등급(RYG)·최약 KPI
governance OFF, RuleContext 직접구성(DB 불필요).
"""
import uuid

import pytest

from app.engine.rule_engine import Finding, RuleContext, Severity
from app.engine.rules import batch, boar, composite

pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
def _governance_off(monkeypatch):
    monkeypatch.setattr("app.engine.threshold_resolver.settings.use_governance_benchmarks", False)


def _ctx(kpi=None, extra=None) -> RuleContext:
    return RuleContext(
        farm_id=uuid.UUID("00000000-0000-0000-0000-0000000000f4"),
        country="KR", kpi=kpi or {}, benchmarks={}, sow_counts={}, extra=extra or {},
    )


def _finding(sev: Severity, gap=0.0, rule_id="r", kpi="K") -> Finding:
    return Finding(
        rule_id=rule_id, kpi=kpi, severity=sev, current_value=1.0, target_value=2.0,
        causes=[], recommended_actions=["a", "b"], detail={"normalized_gap": gap},
    )


class TestBoar:
    async def test_empty_stats_returns_empty(self):
        assert await boar._boar_farrow_rate_low(_ctx(extra={"boar_stats": []})) == []

    async def test_low_fr_fires_per_boar(self):
        ctx = _ctx(extra={"boar_stats": [
            {"fr": 70, "boar_id": "B1"},            # ≥65 정상 → 미발화
            {"fr": 50, "boar_id": "B2", "ear_tag": "E2", "matings": 12},  # <55 CRITICAL
        ]})
        out = await boar._boar_farrow_rate_low(ctx)
        assert len(out) == 1
        assert out[0].severity == Severity.CRITICAL
        assert out[0].detail["boar_id"] == "B2"

    async def test_warning_band_and_none_fr_skipped(self):
        ctx = _ctx(extra={"boar_stats": [{"fr": 60, "boar_id": "B3"}, {"fr": None, "boar_id": "B4"}]})
        out = await boar._boar_farrow_rate_low(ctx)
        assert len(out) == 1 and out[0].severity == Severity.WARNING  # 60<65, None은 skip


class TestBatch:
    async def test_missing_kpi_empty(self):
        assert await batch._batch_aiao_detect(_ctx()) == []

    async def test_below_threshold_silent(self):
        assert await batch._batch_aiao_detect(_ctx(kpi={"BATCH_DOW_CONCENTRATION": 40})) == []

    async def test_at_or_above_threshold_info(self):
        # 경계 포함(v < threshold 만 침묵) — 50 이상이면 INFO 발화
        for v in (50, 65):
            out = await batch._batch_aiao_detect(_ctx(kpi={"BATCH_DOW_CONCENTRATION": v}))
            assert len(out) == 1 and out[0].severity == Severity.INFO


class TestCompositeHealthClass:
    async def test_green_when_no_issues(self):
        out = await composite._farm_health_class(_ctx(extra={"_prior_findings": []}))
        assert out[0].detail["grade"] == "GREEN" and out[0].severity == Severity.INFO

    async def test_yellow_on_single_warning(self):
        out = await composite._farm_health_class(_ctx(extra={"_prior_findings": [_finding(Severity.WARNING)]}))
        assert out[0].detail["grade"] == "YELLOW"

    async def test_red_on_critical_or_three_warnings(self):
        crit = await composite._farm_health_class(_ctx(extra={"_prior_findings": [_finding(Severity.CRITICAL)]}))
        assert crit[0].detail["grade"] == "RED"
        warns = await composite._farm_health_class(
            _ctx(extra={"_prior_findings": [_finding(Severity.WARNING) for _ in range(3)]}))
        assert warns[0].detail["grade"] == "RED"


class TestCompositeWeakestKpi:
    async def test_no_issues_empty(self):
        assert await composite._farm_weakest_kpi(_ctx(extra={"_prior_findings": [_finding(Severity.INFO)]})) == []

    async def test_picks_highest_severity(self):
        prior = [_finding(Severity.WARNING, gap=0.9, rule_id="warn"), _finding(Severity.CRITICAL, gap=0.1, rule_id="crit")]
        out = await composite._farm_weakest_kpi(_ctx(extra={"_prior_findings": prior}))
        assert out[0].detail["weakest_rule"] == "crit"  # severity 우선
