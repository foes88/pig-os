"""GLOBAL 표현 정책 시드 — 현재 화면 순서를 데이터로 codify.

배경: country_kpi_policy GLOBAL seed(c7d9e1f3a5b8) 14행은 priority_class·display_order 가
전부 NULL 이다. Presentation Policy 를 켜면 정렬이 kpi_code ASC 로 떨어져
비-BR 농장의 카드 순서가 바뀐다:

    현재(폴백)     PSY · NPD · FARROWING_RATE · SOW_TURNOVER
    seed 투입 후   FARROWING_RATE · NPD · PSY · SOW_TURNOVER   ← 알파벳순

이 시드는 새 정책을 만드는 게 아니라 **지금 화면에 나오는 순서를 그대로 기록**한다.
값의 출처는 src/lib/kpi/cardRegistry.ts 의 KPI_CARD_REGISTRY 배열 순서다.

local_label 은 넣지 않는다 — GLOBAL 에는 현지 용어가 없고 공용 라벨(i18n)을 쓴다.
나머지 10개 KPI 는 display_order NULL(맨 뒤) 그대로 둔다. 대시보드 페이로드에 값이
없어 카드로 그려지지 않으므로 순서를 정할 근거가 없다.
"""
from __future__ import annotations

NOTE = "현행 화면 순서 codify (src/lib/kpi/cardRegistry.ts). 신규 정책 아님."

# (kpi_code, display_order) — 간격 10 규약. 순서는 cardRegistry.ts 배열 순서와 동일.
GLOBAL_DISPLAY_ORDER: tuple[tuple[str, int], ...] = (
    ("PSY", 10),
    ("NPD", 20),
    ("FARROWING_RATE", 30),
    ("SOW_TURNOVER", 40),
)


def presentation_rows() -> list[dict]:
    return [
        dict(
            scope_level="GLOBAL", country_code=None, kpi_code=code,
            display_order=order, display_order_override=True, local_label=None,
            decision_status="APPROVED", note=NOTE,
        )
        for code, order in GLOBAL_DISPLAY_ORDER
    ]
