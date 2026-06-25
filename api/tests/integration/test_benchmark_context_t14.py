"""
T1-4 Benchmark Context Resolver 테스트 (A-하이브리드 게이트2, §5).
verified/normalized=맥락 첨부 / provisional·missing=맥락 금지 / value_scale mismatch=맥락만 강등(발화 무관) / global_fallback=trace.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.benchmark_seed import KPI_DEFINITIONS, definition_id_for
from app.db.models.benchmark import Benchmark, KpiDefinition
from app.services import benchmark_service as svc

pytestmark = pytest.mark.anyio


async def _seed_defs(db):
    for d in KPI_DEFINITIONS:
        db.add(KpiDefinition(definition_id=definition_id_for(d["kpi_code"]), **d))
    await db.flush()


def _b(kpi="psy", **over):
    base = dict(country_code="ZZ", production_system="all", farm_size_band="all", population_scope="national",
                kpi_code=kpi, definition_id=definition_id_for(kpi), value_scale="n/a",
                benchmark_status="verified", comparison_status="compatible", mapping_status="exact",
                is_provisional=False, transformed_value=22.4)
    base.update(over)
    return Benchmark(**base)


async def test_verified_context_attached(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", transformed_value=22.4))
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "ZZ", "psy")
    assert ctx.available is True and ctx.benchmark_value == 22.4 and ctx.unavailable_reason is None


async def test_provisional_context_blocked(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="provisional", is_provisional=True, transformed_value=None))
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "ZZ", "psy")
    assert ctx.available is False and ctx.unavailable_reason == "provisional" and ctx.benchmark_value is None


async def test_missing_context_blocked(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="missing", comparison_status="incompatible",
              transformed_value=None, value_scale=None))
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "ZZ", "psy")
    assert ctx.available is False and ctx.unavailable_reason == "missing"


async def test_value_scale_mismatch_degrades_context_not_fire(db: AsyncSession):
    """verified인데 value_scale 불일치 → 맥락만 강등(reason), 발화 차단 아님(§5)."""
    await _seed_defs(db)
    db.add(_b("farrowing_rate", value_scale="n/a", transformed_value=85.7))  # kpi_def=percent_0_100
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "ZZ", "farrowing_rate")
    assert ctx.available is False and ctx.unavailable_reason == "benchmark_value_scale_mismatch"


async def test_global_fallback_context_trace(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="global_fallback", transformed_value=20.0))
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "ZZ", "psy")
    assert ctx.available is True and ctx.is_global_fallback is True


async def test_no_row_context_none(db: AsyncSession):
    await _seed_defs(db)
    ctx = await svc.resolve_benchmark_context(db, "ZZ", "psy")
    assert ctx.available is False and ctx.unavailable_reason == "none"


async def test_us_stillbirth_normalized_context(db: AsyncSession):
    """US 사산율 normalized_verified → 맥락 첨부 가능(§8.1)."""
    await _seed_defs(db)
    db.add(_b("stillbirth_rate", country_code="US", population_scope="national_avg",
              benchmark_status="normalized_verified", mapping_status="normalized",
              comparison_status="normalized", value_scale="percent_0_100", transformed_value=9.93,
              transform_formula="(stillborn+mummified)/total_born*100", obs_group_id="PIGCHAMP_USA_2025_SPRING"))
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "US", "stillbirth_rate")
    assert ctx.available is True and ctx.benchmark_value == 9.93


async def test_us_psy_missing_no_context(db: AsyncSession):
    """US psy=missing(PWMFY 비호환) → 맥락도 금지(§8.2)."""
    await _seed_defs(db)
    db.add(_b("psy", country_code="US", population_scope="national_avg", benchmark_status="missing",
              comparison_status="incompatible", mapping_status="incompatible",
              transformed_value=None, value_scale=None))
    await db.flush()
    ctx = await svc.resolve_benchmark_context(db, "US", "psy")
    assert ctx.available is False
