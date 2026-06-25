"""
Codex 교차검증 P0(mutation GREEN_GAP) 후속 — 규칙별 '단독 위반' 격리 테스트.

기존 테스트는 입력이 여러 규칙을 동시에 위반해, 한 규칙을 무력화해도 다른 규칙이 대신 잡아
RED가 안 됐다(빈 통과). 본 파일은 각 규칙을 **그 규칙만** 위반하는 입력으로 격리 → 해당 규칙을
무력화하면 정확히 그 테스트만 RED가 되도록 한다.

대상(Codex 지적): ★⑧ mapping_status / ★⑧ value_scale / ★⑧ source_obs|obs_group /
★⑫-1 verified comparison / ★⑫-3 verified transform_formula / ★⑫-5 missing transformed_value /
can_fire() value_scale 게이트.
(value_scale enum 분기는 ★⑫-4·DB CHECK에 가려진 죽은코드라 제거 — 테스트 대신 삭제로 해소.)
"""
import pytest

from app.db.benchmark_seed import SeedValidationError, kpi_definition_index, validate_benchmark
from app.engine.benchmark_thresholds import can_fire

KDEFS = kpi_definition_index()


def _nv(**over) -> dict:
    """정상 normalized_verified(stillbirth_rate) 기준 — 단일 필드만 깨서 ★⑧ 각 조건 격리."""
    base = dict(
        country_code="KR", production_system="all", farm_size_band="all", population_scope="professional",
        kpi_code="stillbirth_rate", definition_id="PIGOS_STILLBIRTH_RATE_V1",
        benchmark_status="normalized_verified", is_provisional=False,
        mapping_status="normalized", comparison_status="normalized",
        transform_formula="복당사산/복당총산*100", transformed_value=9.3, value_scale="percent_0_100",
        obs_group_id="G", source_obs_id=None,
        warning_min=None, warning_max=None, critical_min=None, critical_max=None, target=None,
    )
    base.update(over)
    return base


def _v(**over) -> dict:
    """정상 verified(psy) 기준 — 단일 필드만 깨서 ★⑫-1/3 격리."""
    base = dict(
        country_code="KR", production_system="all", farm_size_band="all", population_scope="national_general",
        kpi_code="psy", definition_id="PIGOS_PSY_V1",
        benchmark_status="verified", is_provisional=False,
        mapping_status="exact", comparison_status="compatible",
        transform_formula=None, transformed_value=22.4, value_scale="n/a",
        obs_group_id="G", source_obs_id=None,
        warning_min=None, warning_max=None, critical_min=None, critical_max=None, target=None,
    )
    base.update(over)
    return base


def test_baselines_pass():
    """기준선은 통과해야(격리 테스트의 전제). 깨지면 단독위반이 아님."""
    validate_benchmark(_nv(), KDEFS)
    validate_benchmark(_v(), KDEFS)


# ── ★⑧ 6조건 개별 격리 (transform_formula는 기존 test_06이 커버, 나머지 보강) ──
def test_iso_nv_mapping_status_only():
    """★⑧ mapping_status=normalized 단독 위반 (line 137)."""
    with pytest.raises(SeedValidationError):
        validate_benchmark(_nv(mapping_status="exact"), KDEFS)


def test_iso_nv_value_scale_only():
    """★⑧ value_scale 필수 단독 위반 (line 143). value_scale=None → enum/⑫-4 스킵."""
    with pytest.raises(SeedValidationError):
        validate_benchmark(_nv(value_scale=None), KDEFS)


def test_iso_nv_source_ref_only():
    """★⑧ source_obs_id|obs_group_id 필수 단독 위반 (line 145)."""
    with pytest.raises(SeedValidationError):
        validate_benchmark(_nv(source_obs_id=None, obs_group_id=None), KDEFS)


# ── ★⑫-1 / ★⑫-3 verified 격리 ──
def test_iso_verified_comparison_only():
    """★⑫-1 verified comparison∉{exact,compatible} 단독 (line 151). 'normalized'는 ⑫-6 비대상."""
    with pytest.raises(SeedValidationError):
        validate_benchmark(_v(comparison_status="normalized"), KDEFS)


def test_iso_verified_transform_formula_only():
    """★⑫-3 verified인데 transform_formula 존재 단독 (line 159). comparison=compatible로 ⑫-1 회피."""
    with pytest.raises(SeedValidationError):
        validate_benchmark(_v(transform_formula="a/b*100"), KDEFS)


# ── ★⑫-5 missing+transformed_value 격리 (기존 test_13은 ⑫-6에 가려졌던 것 수정) ──
def test_iso_missing_transformed_value_only():
    """★⑫-5 missing인데 transformed_value 존재 단독 (line 163).
    comparison=compatible(⑫-6 회피) + value_scale=None(enum/⑫-4 회피)."""
    b = dict(country_code="KR", kpi_code="psy", definition_id="PIGOS_PSY_V1",
             benchmark_status="missing", transformed_value=24.0, comparison_status="compatible",
             mapping_status=None, value_scale=None, is_provisional=False,
             warning_min=None, warning_max=None, critical_min=None, critical_max=None, target=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


# ── can_fire() value_scale 게이트 격리 ──
def test_iso_can_fire_value_scale_gate():
    """can_fire value_scale 게이트 단독: status·comparison은 통과조건, value_scale만으로 결정."""
    assert can_fire("verified", "compatible", "n/a") is True
    assert can_fire("verified", "compatible", None) is False   # value_scale 게이트가 막아야
    assert can_fire("verified", "compatible", "") is False
