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


def _split_sql(sql: str) -> list[str]:
    """세미콜론 기준 분할하되 작은따옴표 문자열('') 안의 ';'는 보존.
    단순 sql.split(';')는 'EU: Severely restricted; ...' 같은 리터럴을 깨뜨려
    ProgrammingError를 냈음. '' 이스케이프도 처리."""
    out, buf, in_str = [], [], False
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        buf.append(c)
        if c == "'":
            if in_str and i + 1 < n and sql[i + 1] == "'":  # '' escape
                buf.append(sql[i + 1])
                i += 2
                continue
            in_str = not in_str
        elif c == ";" and not in_str:
            out.append("".join(buf))
            buf = []
        i += 1
    if "".join(buf).strip():
        out.append("".join(buf))
    return out


async def seed() -> None:
    sql = SEED_FILE.read_text(encoding="utf-8")

    # 문자열 내 ';' 보존 분할(단순 split(";")는 notes의 세미콜론에서 깨짐)
    statements = [s.strip() for s in _split_sql(sql) if s.strip()]
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
