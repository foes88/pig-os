"""KPI 정책·표현 리졸버 (COUNTRY_KPI_RULE_SPEC v0.3.1 §4.2~4.3 + v0.4).

축 분리:
  country_kpi_policy       → resolve_kpi_policy()        그 KPI 를 써도 되는가 / 어느 군인가
  country_kpi_presentation → resolve_kpi_presentation()  뭐라 부르고 몇 번째인가
  두 결과의 합성            → resolve_display_kpis()      ★ application/service layer

★ 합성을 라우트 함수 안에서 하지 말 것.
  대시보드·리포트·모바일 API·AI context 가 같은 목록을 필요로 하므로, 라우트에 조인·정렬을
  두면 네 군데에 복제된다. 라우트는 이 함수 결과를 직렬화만 한다.

공통 규칙:
- 상속 체인 GLOBAL → COUNTRY → FARM_TYPE → TENANT. 하위가 NULL 아닌 축만 override.
- decision_status='APPROVED' 행만 반영(fail-closed). 미승인/미검증 무시.
- 유효기간: effective_from <= as_of <= (effective_to or ∞). 두 리졸버 모두 동일 적용.
- GLOBAL 행 없으면 정책은 None(미거버넌스 → 호출자가 안전 처리).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kpi_policy import CountryKpiPolicy
from app.db.models.kpi_presentation import CountryKpiPresentation

# 거버넌스 벡터 축(상속 대상) — display_order 는 여기 없다(표현 축, CKPRES 소관).
_VECTOR = (
    "compute_enabled", "display_role", "priority_class", "rule_enabled",
    "benchmark_exposure", "prediction_feature", "api_export_policy", "evidence_status",
)
_SCOPE_RANK = {"GLOBAL": 0, "COUNTRY": 1, "FARM_TYPE": 2, "TENANT": 3}
_NULLS_LAST = 10**9


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


@dataclass
class ResolvedKpiPresentation:
    """표현 벡터 해석 결과. 행이 하나도 없어도 None 이 아니라 전부 NULL 인 객체를 준다
    (CKP 가 visible 인 KPI 는 presentation row 유무와 무관하게 노출돼야 하므로)."""
    kpi_code: str
    display_order: int | None = None
    local_label: str | None = None
    resolved_from: list[str] = field(default_factory=list)


@dataclass
class DisplayKpi:
    """거버넌스 + 표현 합성 결과 — 대시보드/리포트/모바일/AI context 공용 단위."""
    kpi_code: str
    # 거버넌스(CKP)
    compute_enabled: bool | None = None
    display_role: str | None = None
    priority_class: str | None = None
    rule_enabled: bool | None = None
    benchmark_exposure: str | None = None
    prediction_feature: bool | None = None
    api_export_policy: str | None = None
    evidence_status: str | None = None
    resolved_from: list[str] | None = None
    # 표현(CKPRES)
    display_order: int | None = None
    local_label: str | None = None


def _effective(r, ref: date) -> bool:
    return ((r.effective_from is None or r.effective_from <= ref)
            and (r.effective_to is None or r.effective_to >= ref))


def _row_matches(r, country: str | None, farm_type: str | None,
                 stage: str | None, tenant_id: UUID | None) -> bool:
    if r.scope_level == "GLOBAL":
        return True
    if r.scope_level == "COUNTRY":
        return country is not None and r.country_code == country
    if r.scope_level == "FARM_TYPE":
        return (country is not None and r.country_code == country
                and farm_type is not None and r.farm_type == farm_type
                and (getattr(r, "production_stage", None) is None
                     or r.production_stage == stage))
    if r.scope_level == "TENANT":
        return tenant_id is not None and r.tenant_id == tenant_id
    return False


async def resolve_kpi_policy(
    db: AsyncSession, *, kpi_code: str, country: str | None = None,
    farm_type: str | None = None, production_stage: str | None = None,
    tenant_id: UUID | None = None, ref: date | None = None,
) -> ResolvedKpiPolicy | None:
    """거버넌스 벡터만 해석. 표현(display_order/local_label)은 여기서 다루지 않는다."""
    ref = ref or date.today()
    stmt = select(CountryKpiPolicy).where(
        CountryKpiPolicy.kpi_code == kpi_code,
        CountryKpiPolicy.decision_status == "APPROVED",
    )
    rows = [
        r for r in (await db.execute(stmt)).scalars().all()
        if _effective(r, ref) and _row_matches(r, country, farm_type, production_stage, tenant_id)
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


async def resolve_kpi_presentation(
    db: AsyncSession, *, kpi_code: str, country: str | None = None,
    farm_type: str | None = None, tenant_id: UUID | None = None,
    ref: date | None = None,
) -> ResolvedKpiPresentation:
    """표현 벡터만 해석.

    display_order 상속은 NULL 유무가 아니라 display_order_override 플래그로 판단한다.
      override=false → 그 스코프는 순서에 관여하지 않음(상위값 유지)
      override=true  → 그 스코프 값 채택. 값이 NULL 이면 명시적으로 마지막이지 상속이 아니다.
    이 구분이 없으면 "브라질에서는 이 KPI 를 맨 뒤로" 를 표현할 수 없다.
    local_label 은 NULL=상속(현재 clear semantics 없음).
    """
    ref = ref or date.today()
    stmt = select(CountryKpiPresentation).where(
        CountryKpiPresentation.kpi_code == kpi_code,
        CountryKpiPresentation.decision_status == "APPROVED",
    )
    rows = [
        r for r in (await db.execute(stmt)).scalars().all()
        if _effective(r, ref) and _row_matches(r, country, farm_type, None, tenant_id)
    ]
    rows.sort(key=lambda r: _SCOPE_RANK[r.scope_level])
    out = ResolvedKpiPresentation(kpi_code=kpi_code)
    for r in rows:
        contributed = False
        if r.display_order_override:
            out.display_order = r.display_order  # NULL 이어도 채택 = 맨 뒤
            contributed = True
        if r.local_label is not None:
            out.local_label = r.local_label
            contributed = True
        if contributed:
            out.resolved_from.append(r.scope_level)
    return out


def sort_display_kpis(items: list[DisplayKpi]) -> list[DisplayKpi]:
    """표시 정렬 규약: ① NORTH_STAR(headline) 최상단 ② display_order ASC(NULL 마지막)
    ③ 동순위는 kpi_code 로 결정론 고정. 프론트에서 재정렬 금지."""
    return sorted(items, key=lambda r: (
        0 if r.priority_class == "NORTH_STAR" else 1,
        r.display_order if r.display_order is not None else _NULLS_LAST,
        r.kpi_code,
    ))


def pick_headline(items: list[DisplayKpi]) -> str | None:
    """국가별 headline KPI = priority_class NORTH_STAR (uq_ckp_north_star 가 국가당 1개 강제)."""
    for r in items:
        if r.priority_class == "NORTH_STAR":
            return r.kpi_code
    return None


async def resolve_display_kpis(
    db: AsyncSession, *, country: str | None = None, farm_type: str | None = None,
    production_stage: str | None = None, tenant_id: UUID | None = None,
    ref: date | None = None,
) -> list[DisplayKpi]:
    """★ 합성 지점 — 거버넌스(CKP) ⨝ 표현(CKPRES).

    포함 기준은 CKP 다: compute_enabled AND display_role in (PRIMARY, SECONDARY).
    Presentation row 가 없는 KPI 도 CKP 가 visible 이면 포함한다(표현값만 NULL).
    """
    stmt = select(CountryKpiPolicy.kpi_code).where(
        CountryKpiPolicy.scope_level == "GLOBAL",
        CountryKpiPolicy.decision_status == "APPROVED",
    ).distinct()
    codes = [c for (c,) in (await db.execute(stmt)).all()]

    out: list[DisplayKpi] = []
    for code in codes:
        rp = await resolve_kpi_policy(
            db, kpi_code=code, country=country, farm_type=farm_type,
            production_stage=production_stage, tenant_id=tenant_id, ref=ref,
        )
        if not (rp and rp.compute_enabled and rp.display_role in ("PRIMARY", "SECONDARY")):
            continue  # HIDDEN·미거버넌스는 여기서 탈락
        pr = await resolve_kpi_presentation(
            db, kpi_code=code, country=country, farm_type=farm_type,
            tenant_id=tenant_id, ref=ref,
        )
        out.append(DisplayKpi(
            kpi_code=code,
            compute_enabled=rp.compute_enabled, display_role=rp.display_role,
            priority_class=rp.priority_class, rule_enabled=rp.rule_enabled,
            benchmark_exposure=rp.benchmark_exposure, prediction_feature=rp.prediction_feature,
            api_export_policy=rp.api_export_policy, evidence_status=rp.evidence_status,
            resolved_from=rp.resolved_from,
            display_order=pr.display_order, local_label=pr.local_label,
        ))
    return sort_display_kpis(out)
