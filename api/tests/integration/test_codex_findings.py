"""Codex 검증 finding 회귀잠금 (2026-06-17) — pigos_test.

P0 분만 mating_id 자동조회 / P1 viewer mutation 차단 / P1 sync 항목별 reject /
P1 reproductive SOLD REST↔sync 통일.
"""
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.models.events import Mating
from app.db.models.health import Removal
from app.db.models.platform import UserFarm
from app.schemas.events import FarrowingCreate, ReproductiveEventCreate
from app.schemas.sync import SyncPigletEvent, SyncReproductiveEvent
from app.services import event_service
from app.services.sync_service import _process_piglet_event, _process_reproductive

pytestmark = pytest.mark.asyncio


# ── P0: 분만 입력 시 mating_id 없으면 최근 미분만 교배 자동 조회 ─────────────
class TestFarrowingAutoMating:
    async def test_farrowing_without_mating_id_autoresolves(self, db, test_farm, test_sow, test_user):
        test_sow.status = "PREGNANT"
        db.add(Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 2, 1),
                      mating_type="AI", mating_number=1))
        await db.flush()
        # mating_id 미지정 → 404 아니라 자동 조회되어 성공해야 함
        ev = await event_service.record_farrowing(
            db, test_farm.id, test_user.id,
            FarrowingCreate(sow_id=test_sow.id, farrowing_date=date(2026, 5, 27),
                            born_alive=11, stillborn=1, mummified=0),
        )
        assert ev.mating_id is not None


# ── P1: 읽기전용 역할(VIEWER)은 farm mutation 불가 ───────────────────────────
class TestViewerBlocked:
    async def test_viewer_cannot_create_sow(self, client: AsyncClient, db, test_user, test_farm):
        test_user.role = "VIEWER"
        test_user.system_role = "VIEWER"
        db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="VIEWER"))
        await db.flush()
        token = create_access_token(str(test_user.id), str(test_user.org_id), ["VIEWER"])
        r = await client.post(
            f"/api/v1/farms/{test_farm.id}/sows",
            headers={"Authorization": f"Bearer {token}"},
            json={"ear_tag": "V-001", "entry_date": "2026-01-01", "entry_type": "GILT"},
        )
        assert r.status_code == 403, r.text


# ── P1: sync 잘못된 항목은 item-level reject (배치 전체 422 아님) ─────────────
class TestSyncItemReject:
    def _repro(self, sow_id, et):
        return SyncReproductiveEvent(id=uuid4(), sow_id=sow_id, event_type=et,
                                     event_date="2026-05-01", client_created_at=datetime.now(UTC))

    def _piglet(self, sow_id, **kw):
        base = dict(id=uuid4(), sow_id=sow_id, event_date="2026-05-01",
                    event_type="DEATH", piglet_count=1, client_created_at=datetime.now(UTC))
        base.update(kw)
        return SyncPigletEvent(**base)

    async def test_reproductive_bad_event_type_rejected(self, db, test_farm, test_sow):
        item = self._repro(test_sow.id, "BAD_EVENT")
        acc, rej, conf = await _process_reproductive(db, test_farm.id, item, dry_run=True)
        assert acc is None and rej is not None and rej.reason == "VALIDATION_FAILED"

    async def test_piglet_bad_event_type_rejected(self, db, test_farm, test_sow):
        item = self._piglet(test_sow.id, event_type="BAD")
        acc, rej, conf = await _process_piglet_event(db, test_farm.id, item, dry_run=True)
        assert acc is None and rej is not None and rej.reason == "VALIDATION_FAILED"

    async def test_piglet_zero_count_rejected(self, db, test_farm, test_sow):
        item = self._piglet(test_sow.id, piglet_count=0)
        acc, rej, conf = await _process_piglet_event(db, test_farm.id, item, dry_run=True)
        assert acc is None and rej is not None and rej.reason == "VALIDATION_FAILED"

    async def test_valid_repro_accepted(self, db, test_farm, test_sow):
        item = self._repro(test_sow.id, "RETURN_TO_ESTRUS")
        acc, rej, conf = await _process_reproductive(db, test_farm.id, item, dry_run=True)
        assert rej is None and acc is not None


# ── P1: reproductive SOLD가 REST에서도 종료 처리(soft-delete + Removal) ──────
class TestReproductiveTerminalUnified:
    async def test_rest_sold_marks_terminal_and_removal(self, db, test_farm, test_sow, test_user):
        test_sow.status = "OPEN"
        await db.flush()
        await event_service.record_reproductive_event(
            db, test_farm.id, test_user.id,
            ReproductiveEventCreate(sow_id=test_sow.id, event_date=date(2026, 5, 1), event_type="SOLD"),
        )
        await db.refresh(test_sow)
        assert test_sow.status == "SOLD"
        assert test_sow.deleted_at is not None
        removal = await db.scalar(select(Removal).where(
            Removal.sow_id == test_sow.id, Removal.removal_type == "SOLD"))
        assert removal is not None
