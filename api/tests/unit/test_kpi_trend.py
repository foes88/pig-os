"""
KPI trend 계산 로직 단위 테스트.
DB 없이 순수 공식으로 검증.
"""
import pytest
from app.schemas.kpi import KpiTrend


# ── trend 계산 공식 ────────────────────────────────────────────────────────────

def monthly_psy(weanings: int, active_sows: int) -> float | None:
    """월간 PSY = (이유수 / 활성모돈수) * 12 (연환산)"""
    if active_sows <= 0:
        return None
    return round((weanings / active_sows) * 12, 1)


def monthly_fr(farrowings: int, matings: int) -> float | None:
    """월간 분만율 = 분만수 / 교배수 * 100"""
    if matings <= 0:
        return None
    return round(farrowings / matings * 100, 1)


class TestMonthlyPsy:
    def test_normal_farm(self):
        """500두 농장, 월 600두 이유 → PSY ~14.4"""
        psy = monthly_psy(600, 500)
        assert psy == pytest.approx(14.4, rel=0.01)

    def test_annualized_matches_yearly(self):
        """월 1,270두 이유 / 500두 * 12 = 연 PSY 30.5"""
        psy = monthly_psy(1270, 500)
        assert psy == pytest.approx(30.5, rel=0.01)

    def test_zero_sows_returns_none(self):
        assert monthly_psy(100, 0) is None

    def test_zero_weanings(self):
        assert monthly_psy(0, 500) == 0.0

    def test_high_performance_farm(self):
        """고성능 농장: 월 1,500두 이유 / 500두 → PSY 36.0"""
        psy = monthly_psy(1500, 500)
        assert psy == 36.0


class TestMonthlyFarrowingRate:
    def test_benchmark_rate(self):
        """교배 100 → 분만 86 → 86.0%"""
        fr = monthly_fr(86, 100)
        assert fr == 86.0

    def test_zero_matings_returns_none(self):
        assert monthly_fr(10, 0) is None

    def test_perfect_rate(self):
        assert monthly_fr(50, 50) == 100.0

    def test_low_rate(self):
        fr = monthly_fr(70, 100)
        assert fr == 70.0


class TestKpiTrendSchema:
    def test_all_nulls_valid(self):
        """데이터 없는 월은 모두 null — 유효한 응답"""
        trend = KpiTrend(period="2026-01", psy=None, npd=None, farrowing_rate=None)
        assert trend.period == "2026-01"
        assert trend.psy is None

    def test_full_data(self):
        trend = KpiTrend(period="2026-05", psy=28.5, npd=32.1, farrowing_rate=87.3)
        assert trend.psy == 28.5
        assert trend.npd == 32.1
        assert trend.farrowing_rate == 87.3

    def test_period_format(self):
        """period는 YYYY-MM 형식"""
        trend = KpiTrend(period="2026-06", psy=30.0, npd=33.0, farrowing_rate=88.0)
        parts = trend.period.split("-")
        assert len(parts) == 2
        assert len(parts[0]) == 4  # 연도
        assert len(parts[1]) == 2  # 월


class TestMonthsClamp:
    """get_trend의 months 파라미터 범위 검증 (서비스 로직과 동일)"""

    def clamp(self, months: int) -> int:
        return max(1, min(months, 24))

    def test_min_clamp(self):
        assert self.clamp(0) == 1

    def test_max_clamp(self):
        assert self.clamp(25) == 24

    def test_normal_values(self):
        assert self.clamp(6) == 6
        assert self.clamp(12) == 12
        assert self.clamp(24) == 24
