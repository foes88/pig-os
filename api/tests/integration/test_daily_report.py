"""일일 사육현황 리포트 — 당일 이벤트 집계 + 돈군 스냅샷."""
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models.events import Farrowing, Mating
from app.db.models.platform import UserFarm

pytestmark = pytest.mark.asyncio


class TestDailyReport:
    async def test_daily_counts_and_herd(self, client: AsyncClient, db, test_user, test_farm, test_sow):
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_OWNER"))
        day = date(2026, 6, 18)
        m = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=day,
                   mating_type="AI", mating_number=1)
        # 다른 날 이벤트(집계 제외 확인용)
        m_other = Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 6, 1),
                         mating_type="AI", mating_number=1)
        db.add_all([m, m_other])
        await db.flush()
        f = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id, farrowing_date=day,
                      total_born=11, born_alive=10, stillborn=1, mummified=0)
        # soft-delete된 분만(집계 제외)
        f_del = Farrowing(farm_id=test_farm.id, sow_id=test_sow.id, mating_id=m.id, farrowing_date=day,
                          total_born=8, born_alive=8, stillborn=0, mummified=0, deleted_at=datetime.now(UTC))
        db.add_all([f, f_del])
        await db.flush()

        token = create_access_token(str(test_user.id), str(test_user.org_id), ["FARM_OWNER"])
        r = await client.get(f"/api/v1/farms/{test_farm.id}/reports/daily?date={day.isoformat()}",
                             headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["matings"] == 1                          # 당일만(다른날 제외)
        assert d["farrowings"]["count"] == 1              # soft-delete 제외
        assert d["farrowings"]["total_born"] == 11
        assert d["farrowings"]["born_alive"] == 10
        assert d["herd"]["active_sows"] >= 1              # test_sow(GILT) 활성
        assert d["herd"]["gilts"] >= 1
