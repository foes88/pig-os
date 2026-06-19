"""데이터 정합성 — 이유 시 자돈그룹 자동생성 + 포유 중 모돈 도태 차단.

목적: 이유된/고아 자돈 두수가 떠다니지 않게(추적 끊김 방지).
"""
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.exceptions import ValidationError
from app.core.security import create_access_token
from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import UserFarm
from app.db.models.sow import PigletGroup, Sow
from app.schemas.events import FarrowingCreate, PigletEventCreate, WeaningCreate, WeaningUpdate
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


class TestEventStateGuards:
    """PigPlan 정합성 — 잘못된 상태/두수/날짜 입력 차단(감사 HIGH 갭)."""

    async def _farrow(self, db, farm, sow, user, born=10):
        m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2024, 2, 1),
                   mating_type="AI", mating_number=1)
        db.add(m)
        await db.flush()
        f = Farrowing(farm_id=farm.id, sow_id=sow.id, mating_id=m.id,
                      farrowing_date=date(2024, 5, 26), total_born=born + 1,
                      born_alive=born, stillborn=1, mummified=0)
        db.add(f)
        await db.flush()
        return f

    async def test_farrowing_wrong_state_blocked(self, db, test_farm, test_sow, test_user):
        # PREGNANT 아닌 상태(OPEN)에서 분만 시도 → 차단
        m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2024, 2, 1),
                   mating_type="AI", mating_number=1)
        db.add(m)
        test_sow.status = "OPEN"
        await db.flush()
        with pytest.raises(ValidationError, match="farrowing"):
            await event_service.record_farrowing(
                db, test_farm.id, test_user.id,
                FarrowingCreate(sow_id=test_sow.id, mating_id=m.id, farrowing_date=date(2024, 5, 26),
                                total_born=11, born_alive=10, stillborn=1, mummified=0),
            )

    async def test_weaning_wrong_state_blocked(self, db, test_farm, test_sow, test_user):
        f = await self._farrow(db, test_farm, test_sow, test_user)
        test_sow.status = "OPEN"  # LACTATING 아님
        await db.flush()
        with pytest.raises(ValidationError, match="weaning"):
            await event_service.record_weaning(
                db, test_farm.id, test_user.id,
                WeaningCreate(sow_id=test_sow.id, farrowing_id=f.id,
                              weaning_date=date(2024, 6, 16), weaned_count=10),
            )

    async def test_piglet_death_exceeds_nursing_blocked(self, db, test_farm, test_sow, test_user):
        test_sow.status = "LACTATING"
        f = await self._farrow(db, test_farm, test_sow, test_user, born=10)
        with pytest.raises(ValidationError, match="exceed"):
            await event_service.record_piglet_event(
                db, test_farm.id, test_user.id,
                PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id,
                                  event_date=date(2024, 6, 1), event_type="DEATH", piglet_count=12),
            )

    async def test_cull_before_entry_blocked(self, client, db, test_user, test_farm, test_sow):
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        test_sow.status = "OPEN"
        await db.flush()
        token = create_access_token(str(test_user.id), str(test_user.org_id), ["FARM_OWNER"])
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/sows/{test_sow.id}/cull",
            headers={"Authorization": f"Bearer {token}"},
            json={"removal_type": "CULLED", "removal_date": "2023-01-01"},  # 입식(2024-01-01) 이전
        )
        assert r.status_code == 422, r.text


class TestPigletDateAndFosterGuards:
    """V1 날짜순서 + V2 양자 전입 모돈 검증."""

    async def _farrow(self, db, farm, sow, born=10, fdate=date(2024, 5, 26)):
        m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2024, 2, 1),
                   mating_type="AI", mating_number=1)
        db.add(m)
        await db.flush()
        f = Farrowing(farm_id=farm.id, sow_id=sow.id, mating_id=m.id, farrowing_date=fdate,
                      total_born=born + 1, born_alive=born, stillborn=1, mummified=0)
        db.add(f)
        await db.flush()
        return f

    async def test_piglet_event_before_farrowing_blocked(self, db, test_farm, test_sow, test_user):
        test_sow.status = "LACTATING"
        f = await self._farrow(db, test_farm, test_sow)
        with pytest.raises(ValidationError, match="farrowing"):
            await event_service.record_piglet_event(
                db, test_farm.id, test_user.id,
                PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id,
                                  event_date=date(2024, 5, 1), event_type="DEATH", piglet_count=1),
            )

    async def test_foster_requires_target(self, db, test_farm, test_sow, test_user):
        test_sow.status = "LACTATING"
        f = await self._farrow(db, test_farm, test_sow)
        with pytest.raises(ValidationError, match="target_sow_id"):
            await event_service.record_piglet_event(
                db, test_farm.id, test_user.id,
                PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id,
                                  event_date=date(2024, 6, 1), event_type="FOSTER_OUT", piglet_count=2),
            )


class TestSowRegistrationGuards:
    """V4 — 모돈 등록 정합성(입식일 미래금지·활성 귀표 중복)."""

    def _token(self, u):
        return create_access_token(str(u.id), str(u.org_id), ["FARM_OWNER"])

    async def test_duplicate_ear_tag_blocked(self, client, db, test_user, test_farm):
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        await db.flush()
        h = {"Authorization": f"Bearer {self._token(test_user)}"}
        body = {"ear_tag": "DUP-001", "entry_date": "2024-01-01", "entry_type": "GILT"}
        r1 = await client.post(f"/api/v1/farms/{test_farm.id}/sows", headers=h, json=body)
        assert r1.status_code == 201, r1.text
        r2 = await client.post(f"/api/v1/farms/{test_farm.id}/sows", headers=h, json=body)
        assert r2.status_code == 422 and "already exists" in r2.text.lower()

    async def test_future_entry_date_blocked(self, client, db, test_user, test_farm):
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        await db.flush()
        h = {"Authorization": f"Bearer {self._token(test_user)}"}
        r = await client.post(f"/api/v1/farms/{test_farm.id}/sows", headers=h,
                              json={"ear_tag": "FUT-001", "entry_date": "2099-01-01", "entry_type": "GILT"})
        assert r.status_code == 422 and "future" in r.text.lower()


class TestWeaningEditGuard:
    """V7 — 이유 수정 시에도 두수 재검증."""
    async def test_update_weaning_over_litter_blocked(self, db, test_farm, test_sow, test_user):
        m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2024, 2, 1),
                   mating_type="AI", mating_number=1)
        db.add(m); await db.flush()
        f = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id,
                      farrowing_date=date(2024, 5, 26), total_born=11, born_alive=10,
                      stillborn=1, mummified=0)
        db.add(f); await db.flush()
        w = Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                    weaning_date=date(2024, 6, 16), weaned_count=10)
        db.add(w); await db.flush()
        with pytest.raises(ValidationError, match="effective litter"):
            await event_service.update_weaning(
                db, test_farm.id, test_user.id, w.id, WeaningUpdate(weaned_count=20),
            )


class TestFosterOvercrowding:
    """V3 — 양자 전입 후 포유두수 상한(과혼잡) 초과 차단."""
    async def test_foster_in_overcrowding_blocked(self, db, test_farm, test_sow, test_user):
        test_sow.status = "LACTATING"
        m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2024, 2, 1),
                   mating_type="AI", mating_number=1)
        db.add(m); await db.flush()
        f = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id,
                      farrowing_date=date(2024, 5, 26), total_born=21, born_alive=20,
                      stillborn=1, mummified=0)
        db.add(f)
        # 상대(전입원) 모돈 — LACTATING
        b = Sow(farm_id=test_farm.id, ear_tag="FOSTER-SRC", parity=1, status="LACTATING",
                entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="PURCHASE")
        db.add(b); await db.flush()
        with pytest.raises(ValidationError, match="exceeds max"):
            await event_service.record_piglet_event(
                db, test_farm.id, test_user.id,
                PigletEventCreate(sow_id=test_sow.id, farrowing_id=f.id, target_sow_id=b.id,
                                  event_date=date(2024, 6, 1), event_type="FOSTER_IN", piglet_count=10),
            )
