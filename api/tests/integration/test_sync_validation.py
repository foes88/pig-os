"""동기화 경로 입력검증 (finding #1 해소) — pigos_test.

REST 생성경로와 동일한 카운트 검증을 sync 경로(_process_farrowing/_weaning)에도 적용.
위반 항목은 배치 전체 422가 아니라 항목별 SyncRejected(reason=VALIDATION_FAILED)로 거부.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.schemas.sync import SyncFarrowing, SyncWeaning
from app.services.sync_service import _process_farrowing, _process_weaning

pytestmark = pytest.mark.asyncio


def _far(sow_id, **kw):
    base = dict(id=uuid4(), sow_id=sow_id, farrowing_date="2026-06-01",
                total_born=12, born_alive=11, born_dead=1, mummies=0,
                client_created_at=datetime.now(UTC))
    base.update(kw)
    return SyncFarrowing(**base)


def _wea(sow_id, **kw):
    base = dict(id=uuid4(), sow_id=sow_id, weaning_date="2026-06-10",
                weaned_count=10, client_created_at=datetime.now(UTC))
    base.update(kw)
    return SyncWeaning(**base)


class TestSyncFarrowingValidation:
    async def test_rejects_total_born_over_35(self, db, test_farm, test_sow):
        test_sow.status = "PREGNANT"
        await db.flush()
        item = _far(test_sow.id, total_born=999, born_alive=999)
        accepted, rejected, conflict = await _process_farrowing(db, test_farm.id, item, dry_run=True)
        assert accepted is None and rejected is not None
        assert rejected.reason == "VALIDATION_FAILED"

    async def test_rejects_negative_born_alive(self, db, test_farm, test_sow):
        test_sow.status = "PREGNANT"
        await db.flush()
        item = _far(test_sow.id, total_born=10, born_alive=-5)
        accepted, rejected, conflict = await _process_farrowing(db, test_farm.id, item, dry_run=True)
        assert rejected is not None and rejected.reason == "VALIDATION_FAILED"

    async def test_rejects_born_alive_over_total(self, db, test_farm, test_sow):
        test_sow.status = "PREGNANT"
        await db.flush()
        item = _far(test_sow.id, total_born=10, born_alive=20)
        accepted, rejected, conflict = await _process_farrowing(db, test_farm.id, item, dry_run=True)
        assert rejected is not None and rejected.reason == "VALIDATION_FAILED"

    async def test_valid_farrowing_accepted(self, db, test_farm, test_sow):
        test_sow.status = "PREGNANT"
        await db.flush()
        item = _far(test_sow.id, total_born=12, born_alive=11, born_dead=1)
        accepted, rejected, conflict = await _process_farrowing(db, test_farm.id, item, dry_run=True)
        assert rejected is None and conflict is None
        assert accepted is not None and accepted.action == "created"


class TestSyncWeaningValidation:
    async def test_rejects_weaned_over_30(self, db, test_farm, test_sow):
        test_sow.status = "LACTATING"
        await db.flush()
        item = _wea(test_sow.id, weaned_count=99)
        accepted, rejected, conflict = await _process_weaning(db, test_farm.id, item, dry_run=True)
        assert rejected is not None and rejected.reason == "VALIDATION_FAILED"

    async def test_rejects_negative_weaned(self, db, test_farm, test_sow):
        test_sow.status = "LACTATING"
        await db.flush()
        item = _wea(test_sow.id, weaned_count=-1)
        accepted, rejected, conflict = await _process_weaning(db, test_farm.id, item, dry_run=True)
        assert rejected is not None and rejected.reason == "VALIDATION_FAILED"

    async def test_valid_weaning_accepted(self, db, test_farm, test_sow):
        test_sow.status = "LACTATING"
        await db.flush()
        item = _wea(test_sow.id, weaned_count=10)
        accepted, rejected, conflict = await _process_weaning(db, test_farm.id, item, dry_run=True)
        assert rejected is None and accepted is not None and accepted.action == "created"
