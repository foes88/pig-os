"""Template Renderer — Base tier response builder.

Converts StructuredResult → human-readable text using static templates.
Addon tier swaps this for an LLM call; the Rule Engine is not touched.

번역 카탈로그는 app/engine/i18n.py 가 SSOT다 (코드 -> 7개 로케일).
이 모듈은 배치/포맷만 담당하고, 문구는 한 줄도 들고 있지 않는다.
"""
from app.engine.i18n import (
    ACTION_LABELS,
    CAUSE_LABELS,
    INTENT_LABELS,
    SUPPORTED_LOCALES,  # noqa: F401  재수출(호출측 편의)
    UNKNOWN_INTENT,
    label,
    normalize_locale,
    ui,
)
from app.engine.rule_engine import Severity, StructuredResult

_SEVERITY_UI_KEY = {
    "OK": "severity_ok",
    "INFO": "severity_info",
    "WARNING": "severity_warning",
    "CRITICAL": "severity_critical",
}


def _severity_prefix(sev: Severity, locale: str) -> str:
    # Severity 는 str Enum 이라 문자열 키로 바로 조회된다. 미지정 등급은 원문 노출.
    key = _SEVERITY_UI_KEY.get(sev)
    return ui(key, locale) if key else str(sev)


def render_text(result: StructuredResult, locale: str = "en") -> str:
    """
    Convert StructuredResult to plain-text report.
    Override with LLM renderer in Addon tier — this function signature is the contract.
    """
    loc = normalize_locale(locale)

    critical_findings = [f for f in result.findings if f.severity == Severity.CRITICAL]
    warning_findings  = [f for f in result.findings if f.severity == Severity.WARNING]
    info_findings     = [f for f in result.findings if f.severity == Severity.INFO]

    # 질문을 지표로 연결하지 못한 경우: 그 사실을 먼저 밝히고 전체 요약으로 이어간다.
    # (예전엔 조용히 dashboard 로 뭉개서 '오늘 날씨' 질문에도 KPI가 그대로 나갔다.)
    prelude: list[str] = [ui("unknown_intent", loc), ""] if result.intent == UNKNOWN_INTENT else []

    if not result.findings:
        # 특정 지표를 물었는데 그 지표에 이상이 없으면 "무엇이" 정상인지 밝힌다.
        # 전체 요약(dashboard/unknown)일 때만 포괄 문구를 쓴다.
        if result.intent in INTENT_LABELS:
            body = ui("intent_within_target", loc).format(
                kpi=label(INTENT_LABELS, result.intent, loc)
            )
        else:
            body = ui("all_normal", loc)
        return "\n".join([*prelude, body]).strip()

    lines: list[str] = list(prelude)

    for f in critical_findings + warning_findings + info_findings:
        prefix = _severity_prefix(f.severity, loc)
        if f.current_value is not None and f.target_value is not None:
            header = f"{prefix} [{f.kpi}] {f.current_value} ({ui('target', loc)}: {f.target_value})"
        elif f.current_value is not None:
            header = f"{prefix} [{f.kpi}] {f.current_value}"
        else:
            header = f"{prefix} [{f.kpi}]"
        grade = getattr(f, "grade", None)
        if grade:
            header += f" — {grade}"
        lines.append(header)

        # 손실 금액(실 룰엔진 계산값) — detail.loss 있을 때만
        detail = getattr(f, "detail", None) or {}
        loss = detail.get("loss") if isinstance(detail, dict) else None
        if loss and loss.get("amount"):
            amt = f"{loss['amount']:,} {loss.get('currency', '')}".strip()
            if loss.get("demo"):
                amt += f" ({ui('estimated', loc)})"
            lines.append(f"  {ui('loss', loc)}: {amt}")

        if f.causes:
            cause_text = ", ".join(label(CAUSE_LABELS, c, loc) for c in f.causes)
            lines.append(f"  {ui('causes', loc)}: {cause_text}")

        if f.recommended_actions:
            action_text = ", ".join(label(ACTION_LABELS, a, loc) for a in f.recommended_actions)
            lines.append(f"  {ui('actions', loc)}: {action_text}")

        lines.append("")

    return "\n".join(lines).strip()
