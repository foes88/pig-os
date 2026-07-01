"""#6 — build_sow_history 부분이유 집계.

기존 w_by={w["cycle_id"]: w ...}는 사이클당 '마지막' 이유만 남겨, 부분이유(8+3) 시
weaned=3(마지막)만 표시하고 첫 부분이유에 status="completed"를 붙였음.
사이클당 이유두수 합산 + 완료판정은 cycle_status(WEANED) 기준으로 정정.
"""
from datetime import date

from app.services.report_service import build_sow_history


def _cyc(status):
    return [{"cycle_id": "c1", "parity": 2, "status": status}]


def test_aggregates_partial_weanings_sum_and_last_date():
    farrowings = [{"cycle_id": "c1", "date": date(2026, 4, 20), "tb": 14, "ba": 13, "sb": 1, "mum": 0}]
    weanings = [
        {"cycle_id": "c1", "date": date(2026, 5, 11), "weaned": 8, "lactation_days": 21},
        {"cycle_id": "c1", "date": date(2026, 5, 18), "weaned": 3, "lactation_days": 28},
    ]
    out = build_sow_history(_cyc("WEANED"), [], farrowings, weanings)
    assert out[0]["weaned"] == 11, "부분이유 합산(8+3)이어야 함(마지막 3만 아님)"
    assert out[0]["weaning_date"] == "2026-05-18", "최종 이유일"
    assert out[0]["lactation_days"] == 28
    assert out[0]["status"] == "completed"


def test_partial_weaning_in_progress_not_completed():
    # 부분이유 1건만 기록, 사이클은 아직 FARROWED(잔여 포유 중)
    weanings = [{"cycle_id": "c1", "date": date(2026, 5, 11), "weaned": 8, "lactation_days": 21}]
    out = build_sow_history(_cyc("FARROWED"), [], [], weanings)
    assert out[0]["weaned"] == 8
    assert out[0]["status"] == "in_progress", "첫 부분이유에 완료표기하면 안 됨(사이클 미완)"


def test_no_weaning_is_in_progress():
    out = build_sow_history(_cyc("MATED"), [], [], [])
    assert out[0]["weaned"] is None and out[0]["status"] == "in_progress"
