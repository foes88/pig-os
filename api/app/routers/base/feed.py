"""사료 급여(Feed) 입력 라우터 — 수기 급이량 기록. farm-scoped.

FCR·grow-finish 리포트의 입력원(handoff/FINDING_feed_input_gap.md 해소).
일상입력 WORKER+, 삭제는 관리자.
"""
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbDep, FarmDep, require_farm_role
from app.schemas.feed import FeedRecordCreate, FeedRecordResponse
from app.services import feed_service

router = APIRouter(prefix="/farms/{farm_id}/feed-records", tags=["Feed"])

_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN")
_MANAGE_ROLES = ("FARM_OWNER", "FARM_MANAGER", "SUPER_ADMIN")


@router.get("", response_model=list[FeedRecordResponse])
async def list_feed_records(
    farm: FarmDep,
    db: DbDep,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await feed_service.list_feed_records(db, farm.id, limit=limit, offset=offset)


@router.post("", response_model=FeedRecordResponse, status_code=201,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
async def create_feed_record(
    farm: FarmDep,
    db: DbDep,
    current_user: CurrentUser,
    body: FeedRecordCreate,
):
    return await feed_service.create_feed_record(db, farm.id, current_user.id, body)


@router.delete("/{record_id}", status_code=204,
               dependencies=[require_farm_role(*_MANAGE_ROLES)])
async def delete_feed_record(
    farm: FarmDep,
    db: DbDep,
    record_id: UUID,
):
    await feed_service.delete_feed_record(db, farm.id, record_id)
