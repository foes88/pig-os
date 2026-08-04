"""resolve_display_kpis 의 TENANT 상호작용 (v0.4 §4.3) — 표시목록 구성 정확성.

resolve_display_kpis 는 GLOBAL 코드 목록을 tenant 포함 상속 해석 후
compute_enabled + display_role in (PRIMARY,SECONDARY) 만 남긴다.
→ TENANT 가 display_role=HIDDEN / compute_enabled=False 로 덮으면 목록에서 빠져야 함.
"""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kpi_policy import CountryKpiPolicy
from app.services.kpi_policy_resolver import resolve_display_kpis

pytestmark = pytest.mark.anyio


def _global(kpi, **kw):
    base = dict(scope_level="GLOBAL", kpi_code=kpi, compute_enabled=True, display_role="PRIMARY",
                rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="test")
    base.update(kw)
    return CountryKpiPolicy(**base)


async def test_tenant_hidden_drops_from_display_list(db: AsyncSession):
    tid = uuid.UUID("00000000-0000-0000-0000-0000000000bb")
    db.add(_global("AAA", display_role="PRIMARY"))
    db.add(_global("BBB", display_role="PRIMARY"))
    # 이 tenant 에서만 BBB 를 숨김
    db.add(CountryKpiPolicy(scope_level="TENANT", tenant_id=tid, kpi_code="BBB",
                            display_role="HIDDEN", decision_status="APPROVED", decided_by="test"))
    await db.flush()

    with_tenant = {r.kpi_code for r in await resolve_display_kpis(db, tenant_id=tid)}
    without_tenant = {r.kpi_code for r in await resolve_display_kpis(db)}

    assert "AAA" in with_tenant and "BBB" not in with_tenant   # BBB 숨김 반영
    assert "AAA" in without_tenant and "BBB" in without_tenant  # tenant 없으면 둘 다


async def test_tenant_compute_off_drops_from_display_list(db: AsyncSession):
    tid = uuid.UUID("00000000-0000-0000-0000-0000000000cc")
    db.add(_global("CCC", display_role="PRIMARY"))
    db.add(CountryKpiPolicy(scope_level="TENANT", tenant_id=tid, kpi_code="CCC",
                            compute_enabled=False, decision_status="APPROVED", decided_by="test"))
    await db.flush()
    with_tenant = {r.kpi_code for r in await resolve_display_kpis(db, tenant_id=tid)}
    assert "CCC" not in with_tenant  # 계산 꺼짐 → 표시목록 제외
