"""
KPI Governance v3.1 — 필수 테스트 15종 (문서 §7 + §7.1).
- 1~5,11: threshold 방향 해석(★⑪)·발화 게이팅(★③) — 순수 로직
- 6,8~10,12~14: seed validator(★⑦⑧⑫) — validate_benchmark 예외
- 7,15: DB 제약(복합 FK ★④ / active verified 중복) — 실제 insert→IntegrityError

실행: cd api && uv run pytest tests/integration/test_benchmark_governance.py -q
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
from app.engine.benchmark_thresholds import (
    CRITICAL,
    OK,
    WARNING,
    severity_for,
    should_generate_insight,
    ui_badge,
)

pytestmark = pytest.mark.anyio

KDEFS = kpi_definition_index()


def _bench(**over) -> dict:
    """유효한 provisional psy benchmark 기본형 + override."""
    base = dict(
        country_code="KR", production_system="all", farm_size_band="all",
        kpi_code="psy", definition_id="PIGOS_PSY_V1",
        transformed_value=None, transform_formula=None, value_scale="n/a",
        source_obs_id=None, obs_group_id="PIGPLAN_KR_2025",
        warning_min=22, warning_max=None, critical_min=18, critical_max=None, target=24,
        mapping_status="exact", comparison_status="compatible",
        benchmark_status="provisional", is_provisional=True,
    )
    base.update(over)
    return base


# ── 1~3, 11: threshold 방향별 해석 (★⑪) ──────────────────────────────────────
def test_01_lower_better_severity_rises_with_value():
    """NPD(lower_better): 값↑일수록 severity↑."""
    kw = dict(warning_max=35, critical_max=50)
    assert severity_for("lower_better", 20, **kw) == OK
    assert severity_for("lower_better", 40, **kw) == WARNING
    assert severity_for("lower_better", 55, **kw) == CRITICAL


def test_02_higher_better_severity_rises_as_value_falls():
    """PSY(higher_better): 값↓일수록 severity↑."""
    kw = dict(warning_min=22, critical_min=18)
    assert severity_for("higher_better", 25, **kw) == OK
    assert severity_for("higher_better", 20, **kw) == WARNING
    assert severity_for("higher_better", 16, **kw) == CRITICAL


def test_03_range_target_both_sides():
    """culling_rate(range_target): 하단 미만·상단 초과 양쪽에서 severity↑."""
    kw = dict(warning_min=30, warning_max=50, critical_min=20, critical_max=60)
    assert severity_for("range_target", 40, **kw) == OK
    assert severity_for("range_target", 25, **kw) == WARNING   # 하단 경고
    assert severity_for("range_target", 55, **kw) == WARNING   # 상단 경고
    assert severity_for("range_target", 15, **kw) == CRITICAL  # 하단 위험
    assert severity_for("range_target", 65, **kw) == CRITICAL  # 상단 위험


def test_11_direction_reads_correct_cells():
    """방향별로 읽는 칸 고정: higher=min, lower=max, range=양방향(★⑪)."""
    # higher_better는 max칸 무시
    assert severity_for("higher_better", 100, warning_min=22, warning_max=5, critical_min=18) == OK
    # lower_better는 min칸 무시
    assert severity_for("lower_better", 0, warning_min=99, warning_max=35, critical_max=50) == OK
    # range_target는 4칸 모두 사용
    assert severity_for("range_target", 55, warning_min=30, warning_max=50) == WARNING


# ── 4, 5: 발화 게이팅 / UI ────────────────────────────────────────────────────
def test_04_incompatible_unknown_no_insight():
    """comparison_status∈{incompatible,unknown}이면 insight 생성 금지."""
    assert should_generate_insight("incompatible", "missing") is False
    assert should_generate_insight("unknown", "provisional") is False
    assert should_generate_insight("compatible", "provisional") is True
    assert should_generate_insight("exact", "verified") is True


def test_05_benchmark_status_ui_badge():
    """benchmark_status 5종 모두 UI 배지가 구분되는지."""
    labels = {ui_badge(s) for s in
              ("verified", "normalized_verified", "provisional", "missing", "global_fallback")}
    assert len(labels) == 5  # 5종 전부 서로 다른 라벨


# ── 6, 8~10, 12~14: seed validator (★⑦⑧⑫) ───────────────────────────────────
def test_06_normalized_verified_without_formula_fails():
    b = _bench(kpi_code="stillbirth_rate", definition_id="PIGOS_STILLBIRTH_RATE_V1",
               benchmark_status="normalized_verified", mapping_status="normalized",
               comparison_status="normalized", transformed_value=9.93, value_scale="percent_0_100",
               transform_formula=None, is_provisional=False,
               warning_min=None, critical_min=None, target=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_08_value_scale_mismatch_blocks():
    """benchmarks.value_scale ≠ kpi_definitions.value_scale → 차단 (★⑫-4)."""
    b = _bench(kpi_code="farrowing_rate", definition_id="PIGOS_FARROWING_RATE_V1",
               value_scale="ratio_0_1",  # kpi_def는 percent_0_100
               warning_min=83, critical_min=78, target=85)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_09_verified_with_provisional_fails():
    """verified인데 is_provisional=true → 실패 (★⑦)."""
    b = _bench(benchmark_status="verified", is_provisional=True, comparison_status="compatible",
               transformed_value=24)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_10_normalized_verified_missing_condition_fails():
    """normalized_verified 6조건 중 하나(comparison_status≠normalized) 누락 → 실패 (★⑧)."""
    b = _bench(kpi_code="stillbirth_rate", definition_id="PIGOS_STILLBIRTH_RATE_V1",
               benchmark_status="normalized_verified", mapping_status="normalized",
               comparison_status="compatible",  # normalized 아님 → 위반
               transformed_value=9.93, value_scale="percent_0_100",
               transform_formula="(stillborn+mummified)/total_born*100", is_provisional=False,
               warning_min=None, critical_min=None, target=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_12_value_scale_neq_kpidef_fails():
    """value_scale 명시했으나 kpi_def와 다름 (★⑫-4) — percent KPI에 n/a."""
    b = _bench(kpi_code="sow_mortality", definition_id="PIGOS_SOW_MORTALITY_V1",
               value_scale="n/a",  # kpi_def는 percent_0_100
               warning_max=10, critical_max=None, target=None, warning_min=None, critical_min=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_13_transformed_value_with_missing_fails():
    """transformed_value 있는데 benchmark_status='missing' → 실패 (★⑫-5)."""
    b = _bench(benchmark_status="missing", transformed_value=24,
               comparison_status="incompatible", mapping_status="incompatible",
               warning_min=None, critical_min=None, target=None, value_scale=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_14_incompatible_with_threshold_fails():
    """comparison_status incompatible인데 threshold 발화가능 → 실패 (★⑫-6)."""
    b = _bench(comparison_status="incompatible", mapping_status="incompatible",
               benchmark_status="provisional", warning_min=22, critical_min=18, value_scale=None,
               transformed_value=None, target=None)
    with pytest.raises(SeedValidationError):
        validate_benchmark(b, KDEFS)


def test_valid_provisional_passes():
    """정상 provisional은 통과(역검증)."""
    validate_benchmark(_bench(), KDEFS)  # 예외 없어야


# ── 7, 15: DB 제약 (복합 FK / active verified 중복) ──────────────────────────
async def _seed_kpi_defs(db: AsyncSession) -> None:
    for d in KPI_DEFINITIONS:
        db.add(KpiDefinition(definition_id=definition_id_for(d["kpi_code"]), **d))
    await db.flush()


async def test_07_composite_fk_mismatch_fails(db: AsyncSession):
    """(kpi_code, definition_id) 불일치 시 복합 FK 위반 → 실패 (★④)."""
    await _seed_kpi_defs(db)
    db.add(Benchmark(country_code="KR", kpi_code="psy", definition_id="PIGOS_WRONG_V1",
                     benchmark_status="missing", value_scale=None))
    with pytest.raises(IntegrityError):
        await db.flush()


async def test_15_duplicate_active_verified_blocked(db: AsyncSession):
    """동일 (country,kpi,def) active verified 2건 → 중복 방지 인덱스 위반 (period 달라도)."""
    await _seed_kpi_defs(db)
    common = dict(country_code="KR", kpi_code="psy", definition_id="PIGOS_PSY_V1",
                  benchmark_status="verified", comparison_status="compatible", mapping_status="exact",
                  transformed_value=24, value_scale="n/a", is_provisional=False, is_active=True,
                  warning_min=22, critical_min=18)
    db.add(Benchmark(**common))
    await db.flush()
    db.add(Benchmark(**common))   # 같은 (country,kpi,def) active verified 중복
    with pytest.raises(IntegrityError):
        await db.flush()
