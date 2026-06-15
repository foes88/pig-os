"""
GET /sows?status= 검증 (모바일 footgun 방지).
잘못된 status는 422여야 한다 (이전엔 빈 목록을 조용히 반환 → "모돈이 안 보여요" 버그).
"""
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.platform import UserFarm


async def _auth(db, user, farm):
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=user.role))
    await db.flush()
    token = create_access_token(str(user.id), str(user.org_id), [user.system_role])
    return {"Authorization": f"Bearer {token}"}


async def test_invalid_status_returns_422(client: AsyncClient, db, test_user, test_farm):
    headers = await _auth(db, test_user, test_farm)
    # 폐기된 옛 값 — 모바일이 잘못 보낼 수 있는 케이스
    r = await client.get(f"/api/v1/farms/{test_farm.id}/sows?status=ACTIVE", headers=headers)
    assert r.status_code == 422


async def test_valid_status_ok(client: AsyncClient, db, test_user, test_farm):
    headers = await _auth(db, test_user, test_farm)
    r = await client.get(f"/api/v1/farms/{test_farm.id}/sows?status=OPEN", headers=headers)
    assert r.status_code == 200


async def test_no_status_ok(client: AsyncClient, db, test_user, test_farm):
    headers = await _auth(db, test_user, test_farm)
    r = await client.get(f"/api/v1/farms/{test_farm.id}/sows", headers=headers)
    assert r.status_code == 200
