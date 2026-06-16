"""분만 /sync 500 재현 — process_sync에 farrowing 1건을 넣고 정확한 traceback 출력.
QA-001(45ea3687, PREGNANT, 교배 보유) / farm dbde1254 사용.
실행: cd api; PYTHONPATH=. .venv/Scripts/python.exe scripts/repro_farrowing_500.py
"""
import asyncio
import traceback
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.models.platform import Farm
from app.db.session import AsyncSessionLocal
from app.schemas.sync import SyncChanges, SyncFarrowing, SyncRequest
from app.services.sync_service import process_sync

FARM_ID = "dbde1254-7905-4ee8-a89c-1f518820c971"
SOW_ID = "45ea3687-073d-4b81-9c88-2f246454d503"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        farm = await db.scalar(select(Farm).where(Farm.id == FARM_ID))
        if not farm:
            print("farm 없음 — 다른 farm/sow로 바꾸세요")
            return
        req = SyncRequest(
            farm_id=FARM_ID,
            client_id=str(uuid4()),
            last_sync_at=datetime.fromisoformat("2026-06-16T01:56:00.172422+00:00"),
            changes=SyncChanges(
                farrowings=[SyncFarrowing(
                    id=uuid4(),
                    sow_id=SOW_ID,
                    farrowing_date="2026-06-16",
                    total_born=12, born_alive=12, born_dead=0, mummies=0,
                    farrowing_type="NORMAL",
                    client_created_at=datetime.now(UTC),
                )],
            ),
        )
        try:
            resp = await process_sync(db, farm, req)
            print("OK:", resp.stats, "rejected=", resp.rejected)
        except Exception:
            print("=== 500 TRACEBACK ===")
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
