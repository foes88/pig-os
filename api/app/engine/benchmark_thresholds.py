"""
KPI Governance v3.1 — threshold 방향별 해석 (★⑪) + 발화 게이팅 (★③).
문서: handoff/KPI_GOVERNANCE_v3.1.md §3.5 ★⑪, §3.3 ★③.

Rule Engine이 benchmark를 읽어 severity를 판정하는 read-side 로직.
direction마다 읽는 칸이 고정 — 구현자가 반대 해석하지 못하게 함수로 박는다.
value_scale·comparison_status 게이팅도 여기서 강제.
"""
from __future__ import annotations

OK = "ok"
WARNING = "warning"
CRITICAL = "critical"

_FIREABLE_COMPARISON = {"exact", "compatible", "normalized"}
_FIRING_STATUSES = {"verified", "normalized_verified", "provisional", "global_fallback"}


def can_fire(benchmark_status: str | None, comparison_status: str | None, value_scale: str | None) -> bool:
    """
    이 benchmark로 룰을 발화해도 되는가? (★③ + 쟁점E)
    - benchmark_status='missing' → 침묵
    - comparison_status ∈ {incompatible, unknown} → 침묵
    - value_scale 없음 → 비교 금지(100배 오류 방지)
    """
    if benchmark_status not in _FIRING_STATUSES:
        return False
    if comparison_status not in _FIREABLE_COMPARISON:
        return False
    if not value_scale:
        return False
    return True


def severity_for(
    direction: str,
    value: float,
    *,
    warning_min: float | None = None,
    warning_max: float | None = None,
    critical_min: float | None = None,
    critical_max: float | None = None,
) -> str:
    """
    direction별 칸을 읽어 severity 판정 (★⑪). critical 우선.

      higher_better : 값 < warning_min → warning, 값 < critical_min → critical
      lower_better  : 값 > warning_max → warning, 값 > critical_max → critical
      range_target  : 값 < warning_min OR > warning_max → warning,
                      값 < critical_min OR > critical_max → critical
    """
    if direction == "higher_better":
        if critical_min is not None and value < critical_min:
            return CRITICAL
        if warning_min is not None and value < warning_min:
            return WARNING
        return OK

    if direction == "lower_better":
        if critical_max is not None and value > critical_max:
            return CRITICAL
        if warning_max is not None and value > warning_max:
            return WARNING
        return OK

    if direction == "range_target":
        crit = (critical_min is not None and value < critical_min) or (
            critical_max is not None and value > critical_max)
        if crit:
            return CRITICAL
        warn = (warning_min is not None and value < warning_min) or (
            warning_max is not None and value > warning_max)
        if warn:
            return WARNING
        return OK

    raise ValueError(f"unknown direction: {direction}")


# benchmark_status → UI 배지 (테스트 5). 발화/침묵과 별개의 표시용 메타.
_UI_BADGE = {
    "verified": "검증됨",
    "normalized_verified": "정규화-검증됨",
    "provisional": "잠정",
    "missing": "기준없음",
    "global_fallback": "글로벌-대체",
}


def ui_badge(benchmark_status: str | None) -> str:
    return _UI_BADGE.get(benchmark_status or "missing", "기준없음")


def should_generate_insight(comparison_status: str | None, benchmark_status: str | None) -> bool:
    """comparison_status ∈ {incompatible, unknown}이면 insight 생성 금지 (테스트 4)."""
    if comparison_status not in _FIREABLE_COMPARISON:
        return False
    if benchmark_status not in _FIRING_STATUSES:
        return False
    return True
