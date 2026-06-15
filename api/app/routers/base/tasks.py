"""
Tasks router — 자동배정 작업(오늘 할 일) 조회/생성/처리. (Phase 2)

alert_service의 지연모돈·도태권고를 Task로 변환하여 담당자가 처리한다.
Reference: CLAUDE.md → "Task 자동배정 시스템".
"""
from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep, FarmDep
from app.schemas.task import TaskGenerateResult, TaskResponse, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/farms/{farm_id}/tasks", tags=["Tasks"])


def _to_response(task, ear_tag: str | None) -> TaskResponse:
    return TaskResponse(
        id=task.id, farm_id=task.farm_id, sow_id=task.sow_id, ear_tag=ear_tag,
        task_type=task.task_type, title=task.title, action=task.action,
        status=task.status, priority=task.priority, overdue_days=task.overdue_days,
        due_date=task.due_date, assigned_to=task.assigned_to,
        completed_at=task.completed_at, created_at=task.created_at,
    )


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    farm: FarmDep, db: DbDep, status: str = "OPEN", assigned_to: UUID | None = None,
) -> list[TaskResponse]:
    rows = await task_service.list_tasks(db, farm.id, status=status or None, assigned_to=assigned_to)
    return [_to_response(t, tag) for t, tag in rows]


@router.post("/generate", response_model=TaskGenerateResult)
async def generate_tasks(farm: FarmDep, db: DbDep) -> TaskGenerateResult:
    created, closed, open_total = await task_service.generate_tasks(db, farm.id)
    return TaskGenerateResult(created=created, closed=closed, open_total=open_total)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID, payload: TaskUpdate, farm: FarmDep, db: DbDep, user: CurrentUser,
) -> TaskResponse:
    task, ear_tag = await task_service.update_task(
        db, farm.id, task_id, user.id, status=payload.status, assigned_to=payload.assigned_to,
    )
    return _to_response(task, ear_tag)
