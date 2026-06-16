"""임계값 라우터 권한 회귀 (C2-Q3) — pigos_test.

검증:
- GET /thresholds: 농장 멤버면 누구나(워커 포함) 조회 가능.
- PATCH /thresholds/{metric}: OWNER/MANAGER/ADMIN만 (워커 403).
- 비멤버: 농장 접근 자체가 403 (FarmDep can_access_farm).
"""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.platform import User, UserFarm

pytestmark = pytest.mark.asyncio


async def _member(db, user, farm):
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=user.system_role))
    await db.flush()
    token = create_access_token(str(user.id), str(user.org_id), [user.system_role])
    return {"Authorization": f"Bearer {token}"}


async def test_worker_can_read_but_cannot_override(client: AsyncClient, db, test_user, test_farm):
    test_user.role = "FARM_WORKER"
    test_user.system_role = "FARM_WORKER"
    await db.flush()
    headers = await _member(db, test_user, test_farm)

    # 읽기: 멤버이므로 200
    r_get = await client.get(f"/api/v1/farms/{test_farm.id}/thresholds", headers=headers)
    assert r_get.status_code == 200, r_get.text

    # override: 워커는 403
    r_patch = await client.patch(
        f"/api/v1/farms/{test_farm.id}/thresholds/STILLBORN_RATE",
        headers=headers, json={"warning": 6.0, "critical": 10.0},
    )
    assert r_patch.status_code == 403, r_patch.text


async def test_owner_can_override(client: AsyncClient, db, test_user, test_farm):
    # test_user 기본 system_role = FARM_OWNER
    headers = await _member(db, test_user, test_farm)
    r = await client.patch(
        f"/api/v1/farms/{test_farm.id}/thresholds/STILLBORN_RATE",
        headers=headers, json={"warning": 6.0, "critical": 10.0},
    )
    assert r.status_code == 200, r.text
    assert r.json()["scope"] == "farm"


async def test_non_member_forbidden(client: AsyncClient, db, test_org, test_farm):
    # 농장 멤버십 없는 다른 사용자 → 농장 접근 403
    other = User(email="outsider@pigos.io", org_id=test_org.id, name="Outsider",
                 system_role="FARM_OWNER", role="FARM_OWNER", active=True, password_hash="x")
    db.add(other)
    await db.flush()
    token = create_access_token(str(other.id), str(other.org_id), [other.system_role])
    headers = {"Authorization": f"Bearer {token}"}
    r = await client.get(f"/api/v1/farms/{test_farm.id}/thresholds", headers=headers)
    assert r.status_code == 403, r.text


async def test_per_farm_role_isolation(client: AsyncClient, db, test_org, test_user, test_farm):
    """finding #2 해소: 한 사용자가 농장마다 다른 역할일 때 농장별로 정확히 판정.
    농장A=OWNER → override 200, 농장B=WORKER → 403.
    (구버전은 전역 system_role만 봐서 둘 다 통과하던 버그)."""
    import uuid as _uuid

    from app.db.models.platform import Farm

    farm_b = Farm(org_id=test_org.id, farm_code=f"TEST-{_uuid.uuid4().hex[:6].upper()}",
                  name="Farm B", country="KR", timezone="Asia/Seoul")
    db.add(farm_b)
    await db.flush()

    db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
    db.add(UserFarm(user_id=test_user.id, farm_id=farm_b.id, role_override="FARM_WORKER"))
    await db.flush()

    token = create_access_token(str(test_user.id), str(test_user.org_id), [test_user.system_role])
    headers = {"Authorization": f"Bearer {token}"}

    ra = await client.patch(f"/api/v1/farms/{test_farm.id}/thresholds/STILLBORN_RATE",
                            headers=headers, json={"warning": 6.0, "critical": 10.0})
    assert ra.status_code == 200, ra.text  # 농장A: OWNER

    rb = await client.patch(f"/api/v1/farms/{farm_b.id}/thresholds/STILLBORN_RATE",
                            headers=headers, json={"warning": 6.0, "critical": 10.0})
    assert rb.status_code == 403, rb.text  # 농장B: WORKER → 거부
