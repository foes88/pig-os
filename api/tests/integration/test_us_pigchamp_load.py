"""
작업 US — PigCHAMP USA 2025 적재 검증 (handoff/KPI_GOVERNANCE_v3.1.md §4.3/§10.6, D-4).
- 분만율 verified / 사산율 normalized_verified(재계산) / PSY missing(PWMFY 비호환)
- pwmfy 별도 kpi_definition 미생성(보류 — source_obs만)
"""
import pytest

from app.db.benchmark_seed import SeedValidationError, kpi_definition_index, validate_benchmark

KDEFS = kpi_definition_index()


def test_us_farrowing_verified_valid():
    b = dict(country_code="US", population_scope="national_avg", kpi_code="farrowing_rate",
             definition_id=KDEFS["farrowing_rate"]["definition_id"], transformed_value=83.81,
             value_scale="percent_0_100", transform_formula=None, mapping_status="exact",
             comparison_status="compatible", benchmark_status="verified", is_provisional=False,
             obs_group_id="PIGCHAMP_USA_2025_SPRING")
    validate_benchmark(b, KDEFS)


def test_us_stillbirth_normalized_recalc():
    """(stillborn+mummified)/total_born = (5526.13+3031.06)/86157.32 ≈ 9.93%."""
    assert round((5526.13 + 3031.06) / 86157.32 * 100, 2) == 9.93
    b = dict(country_code="US", population_scope="national_avg", kpi_code="stillbirth_rate",
             definition_id=KDEFS["stillbirth_rate"]["definition_id"], transformed_value=9.93,
             value_scale="percent_0_100", transform_formula="(stillborn+mummified)/total_born*100",
             mapping_status="normalized", comparison_status="normalized",
             benchmark_status="normalized_verified", is_provisional=False,
             obs_group_id="PIGCHAMP_USA_2025_SPRING")
    validate_benchmark(b, KDEFS)


def test_us_psy_missing_incompatible():
    """PWMFY(분모=교배모돈)≠PSY(상시모돈) → missing/incompatible, 발화값 없음."""
    b = dict(country_code="US", population_scope="national_avg", kpi_code="psy",
             definition_id=KDEFS["psy"]["definition_id"], transformed_value=None, value_scale=None,
             mapping_status="incompatible", comparison_status="incompatible",
             benchmark_status="missing", is_provisional=False, obs_group_id="PIGCHAMP_USA_2025_SPRING")
    validate_benchmark(b, KDEFS)
    # PSY 슬롯에 PWMFY값 27.1을 넣으려하면 비호환+발화가능 → 차단(★⑫-6)
    leak = dict(b, transformed_value=27.1, benchmark_status="provisional")
    with pytest.raises(SeedValidationError):
        validate_benchmark(leak, KDEFS)


def test_pwmfy_not_a_kpi_definition():
    """D-4 보류: pwmfy는 kpi_definitions에 없음(source_obs 보존만)."""
    assert "pwmfy" not in KDEFS and "pwmfy_us" not in KDEFS
