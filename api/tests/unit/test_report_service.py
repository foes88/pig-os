"""Unit tests for report aggregation pure builders."""
from datetime import date

from app.services.report_service import (
    benchmark_values_from_effective,
    build_grow_finish_rows,
    build_reproduction_rows,
    build_sow_history,
    period_key,
)


class TestPeriodKey:
    def test_monthly(self):
        assert period_key(date(2026, 3, 15), "monthly") == "2026-03"

    def test_quarterly(self):
        assert period_key(date(2026, 4, 1), "quarterly") == "2026-Q2"
        assert period_key(date(2026, 12, 31), "quarterly") == "2026-Q4"

    def test_annual(self):
        assert period_key(date(2026, 7, 1), "annual") == "2026"


class TestReproductionRows:
    def test_three_months_monthly(self):
        matings = [date(2026, 1, 5), date(2026, 1, 20), date(2026, 2, 3), date(2026, 3, 1)]
        farrowings = [
            (date(2026, 1, 10), 14, 13),
            (date(2026, 2, 12), 12, 11),
            (date(2026, 3, 15), 16, 15),
        ]
        weanings = [
            (date(2026, 1, 28), 11, 21),
            (date(2026, 2, 27), 10, 22),
        ]
        rts = [date(2026, 1, 25)]
        deaths = [(date(2026, 1, 15), 2)]
        rows = build_reproduction_rows("monthly", matings, farrowings, weanings, rts, deaths)
        assert [r["period"] for r in rows] == ["2026-01", "2026-02", "2026-03"]
        jan = rows[0]
        assert jan["total_matings"] == 2
        assert jan["total_farrowings"] == 1
        assert jan["avg_tb"] == 14.0
        assert jan["fr"] == 50.0  # 1 farrowing / 2 matings
        assert jan["rts_rate"] == 50.0
        # pwmr_b = (14 - 11)/14*100 = 21.4
        assert jan["pwmr_b"] == 21.4
        # pwmr_a = deaths 2 / (weaned 11 + deaths 2) = 15.4
        assert jan["pwmr_a"] == 15.4

    def test_quarterly_bucketing(self):
        farrowings = [(date(2026, 1, 1), 12, 11), (date(2026, 4, 1), 14, 13)]
        rows = build_reproduction_rows("quarterly", [], farrowings, [], [], [])
        assert [r["period"] for r in rows] == ["2026-Q1", "2026-Q2"]

    def test_empty(self):
        assert build_reproduction_rows("monthly", [], [], [], [], []) == []

    def test_no_matings_fr_none(self):
        rows = build_reproduction_rows("annual", [], [(date(2026, 1, 1), 12, 11)], [], [], [])
        assert rows[0]["fr"] is None
        assert rows[0]["rts_rate"] is None


class TestReproductionExtended:
    def test_backward_compat_adds_zero_fields(self):
        # 기존 positional 호출 — 신규 필드는 0/None, 기존 필드 무회귀
        farrowings = [(date(2026, 1, 10), 14, 13)]
        rows = build_reproduction_rows("monthly", [date(2026, 1, 5)], farrowings, [], [], [])
        r = rows[0]
        assert r["avg_tb"] == 14.0
        assert r["total_stillborn"] == 0
        assert r["total_born_sum"] == 14
        assert r["born_alive_sum"] == 13
        assert r["stillborn_rate"] == 0.0   # sb 0 / tb 14
        assert r["mating_1_count"] == 0     # mating_numbers 미전달

    def test_stillborn_mummified_rates(self):
        farrowings = [(date(2026, 1, 10), 14, 12), (date(2026, 1, 20), 16, 14)]
        rows = build_reproduction_rows(
            "monthly", [], farrowings, [], [], [],
            stillborn=[1, 1], mummified=[1, 1],
        )
        r = rows[0]
        # tb_sum=30, sb=2 → 6.7%, mum=2 → 6.7%, loss=4/30 → 13.3%
        assert r["total_stillborn"] == 2
        assert r["total_mummified"] == 2
        assert r["stillborn_rate"] == 6.7
        assert r["birth_loss_rate"] == 13.3

    def test_mating_breakdown(self):
        matings = [date(2026, 1, 1)] * 4
        rows = build_reproduction_rows(
            "annual", matings, [], [], [], [],
            mating_numbers=[1, 1, 2, 3], mating_types=["AI", "AI", "NATURAL", "AI"],
        )
        r = rows[0]
        assert r["mating_1_count"] == 2
        assert r["mating_2_count"] == 1
        assert r["mating_3plus_count"] == 1
        assert r["ai_count"] == 3
        assert r["natural_count"] == 1

    def test_group_by_breed(self):
        matings = [date(2026, 1, 1), date(2026, 6, 1), date(2026, 7, 1)]
        rows = build_reproduction_rows(
            "monthly", matings, [], [], [], [],
            group_by="breed", mating_breeds=["LY", "LY", "Duroc"],
        )
        by = {r["period"]: r for r in rows}
        assert set(by) == {"LY", "Duroc"}
        assert by["LY"]["total_matings"] == 2
        assert by["Duroc"]["total_matings"] == 1

    def test_group_by_breed_unknown(self):
        rows = build_reproduction_rows(
            "monthly", [date(2026, 1, 1)], [], [], [], [],
            group_by="breed", mating_breeds=[None],
        )
        assert rows[0]["period"] == "unknown"


class TestBenchmarkMapping:
    def test_maps_effective_fields(self):
        effective = [{
            "metric_code": "PSY", "target": 24.0, "avg": 22.1, "top25": 28.0,
            "warning": 22.0, "critical": 18.0, "direction": "below",
            "unit": "두/모돈/년", "source": "한돈팜스2023", "confidence": "high",
        }]
        out = benchmark_values_from_effective(effective)
        assert out[0]["metric_code"] == "PSY"
        assert out[0]["target"] == 24.0
        assert out[0]["benchmark_avg"] == 22.1
        assert out[0]["benchmark_top25"] == 28.0
        assert out[0]["alert_direction"] == "below"
        assert out[0]["source_ref"] == "한돈팜스2023"

    def test_empty(self):
        assert benchmark_values_from_effective([]) == []


class TestGrowFinishRows:
    def test_adg_fcr_mortality(self):
        groups = [{
            "group_code": "G1", "start_date": date(2026, 1, 1), "end_date": date(2026, 4, 1),
            "head_in": 100, "head_out": 96, "entry_w": 25.0, "exit_w": 115.0,
        }]
        # days = 90, gain/head = 90kg, adg = 90/90*1000 = 1000 g/day
        # gain_total = 90 * 96 = 8640 kg; feed 19872 → fcr = 2.3
        rows = build_grow_finish_rows(groups, {"G1": 19872.0})
        r = rows[0]
        assert r["adg_g"] == 1000.0
        assert r["mortality_rate"] == 4.0
        assert r["fcr"] == 2.3

    def test_no_feed_fcr_none(self):
        groups = [{
            "group_code": "G2", "start_date": date(2026, 1, 1), "end_date": date(2026, 4, 1),
            "head_in": 100, "head_out": 100, "entry_w": 25.0, "exit_w": 115.0,
        }]
        rows = build_grow_finish_rows(groups, {})
        assert rows[0]["fcr"] is None
        assert rows[0]["adg_g"] == 1000.0

    def test_open_group_no_end_date(self):
        groups = [{
            "group_code": "G3", "start_date": date(2026, 1, 1), "end_date": None,
            "head_in": 100, "head_out": None, "entry_w": 25.0, "exit_w": None,
        }]
        rows = build_grow_finish_rows(groups, {})
        assert rows[0]["adg_g"] is None
        assert rows[0]["mortality_rate"] is None


class TestSowHistory:
    def test_completed_and_in_progress(self):
        cycles = [{"cycle_id": "c1", "parity": 1}, {"cycle_id": "c2", "parity": 2}]
        matings = [
            {"cycle_id": "c1", "date": date(2026, 1, 1), "boar_id": "b1"},
            {"cycle_id": "c2", "date": date(2026, 5, 1), "boar_id": "b2"},
        ]
        farrowings = [{"cycle_id": "c1", "date": date(2026, 4, 25), "tb": 14, "ba": 13, "sb": 1, "mum": 0}]
        weanings = [{"cycle_id": "c1", "date": date(2026, 5, 16), "weaned": 11, "lactation_days": 21}]
        rows = build_sow_history(cycles, matings, farrowings, weanings)
        assert rows[0]["parity"] == 1
        assert rows[0]["status"] == "completed"
        assert rows[0]["weaned"] == 11
        assert rows[0]["boar_ids"] == ["b1"]
        assert rows[1]["parity"] == 2
        assert rows[1]["status"] == "in_progress"
        assert rows[1]["farrowing_date"] is None
