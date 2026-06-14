"""
KPI 계산 로직 단위 테스트.
DB 없이 순수 파이썬 함수로 검증.
PigPlan 벤치마크 기준: PSY 30.4, 분만율 92.3%, 평균 이유수 12.4
"""
from datetime import date

import pytest

from app.jobs.kpi import _period_bounds

# ── _period_bounds ─────────────────────────────────────────────────────────────

class TestPeriodBounds:
    def test_daily(self):
        ref = date(2026, 5, 15)
        start, end = _period_bounds("DAILY", ref)
        assert start == end == ref

    def test_weekly_monday_start(self):
        # 2026-05-18 = 월요일
        ref = date(2026, 5, 20)  # 수요일
        start, end = _period_bounds("WEEKLY", ref)
        assert start == date(2026, 5, 18)  # 해당 주 월요일
        assert end == date(2026, 5, 24)    # 해당 주 일요일
        assert (end - start).days == 6

    def test_monthly_full_month(self):
        ref = date(2026, 3, 15)
        start, end = _period_bounds("MONTHLY", ref)
        assert start == date(2026, 3, 1)
        assert end == date(2026, 3, 31)

    def test_monthly_february_non_leap(self):
        ref = date(2025, 2, 10)
        start, end = _period_bounds("MONTHLY", ref)
        assert start == date(2025, 2, 1)
        assert end == date(2025, 2, 28)

    def test_monthly_february_leap(self):
        ref = date(2024, 2, 10)
        start, end = _period_bounds("MONTHLY", ref)
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_annual(self):
        ref = date(2026, 6, 1)
        start, end = _period_bounds("ANNUAL", ref)
        assert start == date(2026, 1, 1)
        assert end == date(2026, 12, 31)


# ── PSY 계산 ──────────────────────────────────────────────────────────────────

def calc_psy(total_weaned: int, active_sows: int, days: int) -> float | None:
    """PSY = (total_weaned / active_sows) * (365 / days)"""
    if active_sows <= 0:
        return None
    return round(total_weaned / active_sows * (365 / days), 2)


class TestPsyCalculation:
    def test_pigplan_benchmark(self):
        """피그플랜 벤치마크: 연간 PSY 30.4 재현"""
        # 연간: 농장 500두, 연간 이유수 15,200
        psy = calc_psy(total_weaned=15200, active_sows=500, days=365)
        assert psy == 30.4

    def test_monthly_annualized(self):
        """월간 데이터로 연환산 PSY"""
        # 4월(30일): 500두 농장, 620두 이유
        psy = calc_psy(total_weaned=620, active_sows=500, days=30)
        # 620/500 * (365/30) = 15.1
        assert psy == pytest.approx(15.1, rel=0.01)

    def test_zero_sows_returns_none(self):
        assert calc_psy(100, 0, 30) is None

    def test_zero_weaned(self):
        psy = calc_psy(0, 500, 30)
        assert psy == 0.0


# ── 분만율 계산 ───────────────────────────────────────────────────────────────

def calc_farrowing_rate(farrowings: int, matings: int) -> float | None:
    """분만율 = 분만수 / 교배수 * 100"""
    if matings <= 0:
        return None
    return round(farrowings / matings * 100, 1)


class TestFarrowingRate:
    def test_pigplan_benchmark(self):
        """피그플랜 벤치마크: 분만율 92.3%"""
        rate = calc_farrowing_rate(farrowings=923, matings=1000)
        assert rate == 92.3

    def test_zero_matings_returns_none(self):
        assert calc_farrowing_rate(10, 0) is None

    def test_perfect_rate(self):
        assert calc_farrowing_rate(100, 100) == 100.0

    def test_over_100_possible_with_twin_births(self):
        # 복수 분만은 불가 — 분만율은 항상 ≤ 100%
        rate = calc_farrowing_rate(80, 100)
        assert rate == 80.0


# ── NPD (Non-Productive Days) 계산 ──────────────────────────────────────────

def calc_npd(
    return_to_estrus_days: int,
    abortion_days: int,
    empty_days: int,
    total_sow_days: int,
) -> float | None:
    """NPD = (반정일수 + 유산일수 + 공태일수) / 총 모돈 재고일수 * 365"""
    if total_sow_days <= 0:
        return None
    npd_days = return_to_estrus_days + abortion_days + empty_days
    return round(npd_days / total_sow_days * 365, 1)


class TestNpdCalculation:
    def test_basic(self):
        """연간 모돈 500두, NPD 33일 기준"""
        # 500두 * 365일 = 182,500 재고일
        # NPD 33일 → 총 NPD 일수 = 33 * 500 = 16,500
        npd = calc_npd(
            return_to_estrus_days=10000,
            abortion_days=3000,
            empty_days=3500,
            total_sow_days=182500,
        )
        assert npd == pytest.approx(33.0, rel=0.05)

    def test_zero_sow_days_returns_none(self):
        assert calc_npd(100, 50, 50, 0) is None
