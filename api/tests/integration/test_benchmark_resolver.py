"""
Benchmark resolver (services/benchmark_service) 테스트 — Rule Engine 연결 read-side 게이트.
문서 §3·§4·§6·§7 / 연결 프롬프트 §11.

발화 적격: verified류 + comparison fireable + value_scale 일치 + direction별 threshold 유효.
그 외 전부 can_fire=False + insufficient_reason. global_fallback은 threshold 있으면 발화+trace.
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
    base = dict(country_code="ZZ", production_system="all", farm_size_band="all",
                population_scope="national", kpi_code=kpi, definition_id=definition_id_for(kpi),
                value_scale="n/a", benchmark_status="verified", comparison_status="compatible",
                mapping_status="exact", is_provisional=False, transformed_value=22.0)
    base.update(over)
    return Benchmark(**base)


async def test_verified_with_thresholds_fires(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", warning_min=22, critical_min=18))  # higher_better
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is True and rb.insufficient_reason is None
    assert svc.evaluate_severity(rb, 20) == "warning"
    assert svc.evaluate_severity(rb, 25) == "ok"
    assert svc.evaluate_severity(rb, 17) == "critical"


async def test_verified_without_thresholds_insufficient(db: AsyncSession):
    """현재 KR/US verified 상태 — 평균만 있고 임계 없음 → threshold_missing."""
    await _seed_defs(db)
    db.add(_b("psy", warning_min=None, critical_min=None))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is False and rb.insufficient_reason == "threshold_missing"


async def test_provisional_blocked(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="provisional", is_provisional=True, warning_min=22, critical_min=18))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is False and "provisional" in rb.insufficient_reason


async def test_missing_blocked(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="missing", comparison_status="incompatible",
              transformed_value=None, value_scale=None))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is False


async def test_incompatible_blocked(db: AsyncSession):
    await _seed_defs(db)
    # value_scale은 일치(n/a==psy)시켜 comparison_status 게이트가 단독으로 잡히게(격리).
    # incompatible은 ⑫-6상 threshold/transformed_value 못 가지므로 status=missing.
    db.add(_b("psy", benchmark_status="missing", comparison_status="incompatible",
              transformed_value=None, value_scale="n/a"))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is False and "incompatible" in (rb.insufficient_reason or "")


async def test_value_scale_mismatch_blocked(db: AsyncSession):
    await _seed_defs(db)
    # farrowing_rate kpi_def=percent_0_100인데 benchmark에 n/a → 불일치
    db.add(_b("farrowing_rate", value_scale="n/a", warning_min=83, critical_min=78))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "farrowing_rate")
    assert rb.can_fire is False and rb.insufficient_reason == "value_scale_mismatch"


async def test_range_target_needs_four_bounds(db: AsyncSession):
    await _seed_defs(db)
    # culling_rate(range_target) 4-bound 중 critical_max 누락 → threshold_missing
    db.add(_b("culling_rate", value_scale="percent_0_100",
              warning_min=10, warning_max=50, critical_min=5, critical_max=None))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "culling_rate")
    assert rb.can_fire is False and rb.insufficient_reason == "threshold_missing"


async def test_range_target_full_bounds_fires_both_sides(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("culling_rate", value_scale="percent_0_100",
              warning_min=30, warning_max=50, critical_min=20, critical_max=60))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "culling_rate")
    assert rb.can_fire is True
    assert svc.evaluate_severity(rb, 40) == "ok"
    assert svc.evaluate_severity(rb, 25) == "warning"   # 하단
    assert svc.evaluate_severity(rb, 65) == "critical"  # 상단


async def test_global_fallback_fires_with_trace(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="global_fallback", comparison_status="compatible",
              warning_min=20, critical_min=16))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is True and rb.is_global_fallback is True


async def test_global_fallback_without_threshold_blocked(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", benchmark_status="global_fallback", comparison_status="compatible",
              warning_min=None, critical_min=None))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.can_fire is False and rb.insufficient_reason == "threshold_missing"


async def test_resolve_picks_highest_status(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", population_scope="p1", benchmark_status="provisional", is_provisional=True,
              warning_min=22, critical_min=18))
    db.add(_b("psy", population_scope="p2", benchmark_status="verified", warning_min=22, critical_min=18))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    assert rb.benchmark_status == "verified"


async def test_no_row_returns_none(db: AsyncSession):
    await _seed_defs(db)
    assert await svc.resolve_benchmark(db, "ZZ", "psy") is None


async def test_trace_has_required_fields(db: AsyncSession):
    await _seed_defs(db)
    db.add(_b("psy", warning_min=22, critical_min=18, obs_group_id="G"))
    await db.flush()
    rb = await svc.resolve_benchmark(db, "ZZ", "psy")
    t = rb.trace()
    for f in ("benchmark_id", "kpi_code", "definition_id", "benchmark_status", "comparison_status",
              "source_obs_id", "obs_group_id", "direction", "value_scale", "is_global_fallback",
              "insufficient_reason"):
        assert f in t
