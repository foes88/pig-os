"""KPI 정책 리졸버 (COUNTRY_KPI_RULE_SPEC v0.3.1 §4.2~4.3 + v0.4).

country_kpi_policy 원본을 상속 해석해 (kpi_code, country, farm_type, production_stage, tenant)에 대한
최종 정책 벡터를 반환. 프론트·룰엔진·API는 이 결과만 사용(원본 직접 조회 금지).

규칙:
- 상속 체인 GLOBAL → COUNTRY → FARM_TYPE → TENANT. 하위가 NULL 아닌 축만 override.
- decision_status='APPROVED' 행만 반영(fail-closed). 미승인/미검증 무시.
- effective_from<=today<=(effective_to or ∞).
- GLOBAL 행 없으면 None(해당 KPI는 미거버넌스 → 호출자가 안전 처리).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kpi_policy import CountryKpiPolicy

# 정책 벡터 축(상속 대상)
_VECTOR = (
    "compute_enabled", "display_role", "priority_class", "rule_enabled",
    "benchmark_exposure", "prediction_feature", "api_export_policy", "evidence_status",
)
_SCOPE_RANK = {"GLOBAL": 0, "COUNTRY": 1, "FARM_TYPE": 2, "TENANT": 3}


@dataclass
class ResolvedKpiPolicy:
    kpi_code: str
    compute_enabled: bool | None = None
    display_role: str | None = None
    priority_class: str | None = None
    rule_enabled: bool | None = None
    benchmark_exposure: str | None = None
    prediction_feature: bool | None = None
    api_export_policy: str | None = None
    evidence_status: str | None = None
    resolved_from: list[str] | None = None  # 어떤 scope들이 기여했나(감사)


def _row_matches(r: CountryKpiPolicy, country: str | None, farm_type: str | None,
                 stage: str | None, tenant_id: UUID | None) -> bool:
    if r.scope_level == "GLOBAL":
        return True
    if r.scope_level == "COUNTRY":
        return country is not None and r.country_code == country
    if r.scope_level == "FARM_TYPE":
        return (country is not None and r.country_code == country
                and farm_type is not None and r.farm_type == farm_type
                and (r.production_stage is None or r.production_stage == stage))
    if r.scope_level == "TENANT":
        return tenant_id is not None and r.tenant_id == tenant_id
    return False


async def resolve_kpi_policy(
    db: AsyncSession, *, kpi_code: str, country: str | None = None,
    farm_type: str | None = None, production_stage: str | None = None,
    tenant_id: UUID | None = None, ref: date | None = None,
) -> ResolvedKpiPolicy | None:
    ref = ref or date.today()
    stmt = select(CountryKpiPolicy).where(
        CountryKpiPolicy.kpi_code == kpi_code,
        CountryKpiPolicy.decision_status == "APPROVED",
        CountryKpiPolicy.effective_from <= ref,
    )
    rows = [
        r for r in (await db.execute(stmt)).scalars().all()
        if (r.effective_to is None or r.effective_to >= ref)
        and _row_matches(r, country, farm_type, production_stage, tenant_id)
    ]
    if not any(r.scope_level == "GLOBAL" for r in rows):
        return None  # fail-closed: GLOBAL 기준 없으면 미거버넌스

    rows.sort(key=lambda r: _SCOPE_RANK[r.scope_level])  # 낮은 scope부터, 높은 scope가 override
    resolved = ResolvedKpiPolicy(kpi_code=kpi_code, resolved_from=[])
    for r in rows:
        contributed = False
        for f in _VECTOR:
            v = getattr(r, f)
            if v is not None:
                setattr(resolved, f, v)
                contributed = True
        if contributed:
            resolved.resolved_from.append(r.scope_level)
    return resolved


async def resolve_display_kpis(
    db: AsyncSession, *, country: str | None = None, farm_type: str | None = None,
    production_stage: str | None = None, tenant_id: UUID | None = None,
) -> list[ResolvedKpiPolicy]:
    """표시 대상(compute+display PRIMARY/SECONDARY) KPI 목록 — 대시보드/리포트 구성용."""
    stmt = select(CountryKpiPolicy.kpi_code).where(
        CountryKpiPolicy.scope_level == "GLOBAL",
        CountryKpiPolicy.decision_status == "APPROVED",
    ).distinct()
    codes = [c for (c,) in (await db.execute(stmt)).all()]
    out: list[ResolvedKpiPolicy] = []
    for code in codes:
        rp = await resolve_kpi_policy(
            db, kpi_code=code, country=country, farm_type=farm_type,
            production_stage=production_stage, tenant_id=tenant_id,
        )
        if rp and rp.compute_enabled and rp.display_role in ("PRIMARY", "SECONDARY"):
            out.append(rp)
    return out
