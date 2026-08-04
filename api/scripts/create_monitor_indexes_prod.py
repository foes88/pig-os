"""프로드 data-monitor 성능 인덱스 생성 — 무중단(CONCURRENTLY).

/admin/data-monitor 8.8s(타임아웃) 원인: 7개 이벤트테이블 (farm_id, created_at) 무인덱스.
CONCURRENTLY = 테이블 잠금 없이 생성(안전·additive). IF NOT EXISTS라 재실행 무해.

사용:
  cd api
  uv run python scripts/create_monitor_indexes_prod.py           # dry-run(생성 안 함, 현재 소요만 측정)
  uv run python scripts/create_monitor_indexes_prod.py --write    # 실제 생성(프로드)
"""
import argparse
import os
import re
import time

from dotenv import load_dotenv

load_dotenv(".env.harvest")
import psycopg2  # noqa: E402

_IDX = [
    ("idx_matings_farm_created", "matings"),
    ("idx_farrowings_farm_created", "farrowings"),
    ("idx_weanings_farm_created", "weanings"),
    ("idx_health_farm_created", "health_events"),
    ("idx_removals_farm_created", "removals"),
    ("idx_piglet_farm_created", "piglet_events"),
    ("idx_feed_farm_created", "feed_records"),
]


def _monitor_sql() -> str:
    src = open("app/routers/admin/admin.py", encoding="utf-8").read()
    sql = re.search(r'_FARM_ACTIVITY_SQL = f"""(.*?)"""', src, re.S).group(1)
    eu = re.search(r'_EVENT_UNION = """(.*?)"""', src, re.S).group(1)
    return sql.replace("{_EVENT_UNION}", eu)


def _time_query(dsn: str) -> float:
    cn = psycopg2.connect(dsn); cn.set_session(readonly=True); c = cn.cursor()
    t = time.time(); c.execute(_monitor_sql()); c.fetchall(); el = time.time() - t
    c.close(); cn.close()
    return el


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    dsn = os.environ["PROD_PG_DSN"]

    print(f"적용 전 data-monitor 쿼리: {_time_query(dsn):.2f}s")
    if not args.write:
        print("=> DRY-RUN. 실제 인덱스 생성은 --write")
        return

    cn = psycopg2.connect(dsn)
    cn.autocommit = True  # CONCURRENTLY는 트랜잭션 밖에서만
    c = cn.cursor()
    for name, table in _IDX:
        t = time.time()
        c.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} ON {table}(farm_id, created_at)")
        print(f"  {name} on {table}  ({time.time() - t:.1f}s)")
    c.close(); cn.close()
    print(f"적용 후 data-monitor 쿼리: {_time_query(dsn):.2f}s")


if __name__ == "__main__":
    main()
