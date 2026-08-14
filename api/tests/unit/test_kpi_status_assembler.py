"""KPI Status Contract Assembler (ADR-KPI-08 Phase 1) 유닛테스트.

ADR §12 게이트 대응:
  G8  normal 적극증명 — 미실행/스킵/INFO가 normal로 새지 않음
  G9  no_policy — rule 없는 KPI는 insufficient(no_policy)
  G10 policy_pending — 잠정 비활성 정책은 insufficient(policy_pending)
  G11 Assembler 순수성 — threshold 비교·country 분기·benchmark 재판정 부재(정적 검사)
"""
from pathlib import Path

from app.engine.rule_engine import Finding, Severity
from app.services.kpi_status_assembler import DASHBOARD_POLICY_KPIS, assemble_kpi_status

POLICY = DASHBOARD_POLICY_KPIS


def _f(kpi: str, sev: Severity) -> Finding:
    return Finding(rule_id=f"{kpi.lower()}.x", kpi=kpi, severity=sev,
                   current_value=1.0, target_value=2.0, causes=[], recommended_actions=[])


class TestSeverityMapping:
    def test_violation_maps_to_warning_critical(self):
        out = assemble_kpi_status(
            values={"PSY": 20.0, "FARROWING_RATE": 70.0},
            findings=[_f("PSY", Severity.WARNING), _f("FARROWING_RATE", Severity.CRITICAL)],
            policy_kpis=POLICY,
        )
        assert out["PSY"].status == "warning" and out["PSY"].reason is None
        assert out["FARROWING_RATE"].status == "critical"

    def test_worst_severity_wins_when_multiple_findings(self):
        out = assemble_kpi_status(
            values={"PSY": 20.0},
            findings=[_f("PSY", Severity.WARNING), _f("PSY", Severity.CRITICAL)],
            policy_kpis=POLICY,
        )
        assert out["PSY"].status == "critical"


class TestNormalIsPositivelyProven:
    """G8 — normal 은 '정책 있음 + 값 있음 + 평가 후 위반 없음'일 때만."""

    def test_no_finding_with_value_and_policy_is_normal(self):
        out = assemble_kpi_status(values={"PSY": 30.0}, findings=[], policy_kpis=POLICY)
        assert out["PSY"].status == "normal" and out["PSY"].reason is None

    def test_missing_value_is_insufficient_not_normal(self):
        out = assemble_kpi_status(values={"PSY": None}, findings=[], policy_kpis=POLICY)
        assert out["PSY"].status == "insufficient" and out["PSY"].reason == "no_data"

    def test_info_severity_does_not_leak_to_normal(self):
        # INFO 는 카드 상태 어휘가 아님 → normal 로 새지 않고 evaluation_skipped
        out = assemble_kpi_status(values={"PSY": 30.0}, findings=[_f("PSY", Severity.INFO)],
                                  policy_kpis=POLICY)
        assert out["PSY"].status == "insufficient"
        assert out["PSY"].reason == "evaluation_skipped"

    def test_ok_severity_is_normal(self):
        out = assemble_kpi_status(values={"PSY": 30.0}, findings=[_f("PSY", Severity.OK)],
                                  policy_kpis=POLICY)
        assert out["PSY"].status == "normal"


class TestNoPolicy:
    """G9 — 정책 없는 KPI(SOW_TURNOVER)는 프론트가 대신 판정하지 않도록 insufficient."""

    def test_sow_turnover_has_no_policy(self):
        out = assemble_kpi_status(values={"SOW_TURNOVER": 2.4}, findings=[], policy_kpis=POLICY)
        assert out["SOW_TURNOVER"].status == "insufficient"
        assert out["SOW_TURNOVER"].reason == "no_policy"

    def test_no_policy_wins_over_value_presence(self):
        out = assemble_kpi_status(values={"SOW_TURNOVER": None}, findings=[], policy_kpis=POLICY)
        assert out["SOW_TURNOVER"].reason == "no_policy"


class TestPolicyPending:
    """G10 — 잠정 비활성 정책(예: 정의 확정 전)은 policy_pending."""

    def test_pending_overrides_everything(self):
        out = assemble_kpi_status(
            values={"NPD": 40.0},
            findings=[_f("NPD", Severity.CRITICAL)],   # 발화가 있어도
            policy_kpis=POLICY,
            pending={"NPD": "policy_pending"},          # pending 이 우선
        )
        assert out["NPD"].status == "insufficient" and out["NPD"].reason == "policy_pending"


class TestReasonAlwaysPresent:
    """D1-1 — reason 키는 항상 존재(값 없으면 None). 프론트가 유무로 분기하지 못하게."""

    def test_reason_field_exists_on_every_status(self):
        out = assemble_kpi_status(
            values={"PSY": 30.0, "SOW_TURNOVER": 2.0, "NPD": None},
            findings=[], policy_kpis=POLICY,
        )
        for st in out.values():
            assert hasattr(st, "reason")
        assert out["PSY"].reason is None            # 정상도 키는 존재
        assert out["SOW_TURNOVER"].reason == "no_policy"


class TestAssemblerPurity:
    """G11 — Assembler 에 판정 로직이 없어야 한다(정적 검사)."""

    def test_no_threshold_or_country_logic(self):
        """AST로 실제 코드만 검사 — 주석·docstring의 '금지' 설명 문구는 제외."""
        import ast

        path = (Path(__file__).resolve().parents[2] / "app" / "services"
                / "kpi_status_assembler.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # docstring 제거
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                body = node.body
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                        and isinstance(body[0].value.value, str):
                    node.body = body[1:]
        code = ast.dump(tree)  # 식별자·문자열 리터럴만 남음(주석은 AST에 없음)
        for banned in ("warning_threshold", "critical_threshold", "alert_direction",
                       "effective_metric_values", "benchmark"):
            assert banned not in code, f"Assembler에 판정 로직 유입: {banned}"
