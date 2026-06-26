"""농장 구성원(/settings/users) 엔드포인트 테스트."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.platform import UserFarm


async def _auth(db, user, farm):
    """user를 farm에 연결하고 Authorization 헤더 반환 (권한은 system_role 기준)."""
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=user.role))
    await db.flush()
    token = create_access_token(str(user.id), str(user.org_id), [user.system_role])
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_members_includes_self(client: AsyncClient, db, test_user, test_farm):
    headers = await _auth(db, test_user, test_farm)
    r = await client.get(f"/api/v1/farms/{test_farm.id}/members", headers=headers)
    assert r.status_code == 200
    members = r.json()
    assert any(m["user_id"] == str(test_user.id) for m in members)


@pytest.mark.asyncio
async def test_owner_can_create_member(client: AsyncClient, db, test_user, test_farm):
    # test_user는 FARM_OWNER (fixture 기본)
    headers = await _auth(db, test_user, test_farm)
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/members",
        headers=headers,
        json={"name": "New Worker", "username": "worker1", "email": "worker1@pigos.io",
              "password": "Worker1234!", "role": "FARM_WORKER"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["role"] == "FARM_WORKER"
    assert body["email"] == "worker1@pigos.io"


@pytest.mark.asyncio
async def test_duplicate_email_conflict(client: AsyncClient, db, test_user, test_farm):
    headers = await _auth(db, test_user, test_farm)
    payload = {"name": "Dup", "username": "dupuser", "email": "dup@pigos.io",
               "password": "Worker1234!", "role": "FARM_WORKER"}
    r1 = await client.post(f"/api/v1/farms/{test_farm.id}/members", headers=headers, json=payload)
    assert r1.status_code == 201
    r2 = await client.post(f"/api/v1/farms/{test_farm.id}/members", headers=headers, json=payload)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_worker_cannot_create_member(client: AsyncClient, db, test_user, test_farm):
    test_user.role = "FARM_WORKER"
    test_user.system_role = "FARM_WORKER"  # 권한 판정 기준
    await db.flush()
    headers = await _auth(db, test_user, test_farm)
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/members",
        headers=headers,
        json={"name": "X", "email": "x@pigos.io", "password": "Worker1234!", "role": "FARM_WORKER"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_manager_cannot_create_member(client: AsyncClient, db, test_user, test_farm):
    """MANAGER는 일상 운영은 가능하나 멤버 임명은 OWNER 전용 → 403."""
    test_user.role = "FARM_MANAGER"
    test_user.system_role = "FARM_MANAGER"
    await db.flush()
    headers = await _auth(db, test_user, test_farm)
    r = await client.post(
        f"/api/v1/farms/{test_farm.id}/members",
        headers=headers,
        json={"name": "X", "email": "mgrx@pigos.io", "password": "Worker1234!", "role": "FARM_WORKER"},
    )
    assert r.status_code == 403
