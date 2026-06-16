"""EventInsight 스키마 — 이벤트 입력 즉시 분석 결과 (구조화; 문구는 프론트 i18n)."""
from pydantic import BaseModel


class EventInsight(BaseModel):
    """백엔드 판정 결과. 프론트는 이걸 '렌더링만' 한다(판정 로직 금지)."""
    metric_code: str          # STILLBORN_RATE, BORN_ALIVE, PRE_WEANING_MORTALITY, ...
    severity: str             # INFO | WARNING | CRITICAL  (← 판정은 백엔드가 함)
    judgment_type: str = "absolute"  # absolute | relative (v1=absolute, relative는 slot)
    value: float | None       # 측정값 (예: 사산율 18.0)
    threshold: float | None   # 위반한 임계값 (warning 또는 critical)
    unit: str = ""            # %, 두/복, 일 ...
    direction: str = "below"  # above | below
    # 배지용 메타 (default_metric_values 출처)
    confidence: str | None = None       # high | medium | low
    is_proxy: bool = False              # 타국/표본 프록시 값
    source: str | None = None           # 출처(기관/연도)
    is_global_fallback: bool = False    # 국가값 없어 글로벌(system) 기준 사용
    # 추후 slot (지금은 항상 None → 프론트는 있을 때만 조건부 표시)
    loss: dict | None = None            # 경제손실 슬롯 (LOSS_CALC)
    relative: dict | None = None        # 상대판정 슬롯 (top25 대비)
