"""
Task 자동배정 서비스 통합 테스트 (Phase 2) — pigos_test (Docker).
alert → Task 멱등 생성, stale 종료, 처리(DONE/DISMISS) 검증.
"""
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Mating
from app.db.models.ops import Task
from app.db.models.platform import Farm, User
from app.db.models.sow import Sow
from app.services import task_service

TODAY = date(2026, 6, 10)


async def _pregnant_overdue(db, farm):
    """114일 초과 미분만 모돈 1마리 세팅 → pregnant_overdue_farrowing 대상."""
    sow = Sow(
        farm_id=farm.id, ear_tag=f"T-{uuid.uuid4().hex[:6].upper()}", parity=2,
        status="PREGNANT",
        entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT",
    )
    db.add(sow)
    await db.flush()
    db.add(Mating(farm_id=farm.id, sow_id=sow.id,
                  mating_date=date.today() - timedelta(days=130),
                  mating_type="AI", mating_number=1))
    await db.flush()
    return sow


async def _open_tasks(db, farm):
    return list(await db.scalars(
        select(Task).where(Task.farm_id == farm.id, Task.status == "OPEN", Task.deleted_at.is_(None))
    ))


class TestGenerate:
    async def test_creates_task_for_overdue_sow(self, db: AsyncSession, test_farm: Farm):
        sow = await _pregnant_overdue(db, test_farm)
        created, _closed, open_total = await task_service.generate_tasks(db, test_farm.id)
        assert created >= 1
        assert open_total >= 1
        tasks = await _open_tasks(db, test_farm)
        mine = [t for t in tasks if t.sow_id == sow.id]
        assert len(mine) == 1
        assert mine[0].task_type == "pregnant_overdue_farrowing"
        assert mine[0].priority == 1

    async def test_idempotent_no_duplicate(self, db: AsyncSession, test_farm: Farm):
        sow = await _pregnant_overdue(db, test_farm)
        await task_service.generate_tasks(db, test_farm.id)
        created2, _c, _o = await task_service.generate_tasks(db, test_farm.id)
        # 2회차엔 신규 생성 0 (기존 OPEN task만 갱신)
        assert created2 == 0
        tasks = [t for t in await _open_tasks(db, test_farm) if t.sow_id == sow.id]
        assert len(tasks) == 1

    async def test_stale_task_dismissed_when_no_longer_overdue(self, db: AsyncSession, test_farm: Farm):
        sow = await _pregnant_overdue(db, test_farm)
        await task_service.generate_tasks(db, test_farm.id)
        # 모돈 상태 변경 → 더 이상 overdue 아님
        sow.status = "LACTATING"
        await db.flush()
        _c, closed, _o = await task_service.generate_tasks(db, test_farm.id)
        assert closed >= 1
        remaining = [t for t in await _open_tasks(db, test_farm) if t.sow_id == sow.id]
        assert remaining == []


class TestUpdate:
    async def test_complete_task(self, db: AsyncSession, test_farm: Farm, test_user: User):
        sow = await _pregnant_overdue(db, test_farm)
        await task_service.generate_tasks(db, test_farm.id)
        task = [t for t in await _open_tasks(db, test_farm) if t.sow_id == sow.id][0]
        updated, _tag = await task_service.update_task(
            db, test_farm.id, task.id, test_user.id, status="DONE",
        )
        assert updated.status == "DONE"
        assert updated.completed_at is not None
        assert updated.completed_by == test_user.id
