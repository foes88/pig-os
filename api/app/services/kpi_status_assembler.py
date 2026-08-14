"""KPI Status Contract Assembler — ADR-KPI-08 Phase 1.

Rule Engine이 이미 국가별 정책(effective_metric_values의 warning/critical/direction)으로
판정한 결과를 canonical status로 **변환·정규화**만 한다.

허용: metric_code ↔ rule finding 연결 · Severity → canonical status 변환 ·
      missing/unavailable/no_policy/disabled → insufficient(+reason) 정규화
금지: threshold 비교 · country 조건 분기 · KPI별 자체 판정 · benchmark 기반 재판정
      (여기서 threshold를 읽어야 한다면 설계 위반 — 판정은 Rule Engine에서 이미 끝나 있어야 한다)

status 결정 규칙 (ADR §4.1.1 — `normal`은 적극적으로 증명된 상태):
  rule 있음 + 평가 완료 + 데이터 충분 + 위반 없음   → normal
  rule 있음 + 평가 완료 + 위반                      → warning / critical
  rule 있음 + 평가 불가/스킵/비활성/컨텍스트 결손   → insufficient(사유별 reason)
  rule 없음                                          → insufficient(no_policy)
  값 없음                                            → insufficient(no_data)
"""
from __future__ import annotations

from app.engine.rule_engine import Finding, Severity
from app.schemas.kpi import KpiStatus

# Severity → canonical status (INFO는 카드 상태가 아니라 알림 도메인 값 → normal 취급하지 않음)
_SEVERITY_TO_STATUS = {
    Severity.OK: "normal",
    Severity.WARNING: "warning",
    Severity.CRITICAL: "critical",
}

# 판정 정책(rule)이 존재하는 metric_code. RuleRegistry는 rule_id만 알고 발화 결과의 kpi는
# 런타임에만 드러나므로, 정책 존재 여부는 여기서 명시적으로 선언한다(추론 금지).
DASHBOARD_POLICY_KPIS = frozenset({"PSY", "NPD", "FARROWING_RATE"})


def assemble_kpi_status(
    *,
    values: dict[str, float | None],
    findings: list[Finding],
    policy_kpis: set[str],
    pending: dict[str, str] | None = None,
) -> dict[str, KpiStatus]:
    """대시보드 KPI별 canonical status 조립.

    values      : metric_code → 값(None이면 no_data)
    findings    : RuleEngine.evaluate 결과 findings (이미 국가별 판정 완료)
    policy_kpis : 판정 정책(rule)이 존재하는 metric_code 집합. 없으면 no_policy.
    pending     : metric_code → reason. 정책이 잠정 비활성인 경우(예: NPD=policy_pending).
    """
    pending = pending or {}
    by_kpi: dict[str, Finding] = {}
    for f in findings:
        prev = by_kpi.get(f.kpi)
        # 같은 KPI에 여러 finding이면 더 심각한 쪽을 대표로(판정이 아니라 선택).
        if prev is None or _rank(f.severity) > _rank(prev.severity):
            by_kpi[f.kpi] = f

    out: dict[str, KpiStatus] = {}
    for code, value in values.items():
        if code in pending:
            out[code] = KpiStatus(status="insufficient", reason=pending[code])
            continue
        if code not in policy_kpis:
            out[code] = KpiStatus(status="insufficient", reason="no_policy")
            continue
        if value is None:
            out[code] = KpiStatus(status="insufficient", reason="no_data")
            continue
        finding = by_kpi.get(code)
        if finding is None:
            # 정책 있음 + 값 있음 + 발화 없음 = 평가 완료 후 위반 없음 → normal(적극 증명)
            out[code] = KpiStatus(status="normal", reason=None)
            continue
        mapped = _SEVERITY_TO_STATUS.get(finding.severity)
        if mapped is None:
            # INFO 등 카드 상태로 매핑되지 않는 severity → 판정 불가로 정규화(normal 누수 차단)
            out[code] = KpiStatus(status="insufficient", reason="evaluation_skipped")
            continue
        out[code] = KpiStatus(status=mapped, reason=None)
    return out


def _rank(sev: Severity) -> int:
    return {Severity.OK: 0, Severity.INFO: 1, Severity.WARNING: 2, Severity.CRITICAL: 3}.get(sev, 0)
