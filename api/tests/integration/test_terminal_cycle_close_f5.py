"""F5 — 도폐사/종료 시 진행 중 BreedingCycle을 FAILED로 종료(고아 사이클 방지).

기존: 임신(PREGNANT, 사이클 MATED) 모돈을 도폐사하면 모돈은 soft-delete되지만
번식 사이클은 영구 open(MATED)으로 남아 open-cycle·번식 분석이 오염됐음.
두 경로(① cull_sow 엔드포인트 ② record_reproductive_event→apply_terminal_reproductive)
모두에서 진행 사이클을 FAILED로 닫는다.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Organization, User
from app.db.models.sow import BreedingCycle, Sow
from app.schemas.events import ReproductiveEventCreate
from app.services import event_service

pytestmark = pytest.mark.anyio


async def _super(db, org) -> User:
    u = User(org_id=org.id, username=f"sa_{uuid.uuid4().hex[:6]}",
             email=f"sa-{uuid.uuid4().hex[:6]}@pigos.io", name="SA",
             password_hash=hash_password("Test1234!"), role="SUPER_ADMIN", system_role="SUPER_ADMIN")
    db.add(u)
    await db.flush()
    return u


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def _pregnant_with_cycle(db, farm) -> tuple[Sow, BreedingCycle]:
    sow = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=1,
              status="PREGNANT", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(sow)
    await db.flush()
    cyc = BreedingCycle(farm_id=farm.id, sow_id=sow.id, parity=2, cycle_status="MATED",
                        started_at=datetime(2026, 1, 5, tzinfo=UTC), mating_count=1)
    db.add(cyc)
    await db.flush()
    return sow, cyc


async def test_cull_endpoint_closes_open_cycle(client: AsyncClient, db: AsyncSession, test_org: Organization, test_farm):
    sow, cyc = await _pregnant_with_cycle(db, test_farm)
    sa = await _super(db, test_org)
    await db.flush()
    r = await client.post(f"/api/v1/farms/{test_farm.id}/sows/{sow.id}/cull", headers=_h(sa),
                          json={"removal_date": "2026-05-01", "removal_type": "CULLED",
                                "reason_category": "REPRODUCTIVE", "reason_detail": "infertile"})
    assert r.status_code == 201, r.text
    await db.refresh(cyc)
    assert cyc.cycle_status == "FAILED" and cyc.ended_at is not None, \
        "도폐사 시 진행 사이클은 FAILED로 종료돼야 함(고아 방지)"


async def test_terminal_reproductive_closes_open_cycle(db: AsyncSession, test_farm, test_user: User):
    sow, cyc = await _pregnant_with_cycle(db, test_farm)
    await event_service.record_reproductive_event(
        db, test_farm.id, test_user.id,
        ReproductiveEventCreate(sow_id=sow.id, event_date=date(2026, 5, 1),
                                event_type="CULLED", notes="pregnant cull reason"))
    await db.refresh(cyc)
    assert cyc.cycle_status == "FAILED" and cyc.ended_at is not None
