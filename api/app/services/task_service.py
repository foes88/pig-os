"""
Task 자동배정 서비스 (Phase 2).

alert_service의 지연모돈(6유형) + 도태권고를 Task로 멱등 생성한다.
- 같은 (farm_id, sow_id, task_type)의 OPEN task가 있으면 overdue_days만 갱신(중복 생성 안 함)
- 더 이상 해당되지 않는 OPEN task는 자동 DONE 처리 안 하고 그대로 둠
  (사용자가 처리/무시) — 단, 모돈 상태가 바뀌어 alert에서 빠지면 stale → close 처리
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.ops import Task
from app.db.models.sow import Sow
from app.services import alert_service

# task_type → (title 템플릿, action 라우트, priority)
# {tag} = 귀표. action의 {sid} = sow_id
_OVERDUE_META: dict[str, tuple[str, str, int]] = {
    "gilt_no_estrus":             ("{tag} 후보돈 발정 미확인",  "/record?tab=repro&sowId={sid}",   2),
    "gilt_overdue_mating":        ("{tag} 후보돈 교배 지연",    "/record?tab=mating&sowId={sid}",  2),
    "pregnant_overdue_farrowing": ("{tag} 분만 예정일 초과",    "/record?tab=farrowing&sowId={sid}", 1),
    "lactating_overdue_weaning":  ("{tag} 이유 지연",          "/record?tab=weaning&sowId={sid}", 1),
    "open_overdue_mating":        ("{tag} 공태 재교배 지연",    "/record?tab=mating&sowId={sid}",  2),
    "accident_overdue_mating":    ("{tag} 사고 후 재교배 지연", "/record?tab=mating&sowId={sid}",  2),
}
_CULL_TYPE = "cull_candidate"


async def generate_tasks(db: AsyncSession, farm_id: UUID) -> tuple[int, int, int]:
    """alert 기준으로 Task 멱등 생성/갱신/stale 종료. (created, closed, open_total) 반환."""
    overdue = await alert_service.get_overdue_sows(db, farm_id)
    culls = await alert_service.get_cull_candidates(db, farm_id)

    # 현재 alert가 가리키는 (sow_id, task_type) 집합
    desired: dict[tuple[UUID, str], dict] = {}
    for o in overdue:
        desired[(o["sow_id"], o["type"])] = o
    for c in culls:
        desired[(c["sow_id"], _CULL_TYPE)] = c

    # 기존 OPEN task
    existing = list(await db.scalars(
        select(Task).where(Task.farm_id == farm_id, Task.status == "OPEN", Task.deleted_at.is_(None))
    ))
    existing_map = {(t.sow_id, t.task_type): t for t in existing}

    created = 0
    closed = 0

    # 1) 신규 생성 / 갱신
    for (sow_id, ttype), data in desired.items():
        cur = existing_map.get((sow_id, ttype))
        if cur:
            # overdue_days만 갱신 (중복 생성 안 함)
            cur.overdue_days = data.get("overdue_days")
            continue
        tag = data.get("ear_tag", "")
        if ttype == _CULL_TYPE:
            title = f"{tag} 도태 권고"
            action = f"/sows/{sow_id}"
            priority = 1
            overdue_days = None
        else:
            tmpl, act, priority = _OVERDUE_META[ttype]
            title = tmpl.format(tag=tag)
            action = act.format(sid=sow_id)
            overdue_days = data.get("overdue_days")
        db.add(Task(
            farm_id=farm_id, sow_id=sow_id, task_type=ttype,
            title=title, action=action, status="OPEN",
            priority=priority, overdue_days=overdue_days,
        ))
        created += 1

    # 2) 더 이상 alert에 없는 OPEN task → stale 종료 (DISMISSED)
    for key, t in existing_map.items():
        if key not in desired:
            t.status = "DISMISSED"
            t.completed_at = datetime.now(UTC)
            closed += 1

    await db.commit()

    open_total = await db.scalar(
        select(func.count()).select_from(Task).where(
            Task.farm_id == farm_id, Task.status == "OPEN", Task.deleted_at.is_(None)
        )
    )
    return created, closed, int(open_total or 0)


async def list_tasks(
    db: AsyncSession, farm_id: UUID, status: str | None = None, assigned_to: UUID | None = None
) -> list[tuple[Task, str | None]]:
    """(Task, ear_tag) 목록 — priority 오름차순, overdue_days 내림차순."""
    q = (
        select(Task, Sow.ear_tag)
        .outerjoin(Sow, Sow.id == Task.sow_id)
        .where(Task.farm_id == farm_id, Task.deleted_at.is_(None))
    )
    if status:
        q = q.where(Task.status == status)
    if assigned_to:
        q = q.where(Task.assigned_to == assigned_to)
    q = q.order_by(Task.priority.asc(), Task.overdue_days.desc().nullslast(), Task.created_at.desc())
    return [(t, tag) for t, tag in (await db.execute(q)).all()]


async def update_task(
    db: AsyncSession, farm_id: UUID, task_id: UUID, user_id: UUID,
    status: str | None = None, assigned_to: UUID | None = None,
) -> tuple[Task, str | None]:
    task = await db.scalar(
        select(Task).where(Task.id == task_id, Task.farm_id == farm_id, Task.deleted_at.is_(None))
    )
    if not task:
        raise NotFoundError(f"Task {task_id} not found")
    if status is not None:
        task.status = status
        if status in ("DONE", "DISMISSED"):
            task.completed_at = datetime.now(UTC)
            task.completed_by = user_id
        else:
            task.completed_at = None
            task.completed_by = None
    if assigned_to is not None:
        task.assigned_to = assigned_to
    await db.commit()
    await db.refresh(task)
    ear_tag = await db.scalar(select(Sow.ear_tag).where(Sow.id == task.sow_id)) if task.sow_id else None
    return task, ear_tag
