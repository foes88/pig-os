"""EventInsight 스키마 — 이벤트 입력 즉시 분석 결과 (구조화; 문구는 프론트 i18n)."""
from pydantic import BaseModel


class EventInsight(BaseModel):
    metric_code: str          # STILLBORN_RATE, BORN_ALIVE, PRE_WEANING_MORTALITY, ...
    severity: str             # INFO | WARNING | CRITICAL
    value: float | None       # 측정값 (예: 사산율 18.0)
    threshold: float | None   # 위반한 임계값 (warning 또는 critical)
    unit: str = ""            # %, 두/복, 일 ...
    direction: str = "below"  # above | below
    is_global_fallback: bool = False  # 국가값 없어 글로벌(system) 기준 사용 시 true
