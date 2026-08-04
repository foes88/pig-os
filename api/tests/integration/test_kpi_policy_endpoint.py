"""GET /farms/{id}/kpi/policy — resolved 정책 노출 (v0.4 B1 배선)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.kpi_policy import CountryKpiPolicy
from app.db.models.platform import Farm, Organization, User

pytestmark = pytest.mark.anyio


async def test_kpi_policy_endpoint_returns_display_kpis(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
):
    admin = User(org_id=test_org.id, username="ckp_admin", email="ckp@x.io", name="A",
                 password_hash=hash_password("Test1234!"), role="FARM_OWNER", system_role="SUPER_ADMIN")
    db.add(admin)
    # 표시 대상 2 + 숨김 1 seed
    db.add_all([
        CountryKpiPolicy(scope_level="GLOBAL", kpi_code="PSY", compute_enabled=True, display_role="PRIMARY",
                         rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                         api_export_policy="TENANT_ONLY", evidence_status="VERIFIED",
                         decision_status="APPROVED", decided_by="t"),
        CountryKpiPolicy(scope_level="GLOBAL", kpi_code="MSY", compute_enabled=True, display_role="SECONDARY",
                         rule_enabled=False, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                         api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="t"),
        CountryKpiPolicy(scope_level="GLOBAL", kpi_code="HID", compute_enabled=True, display_role="HIDDEN",
                         rule_enabled=True, benchmark_exposure="NONE", prediction_feature=False,
                         api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="t"),
    ])
    await db.flush()

    token = create_access_token(str(admin.id), str(admin.org_id), ["SUPER_ADMIN"])
    r = await client.get(f"/api/v1/farms/{test_farm.id}/kpi/policy",
                         headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    codes = {x["kpi_code"]: x for x in r.json()}
    assert "PSY" in codes and codes["PSY"]["display_role"] == "PRIMARY"
    assert "MSY" in codes and codes["MSY"]["display_role"] == "SECONDARY"
    assert "HID" not in codes, "HIDDEN은 표시 목록에서 제외"


async def test_kpi_policy_endpoint_requires_auth(client: AsyncClient, test_farm: Farm):
    r = await client.get(f"/api/v1/farms/{test_farm.id}/kpi/policy")
    assert r.status_code in (401, 403)
