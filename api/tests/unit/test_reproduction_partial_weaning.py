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


def test_pwmr_b_is_per_litter_not_mismatched_sets():
    # 같은 버킷 분만 2복(tb 14,12) + 그 복들의 총 이유(11,9)
    farrowings = [(date(2026, 5, 5), 14, 13), (date(2026, 5, 8), 12, 11)]
    rows = build_reproduction_rows("monthly", [], farrowings, [], [], [],
                                   farrowing_weaned=[11, 9])
    r = next(x for x in rows if x["period"] == "2026-05")
    # 복단위: (14-11)/14=21.43, (12-9)/12=25.0 → avg 23.2 (무관 세트 평균 아님)
    assert r["pwmr_b"] == 23.2


def test_pwmr_b_none_when_no_litter_weaned():
    farrowings = [(date(2026, 5, 5), 14, 13)]
    rows = build_reproduction_rows("monthly", [], farrowings, [], [], [],
                                   farrowing_weaned=[None])  # 아직 이유 안 된 복
    r = next(x for x in rows if x["period"] == "2026-05")
    assert r["pwmr_b"] is None
