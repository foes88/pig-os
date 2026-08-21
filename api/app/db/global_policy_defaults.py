"""GLOBAL 정책 기본값 — "미결정 국가의 최소 안전값" (D-10-1).

GLOBAL 은 원래 "현재 라이브 동작 codify"(c7d9e1f3a5b8)로 14개를 전부 visible 로 뒀다.
그때는 프론트가 4개만 그릴 수 있어서 화면상 문제가 없었지만, 그건 **정책이 아니라
프론트 구현 한계**였다. metrics 맵 노출(1d07768)로 그 한계가 사라지는 순간
결정한 적 없는 지표가 11개국에 자동으로 노출된다.

그래서 GLOBAL 의 의미를 재정의한다:
    이전  "일단 전부 보여준다"
    이후  "결정 안 한 나라에는 최소한만 보여준다" (default-deny)

★ GLOBAL visible 3개는 "카드를 표시할 수 있다"는 뜻까지만이다.
  "이 3개는 모든 나라에서 현지 기준까지 검증됐다"는 뜻이 아니다. 축은 계속 분리된다:

    Presentation policy      카드 표시 여부              ← 이 파일
    Definition/Evidence      정의 호환성·근거 승인
    Benchmark policy         국가 benchmark 사용 가능 여부·severity 산출 가능 여부
    Entitlement              FCR 등 유료/제한 기능 노출 여부

  즉 미국에서 PSY 카드를 표시하더라도, 미국 benchmark 가 승인되지 않았다면
  미국 기준인 것처럼 severity·비교문구를 만들어서는 안 된다.

확대는 국가별 명시 승인 + 검증된 현지명이 있을 때만 COUNTRY 정책으로 켠다.
"""
from __future__ import annotations

# 미결정 국가에 노출할 최소 지표. 늘리려면 D-10 급 결정이 필요하다.
GLOBAL_VISIBLE: tuple[str, ...] = ("PSY", "NPD", "FARROWING_RATE")

# c7d9e1f3a5b8 GLOBAL seed 14개 중 위 3개를 뺀 나머지 — 명시적으로 숨긴다.
# compute_enabled 는 건드리지 않는다(계산·룰 판정은 계속, 표시만 숨김).
GLOBAL_HIDDEN: tuple[str, ...] = (
    "ADG",
    "BORN_ALIVE",
    "FCR",
    "MSY",
    "PWMR",
    "RTS_RATE",
    "SOW_MORTALITY",
    "SOW_TURNOVER",
    "STILLBORN_RATE",
    "WEANED_COUNT",
    "WSI",
)

DECISION = "D-10-1 (A) — GLOBAL 은 미결정 국가의 최소 안전값"
