"""회귀 잠금 — 이벤트 목록(matings/farrowings/weanings)이 soft-delete(deleted_at) 제외.

라이브 E2E(event-rollback)가 발견: 삭제(204)된 교배가 GET /events/matings 목록에 남던 버그.
"""
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import UserFarm

pytestmark = pytest.mark.asyncio


class TestEventListSoftDelete:
    async def _token(self, user):
        return create_access_token(str(user.id), str(user.org_id), ["FARM_OWNER"])

    async def _member(self, db, user, farm):
        db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override="FARM_OWNER"))
        await db.flush()

    async def test_deleted_mating_excluded(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        await self._member(db, test_user, test_farm)
        live = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 2, 1),
                      mating_type="AI", mating_number=1)
        dead = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 2, 2),
                      mating_type="AI", mating_number=1, deleted_at=datetime.now(UTC))
        db.add_all([live, dead])
        await db.flush()

        token = await self._token(test_user)
        r = await client.get(
            f"/api/v1/farms/{test_farm.id}/events/matings?sow_id={test_sow.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200, r.text
        ids = [m["id"] for m in r.json()]
        assert str(live.id) in ids
        assert str(dead.id) not in ids

    async def test_deleted_farrowing_and_weaning_excluded(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        await self._member(db, test_user, test_farm)
        m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 1, 10),
                   mating_type="AI", mating_number=1)
        db.add(m)
        await db.flush()
        f_live = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id, farrowing_date=date(2026, 5, 1),
                           total_born=10, born_alive=9, stillborn=1, mummified=0)
        f_dead = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id, farrowing_date=date(2026, 5, 2),
                           total_born=8, born_alive=8, stillborn=0, mummified=0,
                           deleted_at=datetime.now(UTC))
        db.add_all([f_live, f_dead])
        await db.flush()
        w_live = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f_live.id,
                         weaning_date=date(2026, 5, 22), weaned_count=9)
        w_dead = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f_live.id,
                         weaning_date=date(2026, 5, 23), weaned_count=8, deleted_at=datetime.now(UTC))
        db.add_all([w_live, w_dead])
        await db.flush()

        token = await self._token(test_user)
        rf = await client.get(f"/api/v1/farms/{test_farm.id}/events/farrowings?sow_id={test_sow.id}",
                              headers={"Authorization": f"Bearer {token}"})
        rw = await client.get(f"/api/v1/farms/{test_farm.id}/events/weanings?sow_id={test_sow.id}",
                              headers={"Authorization": f"Bearer {token}"})
        assert rf.status_code == 200 and rw.status_code == 200
        f_ids = [x["id"] for x in rf.json()]
        w_ids = [x["id"] for x in rw.json()]
        assert str(f_live.id) in f_ids and str(f_dead.id) not in f_ids
        assert str(w_live.id) in w_ids and str(w_dead.id) not in w_ids
