"""KPI 정책 리졸버 엣지 (v0.4 §4.2~4.3) — 기존 resolver 테스트 미커버분.

- TENANT scope: GLOBAL→COUNTRY→TENANT 전체 상속 체인 + resolved_from 순서
- effective dating: effective_from 미래 / effective_to 과거 행은 무시(시점 밖)
- production_stage 특정 FARM_TYPE 행은 해당 stage 에만 적용
"""
import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kpi_policy import CountryKpiPolicy
from app.services.kpi_policy_resolver import resolve_kpi_policy

pytestmark = pytest.mark.anyio


def _global(kpi, **kw):
    base = dict(scope_level="GLOBAL", kpi_code=kpi, compute_enabled=True, display_role="SECONDARY",
                rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="test")
    base.update(kw)
    return CountryKpiPolicy(**base)


async def test_tenant_overrides_full_chain(db: AsyncSession):
    tid = uuid.UUID("00000000-0000-0000-0000-0000000000aa")
    db.add(_global("PSY", display_role="SECONDARY"))
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="US", kpi_code="PSY",
                            display_role="PRIMARY", decision_status="APPROVED", decided_by="test"))
    db.add(CountryKpiPolicy(scope_level="TENANT", tenant_id=tid, kpi_code="PSY",
                            priority_class="DRIVER", decision_status="APPROVED", decided_by="test"))
    await db.flush()
    r = await resolve_kpi_policy(db, kpi_code="PSY", country="US", tenant_id=tid)
    assert r.display_role == "PRIMARY"       # COUNTRY override
    assert r.priority_class == "DRIVER"      # TENANT override
    assert r.compute_enabled is True         # GLOBAL 상속
    assert r.resolved_from == ["GLOBAL", "COUNTRY", "TENANT"]  # 낮은→높은 scope 순


async def test_future_effective_from_ignored(db: AsyncSession):
    db.add(_global("BAR", display_role="SECONDARY"))
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="US", kpi_code="BAR",
                            display_role="PRIMARY", effective_from=date(2099, 1, 1),
                            decision_status="APPROVED", decided_by="test"))
    await db.flush()
    r = await resolve_kpi_policy(db, kpi_code="BAR", country="US")
    assert r.display_role == "SECONDARY"     # 미래 발효 override 무시 → GLOBAL
    assert r.resolved_from == ["GLOBAL"]


async def test_past_effective_to_ignored(db: AsyncSession):
    db.add(_global("BAZ", display_role="SECONDARY"))
    db.add(CountryKpiPolicy(scope_level="COUNTRY", country_code="US", kpi_code="BAZ",
                            display_role="PRIMARY", effective_to=date(2000, 1, 1),
                            decision_status="APPROVED", decided_by="test"))
    await db.flush()
    r = await resolve_kpi_policy(db, kpi_code="BAZ", country="US")
    assert r.display_role == "SECONDARY"     # 만료된 override 무시 → GLOBAL


async def test_production_stage_specific_row(db: AsyncSession):
    db.add(_global("QUX", display_role="SECONDARY"))
    db.add(CountryKpiPolicy(scope_level="FARM_TYPE", country_code="US", farm_type="SOW_FARM",
                            production_stage="BREEDING", kpi_code="QUX", priority_class="GUARDRAIL",
                            decision_status="APPROVED", decided_by="test"))
    await db.flush()
    breeding = await resolve_kpi_policy(db, kpi_code="QUX", country="US",
                                        farm_type="SOW_FARM", production_stage="BREEDING")
    nursery = await resolve_kpi_policy(db, kpi_code="QUX", country="US",
                                       farm_type="SOW_FARM", production_stage="NURSERY")
    assert breeding.priority_class == "GUARDRAIL"   # stage 일치
    assert nursery.priority_class is None           # stage 불일치 → 미적용
