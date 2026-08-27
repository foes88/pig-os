"""트렌드 npd 노출 억제 — 재노출 금지 가드 (HOTFIX 2026-08-27).

## 배경
`get_trend()`의 `npd_by_month` CTE는 `AVG(wei_days)`(WEI = 이유→교배 간격)를 계산해
응답 필드 `npd`로 노출해 왔다. 즉 **실고객 계정에서 WEI 값이 NPD로 표시**됐다(실측 확인).

핫픽스는 값 계산·SQL·API shape을 건드리지 않고 **응답 npd만 null**로 억제한다.
(NPD 공식 수정이 아니다 — 원인 규명은 D-13 재실사. 이 둘을 섞지 말 것.)

## 이 테스트가 잠그는 것
`get_trend`가 `KpiTrend(npd=...)`에 **row 값을 다시 매핑하지 않고 None을 반환**한다는 사실.
값 비교(DB)로는 "데이터가 없어서 None"과 "억제해서 None"을 구분 못 하므로,
구조(소스)로 재노출을 잠근다 — test_npd_calc_path_isolation.py 와 같은 철학.
"""
import inspect
import re

from app.services import kpi_service


def _return_block(src: str) -> str:
    """get_trend의 KpiTrend(...) 생성 블록만 추출 (SQL 문자열 제외)."""
    idx = src.rfind("KpiTrend(")
    assert idx != -1, "get_trend에 KpiTrend(...) 생성이 없음"
    return src[idx:]


def test_trend_npd_hardcoded_none():
    """응답 npd는 하드코딩 None — row.npd를 다시 매핑하면 실패."""
    block = _return_block(inspect.getsource(kpi_service.get_trend))
    assert re.search(r"\bnpd\s*=\s*None\b", block), \
        "get_trend는 KpiTrend(npd=None)으로 노출을 억제해야 한다(HOTFIX 2026-08-27)."


def test_trend_npd_not_derived_from_row():
    """옛 노출(npd=float(row.npd)...)이 되살아나면 실패 — 재노출 금지."""
    block = _return_block(inspect.getsource(kpi_service.get_trend))
    assert "npd=float(row.npd)" not in block.replace(" ", ""), \
        "트렌드 npd를 row에서 다시 노출하면 안 된다 — WEI 오노출 재발(원인 수정은 D-13 후)."
