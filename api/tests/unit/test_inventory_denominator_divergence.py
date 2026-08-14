"""D-2 진단 — 재고(모돈 분모) 정의 불일치 고정 (수정 아님, 현상 기록).

main @ b71bb20 판독:
  ① _avg_active_inventory (kpi_service.py L344~) — CULLING_RATE·SOW_MORTALITY·
     REPLACEMENT_RATE·MSY 의 분모.  parity 조건 없음 + deleted_at 기반 퇴출 판정.
  ② PSY 분모 / 여집합 NPD 재고 (L78-86, L134-135, L142-143) — parity>=1 + exit_date 기반.
     주석은 "PSY 분모와 완전 동일"이라고 하나 ①과 실제로 다르다.

본 테스트는 SQL 문자열 수준에서 그 차이를 고정한다. 수정(통일)은 impact 산출 후 별도 결정.
통일이 이뤄지면 이 테스트가 실패하므로, 그때 함께 갱신한다(의도된 실패 = 변경 감지).
"""
import re
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2] / "app" / "services" / "kpi_service.py"
_TEXT = _SRC.read_text(encoding="utf-8")


def _avg_active_inventory_sql() -> str:
    """_avg_active_inventory 본문에서 SQL 문자열 블록만 추출."""
    start = _TEXT.index("async def _avg_active_inventory")
    end = _TEXT.index("async def ", start + 10)
    return _TEXT[start:end]


def test_current_inventory_denominator_has_no_parity_filter():
    """① 현재 분모는 parity 조건이 없다 → 후보돈(parity=0) 포함."""
    body = _avg_active_inventory_sql()
    assert "parity" not in body, (
        "분모 정의가 바뀌었다(parity 조건 등장). D-2 통일 작업이면 본 진단 테스트를 갱신할 것."
    )


def test_current_inventory_denominator_uses_deleted_at_for_exit():
    """① 현재 분모는 deleted_at 기반 OR 조건으로 퇴출을 판정한다."""
    body = _avg_active_inventory_sql()
    assert "deleted_at IS NULL OR" in body


def test_psy_denominator_uses_parity_and_exit_date():
    """② PSY/NPD 재고는 parity>=1 + exit_date 기반(PigPlan 035001 정합)."""
    assert "s.parity >= 1" in _TEXT
    assert "s.exit_date IS NULL OR s.exit_date >= mo.m" in _TEXT


def test_two_definitions_diverge():
    """① 과 ② 가 서로 다르다는 사실 자체를 고정(주석의 '완전 동일'과 배치)."""
    body = _avg_active_inventory_sql()
    has_parity_in_avg = "parity" in body
    has_parity_in_psy = "s.parity >= 1" in _TEXT
    assert has_parity_in_psy and not has_parity_in_avg, (
        "두 재고 정의가 통일되었다면 D-2가 해소된 것 — 본 진단 테스트를 제거/갱신할 것."
    )


def test_affected_kpis_documented():
    """분모 변경 시 영향받는 KPI 4종이 실제로 inv_denom을 쓰는지 고정."""
    # `"CULLING_RATE": _rate(float(...), inv_denom),` 처럼 인자 안에 콤마가 있어
    # [^,]* 로는 못 잡는다 → 같은 줄에 metric_code 와 inv_denom 이 함께 오는지로 판정.
    affected = [
        m.group(1)
        for line in _TEXT.splitlines()
        if "inv_denom" in line and (m := re.search(r'"([A-Z_]+)":', line))
    ]
    for kpi in ("CULLING_RATE", "SOW_MORTALITY", "REPLACEMENT_RATE"):
        assert kpi in affected, f"{kpi} 가 inv_denom 분모를 더 이상 쓰지 않는다 — 영향도 재판독 필요"
    assert "inv_denom" in _TEXT and "MSY" in _TEXT
