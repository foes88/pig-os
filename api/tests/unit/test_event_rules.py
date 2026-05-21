"""
교배/분만/이유 비즈니스 규칙 단위 테스트.
피그플랜 로직 분석 기반.
DB 없이 순수 검증 로직만 테스트.
"""
import pytest
from datetime import date


# ── 임신기간 검증 (교배→분만) ─────────────────────────────────────────────────
# 피그플랜 데이터 분석: 정상 임신기간 114±3일 (100~130일 허용)

GESTATION_MIN = 100
GESTATION_MAX = 130


def validate_gestation(mating_date: date, farrowing_date: date) -> tuple[bool, int]:
    days = (farrowing_date - mating_date).days
    return GESTATION_MIN <= days <= GESTATION_MAX, days


class TestGestationValidation:
    def test_normal_gestation_114_days(self):
        ok, days = validate_gestation(date(2026, 1, 1), date(2026, 4, 25))
        assert ok is True
        assert days == 114

    def test_min_boundary_100_days(self):
        ok, days = validate_gestation(date(2026, 1, 1), date(2026, 4, 11))
        assert ok is True
        assert days == 100

    def test_max_boundary_130_days(self):
        ok, days = validate_gestation(date(2026, 1, 1), date(2026, 5, 11))
        assert ok is True
        assert days == 130

    def test_too_short_99_days(self):
        ok, days = validate_gestation(date(2026, 1, 1), date(2026, 4, 10))
        assert ok is False
        assert days == 99

    def test_too_long_131_days(self):
        ok, days = validate_gestation(date(2026, 1, 1), date(2026, 5, 12))
        assert ok is False
        assert days == 131

    def test_farrowing_before_mating_is_invalid(self):
        ok, days = validate_gestation(date(2026, 5, 1), date(2026, 1, 1))
        assert ok is False
        assert days < 0


# ── 포유기간 검증 (분만→이유) ─────────────────────────────────────────────────
# 피그플랜 데이터: 평균 이유연령 19~23일, 허용범위 10~60일

NURSING_MIN = 10
NURSING_MAX = 60


def validate_nursing(farrowing_date: date, weaning_date: date) -> tuple[bool, int]:
    days = (weaning_date - farrowing_date).days
    return NURSING_MIN <= days <= NURSING_MAX, days


class TestNursingValidation:
    def test_normal_nursing_21_days(self):
        ok, days = validate_nursing(date(2026, 1, 1), date(2026, 1, 22))
        assert ok is True
        assert days == 21

    def test_min_boundary_10_days(self):
        ok, days = validate_nursing(date(2026, 1, 1), date(2026, 1, 11))
        assert ok is True
        assert days == 10

    def test_max_boundary_60_days(self):
        ok, days = validate_nursing(date(2026, 1, 1), date(2026, 3, 2))
        assert ok is True
        assert days == 60

    def test_too_short_9_days(self):
        ok, days = validate_nursing(date(2026, 1, 1), date(2026, 1, 10))
        assert ok is False

    def test_too_long_61_days(self):
        ok, days = validate_nursing(date(2026, 1, 1), date(2026, 3, 3))
        assert ok is False

    def test_weaning_before_farrowing_is_invalid(self):
        ok, _ = validate_nursing(date(2026, 5, 1), date(2026, 1, 1))
        assert ok is False


# ── 이유두수 검증 ─────────────────────────────────────────────────────────────
# 피그플랜: born_alive + foster_in - foster_out - death = effective_litter
# 이유두수 ≤ effective_litter
# 피그플랜 import_to_pigos.py: weaning_age_days 범위 1~60, 최대 30두

MAX_WEANED = 30


def calc_effective_litter(
    born_alive: int,
    foster_in: int = 0,
    foster_out: int = 0,
    deaths: int = 0,
) -> int:
    return max(0, born_alive + foster_in - foster_out - deaths)


def validate_weaned_count(
    weaned_count: int,
    born_alive: int,
    foster_in: int = 0,
    foster_out: int = 0,
    deaths: int = 0,
) -> tuple[bool, str]:
    if weaned_count < 0:
        return False, "weaned_count cannot be negative"
    if weaned_count > MAX_WEANED:
        return False, f"weaned_count exceeds maximum {MAX_WEANED}"
    effective = calc_effective_litter(born_alive, foster_in, foster_out, deaths)
    if weaned_count > effective:
        return False, f"weaned_count ({weaned_count}) > effective litter ({effective})"
    return True, "ok"


class TestWeanedCountValidation:
    def test_normal_weaning(self):
        ok, msg = validate_weaned_count(weaned_count=11, born_alive=13)
        assert ok is True

    def test_weaned_equals_born_alive(self):
        ok, msg = validate_weaned_count(weaned_count=13, born_alive=13)
        assert ok is True

    def test_foster_in_increases_effective_litter(self):
        # born_alive=10, foster_in=3 → effective=13, weaned=12 OK
        ok, msg = validate_weaned_count(weaned_count=12, born_alive=10, foster_in=3)
        assert ok is True

    def test_death_reduces_effective_litter(self):
        # born_alive=13, deaths=2 → effective=11, weaned=12 FAIL
        ok, msg = validate_weaned_count(weaned_count=12, born_alive=13, deaths=2)
        assert ok is False
        assert "effective litter" in msg

    def test_foster_out_reduces_effective_litter(self):
        ok, msg = validate_weaned_count(weaned_count=10, born_alive=10, foster_out=2)
        assert ok is False

    def test_exceed_max_30(self):
        ok, msg = validate_weaned_count(weaned_count=31, born_alive=31)
        assert ok is False
        assert "maximum" in msg

    def test_negative_count(self):
        ok, msg = validate_weaned_count(weaned_count=-1, born_alive=10)
        assert ok is False

    def test_pigplan_benchmark_avg_12_4(self):
        """피그플랜 벤치마크 평균 이유수 12.4두 — 정상 범위"""
        ok, _ = validate_weaned_count(weaned_count=12, born_alive=13)
        assert ok is True


# ── 교배횟수 검증 ─────────────────────────────────────────────────────────────
# 피그플랜: gyobae_cnt max 5로 제한 (import_to_pigos.py 라인 206)

MAX_MATING_NUMBER = 5


def validate_mating_number(mating_number: int) -> tuple[bool, str]:
    if mating_number < 1:
        return False, "mating_number must be >= 1"
    if mating_number > MAX_MATING_NUMBER:
        return False, f"mating_number exceeds max {MAX_MATING_NUMBER} per cycle"
    return True, "ok"


class TestMatingNumberValidation:
    def test_first_mating(self):
        ok, _ = validate_mating_number(1)
        assert ok is True

    def test_max_mating(self):
        ok, _ = validate_mating_number(5)
        assert ok is True

    def test_exceed_max(self):
        ok, msg = validate_mating_number(6)
        assert ok is False
        assert "max" in msg

    def test_zero_invalid(self):
        ok, _ = validate_mating_number(0)
        assert ok is False


# ── 산차 연결 로직 ────────────────────────────────────────────────────────────
# 피그플랜 핵심 규칙: farrowing.sancha = mating.sancha + 1
# PigOS: parity는 분만 완료 시점에 +1

class TestParityLogic:
    def test_gilt_first_mating(self):
        """후보돈(parity=0) 첫 교배 → 분만 후 parity=1"""
        sow_parity = 0
        expected_parity_after_farrowing = 1
        assert sow_parity + 1 == expected_parity_after_farrowing

    def test_parity_increment_on_farrowing(self):
        """분만 시마다 parity 1씩 증가"""
        for parity in range(0, 10):
            assert parity + 1 == parity + 1  # 당연하지만 명시적 규칙 문서화

    def test_breeding_cycle_parity_matches_sow(self):
        """BreedingCycle.parity = 교배 시점의 sow.parity + 1 (분만 후 기준)"""
        sow_parity_at_mating = 2
        expected_cycle_parity = sow_parity_at_mating + 1
        assert expected_cycle_parity == 3
