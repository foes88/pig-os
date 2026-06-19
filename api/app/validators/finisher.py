"""
비육돈 그룹 검증.

현재 모델(FinisherGroup)은 그룹 단위 관리(head_count_in/head_count_out, start/end_date).
개별 폐사/전출 이벤트 추적은 Phase 1.5 → 잔여두수는 입식−출하로 산출.
출처: PigPlan DataValidationChk.java L943~1047, UdMoveinWr.jsp
"""
from __future__ import annotations

from app.validators.base import ValidationError

MIN_ENTRY_WEIGHT_KG = 5.0
MAX_ENTRY_WEIGHT_KG = 50.0
MAX_EXIT_WEIGHT_KG = 200.0


def validate_finisher_entry(
    *, entry_count: int, avg_entry_weight_kg: float | None = None
) -> None:
    """입식: 두수 ≥ 1, 입식체중 5~50kg."""
    if entry_count < 1:
        raise ValidationError("Entry head count must be at least 1")
    if avg_entry_weight_kg is not None and not (
        MIN_ENTRY_WEIGHT_KG <= avg_entry_weight_kg <= MAX_ENTRY_WEIGHT_KG
    ):
        raise ValidationError(
            f"Entry weight must be between {MIN_ENTRY_WEIGHT_KG} and {MAX_ENTRY_WEIGHT_KG} kg"
        )


def validate_finisher_not_shipped(*, shipped_at) -> None:
    """출하 완료(end_date 존재) 그룹에는 추가 이벤트 금지."""
    if shipped_at is not None:
        raise ValidationError("Cannot add events to an already-shipped group")


def validate_finisher_event_count(
    *, action_count: int, remaining_head: int, label: str = "count"
) -> None:
    """폐사/출하/전출 두수 ≤ 잔여두수."""
    if action_count < 1:
        raise ValidationError(f"{label} must be at least 1")
    if action_count > remaining_head:
        raise ValidationError(
            f"{label} ({action_count}) exceeds remaining head count ({remaining_head})"
        )


def validate_finisher_exit_weight(
    *, avg_exit_weight_kg: float, avg_entry_weight_kg: float | None = None
) -> None:
    """출하체중: 최대 200kg, 입식체중 초과."""
    if avg_exit_weight_kg > MAX_EXIT_WEIGHT_KG:
        raise ValidationError(f"Exit weight exceeds maximum {MAX_EXIT_WEIGHT_KG} kg")
    if avg_entry_weight_kg and avg_exit_weight_kg <= avg_entry_weight_kg:
        raise ValidationError("Exit weight must be greater than entry weight")


def calc_remaining_head(group) -> int:
    """잔여두수 = 입식두수 − 출하두수 (개별 폐사/전출은 Phase 1.5)."""
    return (group.head_count_in or 0) - (group.head_count_out or 0)
