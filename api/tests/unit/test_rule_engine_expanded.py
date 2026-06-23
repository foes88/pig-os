"""
확장 Rule Engine 단위 테스트 — litter / grow-finish / abortion 규칙 + 임계 해석.
DB 없이 RuleContext를 직접 생성해 규칙 함수를 호출(국가 중립 로직, 임계만 조정).
"""
import asyncio
from uuid import uuid4

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules._common import resolve, sev_above, sev_below
from app.engine.rules.grow_finish import _adg_low, _fcr_high, _finish_mortality_high
from app.engine.rules.litter import (
    _born_alive_low,
    _lactation_long,
    _lactation_short,
    _mummified_high,
    _stillborn_high,
    _total_born_low,
    _weaned_low,
)
from app.engine.rules.reproduction import _abortion_rate_high, _summer_infertility
from app.engine.rules.sow_herd import (
    _accident_parity_skew,
    _culling_rate_high,
    _parity_high_ratio,
    _replacement_rate_abnormal,
    _second_litter_slump,
    _sow_mortality_high,
)


def ctx(kpi: dict, rule_configs: dict | None = None, benchmarks: dict | None = None) -> RuleContext:
    return RuleContext(
        farm_id=uuid4(), country="KR", kpi=kpi,
        benchmarks=benchmarks or {}, sow_counts={"OPEN": 50},
        extra={"rule_configs": rule_configs or {}},
    )


def run(coro):
    return asyncio.run(coro)


# ── severity 헬퍼 ───────────────────────────────────────────────────────────────
class TestSeverityHelpers:
    def test_above(self):
        assert sev_above(5.0, 8.0, 12.0) is None
        assert sev_above(9.0, 8.0, 12.0) == Severity.WARNING
        assert sev_above(13.0, 8.0, 12.0) == Severity.CRITICAL

    def test_below(self):
        assert sev_below(12.0, 11.0, 10.0) is None
        assert sev_below(10.5, 11.0, 10.0) == Severity.WARNING
        assert sev_below(9.0, 11.0, 10.0) == Severity.CRITICAL


# ── 임계 해석 우선순위: rule_config > benchmark > code default ──────────────────
class TestResolvePrecedence:
    def test_code_default_when_nothing(self):
        assert resolve(ctx({}), "stillborn.rate_high", "STILLBORN_RATE", 8.0, 12.0) == (8.0, 12.0)

    def test_benchmark_overrides_default(self):
        c = ctx({}, benchmarks={"STILLBORN_RATE": {"warning": 6.0, "critical": 9.0}})
        assert resolve(c, "stillborn.rate_high", "STILLBORN_RATE", 8.0, 12.0) == (6.0, 9.0)

    def test_rule_config_wins_over_benchmark(self):
        c = ctx({}, rule_configs={"stillborn.rate_high": {"warning": 5.0, "critical": 7.0}},
                benchmarks={"STILLBORN_RATE": {"warning": 6.0, "critical": 9.0}})
        assert resolve(c, "stillborn.rate_high", "STILLBORN_RATE", 8.0, 12.0) == (5.0, 7.0)


# ── litter 규칙 ─────────────────────────────────────────────────────────────────
class TestLitterRules:
    def test_stillborn_none_when_normal(self):
        assert run(_stillborn_high(ctx({"STILLBORN_RATE": 5.0}))) == []

    def test_stillborn_warning(self):
        f = run(_stillborn_high(ctx({"STILLBORN_RATE": 10.0})))
        assert f and f[0].severity == Severity.WARNING

    def test_stillborn_critical(self):
        f = run(_stillborn_high(ctx({"STILLBORN_RATE": 15.0})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_mummified_critical(self):
        f = run(_mummified_high(ctx({"MUMMIFIED_RATE": 5.0})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_born_alive_low_below(self):
        f = run(_born_alive_low(ctx({"BORN_ALIVE": 9.5})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_born_alive_ok(self):
        assert run(_born_alive_low(ctx({"BORN_ALIVE": 12.0}))) == []

    def test_weaned_low_warning(self):
        f = run(_weaned_low(ctx({"WEANED_COUNT": 9.5})))
        assert f and f[0].severity == Severity.WARNING

    def test_lactation_short(self):
        f = run(_lactation_short(ctx({"WEANING_AGE": 17.0})))
        assert f and f[0].severity == Severity.WARNING

    def test_lactation_long(self):
        f = run(_lactation_long(ctx({"WEANING_AGE": 30.0})))
        assert f and f[0].severity == Severity.WARNING

    def test_missing_kpi_no_finding(self):
        assert run(_stillborn_high(ctx({}))) == []
        assert run(_weaned_low(ctx({}))) == []


# ── grow-finish 규칙 ────────────────────────────────────────────────────────────
class TestGrowFinishRules:
    def test_fcr_high_warning(self):
        f = run(_fcr_high(ctx({"FCR": 3.1})))
        assert f and f[0].severity == Severity.WARNING

    def test_fcr_high_critical(self):
        f = run(_fcr_high(ctx({"FCR": 3.5})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_fcr_ok(self):
        assert run(_fcr_high(ctx({"FCR": 2.7}))) == []

    def test_adg_low_critical(self):
        f = run(_adg_low(ctx({"ADG": 500.0})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_finish_mortality_high(self):
        f = run(_finish_mortality_high(ctx({"FINISH_MORTALITY": 9.0})))
        assert f and f[0].severity == Severity.CRITICAL


# ── abortion 규칙 ───────────────────────────────────────────────────────────────
class TestAbortionRule:
    def test_abortion_ok(self):
        assert run(_abortion_rate_high(ctx({"ABORTION_RATE": 2.0}))) == []

    def test_abortion_warning(self):
        f = run(_abortion_rate_high(ctx({"ABORTION_RATE": 4.0})))
        assert f and f[0].severity == Severity.WARNING

    def test_abortion_critical_has_disease_cause(self):
        f = run(_abortion_rate_high(ctx({"ABORTION_RATE": 6.0})))
        assert f and f[0].severity == Severity.CRITICAL
        assert "possible_abortive_disease" in f[0].causes


# ── 모돈군 구조 규칙 ────────────────────────────────────────────────────────────
class TestSowHerdRules:
    def test_culling_ok(self):
        assert run(_culling_rate_high(ctx({"CULLING_RATE": 40.0}))) == []

    def test_culling_warning(self):
        f = run(_culling_rate_high(ctx({"CULLING_RATE": 50.0})))
        assert f and f[0].severity == Severity.WARNING

    def test_culling_critical(self):
        f = run(_culling_rate_high(ctx({"CULLING_RATE": 60.0})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_sow_mortality_critical(self):
        f = run(_sow_mortality_high(ctx({"SOW_MORTALITY": 13.0})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_parity_high_ratio_warning(self):
        f = run(_parity_high_ratio(ctx({"HIGH_PARITY_RATIO": 25.0})))
        assert f and f[0].severity == Severity.WARNING

    def test_total_born_low(self):
        f = run(_total_born_low(ctx({"TOTAL_BORN": 10.5})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_missing_no_finding(self):
        assert run(_culling_rate_high(ctx({}))) == []
        assert run(_parity_high_ratio(ctx({}))) == []


# ── Phase B2: herd dynamics 탐지 규칙 ───────────────────────────────────────────
class TestHerdDynamicsRules:
    def test_replacement_high_warning(self):
        f = run(_replacement_rate_abnormal(ctx({"REPLACEMENT_RATE": 55.0})))
        assert f and f[0].severity == Severity.WARNING and "excessive_sow_replacement" in f[0].causes

    def test_replacement_high_critical(self):
        f = run(_replacement_rate_abnormal(ctx({"REPLACEMENT_RATE": 65.0})))
        assert f and f[0].severity == Severity.CRITICAL

    def test_replacement_low_warning(self):
        f = run(_replacement_rate_abnormal(ctx({"REPLACEMENT_RATE": 25.0})))
        assert f and "insufficient_sow_replacement" in f[0].causes

    def test_replacement_ok(self):
        assert run(_replacement_rate_abnormal(ctx({"REPLACEMENT_RATE": 40.0}))) == []

    def test_second_litter_slump(self):
        assert run(_second_litter_slump(ctx({"SECOND_LITTER_DROP": 1.0}))) == []
        f = run(_second_litter_slump(ctx({"SECOND_LITTER_DROP": 2.0})))
        assert f and f[0].severity == Severity.WARNING
        f2 = run(_second_litter_slump(ctx({"SECOND_LITTER_DROP": 3.0})))
        assert f2 and f2[0].severity == Severity.CRITICAL

    def test_accident_parity_skew(self):
        assert run(_accident_parity_skew(ctx({"ACCIDENT_P1_RATIO": 30.0}))) == []
        f = run(_accident_parity_skew(ctx({"ACCIDENT_P1_RATIO": 45.0})))
        assert f and f[0].severity == Severity.WARNING
        f2 = run(_accident_parity_skew(ctx({"ACCIDENT_P1_RATIO": 60.0})))
        assert f2 and "possible_reproductive_disease_in_gilts" in f2[0].causes

    def test_summer_infertility(self):
        assert run(_summer_infertility(ctx({"SUMMER_FARROW_DROP": 4.0}))) == []
        f = run(_summer_infertility(ctx({"SUMMER_FARROW_DROP": 8.0})))
        assert f and f[0].severity == Severity.WARNING
        f2 = run(_summer_infertility(ctx({"SUMMER_FARROW_DROP": 12.0})))
        assert f2 and f2[0].severity == Severity.CRITICAL

    def test_missing_no_finding(self):
        assert run(_replacement_rate_abnormal(ctx({}))) == []
        assert run(_summer_infertility(ctx({}))) == []


# ── 운영자 임계 조정 반영(국가별 KPI 조정 구조) ────────────────────────────────
class TestOperatorOverride:
    def test_operator_tightens_threshold(self):
        # 기본 8.0이면 7.0은 정상이지만, 운영자가 6.0으로 조이면 경고
        assert run(_stillborn_high(ctx({"STILLBORN_RATE": 7.0}))) == []
        c = ctx({"STILLBORN_RATE": 7.0},
                rule_configs={"stillborn.rate_high": {"warning": 6.0, "critical": 9.0}})
        f = run(_stillborn_high(c))
        assert f and f[0].severity == Severity.WARNING
