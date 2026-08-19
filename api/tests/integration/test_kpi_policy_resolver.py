"""KPI 정책 리졸버 — 상속·APPROVED만·fail-closed (v0.4 §4.2~4.3)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kpi_policy import CountryKpiPolicy
from app.services.kpi_policy_resolver import resolve_display_kpis, resolve_kpi_policy

pytestmark = pytest.mark.anyio


def _global(kpi, **kw):
    base = dict(scope_level="GLOBAL", kpi_code=kpi, compute_enabled=True, display_role="PRIMARY",
                rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="test")
    base.update(kw)
    return CountryKpiPolicy(**base)


async def test_global_only_resolves(db: AsyncSession):
    db.add(_global("PSY", display_role="PRIMARY", evidence_status="VERIFIED"))
    await db.flush()
    r = await resolve_kpi_policy(db, kpi_code="PSY", country="US")
    assert r is not None and r.display_role == "PRIMARY" and r.compute_enabled is True
    assert r.resolved_from == ["GLOBAL"]


async def test_country_overrides_single_axis(db: AsyncSession):
    db.add(_global("MSY", display_role="SECONDARY"))
    # US에서만 MSY를 PRIMARY로 (다른 축은 상속)
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="US", kpi_code="MSY",
                            display_role="PRIMARY", decision_status="APPROVED", decided_by="test"))
    await db.flush()
    us = await resolve_kpi_policy(db, kpi_code="MSY", country="US")
    kr = await resolve_kpi_policy(db, kpi_code="MSY", country="KR")
    assert us.display_role == "PRIMARY" and us.compute_enabled is True  # override + 상속
    assert kr.display_role == "SECONDARY"  # KR은 GLOBAL 유지
    assert "COUNTRY" in us.resolved_from


async def test_proposed_row_ignored(db: AsyncSession):
    db.add(_global("NPD", display_role="SECONDARY"))
    # PROPOSED override는 무시돼야 함
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="US", kpi_code="NPD",
                            display_role="HIDDEN", decision_status="PROPOSED", decided_by="test"))
    await db.flush()
    r = await resolve_kpi_policy(db, kpi_code="NPD", country="US")
    assert r.display_role == "SECONDARY", "PROPOSED override 무시(APPROVED만)"


async def test_no_global_is_none_fail_closed(db: AsyncSession):
    # COUNTRY만 있고 GLOBAL 없음 → fail-closed None
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="US", kpi_code="FOO",
                            display_role="PRIMARY", decision_status="APPROVED", decided_by="test"))
    await db.flush()
    assert await resolve_kpi_policy(db, kpi_code="FOO", country="US") is None


async def test_farm_type_scope_matches_country_and_type(db: AsyncSession):
    db.add(_global("ADG", display_role="SECONDARY"))
    db.add(CountryKpiPolicy(scope_level="FARM_TYPE", country_code="US", farm_type="FARROW_TO_FINISH",
                            kpi_code="ADG", priority_class="DRIVER", decision_status="APPROVED", decided_by="test"))
    await db.flush()
    f2f = await resolve_kpi_policy(db, kpi_code="ADG", country="US", farm_type="FARROW_TO_FINISH")
    sow = await resolve_kpi_policy(db, kpi_code="ADG", country="US", farm_type="SOW_FARM")
    assert f2f.priority_class == "DRIVER"       # FARM_TYPE 매칭
    assert sow.priority_class is None            # 다른 farm_type엔 미적용


async def test_display_list_filters_computed_visible(db: AsyncSession):
    db.add(_global("PSY", display_role="PRIMARY"))
    db.add(_global("HIDDENK", display_role="HIDDEN", rule_enabled=True))
    db.add(_global("OFFK", compute_enabled=False, display_role="SECONDARY"))
    await db.flush()
    codes = {r.kpi_code for r in await resolve_display_kpis(db, country="US")}
    assert "PSY" in codes and "HIDDENK" not in codes and "OFFK" not in codes


# ── Presentation Policy STEP B — display_order ────────────────────────────────

async def test_display_order_inherits_country_over_global(db: AsyncSession):
    """게이트2: display_order 가 상속 체인(GLOBAL→COUNTRY)에 포함되는가."""
    db.add(_global("ORD1", display_role="PRIMARY", display_order=30))
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="BR", kpi_code="ORD1",
                            display_order=10, decision_status="APPROVED", decided_by="test"))
    await db.flush()
    br = await resolve_kpi_policy(db, kpi_code="ORD1", country="BR")
    kr = await resolve_kpi_policy(db, kpi_code="ORD1", country="KR")
    assert br.display_order == 10, "COUNTRY 값이 GLOBAL 을 덮어야 함"
    assert kr.display_order == 30, "COUNTRY 행 없으면 GLOBAL 유지"
    assert br.display_role == "PRIMARY"  # 다른 축은 상속 그대로


async def test_display_list_sorted_north_star_then_order(db: AsyncSession):
    """게이트: NORTH_STAR 최상단 → display_order ASC → NULL 마지막."""
    db.add(_global("SB", display_role="PRIMARY", display_order=20))
    db.add(_global("SA", display_role="PRIMARY", display_order=10))
    db.add(_global("SNULL", display_role="PRIMARY"))            # display_order 없음
    db.add(_global("SHEAD", display_role="PRIMARY", display_order=99,
                   priority_class="NORTH_STAR"))                 # headline
    await db.flush()
    codes = [r.kpi_code for r in await resolve_display_kpis(db, country="BR")]
    codes = [c for c in codes if c in ("SHEAD", "SA", "SB", "SNULL")]
    assert codes == ["SHEAD", "SA", "SB", "SNULL"], codes
