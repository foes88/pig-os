"""
Threshold Resolver (A-하이브리드 T1-3) — 발화 임계의 권위.

flag ON(USE_GOVERNANCE_BENCHMARKS): rule_configs → operational_defaults → code default.
  - 옛 default_metric_values(ctx.benchmarks)는 threshold source로 쓰지 않는다(§14.6).
flag OFF(기본): 각 룰 모듈의 기존 경로를 그대로 둔다(이 모듈 미사용) — 동작 변화 0.

operational_defaults는 ctx.extra["operational_defaults"][rule_id] = {"warning","critical",...} 로 미리 적재(엔진, T1-5).
direction은 governance KPI면 kpi_definitions가 권위(여기선 값만 해소, 방향 적용은 호출 룰).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.operational_default import OperationalDefault
from app.engine.rule_engine import RuleContext


def governance_enabled() -> bool:
    return bool(settings.use_governance_benchmarks)


def gov_resolve_thresholds(
    ctx: RuleContext, rule_id: str, default_w: float, default_c: float
) -> tuple[float, float, str]:
    """
    flag ON 경로: rule_configs(운영자) → operational_defaults(글로벌) → code default.
    반환 (warning, critical, source). source ∈ {rule_config, operational_default, code_default}.
    """
    extra = ctx.extra or {}
    cfg = (extra.get("rule_configs", {}) or {}).get(rule_id) or {}
    w, c = cfg.get("warning"), cfg.get("critical")
    src = "rule_config" if (w is not None or c is not None) else None

    if w is None or c is None:
        opd = (extra.get("operational_defaults", {}) or {}).get(rule_id) or {}
        if w is None and opd.get("warning") is not None:
            w = opd["warning"]
            src = src or "operational_default"
        if c is None and opd.get("critical") is not None:
            c = opd["critical"]
            src = src or "operational_default"

    if w is None:
        w = default_w
        src = src or "code_default"
    if c is None:
        c = default_c
        src = src or "code_default"
    return w, c, (src or "code_default")


async def load_operational_defaults_map(
    db: AsyncSession, country_code: str | None = None
) -> dict[str, dict]:
    """
    operational_defaults → {rule_id: {"warning","critical","direction","value_scale","scope"}}.
    country_code 지정 시 해당국 우선, 없으면 global. (현재 시드는 전부 global.)
    엔진(T1-5)이 RuleContext.extra["operational_defaults"]에 주입.
    """
    rows = (await db.scalars(select(OperationalDefault))).all()
    out: dict[str, dict] = {}
    for r in rows:
        # 국가 우선: country 매칭이 있으면 global을 덮어씀
        if r.scope == "global" and r.rule_id in out and out[r.rule_id].get("scope") != "global":
            continue
        if country_code is not None and r.country_code not in (None, country_code):
            continue
        prev = out.get(r.rule_id)
        if prev and prev.get("scope") == "country" and r.scope == "global":
            continue
        out[r.rule_id] = {
            "warning": float(r.original_warning) if r.original_warning is not None else None,
            "critical": float(r.original_critical) if r.original_critical is not None else None,
            "direction": r.direction,
            "value_scale": r.value_scale,
            "scope": "country" if r.country_code else "global",
        }
    return out
