"""BR Pilot v1 시드 — 정본: docs/product/COUNTRY_PRODUCT_SPEC_BR.md v0.3.

이 모듈이 마이그레이션과 게이트 테스트의 공용 SSOT 다.
값을 바꿀 때는 문서를 먼저 고친다 — 게이트가 둘의 불일치를 잡는다.

OPTION A: BR 이 표시할 KPI 는 explicit visible, 표시하지 않을 KPI 는 explicit HIDDEN.
GLOBAL 정책을 암묵 상속해 화면 KPI 가 늘어나게 하지 않는다.

★ 현지 명칭은 확정된 것만 넣는다. SOW_TURNOVER 는 UNVERIFIED 라 라벨을 넣지 않고
  애초에 HIDDEN 이므로 presentation 행 자체가 없다.
"""
from __future__ import annotations

COUNTRY = "BR"

# 결정 출처. 사람 이름이 아니라 결정 근거 문서를 기록한다(c7d9e1f3a5b8 의 v0.4-P1-baseline 과 동일 관례).
DECIDED_BY = "BR-PILOT-v1"
NOTE = "COUNTRY_PRODUCT_SPEC_BR.md v0.3"

# (kpi_code, display_order, local_label) — 순서·현지명 모두 v0.2 확정값.
BR_PILOT_VISIBLE: tuple[tuple[str, int, str], ...] = (
    ("PSY", 10, "Desmamados por fêmea/ano"),
    ("FARROWING_RATE", 20, "Taxa de Parto"),
    ("NPD", 30, "Dias Não Produtivos"),
)

HEADLINE_KPI = "PSY"  # priority_class='NORTH_STAR'

# GLOBAL seed(c7d9e1f3a5b8) 14개 중 visible 3개를 뺀 나머지 — BR 에서 명시적으로 숨긴다.
# full target(BORN_ALIVE·PWMR·STILLBORN_RATE·FCR)도 Pilot v1 에서는 여기 들어간다.
# 사유는 문서 §2.1 참조: 대시보드 페이로드 부재 / 유료 애드온.
BR_PILOT_HIDDEN: tuple[str, ...] = (
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

VISIBLE_CODES: frozenset[str] = frozenset(k for k, _, _ in BR_PILOT_VISIBLE)


def policy_rows() -> list[dict]:
    """country_kpi_policy 에 넣을 BR COUNTRY 행."""
    rows: list[dict] = []
    for code, _order, _label in BR_PILOT_VISIBLE:
        rows.append(dict(
            scope_level="COUNTRY", country_code=COUNTRY, kpi_code=code,
            compute_enabled=True, display_role="PRIMARY",
            priority_class="NORTH_STAR" if code == HEADLINE_KPI else None,
            decision_status="APPROVED", decided_by=DECIDED_BY, note=NOTE,
        ))
    for code in BR_PILOT_HIDDEN:
        rows.append(dict(
            scope_level="COUNTRY", country_code=COUNTRY, kpi_code=code,
            compute_enabled=None,          # 계산 여부는 GLOBAL 상속 — 숨기는 것과 무관
            display_role="HIDDEN", priority_class=None,
            decision_status="APPROVED", decided_by=DECIDED_BY, note=NOTE,
        ))
    return rows


def presentation_rows() -> list[dict]:
    """country_kpi_presentation 에 넣을 BR COUNTRY 행. visible KPI 만 대상."""
    return [
        dict(
            scope_level="COUNTRY", country_code=COUNTRY, kpi_code=code,
            display_order=order, display_order_override=True, local_label=label,
            decision_status="APPROVED", note=NOTE,
        )
        for code, order, label in BR_PILOT_VISIBLE
    ]
