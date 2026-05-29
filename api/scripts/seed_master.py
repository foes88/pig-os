"""
Master data seeder — run once after schema migration.

Usage:
  cd api
  python scripts/seed_master.py

The SQL file is idempotent (ON CONFLICT DO NOTHING), safe to re-run.
"""
import asyncio
import pathlib
import sys

# Add parent to path so `app` is importable without install
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

SEED_FILE = (
    pathlib.Path(__file__).parent.parent.parent
    / "docs" / "master-data" / "2026-05-19_seed-v2.sql"
)


async def seed() -> None:
    sql = SEED_FILE.read_text(encoding="utf-8")

    # Split on statement boundaries; skip blank / comment-only blocks
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    comment_prefix = ("--", "/*")
    runnable = [
        s for s in statements
        if not all(line.startswith(comment_prefix) or not line for line in s.splitlines())
    ]

    async with AsyncSessionLocal() as db:
        async with db.begin():
            for stmt in runnable:
                await db.execute(text(stmt))

    print(f"[seed] Done — {len(runnable)} statement(s) executed from {SEED_FILE.name}")


if __name__ == "__main__":
    asyncio.run(seed())
