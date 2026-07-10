#!/usr/bin/env python
"""
파일럿 후속 Phase C — 수치 정합성 검증 (적재된 pigos DB ↔ 피그플랜 raw CSV).

농장×연도: PigOS DB 이벤트 카운트(교배/분만/이유두수) ↔ 원본 CSV 카운트 대조.
+ 무결성 DB 체크: 두수 항등식·상태 고아·날짜 역전.
전제: import_pigplan(적재) 완료. 로컬 Docker pigos DB.
실행: cd api && uv run python -m scripts.verify_pilot
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from sqlalchemy import text

from app.db.session import AsyncSessionLocal
from scripts.import_pigplan import DEFAULT_CSV, _farm_uuid, fnum, load_csv, pdate

PILOT = [2807, 4448, 848, 978]
TOL = 0.03  # 카운트 허용오차 3%


def raw_counts(csv_dir, farm_no):
    """원본 CSV 연도별 카운트: 교배·분만·이유두수합."""
    g, b, w = defaultdict(int), defaultdict(int), defaultdict(int)
    for r in load_csv(csv_dir, "TB_GYOBAE", {farm_no}):
        d = pdate(r["wk_dt"]); g[d.year] += 1 if d else 0
    for r in load_csv(csv_dir, "TB_BUNMAN", {farm_no}):
        d = pdate(r["wk_dt"]); b[d.year] += 1 if d else 0
    for r in load_csv(csv_dir, "TB_EU", {farm_no}):
        d = pdate(r["wk_dt"]); w[d.year] += int(fnum(r["dusu"])) if d else 0
    return g, b, w


async def pigos_counts(db, fid, year):
    q = lambda tbl, dcol: text(  # noqa: E731
        f"SELECT COUNT(*) FROM {tbl} WHERE farm_id=:f AND deleted_at IS NULL "
        f"AND EXTRACT(YEAR FROM {dcol})=:y")
    m = await db.scalar(q("matings", "mating_date"), {"f": str(fid), "y": year})
    b = await db.scalar(q("farrowings", "farrowing_date"), {"f": str(fid), "y": year})
    w = await db.scalar(text(
        "SELECT COALESCE(SUM(weaned_count),0) FROM weanings WHERE farm_id=:f "
        "AND deleted_at IS NULL AND EXTRACT(YEAR FROM weaning_date)=:y"), {"f": str(fid), "y": year})
    return int(m or 0), int(b or 0), int(w or 0)


async def integrity(db, fid):
    ident = await db.scalar(text(
        "SELECT COUNT(*) FROM farrowings WHERE farm_id=:f AND deleted_at IS NULL "
        "AND total_born <> born_alive + stillborn + mummified"), {"f": str(fid)})
    orphan = await db.scalar(text(
        "SELECT COUNT(*) FROM sows WHERE farm_id=:f AND status='LACTATING' AND deleted_at IS NULL "
        "AND id NOT IN (SELECT sow_id FROM farrowings WHERE farm_id=:f AND deleted_at IS NULL)"),
        {"f": str(fid)})
    rev = await db.scalar(text(
        "SELECT COUNT(*) FROM weanings w JOIN farrowings f ON f.id=w.farrowing_id "
        "WHERE w.farm_id=:f AND w.weaning_date < f.farrowing_date"), {"f": str(fid)})
    return int(ident or 0), int(orphan or 0), int(rev or 0)


def _match(pg, raw):
    if raw == 0:
        return "OK" if pg == 0 else f"+{pg}"
    diff = abs(pg - raw) / raw
    return "OK" if diff <= TOL else f"d{pg-raw:+d}({diff*100:.1f}%)"


async def main():
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    csv_dir = DEFAULT_CSV
    overall_pass = True
    async with AsyncSessionLocal() as db:
        for fn in PILOT:
            fid = _farm_uuid(fn)
            exists = await db.scalar(text("SELECT COUNT(*) FROM sows WHERE farm_id=:f"), {"f": str(fid)})
            if not exists:
                print(f"\n농장 {fn}: 적재 안 됨(스킵)")
                continue
            g, b, w = raw_counts(csv_dir, fn)
            years = sorted(y for y in set(g) | set(b) | set(w) if y >= 2020)
            print(f"\n=== 농장 {fn} 수치검증 (모돈 {exists}두) ===")
            print(f"  {'YR':4s} {'mate P/R':>14s} {'farr P/R':>14s} {'wean P/R':>16s}")
            for y in years:
                pm, pb, pw = await pigos_counts(db, fid, y)
                print(f"  {y:<4d} {f'{pm}/{g[y]}':>10s}{_match(pm,g[y]):>4s} "
                      f"{f'{pb}/{b[y]}':>10s}{_match(pb,b[y]):>4s} "
                      f"{f'{pw}/{w[y]}':>12s}{_match(pw,w[y]):>4s}")
            ident, orphan, rev = await integrity(db, fid)
            ok = ident == 0 and rev == 0
            overall_pass = overall_pass and ok
            print(f"  무결성: 두수항등식위반={ident} 상태고아(LACT)={orphan} 날짜역전={rev} "
                  f"→ {'PASS' if ok else 'FAIL'}")
    print(f"\n{'='*40}\n전체 무결성: {'PASS' if overall_pass else 'FAIL'}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
