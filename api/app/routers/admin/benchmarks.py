"""운영자 어드민 — KPI Governance benchmark 열람 (읽기 전용).

3-table(kpi_definitions/benchmarks/source_observations)을 조회. require_super_admin.
KR 등 내부 참조 benchmark는 운영자만 열람(§10.1 — 한국 서비스 노출 경로 아님).
쓰기/시드는 마이그레이션·seed validator 경로로만(여기선 GET만).
"""
from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbDep, require_super_admin
from app.core.exceptions import NotFoundError
from app.services import benchmark_service as svc

router = APIRouter(
    prefix="/admin/governance",
    tags=["Admin · KPI Governance"],
    dependencies=[Depends(require_super_admin)],
)


@router.get("/kpi-definitions")
async def get_kpi_definitions(db: DbDep):
    """§2 KPI 정의 16종 (국가 무관 본질 정의)."""
    rows = await svc.list_kpi_definitions(db)
    return {
        "count": len(rows),
        "items": [
            {
                "kpi_code": r.kpi_code, "definition_id": r.definition_id, "name_ko": r.name_ko,
                "numerator_def": r.numerator_def, "denominator_def": r.denominator_def,
                "denominator_type": r.denominator_type, "period_basis": r.period_basis,
                "direction": r.direction, "unit": r.unit, "value_scale": r.value_scale,
            }
            for r in rows
        ],
    }


@router.get("/benchmarks")
async def get_benchmarks(
    db: DbDep,
    country: str | None = Query(None, description="country_code 필터 (KR/US ...)"),
    kpi: str | None = Query(None, description="kpi_code 필터"),
):
    """benchmark 행 목록 (status/값/임계/모집단 포함)."""
    rows = await svc.list_benchmarks(db, country_code=country, kpi_code=kpi)
    return {
        "count": len(rows),
        "items": [
            {
                "bench_id": r.bench_id, "country_code": r.country_code,
                "population_scope": r.population_scope, "kpi_code": r.kpi_code,
                "definition_id": r.definition_id, "benchmark_status": r.benchmark_status,
                "comparison_status": r.comparison_status, "mapping_status": r.mapping_status,
                "transformed_value": float(r.transformed_value) if r.transformed_value is not None else None,
                "value_scale": r.value_scale, "transform_formula": r.transform_formula,
                "warning_min": _f(r.warning_min), "warning_max": _f(r.warning_max),
                "critical_min": _f(r.critical_min), "critical_max": _f(r.critical_max),
                "target": _f(r.target), "is_provisional": r.is_provisional,
                "source_obs_id": r.source_obs_id, "obs_group_id": r.obs_group_id,
            }
            for r in rows
        ],
    }


@router.get("/benchmarks/resolve")
async def resolve(
    db: DbDep,
    country: str = Query(..., description="country_code"),
    kpi: str = Query(..., description="kpi_code"),
    population: str | None = Query(None, description="population_scope (선택)"),
    value: float | None = Query(None, description="주면 severity까지 평가"),
):
    """(country, kpi)의 발화 적격 benchmark resolve + can_fire/insufficient_reason/trace. value 주면 severity."""
    rb = await svc.resolve_benchmark(db, country, kpi, population_scope=population)
    if rb is None:
        raise NotFoundError(f"benchmark 없음: {country}/{kpi} (미시드 → 발화 안 함)")
    severity = svc.evaluate_severity(rb, value) if value is not None else None
    return {"resolved": rb.trace(), "severity": severity}


def _f(v):
    return float(v) if v is not None else None
