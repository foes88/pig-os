"""하베스트 orphan 분만 백필 — 누락된 분만/교배/이유만 삽입(breeding_cycle_id=NULL).

배경: reconstruct가 선행 교배 없는 분만("orphan")을 버려 PigPlan 대비 ~9% 분만 누락 →
PSY·모돈회전율·NPD 왜곡. reconstruct 수정(교배 합성) 후, 기존 데이터를 전체 재임포트하면
cycle uid(idx 기반)가 밀려 사이클이 대량 중복됨. 그래서 여기서는 이벤트 테이블만
안정적 uid(wk 기반)로 ON CONFLICT DO NOTHING 삽입하고 breeding_cycle_id는 NULL로 둔다
(KPI는 cycle을 참조하지 않음). 기존 행은 건드리지 않음.

사용:
  cd api
  uv run --with oracledb python scripts/backfill_orphan_farrowings.py --farm 2807           # dry-run(읽기만)
  uv run --with oracledb python scripts/backfill_orphan_farrowings.py --farm 2807 --write    # 실제 삽입(prod)

주의: PROD_PG_DSN/ORACLE_PW 는 api/.env.harvest 에서 로드. Oracle 은 READ-ONLY(SELECT) 만 사용.
"""
import argparse
import os

from dotenv import load_dotenv

load_dotenv(".env.harvest")
os.environ.setdefault("ORACLE_USER", "pksu")

import harvest_import as h  # noqa: E402
import psycopg2  # noqa: E402
import psycopg2.extras as ex  # noqa: E402

# 이벤트 튜플에서 breeding_cycle_id 위치(harvest_import.build_rows 스키마 기준)
_CYC_IDX = {"matings": 3, "farrowings": 4, "weanings": 4}

_SQL = {
    "matings": (
        "INSERT INTO matings (id, farm_id, sow_id, breeding_cycle_id, mating_date, "
        "mating_type, mating_number) VALUES %s ON CONFLICT (id) DO NOTHING"
    ),
    "farrowings": (
        "INSERT INTO farrowings (id, farm_id, sow_id, mating_id, breeding_cycle_id, "
        "farrowing_date, total_born, born_alive, stillborn, mummified, nursing_head, "
        "avg_birth_weight_kg) VALUES %s ON CONFLICT (id) DO NOTHING"
    ),
    "weanings": (
        "INSERT INTO weanings (id, farm_id, sow_id, farrowing_id, breeding_cycle_id, "
        "weaning_date, weaned_count, weaning_age_days, avg_weaning_weight_kg) "
        "VALUES %s ON CONFLICT (id) DO NOTHING"
    ),
}


def _null_cycle(rows, idx):
    out = []
    for r in rows:
        t = list(r)
        t[idx] = None  # breeding_cycle_id -> NULL (백필분은 사이클 미링크)
        out.append(tuple(t))
    return out


def _count(cur, table, farm_id):
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE farm_id=%s AND deleted_at IS NULL", (str(farm_id),))
    return cur.fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--farm", type=int, required=True)
    ap.add_argument("--write", action="store_true", help="실제 prod 삽입(미지정 시 dry-run)")
    args = ap.parse_args()

    import oracledb
    ocn = oracledb.connect(user=os.getenv("ORACLE_USER", "pksu"), password=os.environ["ORACLE_PW"],
                           dsn=os.getenv("ORACLE_DSN", h.ORACLE_DSN))
    ocur = ocn.cursor()
    src = h.fetch_farm(ocur, args.farm)          # READ-ONLY
    farm_id = h.uid("farm", args.farm)
    R, stats = h.build_rows(args.farm, farm_id, src)
    ocur.close()
    ocn.close()

    rows = {t: _null_cycle(R[t], _CYC_IDX[t]) for t in _SQL}

    pg = psycopg2.connect(os.environ["PROD_PG_DSN"])
    cur = pg.cursor()
    before = {t: _count(cur, t, farm_id) for t in ("farrowings", "weanings")}
    print(f"farm={args.farm} farm_id={farm_id}")
    print(f"재구성(수정 로직): 교배 {len(rows['matings'])} / 분만 {len(rows['farrowings'])} / "
          f"이유 {len(rows['weanings'])}  (합성복구 {stats['orphan_far']})")
    print(f"prod 현재: 분만 {before['farrowings']} / 이유 {before['weanings']}")

    if not args.write:
        print("=> DRY-RUN (쓰기 없음). 실제 삽입은 --write")
        cur.close()
        pg.close()
        return

    ex.register_uuid()
    for t in ("matings", "farrowings", "weanings"):  # FK 순서
        ex.execute_values(cur, _SQL[t], rows[t], page_size=1000)
    pg.commit()

    after = {t: _count(cur, t, farm_id) for t in ("farrowings", "weanings")}
    print(f"=> WROTE. 분만 {before['farrowings']}→{after['farrowings']} "
          f"(+{after['farrowings'] - before['farrowings']}) / "
          f"이유 {before['weanings']}→{after['weanings']} (+{after['weanings'] - before['weanings']})")
    cur.close()
    pg.close()


if __name__ == "__main__":
    main()
