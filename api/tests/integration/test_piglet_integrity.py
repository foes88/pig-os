"""데이터 정합성 — 이유 시 자돈그룹 자동생성 + 포유 중 모돈 도태 차단.

목적: 이유된/고아 자돈 두수가 떠다니지 않게(추적 끊김 방지).
"""
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.models.events import Farrowing, Mating
from app.db.models.platform import UserFarm
from app.db.models.sow import PigletGroup
from app.schemas.events import WeaningCreate
from app.services import event_service

pytestmark = pytest.mark.asyncio


class TestWeaningCreatesPigletGroup:
    async def test_weaning_auto_creates_group(self, db, test_farm, test_sow, test_user):
        test_sow.status = "LACTATING"
        m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2024, 2, 1),
                   mating_type="AI", mating_number=1)
        db.add(m)
        await db.flush()
        f = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id,
                      farrowing_date=date(2024, 5, 26), total_born=11, born_alive=10,
                      stillborn=1, mummified=0)
        db.add(f)
        await db.flush()

        await event_service.record_weaning(
            db, test_farm.id, test_user.id,
            WeaningCreate(sow_id=test_sow.id, weaning_date=date(2024, 6, 16), weaned_count=10),
        )

        groups = list(await db.scalars(
            select(PigletGroup).where(PigletGroup.farm_id == test_farm.id)
        ))
        assert len(groups) == 1
        assert groups[0].head_count_in == 10           # 떠다니는 두수 없이 그룹으로 추적
        assert groups[0].weaning_date == date(2024, 6, 16)


class TestCullLactatingBlocked:
    async def _token(self, u):
        return create_access_token(str(u.id), str(u.org_id), ["FARM_OWNER"])

    async def test_cull_lactating_sow_blocked(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        test_sow.status = "LACTATING"
        await db.flush()
        token = await self._token(test_user)
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull",
            headers={"Authorization": f"Bearer {token}"},
            json={"removal_type": "CULLED", "removal_date": "2024-06-01"},
        )
        assert r.status_code == 422, r.text          # 포유 중 → 차단
        assert "lactating" in r.text.lower()

    async def test_dead_lactating_sow_allowed(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        test_sow.status = "LACTATING"
        await db.flush()
        token = await self._token(test_user)
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull",
            headers={"Authorization": f"Bearer {token}"},
            json={"removal_type": "DEAD", "removal_date": "2024-06-01"},
        )
        assert r.status_code == 201, r.text          # 사고사는 허용
