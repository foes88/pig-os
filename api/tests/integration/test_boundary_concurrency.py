"""Section E — 경계·동시성 회귀 (pigos_test).

- 보고서 기간 경계(>2년 / end<start → 400)
- sync 동일 batch 중복 id 멱등 처리
- 동일 이벤트 재처리 멱등(merged)
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.platform import UserFarm
from app.schemas.sync import SyncMating
from app.services.sync_service import _process_mating

pytestmark = pytest.mark.asyncio


async def _auth(db, user, farm):
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=user.system_role))
    await db.flush()
    token = create_access_token(str(user.id), str(user.org_id), [user.system_role])
    return {"Authorization": f"Bearer {token}"}


class TestReportRangeBoundary:
    async def test_over_two_years_rejected(self, client: AsyncClient, db, test_user, test_farm):
        headers = await _auth(db, test_user, test_farm)
        r = await client.get(
            f"/api/v1/farms/{test_farm.id}/reports/reproduction",
            headers=headers, params={"start_date": "2023-01-01", "end_date": "2026-01-02", "period": "monthly"},
        )
        assert r.status_code == 400, r.text

    async def test_end_before_start_rejected(self, client: AsyncClient, db, test_user, test_farm):
        headers = await _auth(db, test_user, test_farm)
        r = await client.get(
            f"/api/v1/farms/{test_farm.id}/reports/reproduction",
            headers=headers, params={"start_date": "2026-06-01", "end_date": "2026-01-01", "period": "monthly"},
        )
        assert r.status_code == 400, r.text

    async def test_within_range_ok(self, client: AsyncClient, db, test_user, test_farm):
        headers = await _auth(db, test_user, test_farm)
        r = await client.get(
            f"/api/v1/farms/{test_farm.id}/reports/reproduction",
            headers=headers, params={"start_date": "2026-01-01", "end_date": "2026-06-30", "period": "monthly"},
        )
        assert r.status_code == 200, r.text


class TestSyncIdempotency:
    def _mat(self, sow_id, mid):
        return SyncMating(id=mid, sow_id=sow_id, mating_date="2026-05-01",
                          mating_type="AI", mating_number=1, client_created_at=datetime.now(UTC))

    async def test_same_id_twice_is_idempotent(self, db, test_farm, test_sow):
        test_sow.status = "OPEN"
        await db.flush()
        mid = uuid4()
        item = self._mat(test_sow.id, mid)
        # 1회차: 생성
        acc1, rej1, _ = await _process_mating(db, test_farm.id, item, dry_run=False)
        assert acc1 is not None and acc1.action == "created"
        await db.flush()
        # 2회차: 동일 id → merged(중복 생성 안 함)
        acc2, rej2, _ = await _process_mating(db, test_farm.id, self._mat(test_sow.id, mid), dry_run=False)
        assert acc2 is not None and acc2.action == "merged"
        assert rej2 is None
