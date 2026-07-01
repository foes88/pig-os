"""#5 — 재생산 보고서 부분이유 복(litter)단위 집계.

기존: 이유 행마다 x["weanings"]+1 · x["weaned"].append(wc) → 부분이유(8+3) 시
avg_weaned=avg([8,3])=5.5(복당 11이어야), total_weanings=2(복 1개여야). 합계만 정상.
복(farrowing_id)단위로 합산해 avg_weaned=복당 평균, total_weanings=복 수로 정정.
"""
from datetime import date

from app.services.report_service import build_reproduction_rows


def test_partial_weaning_counts_per_litter_not_per_row():
    # 한 복(f1)을 같은 달 8+3으로 부분이유 + 다른 복(f2) 10 한 번에
    weanings = [
        (date(2026, 5, 11), 8, 21),
        (date(2026, 5, 18), 3, 28),
        (date(2026, 5, 20), 10, 25),
    ]
    litter_ids = ["f1", "f1", "f2"]
    rows = build_reproduction_rows(
        "monthly", [], [], weanings, [], [], weaning_litter_ids=litter_ids)
    r = next(x for x in rows if x["period"] == "2026-05")
    assert r["total_weanings"] == 2, "복 2개(이유 3건 아님)"
    assert r["avg_weaned"] == 10.5, "복당 평균 (f1=11, f2=10) → 10.5 (avg[8,3,10]=7.0 아님)"


def test_without_litter_ids_falls_back_to_per_row():
    # 하위호환: litter_id 미전달 시 행 자체를 1복으로(구동작)
    weanings = [(date(2026, 5, 11), 8, 21), (date(2026, 5, 18), 10, 28)]
    rows = build_reproduction_rows("monthly", [], [], weanings, [], [])
    r = next(x for x in rows if x["period"] == "2026-05")
    assert r["total_weanings"] == 2 and r["avg_weaned"] == 9.0
