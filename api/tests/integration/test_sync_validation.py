"""동기화 경로 입력검증 회귀 (야간QA finding #1) — pigos_test.

REST 생성경로는 validator(분만 TB≤35 등)를 거치지만 sync 경로(_process_farrowing/_weaning)는
카운트 validator를 호출하지 않는다(2026-06-16 발견). 아래는 '수정되면 통과'할 기대 스펙을
strict xfail로 고정 — 수정(검증 추가) 시 XPASS가 되어 마커 제거를 강제한다.
계약 변경(SyncRejected 신규 사유 + offline-sync-spec 갱신)이 필요하므로 사람 승인 후 수정.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.schemas.sync import SyncFarrowing
from app.services.sync_service import _process_farrowing

pytestmark = pytest.mark.asyncio


@pytest.mark.xfail(reason="sync 경로 카운트 validator 미적용(finding #1) — 수정 시 XPASS", strict=True)
async def test_sync_farrowing_rejects_out_of_range_total_born(db, test_farm, test_sow):
    test_sow.status = "PREGNANT"
    await db.flush()
    item = SyncFarrowing(
        id=uuid4(), sow_id=test_sow.id, farrowing_date="2026-06-01",
        total_born=999, born_alive=999, born_dead=0, mummies=0,
        client_created_at=datetime.now(UTC),
    )
    accepted, rejected, conflict = await _process_farrowing(db, test_farm.id, item, dry_run=True)
    # 기대(검증 추가 후): 범위 초과(TB>35)는 거부되어야 함
    assert rejected is not None, "sync가 비정상 카운트를 수용함 (검증 필요)"
