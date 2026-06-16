"""농장 스코프 쓰기 RBAC 회귀 (Section D) — pigos_test.

원칙: 일상 입력(교배/분만/이유 기록)은 FARM_WORKER 허용.
단 파괴적(도태·삭제)·설정성 변경은 OWNER/MANAGER만 (워커 403).
"""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.platform import UserFarm

pytestmark = pytest.mark.asyncio


async def _member_headers(db, user, farm, role: str):
    user.role = role
    user.system_role = role
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=role))
    await db.flush()
    token = create_access_token(str(user.id), str(user.org_id), [role])
    return {"Authorization": f"Bearer {token}"}


class TestWorkerBlockedFromDestructive:
    async def test_worker_cannot_cull_sow(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        headers = await _member_headers(db, test_user, test_farm, "FARM_WORKER")
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull",
            headers=headers, json={"removal_type": "CULLED", "removal_date": "2026-06-01"},
        )
        assert r.status_code == 403, r.text

    async def test_worker_cannot_delete_sow(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        headers = await _member_headers(db, test_user, test_farm, "FARM_WORKER")
        r = await client.delete(f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}", headers=headers)
        assert r.status_code == 403, r.text

    async def test_worker_cannot_update_farm_config(self, client: AsyncClient, db, test_user, test_farm):
        headers = await _member_headers(db, test_user, test_farm, "FARM_WORKER")
        r = await client.patch(
            f"/api/v1/farms/{test_farm.id}/config/repro",
            headers=headers, json={"gestation_days": 115},
        )
        assert r.status_code == 403, r.text


class TestWorkerAllowedDailyEntry:
    async def test_worker_can_record_mating(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        test_sow.status = "OPEN"
        await db.flush()
        headers = await _member_headers(db, test_user, test_farm, "FARM_WORKER")
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/events/matings",
            headers=headers,
            json={"sow_id": str(test_sow.id), "mating_date": "2026-05-01", "mating_type": "AI"},
        )
        # 일상 입력은 워커 허용 → 403이 아니어야 함 (201 또는 검증 관련 4xx여도 권한 통과)
        assert r.status_code != 403, r.text


class TestOwnerAllowedDestructive:
    async def test_owner_can_cull(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        headers = await _member_headers(db, test_user, test_farm, "FARM_OWNER")
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull",
            headers=headers, json={"removal_type": "CULLED", "removal_date": "2026-06-01"},
        )
        assert r.status_code in (200, 201), r.text
