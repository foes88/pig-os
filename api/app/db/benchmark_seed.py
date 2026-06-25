"""
KPI Governance v3.1 — kpi_definitions 시드 데이터 (§2) + seed validator (§3.5 ★⑦⑧⑫ + §6 게이트).

문서: handoff/KPI_GOVERNANCE_v3.1.md
- KPI_DEFINITIONS: §2.1~2.3 표 16종. direction/denominator_type/period_basis/unit/value_scale.
- validate_benchmark(): benchmark 행 1건을 kpi_definitions 대비 검증. 위반 시 SeedValidationError.
  마이그레이션의 KR 이전·향후 시드 스크립트·테스트가 공용으로 사용.

⚠️ 발견된 결정사항 D-13 (문서 §2.2 vs §3.1 내부 충돌):
  §2.2는 fcr value_scale='ratio'로 표기하나, §3.1/§4.3 허용 enum은 percent_0_100|ratio_0_1|n/a 뿐.
  FCR(≈2.5)은 0~100 percent도 0~1 ratio도 아니므로(turns·days처럼) enum-safe하게 'n/a'로 시드.
  → 사용자 확정 필요. 아래 _FCR_VALUE_SCALE 한 곳만 바꾸면 됨.
"""
from __future__ import annotations

_FCR_VALUE_SCALE = "n/a"  # D-13: 문서 §2.2 'ratio' → enum 미존재 → 'n/a' 잠정 (사용자 확정 대기)

# ── §2 KPI 정의 (definition_id = PIGOS_<UPPER>_V1) ────────────────────────────
# (kpi_code, name_ko, numerator_def, denominator_def, denominator_type, period_basis, direction, unit, value_scale)
KPI_DEFINITIONS: list[dict] = [
    # 2.1 higher_better
    dict(kpi_code="psy", name_ko="모돈두당연간이유두수", numerator_def="총이유두수", denominator_def="평균사육모돈",
         denominator_type="avg_inventory_sow", period_basis="rolling_365", direction="higher_better",
         unit="head_per_sow_year", value_scale="n/a"),
    dict(kpi_code="msy", name_ko="모돈두당연간출하두수", numerator_def="총출하두수", denominator_def="평균사육모돈",
         denominator_type="avg_inventory_sow", period_basis="rolling_365", direction="higher_better",
         unit="head_per_sow_year", value_scale="n/a"),
    dict(kpi_code="farrowing_rate", name_ko="분만율", numerator_def="분만복수", denominator_def="교배복수",
         denominator_type="litter", period_basis="period", direction="higher_better",
         unit="percent", value_scale="percent_0_100"),
    dict(kpi_code="weaned_per_litter", name_ko="복당이유두수", numerator_def="이유두수", denominator_def="이유복수",
         denominator_type="litter", period_basis="period", direction="higher_better",
         unit="head", value_scale="n/a"),
    dict(kpi_code="sow_turnover", name_ko="모돈회전율", numerator_def="분만복수", denominator_def="평균사육모돈",
         denominator_type="avg_inventory_sow", period_basis="rolling_365", direction="higher_better",
         unit="turns", value_scale="n/a"),
    dict(kpi_code="prewean_survival", name_ko="이유전육성률", numerator_def="이유두수", denominator_def="포유개시두수",
         denominator_type="piglet", period_basis="period", direction="higher_better",
         unit="percent", value_scale="percent_0_100"),
    dict(kpi_code="postwean_survival", name_ko="이유후육성률", numerator_def="출하두수", denominator_def="이유두수",
         denominator_type="piglet", period_basis="period", direction="higher_better",
         unit="percent", value_scale="percent_0_100"),
    # 2.2 lower_better
    dict(kpi_code="npd", name_ko="비생산일수", numerator_def="비생산일수합", denominator_def="평균사육모돈",
         denominator_type="avg_inventory_sow", period_basis="rolling_365", direction="lower_better",
         unit="days", value_scale="n/a", notes="gilt_entry_included 플래그(D-1)"),
    dict(kpi_code="stillbirth_rate", name_ko="사산율", numerator_def="사산+미라", denominator_def="총산",
         denominator_type="total_born", period_basis="period", direction="lower_better",
         unit="percent", value_scale="percent_0_100", notes="PigOS 비표준 분자(미라 포함)"),
    dict(kpi_code="mummy_rate", name_ko="미라율", numerator_def="미라", denominator_def="총산",
         denominator_type="total_born", period_basis="period", direction="lower_better",
         unit="percent", value_scale="percent_0_100"),
    dict(kpi_code="prewean_mortality", name_ko="이유전폐사율", numerator_def="이유전폐사", denominator_def="포유개시두수",
         denominator_type="piglet", period_basis="period", direction="lower_better",
         unit="percent", value_scale="percent_0_100"),
    dict(kpi_code="postwean_mortality", name_ko="이유후폐사율", numerator_def="이유후폐사", denominator_def="이유두수",
         denominator_type="piglet", period_basis="period", direction="lower_better",
         unit="percent", value_scale="percent_0_100"),
    dict(kpi_code="sow_mortality", name_ko="모돈폐사율", numerator_def="모돈폐사", denominator_def="평균사육모돈",
         denominator_type="avg_inventory_sow", period_basis="rolling_365", direction="lower_better",
         unit="percent", value_scale="percent_0_100"),
    dict(kpi_code="fcr", name_ko="사료요구율", numerator_def="사료급여량", denominator_def="증체량",
         denominator_type="weight", period_basis="period", direction="lower_better",
         unit="kg_per_kg", value_scale=_FCR_VALUE_SCALE, notes="체중구간 정의필요. value_scale D-13"),
    dict(kpi_code="wsi", name_ko="이유후재교배간격", numerator_def="이유~초교배일수", denominator_def="교배모돈수",
         denominator_type="mated_female", period_basis="period", direction="lower_better",
         unit="days", value_scale="n/a", notes="KR임계7일"),
    # 2.3 range_target
    dict(kpi_code="culling_rate", name_ko="모돈도태율/갱신율", numerator_def="도태(갱신)모돈수", denominator_def="평균사육모돈",
         denominator_type="avg_inventory_sow", period_basis="rolling_365", direction="range_target",
         unit="percent", value_scale="percent_0_100"),
]


def definition_id_for(kpi_code: str) -> str:
    return f"PIGOS_{kpi_code.upper()}_V1"


def kpi_definition_index() -> dict[str, dict]:
    """kpi_code → 정의 dict (definition_id 포함)."""
    out: dict[str, dict] = {}
    for d in KPI_DEFINITIONS:
        rec = dict(d)
        rec["definition_id"] = definition_id_for(d["kpi_code"])
        out[d["kpi_code"]] = rec
    return out


# ── Seed Validator (§3.5 ★⑦⑧⑫ + §6 게이트) ──────────────────────────────────
class SeedValidationError(ValueError):
    """benchmark seed가 거버넌스 제약을 위반."""


_FIREABLE = {"exact", "compatible", "normalized"}


def _has_threshold(b: dict) -> bool:
    return any(b.get(k) is not None for k in ("warning_min", "warning_max", "critical_min", "critical_max"))


def validate_benchmark(b: dict, kpi_defs: dict[str, dict]) -> None:
    """
    benchmark 행 1건 검증. 위반 시 SeedValidationError.
    b: benchmark dict. kpi_defs: kpi_code → 정의 dict (kpi_definition_index()).
    DB CHECK와 중복되는 단일행 규칙도 친절한 메시지를 위해 재검증 + 크로스테이블(★⑫-4)은 여기서만.
    """
    status = b.get("benchmark_status", "missing")
    kpi = b.get("kpi_code")
    cmp_ = b.get("comparison_status")

    # 복합 FK 사전검증 (★④ — DB도 강제하나 메시지용)
    kdef = kpi_defs.get(kpi)
    if kdef is None:
        raise SeedValidationError(f"[{kpi}] kpi_definitions에 없는 kpi_code (복합 FK 위반)")
    if b.get("definition_id") != kdef["definition_id"]:
        raise SeedValidationError(
            f"[{kpi}] definition_id 불일치: {b.get('definition_id')} ≠ {kdef['definition_id']} (★④ 복합 FK)")

    # ★⑫-4 value_scale ≠ kpi_definitions.value_scale (크로스테이블 — DB CHECK 불가)
    bvs = b.get("value_scale")
    if bvs is not None and bvs != kdef["value_scale"]:
        raise SeedValidationError(
            f"[{kpi}] value_scale 불일치: benchmarks={bvs} ≠ kpi_definitions={kdef['value_scale']} (★⑫-4)")

    # ★⑦ verified/normalized_verified → is_provisional=false + transformed_value NOT NULL
    if status in ("verified", "normalized_verified"):
        if b.get("is_provisional"):
            raise SeedValidationError(f"[{kpi}] {status}인데 is_provisional=true (★⑦)")
        if b.get("transformed_value") is None:
            raise SeedValidationError(f"[{kpi}] {status}인데 transformed_value NULL (★⑦)")

    # ★⑧ normalized_verified 6조건
    if status == "normalized_verified":
        missing = []
        if not b.get("transform_formula"):
            missing.append("transform_formula")
        if b.get("mapping_status") != "normalized":
            missing.append("mapping_status=normalized")
        if cmp_ != "normalized":
            missing.append("comparison_status=normalized")
        if b.get("transformed_value") is None:
            missing.append("transformed_value")
        if b.get("value_scale") is None:
            missing.append("value_scale")
        if not (b.get("source_obs_id") is not None or b.get("obs_group_id")):
            missing.append("source_obs_id|obs_group_id")
        if missing:
            raise SeedValidationError(f"[{kpi}] normalized_verified 6조건 누락: {missing} (★⑧)")

    # ★⑫-1 verified → comparison_status ∈ {exact, compatible}
    if status == "verified" and cmp_ not in ("exact", "compatible"):
        raise SeedValidationError(f"[{kpi}] verified인데 comparison_status={cmp_} ∉ exact/compatible (★⑫-1)")

    # ★⑫-2 normalized_verified → comparison_status = normalized (★⑧에 포함되나 명시)
    if status == "normalized_verified" and cmp_ != "normalized":
        raise SeedValidationError(f"[{kpi}] normalized_verified인데 comparison_status≠normalized (★⑫-2)")

    # ★⑫-3 verified → transform_formula 없어야 (재정규화 필요하면 normalized_verified)
    if status == "verified" and b.get("transform_formula"):
        raise SeedValidationError(f"[{kpi}] verified인데 transform_formula 존재 → normalized_verified여야 (★⑫-3)")

    # ★⑫-5 transformed_value 있는데 missing
    if status == "missing" and b.get("transformed_value") is not None:
        raise SeedValidationError(f"[{kpi}] transformed_value 있는데 benchmark_status=missing (★⑫-5)")

    # ★⑫-6 incompatible/unknown인데 발화가능(threshold/transformed_value)
    if cmp_ in ("incompatible", "unknown") and (b.get("transformed_value") is not None or _has_threshold(b)):
        raise SeedValidationError(
            f"[{kpi}] comparison_status={cmp_}인데 transformed_value/threshold 발화가능 상태 (★⑫-6)")

    # value_scale enum (kpi_definitions와 동일 집합 — n/a 포함)
    if bvs is not None and bvs not in ("percent_0_100", "ratio_0_1", "n/a"):
        raise SeedValidationError(f"[{kpi}] benchmarks.value_scale={bvs} 허용 외 (★⑧-5/§E)")
