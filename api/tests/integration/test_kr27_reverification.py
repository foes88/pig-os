"""
작업 B — KR 27 재검증 불변식 테스트 (handoff/KPI_GOVERNANCE_v3.1.md §6/§7, PROMPT_B §7).

1차자료(한돈팜스 PDF) 미확보 → KR verified 금지(D-6). 본 테스트는 그 가드와
A 강등 결과의 안전성(역발화 없음·근거없는 승격 차단·orphan 미정의)을 고정한다.
"""
import pytest

from app.db.benchmark_seed import SeedValidationError, kpi_definition_index, validate_benchmark
from app.engine.benchmark_thresholds import CRITICAL, OK, WARNING, severity_for

KDEFS = kpi_definition_index()

# A가 이전한 KR lower_better 실제 임계 (DB 실측값)
_KR_LOWER = {
    "npd": dict(warning_max=35, critical_max=50),
    "wsi": dict(warning_max=7, critical_max=10),
    "fcr": dict(warning_max=3.0, critical_max=3.2),
    "prewean_mortality": dict(warning_max=10, critical_max=14),
    "sow_mortality": dict(warning_max=10),
}


def _kr_provisional(kpi_code: str, **over) -> dict:
    kdef = KDEFS[kpi_code]
    base = dict(country_code="KR", kpi_code=kpi_code, definition_id=kdef["definition_id"],
                benchmark_status="provisional", is_provisional=True,
                mapping_status="exact", comparison_status="compatible",
                value_scale=kdef["value_scale"], transformed_value=None,
                obs_group_id="PIGPLAN_KR_2025")
    base.update(over)
    return base


@pytest.mark.parametrize("kpi", list(_KR_LOWER))
def test_kr_lower_better_no_inverse_firing(kpi):
    """KR lower_better 지표: 값↑일수록 severity↑ (역발화 없음)."""
    th = _KR_LOWER[kpi]
    low = severity_for("lower_better", 1.0, **th)
    high = severity_for("lower_better", 999.0, **th)
    assert low == OK
    assert high in (WARNING, CRITICAL)
    if "critical_max" in th:
        assert severity_for("lower_better", th["critical_max"] + 1, **th) == CRITICAL


def test_kr_psy_higher_better_direction():
    """KR PSY(higher_better): 값↓→경고 (warning_min 22 미만)."""
    assert severity_for("higher_better", 25, warning_min=22, critical_min=18) == OK
    assert severity_for("higher_better", 20, warning_min=22, critical_min=18) == WARNING
    assert severity_for("higher_better", 17, warning_min=22, critical_min=18) == CRITICAL


def test_kr_provisional_cannot_verify_without_confirmed_value():
    """1차자료 미확인 KR(transformed_value NULL)을 verified로 올리면 차단 (★⑦ / D-6)."""
    b = _kr_provisional("psy", benchmark_status="verified", is_provisional=False)  # transformed_value None
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_kr_stillbirth_cannot_normalize_without_basis():
    """A가 missing 처리한 사산율을 transform_formula/원자료 없이 normalized_verified 승격 시 차단 (★⑧)."""
    b = _kr_provisional("stillbirth_rate", benchmark_status="normalized_verified", is_provisional=False,
                        mapping_status="normalized", comparison_status="normalized",
                        transformed_value=9.93, value_scale="percent_0_100",
                        transform_formula=None)  # 원자료 분리/공식 없음
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_kr_missing_not_promoted_to_verified_blindly():
    """A의 missing(사산율)을 근거 없이 verified 승격 차단."""
    b = _kr_provisional("stillbirth_rate", benchmark_status="verified", is_provisional=False,
                        comparison_status="incompatible", mapping_status="incompatible",
                        value_scale=None, transformed_value=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


@pytest.mark.parametrize("orphan", ["ABORTION_RATE", "RTS_RATE", "SOW_RESIDUAL_P0", "WEANING_WEIGHT", "HIGH_PARITY_RATIO"])
def test_orphan_codes_have_no_kpi_definition(orphan):
    """orphan(KR고유)은 §2 kpi_definitions에 없음 → benchmarks 승격 불가(복합FK 전 단계서 차단)."""
    assert orphan.lower() not in KDEFS  # 정의 자체가 없음
    b = dict(country_code="KR", kpi_code=orphan.lower(), definition_id=f"PIGOS_{orphan}_V1",
             benchmark_status="provisional", value_scale=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_kr_provisional_valid_passes():
    """정상 KR provisional은 통과(역검증) — A 이전 결과가 게이트를 깨지 않음."""
    validate_benchmark(_kr_provisional("psy", warning_min=22, critical_min=18, target=24), KDEFS)
    validate_benchmark(_kr_provisional("npd", warning_max=35, critical_max=50, target=20), KDEFS)
