"""BACKFILL-PENDING — 기존 reproductive_events의 mating_id/breeding_cycle_id 채움 (QA C 옵션A 전제).

순방향 링크(record_reproductive_event)는 신규만 채운다. 기존 이벤트는 이 스크립트로 백필해야
옵션A(RTS/ABORTION rate 코호트 정합)를 안전히 적용할 수 있다(미링크 이벤트 탈락 방지).

로직: mating_id IS NULL인 각 이벤트 → sow의 event_date 이전 최근 교배로 매칭.
실행(사람 승인 후): cd api && .venv\\Scripts\\python.exe -m scripts.backfill_reproductive_links [--dry-run]
분석: docs(android)/DECISION_RTS_COHORT_2026-07-01.md
"""
import asyncio
import sys

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

_BACKFILL_SQL = text("""
    UPDATE reproductive_events re
    SET mating_id = m.id, breeding_cycle_id = m.breeding_cycle_id
    FROM LATERAL (
        SELECT id, breeding_cycle_id FROM matings
        WHERE sow_id = re.sow_id AND deleted_at IS NULL AND mating_date <= re.event_date
        ORDER BY mating_date DESC LIMIT 1
    ) m
    WHERE re.mating_id IS NULL AND re.deleted_at IS NULL
""")

_COUNT_SQL = text("SELECT count(*) FROM reproductive_events WHERE mating_id IS NULL AND deleted_at IS NULL")


async def main(dry_run: bool) -> None:
    async with AsyncSessionLocal() as db:
        before = (await db.execute(_COUNT_SQL)).scalar()
        print(f"미링크 reproductive_events: {before}건")
        if dry_run:
            print("--dry-run: 변경 없음. 실제 적용은 인자 없이 재실행.")
            return
        res = await db.execute(_BACKFILL_SQL)
        await db.commit()
        after = (await db.execute(_COUNT_SQL)).scalar()
        print(f"백필 완료: {res.rowcount}건 링크됨. 잔여 미링크(대응 교배 없음): {after}건")


if __name__ == "__main__":
    asyncio.run(main("--dry-run" in sys.argv))
