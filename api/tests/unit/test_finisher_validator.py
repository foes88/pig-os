"""비육돈 그룹 검증 (app/validators/finisher.py) — 순수함수, 기존 테스트 없음.

입식 두수/체중·출하 완료 잠금·이벤트 두수 ≤ 잔여·출하체중 상한/증가·잔여두수 산출.
출처: PigPlan DataValidationChk.java 파생. 422(ValidationError)로 매핑.
"""
from types import SimpleNamespace

import pytest

from app.validators.base import ValidationError
from app.validators.finisher import (
    calc_remaining_head,
    validate_finisher_entry,
    validate_finisher_event_count,
    validate_finisher_exit_weight,
    validate_finisher_not_shipped,
)


class TestEntry:
    def test_valid(self):
        validate_finisher_entry(entry_count=10, avg_entry_weight_kg=25.0)  # no raise

    def test_zero_count_raises(self):
        with pytest.raises(ValidationError):
            validate_finisher_entry(entry_count=0)

    def test_weight_bounds_inclusive(self):
        validate_finisher_entry(entry_count=1, avg_entry_weight_kg=5.0)   # 하한 포함
        validate_finisher_entry(entry_count=1, avg_entry_weight_kg=50.0)  # 상한 포함

    def test_weight_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            validate_finisher_entry(entry_count=1, avg_entry_weight_kg=4.9)
        with pytest.raises(ValidationError):
            validate_finisher_entry(entry_count=1, avg_entry_weight_kg=50.1)

    def test_weight_none_ok(self):
        validate_finisher_entry(entry_count=1, avg_entry_weight_kg=None)


class TestNotShipped:
    def test_shipped_group_blocks(self):
        with pytest.raises(ValidationError):
            validate_finisher_not_shipped(shipped_at="2026-06-01")

    def test_open_group_ok(self):
        validate_finisher_not_shipped(shipped_at=None)


class TestEventCount:
    def test_exceeds_remaining_raises(self):
        with pytest.raises(ValidationError):
            validate_finisher_event_count(action_count=11, remaining_head=10)

    def test_equal_remaining_ok(self):
        validate_finisher_event_count(action_count=10, remaining_head=10)

    def test_zero_raises(self):
        with pytest.raises(ValidationError):
            validate_finisher_event_count(action_count=0, remaining_head=10)


class TestExitWeight:
    def test_over_max_raises(self):
        with pytest.raises(ValidationError):
            validate_finisher_exit_weight(avg_exit_weight_kg=200.1)

    def test_max_boundary_ok(self):
        validate_finisher_exit_weight(avg_exit_weight_kg=200.0)

    def test_not_greater_than_entry_raises(self):
        with pytest.raises(ValidationError):
            validate_finisher_exit_weight(avg_exit_weight_kg=25.0, avg_entry_weight_kg=25.0)

    def test_greater_than_entry_ok(self):
        validate_finisher_exit_weight(avg_exit_weight_kg=110.0, avg_entry_weight_kg=25.0)


class TestRemainingHead:
    def test_in_minus_out(self):
        g = SimpleNamespace(head_count_in=100, head_count_out=30)
        assert calc_remaining_head(g) == 70

    def test_none_treated_as_zero(self):
        g = SimpleNamespace(head_count_in=None, head_count_out=None)
        assert calc_remaining_head(g) == 0
