"""BUG-ACC-SYNC-RBAC — /sync 쓰기 권한 가드 (codex 독립검증 발견, High/NO-GO).

과거 /sync는 get_farm_context(멤버십)만 있어 VIEWER/VET가 sync로 이벤트를 insert +
모돈 상태 변경 가능했음. sync=데이터 입력이므로 ENTRY 권한(OWNER/MANAGER/WORKER+조직롤) 필요.
"""
import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.platform import UserFarm

pytestmark = pytest.mark.anyio


async def _member(db, user, farm, role):
    user.role = role
    user.system_role = role
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=role))
    await db.flush()
    return {"Authorization": f"Bearer {create_access_token(str(user.id), str(user.org_id), [role])}"}


def _body(farm_id):
    return {"farm_id": str(farm_id), "client_id": str(uuid.uuid4()), "dry_run": True, "changes": {}}


async def test_viewer_cannot_sync(client: AsyncClient, db, test_user, test_farm):
    headers = await _member(db, test_user, test_farm, "VIEWER")
    r = await client.post(f"/api/v1/farms/{test_farm.id}/sync", headers=headers, json=_body(test_farm.id))
    assert r.status_code == 403, r.text


async def test_vet_cannot_sync(client: AsyncClient, db, test_user, test_farm):
    headers = await _member(db, test_user, test_farm, "VET")
    r = await client.post(f"/api/v1/farms/{test_farm.id}/sync", headers=headers, json=_body(test_farm.id))
    assert r.status_code == 403, r.text


async def test_worker_can_sync(client: AsyncClient, db, test_user, test_farm):
    headers = await _member(db, test_user, test_farm, "FARM_WORKER")
    r = await client.post(f"/api/v1/farms/{test_farm.id}/sync", headers=headers, json=_body(test_farm.id))
    assert r.status_code == 200, r.text
