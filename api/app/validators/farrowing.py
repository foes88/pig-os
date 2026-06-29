"""
Farrowing event validation (PigPlan-derived limits).

Reference: docs/SCREEN_MENU_SPEC.md → Events / Farrowing tab.
    Total Born (TB)     max 35
    Stillborn (SB)      max 25
    Mummified (MUM)     max 25
    Born Alive (BA)     <= TB ; = Male + Female (when sexed counts entered)
    Avg. Birth Weight   max 3.0 kg
"""
from __future__ import annotations

from app.validators.base import ValidationError

MAX_TOTAL_BORN = 35
MIN_TOTAL_BORN = 1
MAX_STILLBORN = 25
MAX_MUMMIFIED = 25
MAX_AVG_BIRTH_WEIGHT_KG = 3.0


def validate_farrowing(
    *,
    total_born: int,
    born_alive: int,
    stillborn: int = 0,
    mummified: int = 0,
    avg_birth_weight_kg: float | None = None,
    male: int | None = None,
    female: int | None = None,
) -> None:
    """Raise :class:`ValidationError` (HTTP 422) on an invalid farrowing record."""
    if total_born > MAX_TOTAL_BORN:
        raise ValidationError(f"Total Born cannot exceed {MAX_TOTAL_BORN}")
    # 최소 1 — 0마리 분만(빈 litter)은 무의미하며 parity·LACTATING 오염. 앱(EventValidation.kt)은 1..35 강제.
    if total_born < MIN_TOTAL_BORN:
        raise ValidationError(f"Total Born must be at least {MIN_TOTAL_BORN}")
    if stillborn > MAX_STILLBORN:
        raise ValidationError(f"Stillborn cannot exceed {MAX_STILLBORN}")
    if mummified > MAX_MUMMIFIED:
        raise ValidationError(f"Mummified cannot exceed {MAX_MUMMIFIED}")
    if born_alive > total_born:
        raise ValidationError(
            f"Born Alive ({born_alive}) cannot exceed Total Born ({total_born})"
        )
    # B1: 두수 항등식 — total_born = born_alive + stillborn + mummified.
    # /sync·직접REST 공통 강제(이전엔 /sync에 누락 → litter 두수 오염 가능). 앱은 항상 합으로 전송.
    if total_born != born_alive + stillborn + mummified:
        raise ValidationError(
            f"Total Born ({total_born}) must equal Born Alive + Stillborn + Mummified "
            f"({born_alive} + {stillborn} + {mummified} = {born_alive + stillborn + mummified})"
        )
    if male is not None and female is not None and born_alive != male + female:
        raise ValidationError(
            f"Born Alive ({born_alive}) must equal Male + Female ({male} + {female})"
        )
    if (
        avg_birth_weight_kg is not None
        and avg_birth_weight_kg > MAX_AVG_BIRTH_WEIGHT_KG
    ):
        raise ValidationError(
            f"Average birth weight cannot exceed {MAX_AVG_BIRTH_WEIGHT_KG} kg"
        )
