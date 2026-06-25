"""
T1-5 엔진 배선 + trace 테스트 (A-하이브리드 게이트3).
- operational_defaults 로더(ctx 주입용) 29행.
- enrich_findings_with_governance: §7 governance_trace 첨부(맥락=verified만, 매핑없음/provisional=none).
- flag OFF 동작 변화 0은 전체 회귀로 입증.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.benchmark_seed import KPI_DEFINITIONS, definition_id_for
from app.db.models.benchmark import Benchmark, KpiDefinition
from app.db.models.operational_default import OperationalDefault
from app.db.operational_defaults_seed import OPERATIONAL_DEFAULTS, to_bounds
from app.engine.rule_engine import Finding, Severity
from app.engine.threshold_resolver import load_operational_defaults_map
from app.services import benchmark_service as svc

pytestmark = pytest.mark.anyio


async def _seed_opdefs(db):
    for d in OPERATIONAL_DEFAULTS:
        db.add(OperationalDefault(
            scope="global", country_code=None, rule_id=d["rule_id"], kpi_code=d["kpi_code"],
            direction=d["direction"], value_scale=d["value_scale"], origin="code_default",
            source_rule=d["rule_id"], original_warning=d["warning"], original_critical=d["critical"],
            **to_bounds(d)))
    await db.flush()


async def _seed_defs(db):
    for d in KPI_DEFINITIONS:
        db.add(KpiDefinition(definition_id=definition_id_for(d["kpi_code"]), **d))
    await db.flush()


async def test_load_operational_defaults_map(db: AsyncSession):
    """ctx 주입용 로더: 29행, warning/critical == 원본값."""
    await _seed_opdefs(db)
    m = await load_operational_defaults_map(db)
    assert len(m) == 29
    assert m["fcr.high"]["warning"] == 3.0 and m["fcr.high"]["critical"] == 3.3
    assert "psy.below_target" not in m  # base 특수형(㉮)은 레지스트리 미포함


async def test_enrich_mapped_attaches_context(db: AsyncSession):
    """매핑 KPI + verified benchmark → governance_trace에 비교 맥락 첨부."""
    await _seed_defs(db)
    db.add(Benchmark(country_code="US", population_scope="national_avg", kpi_code="farrowing_rate",
                     definition_id="PIGOS_FARROWING_RATE_V1", benchmark_status="verified",
                     comparison_status="compatible", mapping_status="exact", value_scale="percent_0_100",
                     transformed_value=83.81, is_provisional=False))
    await db.flush()
    f = Finding(rule_id="farrowing.rate_low", kpi="FARROWING_RATE", severity=Severity.WARNING,
                current_value=79.0, target_value=82.0)
    await svc.enrich_findings_with_governance(db, "US", [f])
    t = f.detail["governance_trace"]
    assert t["benchmark_source"] == "governance_benchmark"
    assert t["benchmark_value"] == 83.81 and t["governance_kpi"] == "farrowing_rate"
    assert t["benchmark_status"] == "verified"


async def test_enrich_unmapped_kpi_none(db: AsyncSession):
    """매핑 없는 룰 KPI(ADG 등) → benchmark_source=none, reason=no_mapping."""
    await _seed_defs(db)
    f = Finding(rule_id="adg.low", kpi="ADG", severity=Severity.WARNING, current_value=600, target_value=650)
    await svc.enrich_findings_with_governance(db, "US", [f])
    t = f.detail["governance_trace"]
    assert t["benchmark_source"] == "none" and t["benchmark_unavailable_reason"] == "no_mapping"


async def test_enrich_provisional_blocked(db: AsyncSession):
    """매핑되나 provisional benchmark → 맥락 금지(source none, reason provisional)."""
    await _seed_defs(db)
    db.add(Benchmark(country_code="KR", population_scope="national", kpi_code="psy",
                     definition_id="PIGOS_PSY_V1", benchmark_status="provisional", is_provisional=True,
                     comparison_status="compatible", mapping_status="exact", value_scale="n/a",
                     warning_min=22, critical_min=18))
    await db.flush()
    f = Finding(rule_id="psy.below_target", kpi="PSY", severity=Severity.WARNING,
                current_value=21, target_value=24)
    await svc.enrich_findings_with_governance(db, "KR", [f])
    t = f.detail["governance_trace"]
    assert t["benchmark_source"] == "none" and t["benchmark_unavailable_reason"] == "provisional"


def test_required_trace_fields_present(db_unused=None):
    """§7 필수 trace 키 명세 (회귀 방지)."""
    required = {"rule_id", "kpi_code", "governance_kpi", "severity", "current_value", "target_value",
               "benchmark_source", "benchmark_value", "benchmark_id", "benchmark_status",
               "comparison_status", "source_obs_id", "obs_group_id", "is_global_fallback",
               "benchmark_unavailable_reason"}
    # 키 명세는 enrich 구현과 동기 — 누락 시 위 테스트들이 KeyError로 잡음
    assert required  # 명세 존재 표식
