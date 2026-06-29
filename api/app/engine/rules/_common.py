"""
공통 임계 해석 + severity 헬퍼 (litter / grow_finish 규칙 공유).

임계 우선순위(말씀하신 "국가별 KPI 조정" 구조):
  1) rule_configs[rule_id]  — 운영자가 /admin/rules 에서 조정 (배포 없이)
  2) benchmarks[kpi]        — 국가별 벤치마크 행 (country_configs/default_metric_values)
  3) code default           — 글로벌 임상 기본값

로직(규칙)은 국가 중립 1벌, 수치(임계)만 위 3계층이 조정한다.
"""
from __future__ import annotations

from app.engine.rule_engine import RuleContext, Severity


def sev_above(value: float, warning: float, critical: float) -> Severity | None:
    """높을수록 나쁜 지표(사산율·FCR·폐사율 등)."""
    if value > critical:
        return Severity.CRITICAL
    if value > warning:
        return Severity.WARNING
    return None


def sev_below(value: float, warning: float, critical: float) -> Severity | None:
    """낮을수록 나쁜 지표(실산자·이유두수·ADG·체중 등)."""
    if value < critical:
        return Severity.CRITICAL
    if value < warning:
        return Severity.WARNING
    return None


def resolve(
    ctx: RuleContext, rule_id: str, kpi: str, default_w: float, default_c: float
) -> tuple[float, float]:
    """rule_config(운영자) → benchmark(국가) → code default 순으로 (warning, critical) 결정.

    A-하이브리드(flag ON): rule_config → operational_defaults → code default.
    옛 default_metric_values(benchmark)는 threshold source에서 제외(§14.6). flag OFF는 기존 경로 유지.
    """
    from app.engine.threshold_resolver import gov_resolve_thresholds, governance_enabled
    if governance_enabled():
        w, c, _ = gov_resolve_thresholds(ctx, rule_id, default_w, default_c)
        return w, c
    cfg = (ctx.extra.get("rule_configs", {}) if ctx.extra else {}).get(rule_id) or {}
    w, c = cfg.get("warning"), cfg.get("critical")
    if w is None or c is None:
        bench = (ctx.benchmarks.get(kpi, {}) if ctx.benchmarks else {}) or {}
        if w is None:
            w = bench.get("warning")
        if c is None:
            c = bench.get("critical")
    return (w if w is not None else default_w, c if c is not None else default_c)
