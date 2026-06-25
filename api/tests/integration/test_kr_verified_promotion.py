"""
작업 C — KR verified 승격 검증 테스트 (handoff/KPI_GOVERNANCE_v3.1.md §10, PROMPT_C §5 STEP6).

- national_general 7종 verified 정합(value_scale=kpi_def)
- 전문사용자 사산율 normalized_verified 유효 + 전국 stillbirth 슬롯으로 누수 금지
- population_scope로 national/professional 같은 KPI 공존 / 같은 population 중복 차단(DB)
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.benchmark_seed import (
    KPI_DEFINITIONS,
    SeedValidationError,
    definition_id_for,
    kpi_definition_index,
    validate_benchmark,
)
from app.db.models.benchmark import Benchmark, KpiDefinition

pytestmark = pytest.mark.anyio
KDEFS = kpi_definition_index()

# 작업 C national_general verified 7종 (값, value_scale)
NATIONAL = {
    "psy": (22.4, "n/a"), "msy": (18.9, "n/a"), "farrowing_rate": (85.7, "percent_0_100"),
    "prewean_survival": (89.1, "percent_0_100"), "postwean_survival": (84.3, "percent_0_100"),
    "weaned_per_litter": (10.45, "n/a"), "sow_turnover": (2.14, "n/a"),
}


def _verified(kpi, value, vscale, population="national_general", **over):
    base = dict(country_code="KR", production_system="all", farm_size_band="all",
                population_scope=population, kpi_code=kpi, definition_id=KDEFS[kpi]["definition_id"],
                transformed_value=value, transform_formula=None, value_scale=vscale,
                obs_group_id="KR_2025_national_general", warning_min=None, warning_max=None,
                critical_min=None, critical_max=None, target=None,
                mapping_status="exact", comparison_status="compatible",
                benchmark_status="verified", is_provisional=False)
    base.update(over)
    return base


@pytest.mark.parametrize("kpi", list(NATIONAL))
def test_national_value_scale_matches_kpidef(kpi):
    """7종 verified value_scale이 kpi_definitions와 일치(override 금지, ★⑫-4)."""
    _, vscale = NATIONAL[kpi]
    assert vscale == KDEFS[kpi]["value_scale"]
    validate_benchmark(_verified(kpi, NATIONAL[kpi][0], vscale), KDEFS)  # 예외 없어야


def test_professional_stillbirth_normalized_valid():
    """전문사용자 사산율 9.3% normalized_verified(★⑧ 6조건 충족)."""
    b = dict(country_code="KR", production_system="all", farm_size_band="all",
             population_scope="professional", kpi_code="stillbirth_rate",
             definition_id=KDEFS["stillbirth_rate"]["definition_id"],
             transformed_value=9.3, transform_formula="복당사산/복당총산*100", value_scale="percent_0_100",
             obs_group_id="KR_2025_professional", mapping_status="normalized",
             comparison_status="normalized", benchmark_status="normalized_verified", is_provisional=False)
    validate_benchmark(b, KDEFS)  # 예외 없어야


def test_national_stillbirth_cannot_take_professional_value():
    """전국(national_general) 사산율에 전문값을 normalized_verified로 채우려해도,
    원자료(formula/근거) 없으면 차단 — 모집단 혼입 가드."""
    b = dict(country_code="KR", population_scope="national_general", kpi_code="stillbirth_rate",
             definition_id=KDEFS["stillbirth_rate"]["definition_id"], transformed_value=9.3,
             value_scale="percent_0_100", benchmark_status="normalized_verified",
             mapping_status="normalized", comparison_status="normalized",
             transform_formula=None, obs_group_id=None, is_provisional=False)  # 근거 없음
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


async def _seed_defs(db: AsyncSession):
    for d in KPI_DEFINITIONS:
        db.add(KpiDefinition(definition_id=definition_id_for(d["kpi_code"]), **d))
    await db.flush()


async def test_national_and_professional_coexist(db: AsyncSession):
    """같은 KPI라도 population 다르면 verified 공존 가능(전국 22.4 / 전문 24.2)."""
    await _seed_defs(db)
    db.add(Benchmark(**_verified("psy", 22.4, "n/a", population="national_general")))
    db.add(Benchmark(**_verified("psy", 24.2, "n/a", population="professional")))
    await db.flush()  # 공존 허용 → 예외 없어야


async def test_same_population_duplicate_verified_blocked(db: AsyncSession):
    """같은 (country,population,kpi) verified 중복 → unique 위반(DB)."""
    await _seed_defs(db)
    db.add(Benchmark(**_verified("psy", 22.4, "n/a", population="national_general")))
    await db.flush()
    db.add(Benchmark(**_verified("psy", 22.4, "n/a", population="national_general")))
    with pytest.raises(IntegrityError):
        await db.flush()
