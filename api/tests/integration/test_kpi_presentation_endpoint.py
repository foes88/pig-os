"""GET /farms/{id}/kpi/presentation — 국가별 표현 정책 노출 (STEP B 보완).

라우트는 직렬화만 한다. 조인·정렬·headline 선택은 service(resolve_display_kpis/pick_headline).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.kpi_policy import CountryKpiPolicy
from app.db.models.kpi_presentation import CountryKpiPresentation
from app.db.models.platform import Farm, Organization, User

pytestmark = pytest.mark.anyio


def _g(kpi, **kw):
    base = dict(scope_level="GLOBAL", kpi_code=kpi, compute_enabled=True, display_role="PRIMARY",
                rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="t")
    base.update(kw)
    return CountryKpiPolicy(**base)


async def test_presentation_endpoint_returns_ordered_items(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
):
    admin = User(org_id=test_org.id, username="pres_admin", email="pres@x.io", name="A",
                 password_hash=hash_password("Test1234!"), role="FARM_OWNER",
                 system_role="SUPER_ADMIN")
    db.add(admin)
    country = test_farm.country
    db.add_all([
        _g("PSY", priority_class="NORTH_STAR"),   # headline
        _g("NPD"),
        _g("BARE"),                                # presentation row 없음
        _g("HID", display_role="HIDDEN"),
        # 표현: NPD 를 앞(10), PSY 는 headline 이라 순서와 무관
        CountryKpiPresentation(scope_level="GLOBAL", kpi_code="NPD", display_order=10,
                               display_order_override=True, decision_status="APPROVED"),
        CountryKpiPresentation(scope_level="COUNTRY", country_code=country, kpi_code="NPD",
                               local_label="Dias não produtivos", decision_status="APPROVED"),
    ])
    await db.flush()

    token = create_access_token(str(admin.id), str(admin.org_id), ["SUPER_ADMIN"])
    r = await client.get(f"/api/v1/farms/{test_farm.id}/kpi/presentation",
                         headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["country"] == country
    assert body["headline_kpi"] == "PSY"
    items = {x["kpi_code"]: x for x in body["items"]}
    assert "HID" not in items, "HIDDEN 은 제외"
    # §4-1: presentation row 가 없어도 CKP visible 이면 포함(표현값만 null)
    assert "BARE" in items
    assert items["BARE"]["display_order"] is None and items["BARE"]["local_label"] is None
    assert items["NPD"]["local_label"] == "Dias não produtivos"
    # 정렬은 백엔드가 확정 — headline 이 항상 첫 항목
    assert body["items"][0]["kpi_code"] == "PSY"


async def test_presentation_endpoint_requires_auth(client: AsyncClient, test_farm: Farm):
    r = await client.get(f"/api/v1/farms/{test_farm.id}/kpi/presentation")
    assert r.status_code in (401, 403)


async def test_policy_endpoint_has_no_presentation_axis(
    client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm: Farm,
):
    """축 분리 회귀: 거버넌스 엔드포인트는 display_order/local_label 을 노출하지 않는다."""
    admin = User(org_id=test_org.id, username="axis_admin", email="axis@x.io", name="A",
                 password_hash=hash_password("Test1234!"), role="FARM_OWNER",
                 system_role="SUPER_ADMIN")
    db.add(admin)
    db.add(_g("PSY"))
    await db.flush()
    token = create_access_token(str(admin.id), str(admin.org_id), ["SUPER_ADMIN"])
    r = await client.get(f"/api/v1/farms/{test_farm.id}/kpi/policy",
                         headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    for item in r.json():
        assert "display_order" not in item
        assert "local_label" not in item
