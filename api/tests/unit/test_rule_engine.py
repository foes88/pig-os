"""
Rule Engine 단위 테스트 — 국가별 임계값 동작 검증.
DB 없이 RuleContext를 직접 생성해 규칙 함수를 호출.
"""
import asyncio
from uuid import uuid4

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules.base import (
    _farrowing_rate_low,
    _npd_overdue,
    _psy_analysis,
    _severity_from_bench,
)

# ── helpers ───────────────────────────────────────────────────────────────────

def make_ctx(
    country: str = "KR",
    kpi: dict | None = None,
    benchmarks: dict | None = None,
) -> RuleContext:
    return RuleContext(
        farm_id=uuid4(),
        country=country,
        kpi=kpi or {},
        benchmarks=benchmarks or {},
        sow_counts={"ACTIVE": 100},
    )


KR_PSY_BENCH  = {"warning": 24.0, "critical": 20.0, "avg": 23.5, "direction": "below"}
VN_PSY_BENCH  = {"warning": 18.0, "critical": 15.0, "avg": 17.5, "direction": "below"}
KR_NPD_BENCH  = {"warning": 35.0, "critical": 50.0, "avg": 42.0, "direction": "above"}
CN_NPD_BENCH  = {"warning": 45.0, "critical": 62.0, "avg": 52.0, "direction": "above"}
KR_FR_BENCH   = {"warning": 85.0, "critical": 75.0, "avg": 83.0, "direction": "below"}


# ── _severity_from_bench ──────────────────────────────────────────────────────

class TestSeverityFromBench:
    def test_below_ok_when_above_warning(self):
        assert _severity_from_bench(25.0, KR_PSY_BENCH, "below") is None

    def test_below_warning_when_between_thresholds(self):
        assert _severity_from_bench(22.0, KR_PSY_BENCH, "below") == Severity.WARNING

    def test_below_critical_when_under_critical(self):
        assert _severity_from_bench(19.0, KR_PSY_BENCH, "below") == Severity.CRITICAL

    def test_above_ok_when_below_warning(self):
        assert _severity_from_bench(30.0, KR_NPD_BENCH, "above") is None

    def test_above_warning_when_between_thresholds(self):
        assert _severity_from_bench(40.0, KR_NPD_BENCH, "above") == Severity.WARNING

    def test_above_critical_when_over_critical(self):
        assert _severity_from_bench(55.0, KR_NPD_BENCH, "above") == Severity.CRITICAL

    def test_no_warning_threshold_returns_none(self):
        assert _severity_from_bench(10.0, {}, "below") is None


# ── PSY rules — country thresholds ───────────────────────────────────────────

class TestPsyRule:
    def test_kr_psy_24_ok(self):
        ctx = make_ctx("KR", kpi={"PSY": 24.0}, benchmarks={"PSY": KR_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert findings == []

    def test_kr_psy_22_warning(self):
        ctx = make_ctx("KR", kpi={"PSY": 22.0}, benchmarks={"PSY": KR_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert len(findings) == 1
        assert findings[0].severity == Severity.WARNING

    def test_kr_psy_19_critical(self):
        ctx = make_ctx("KR", kpi={"PSY": 19.0}, benchmarks={"PSY": KR_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert findings[0].severity == Severity.CRITICAL

    def test_vn_psy_19_ok(self):
        # PSY=19 is CRITICAL in KR but OK in VN — threshold matters
        ctx = make_ctx("VN", kpi={"PSY": 19.0}, benchmarks={"PSY": VN_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert findings == []

    def test_vn_psy_17_warning(self):
        ctx = make_ctx("VN", kpi={"PSY": 17.0}, benchmarks={"PSY": VN_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert findings[0].severity == Severity.WARNING

    def test_vn_psy_14_critical(self):
        ctx = make_ctx("VN", kpi={"PSY": 14.0}, benchmarks={"PSY": VN_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert findings[0].severity == Severity.CRITICAL

    def test_psy_none_returns_info(self):
        ctx = make_ctx("KR", kpi={"PSY": None}, benchmarks={"PSY": KR_PSY_BENCH})
        findings = asyncio.run(_psy_analysis(ctx))
        assert findings[0].severity == Severity.INFO
        assert findings[0].rule_id == "psy.no_data"

    def test_high_npd_adds_cross_kpi_cause(self):
        ctx = make_ctx(
            "KR",
            kpi={"PSY": 22.0, "NPD": 40.0},
            benchmarks={"PSY": KR_PSY_BENCH, "NPD": KR_NPD_BENCH},
        )
        findings = asyncio.run(_psy_analysis(ctx))
        assert any("non_productive" in c for c in findings[0].causes)


# ── NPD rules — country thresholds ───────────────────────────────────────────

class TestNpdRule:
    def test_kr_npd_30_ok(self):
        ctx = make_ctx("KR", kpi={"NPD": 30.0}, benchmarks={"NPD": KR_NPD_BENCH})
        assert asyncio.run(_npd_overdue(ctx)) == []

    def test_kr_npd_40_warning(self):
        ctx = make_ctx("KR", kpi={"NPD": 40.0}, benchmarks={"NPD": KR_NPD_BENCH})
        findings = asyncio.run(_npd_overdue(ctx))
        assert findings[0].severity == Severity.WARNING

    def test_kr_npd_55_critical(self):
        ctx = make_ctx("KR", kpi={"NPD": 55.0}, benchmarks={"NPD": KR_NPD_BENCH})
        findings = asyncio.run(_npd_overdue(ctx))
        assert findings[0].severity == Severity.CRITICAL

    def test_cn_npd_40_ok(self):
        # NPD=40 is WARNING in KR but OK in CN
        ctx = make_ctx("CN", kpi={"NPD": 40.0}, benchmarks={"NPD": CN_NPD_BENCH})
        assert asyncio.run(_npd_overdue(ctx)) == []

    def test_cn_npd_50_warning(self):
        ctx = make_ctx("CN", kpi={"NPD": 50.0}, benchmarks={"NPD": CN_NPD_BENCH})
        findings = asyncio.run(_npd_overdue(ctx))
        assert findings[0].severity == Severity.WARNING

    def test_npd_none_no_finding(self):
        ctx = make_ctx("KR", kpi={"NPD": None}, benchmarks={"NPD": KR_NPD_BENCH})
        assert asyncio.run(_npd_overdue(ctx)) == []

    def test_critical_npd_adds_extended_cause(self):
        ctx = make_ctx("KR", kpi={"NPD": 55.0}, benchmarks={"NPD": KR_NPD_BENCH})
        findings = asyncio.run(_npd_overdue(ctx))
        assert any("extended" in c for c in findings[0].causes)


# ── Farrowing rate rules ──────────────────────────────────────────────────────

class TestFarrowingRateRule:
    def test_kr_fr_86_ok(self):
        ctx = make_ctx("KR", kpi={"FARROWING_RATE": 86.0}, benchmarks={"FARROWING_RATE": KR_FR_BENCH})
        assert asyncio.run(_farrowing_rate_low(ctx)) == []

    def test_kr_fr_80_warning(self):
        ctx = make_ctx("KR", kpi={"FARROWING_RATE": 80.0}, benchmarks={"FARROWING_RATE": KR_FR_BENCH})
        findings = asyncio.run(_farrowing_rate_low(ctx))
        assert findings[0].severity == Severity.WARNING

    def test_kr_fr_70_critical(self):
        ctx = make_ctx("KR", kpi={"FARROWING_RATE": 70.0}, benchmarks={"FARROWING_RATE": KR_FR_BENCH})
        findings = asyncio.run(_farrowing_rate_low(ctx))
        assert findings[0].severity == Severity.CRITICAL

    def test_fr_none_no_finding(self):
        ctx = make_ctx("KR", kpi={"FARROWING_RATE": None}, benchmarks={"FARROWING_RATE": KR_FR_BENCH})
        assert asyncio.run(_farrowing_rate_low(ctx)) == []

    def test_critical_fr_adds_disease_cause(self):
        ctx = make_ctx("KR", kpi={"FARROWING_RATE": 70.0}, benchmarks={"FARROWING_RATE": KR_FR_BENCH})
        findings = asyncio.run(_farrowing_rate_low(ctx))
        assert any("disease" in c for c in findings[0].causes)
