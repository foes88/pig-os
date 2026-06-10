"""Unit tests for alert classification logic (pure functions)."""
from datetime import date

from app.services.alert_service import (
    AlertThresholds,
    classify_cull,
    classify_overdue,
)

TODAY = date(2026, 6, 10)
TH = AlertThresholds()


class TestClassifyOverdue:
    def test_gilt_overdue_mating(self):
        # age 260 > 240, never mated
        res = classify_overdue(status="GILT", today=TODAY, age_days=260)
        assert res == ("gilt_overdue_mating", 20)

    def test_gilt_no_estrus(self):
        # age 200 >= 180, no heat, not yet past mating age
        res = classify_overdue(status="GILT", today=TODAY, age_days=200, has_heat=False)
        assert res == ("gilt_no_estrus", 20)

    def test_gilt_with_heat_on_schedule(self):
        res = classify_overdue(status="GILT", today=TODAY, age_days=200, has_heat=True)
        assert res is None

    def test_gilt_young_on_schedule(self):
        res = classify_overdue(status="GILT", today=TODAY, age_days=150)
        assert res is None

    def test_pregnant_overdue_farrowing(self):
        res = classify_overdue(
            status="PREGNANT", today=TODAY, last_mating=date(2026, 2, 1)
        )
        # 129 days since mating > 114
        assert res[0] == "pregnant_overdue_farrowing"
        assert res[1] == (TODAY - date(2026, 2, 1)).days - 114

    def test_pregnant_on_schedule(self):
        res = classify_overdue(
            status="PREGNANT", today=TODAY, last_mating=date(2026, 5, 1)
        )
        assert res is None  # 40 days < 114

    def test_lactating_overdue_weaning(self):
        res = classify_overdue(
            status="LACTATING", today=TODAY, last_farrowing=date(2026, 5, 1)
        )
        assert res[0] == "lactating_overdue_weaning"  # 40 days > 21

    def test_lactating_on_schedule(self):
        res = classify_overdue(
            status="LACTATING", today=TODAY, last_farrowing=date(2026, 6, 1)
        )
        assert res is None  # 9 days < 21

    def test_open_overdue_mating(self):
        res = classify_overdue(
            status="OPEN", today=TODAY, last_weaning=date(2026, 5, 25)
        )
        assert res[0] == "open_overdue_mating"  # 16 days > 7

    def test_open_on_schedule(self):
        res = classify_overdue(
            status="OPEN", today=TODAY, last_weaning=date(2026, 6, 6)
        )
        assert res is None  # 4 days < 7

    def test_accident_overdue_mating(self):
        res = classify_overdue(
            status="ACCIDENT", today=TODAY, last_rts=date(2026, 5, 20)
        )
        assert res[0] == "accident_overdue_mating"  # 21 days > 7

    def test_boundary_exactly_on_threshold_not_overdue(self):
        # exactly gestation_days (114) is NOT overdue (strictly greater)
        res = classify_overdue(
            status="PREGNANT", today=TODAY, last_mating=TODAY - __import__("datetime").timedelta(days=114)
        )
        assert res is None


class TestClassifyCull:
    def test_repeat_rts(self):
        assert "repeat_rts" in classify_cull(status="OPEN", parity=3, consecutive_rts=3)

    def test_repeat_rts_below_threshold(self):
        assert classify_cull(status="OPEN", parity=3, consecutive_rts=2) == []

    def test_aged_low_performer(self):
        reasons = classify_cull(status="OPEN", parity=8, last_weaned_count=8)
        assert "aged_low_performer" in reasons

    def test_aged_but_good_performer(self):
        reasons = classify_cull(status="OPEN", parity=8, last_weaned_count=11)
        assert "aged_low_performer" not in reasons

    def test_overdue_gilt(self):
        reasons = classify_cull(status="GILT", parity=0, age_days=320)
        assert "overdue_gilt" in reasons

    def test_overdue_gilt_but_mated(self):
        reasons = classify_cull(
            status="GILT", parity=0, age_days=320, last_mating=date(2026, 1, 1)
        )
        assert "overdue_gilt" not in reasons

    def test_multiple_reasons(self):
        reasons = classify_cull(
            status="OPEN", parity=9, last_weaned_count=7, consecutive_rts=4
        )
        assert set(reasons) == {"repeat_rts", "aged_low_performer"}

    def test_no_reasons(self):
        assert classify_cull(status="OPEN", parity=4, last_weaned_count=12) == []
