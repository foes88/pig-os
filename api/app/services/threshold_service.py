"""
임계값 관리 — 농장이 자기 KPI 임계값을 보고, 필요시 농장 스코프로 override (#4).

유효값 = 농장 > 국가(region) > 글로벌(system) 우선순위 해석.
농장 override = scope_type='farm', scope_code=farm.id 행 upsert.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.db.models.config import DefaultMetricValue
from app.db.models.platform import Farm

_SCOPE_RANK = {"farm": 0, "region": 1, "market": 2, "system": 3}
_SCOPE_LABEL = {"farm": "farm", "region": "country", "market": "market", "system": "global"}


async def list_effective(db: AsyncSession, farm: Farm) -> list[dict]:
    """농장에 유효한 모든 메트릭 임계값 + 어느 scope에서 왔는지."""
    rows = list(await db.scalars(
        select(DefaultMetricValue).where(
            DefaultMetricValue.scope_code.in_([str(farm.id), farm.country, "SYSTEM"]),
        )
    ))
    rows = [r for r in rows if (
        (r.scope_type == "farm" and r.scope_code == str(farm.id))
        or (r.scope_type == "region" and r.scope_code == farm.country)
        or (r.scope_type == "system" and r.scope_code == "SYSTEM")
    )]
    by_metric: dict[str, DefaultMetricValue] = {}
    for r in rows:
        cur = by_metric.get(r.metric_code)
        if cur is None or _SCOPE_RANK[r.scope_type] < _SCOPE_RANK[cur.scope_type]:
            by_metric[r.metric_code] = r
    out = []
    for code, r in sorted(by_metric.items()):
        out.append({
            "metric_code": code,
            "warning": float(r.warning_threshold) if r.warning_threshold is not None else None,
            "critical": float(r.critical_threshold) if r.critical_threshold is not None else None,
            "avg": float(r.benchmark_avg) if r.benchmark_avg is not None else None,
            "top25": float(r.benchmark_top25) if r.benchmark_top25 is not None else None,
            "target": float(r.target_value) if r.target_value is not None else None,
            "direction": r.alert_direction or "below",
            "unit": r.unit_code or "",
            "confidence": r.confidence,
            "is_proxy": bool(r.is_proxy),
            "source": r.source_ref,
            "scope": _SCOPE_LABEL.get(r.scope_type, r.scope_type),
            "is_override": r.scope_type == "farm",
        })
    return out


async def set_override(
    db: AsyncSession, farm: Farm, metric_code: str,
    warning: float | None, critical: float | None,
) -> dict:
    """농장 스코프 override upsert. 기준 메타(direction/unit)는 상위 scope에서 상속."""
    # 기존 farm 행
    farm_row = await db.scalar(select(DefaultMetricValue).where(
        DefaultMetricValue.scope_type == "farm",
        DefaultMetricValue.scope_code == str(farm.id),
        DefaultMetricValue.metric_code == metric_code,
    ))
    # 상속용: 현재 유효값(국가/글로벌)에서 direction/unit
    effective = {e["metric_code"]: e for e in await list_effective(db, farm)}.get(metric_code)
    direction = effective["direction"] if effective else "below"
    unit = effective["unit"] if effective else ""
    # 방향 일관성 검증(QA 룰엔진 M1): warning/critical 둘 다 주어지면 메트릭 방향과 정합해야.
    # below(낮을수록 나쁨)=critical≤warning, above(높을수록 나쁨)=critical≥warning. 역전 시 severity 오분류.
    if warning is not None and critical is not None:
        if direction == "below" and critical > warning:
            raise ValidationError(
                f"For a 'below' metric, critical ({critical}) must be <= warning ({warning})")
        if direction == "above" and critical < warning:
            raise ValidationError(
                f"For an 'above' metric, critical ({critical}) must be >= warning ({warning})")
    if farm_row:
        farm_row.warning_threshold = warning
        farm_row.critical_threshold = critical
        farm_row.confidence = "high"
        farm_row.source_ref = "farm_override"
    else:
        farm_row = DefaultMetricValue(
            scope_type="farm", scope_code=str(farm.id), metric_code=metric_code,
            warning_threshold=warning, critical_threshold=critical,
            alert_direction=direction, unit_code=unit,
            confidence="high", is_proxy=False, source_ref="farm_override",
        )
        db.add(farm_row)
    await db.commit()
    return {e["metric_code"]: e for e in await list_effective(db, farm)}[metric_code]


async def clear_override(db: AsyncSession, farm: Farm, metric_code: str) -> int:
    """농장 override 삭제 → 국가/글로벌 값으로 복귀."""
    row = await db.scalar(select(DefaultMetricValue).where(
        DefaultMetricValue.scope_type == "farm",
        DefaultMetricValue.scope_code == str(farm.id),
        DefaultMetricValue.metric_code == metric_code,
    ))
    if not row:
        return 0
    await db.delete(row)
    await db.commit()
    return 1
