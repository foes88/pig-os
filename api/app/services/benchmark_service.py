"""
KPI Governance v3.1 — benchmark resolver (Rule Engine ↔ 3-table 연결의 read-side).

문서: handoff/KPI_GOVERNANCE_v3.1.md §3·§4·§6·§7 / Rule Engine 연결 프롬프트.
- resolve_benchmark(): (country, kpi, [population]) → governance benchmark를 조회하고 발화 적격 판정.
- 발화 게이트(§4): benchmark_status∈{verified,normalized_verified} + comparison_status∈{exact,compatible,normalized}
  + value_scale 일치(kpi_definitions) + direction별 threshold 유효. 하나라도 불충족 → can_fire=False + insufficient_reason.
- global_fallback(§4.2): 명시 threshold 있으면 발화 가능, is_global_fallback=True trace.
- default_metric_values는 여기서 metric-level fallback으로 쓰지 않는다(§5). 이 resolver는 3-table만 본다.

⚠️ 현재 verified benchmark는 transformed_value(국가 평균)만 있고 threshold가 비어 있어 대부분 threshold_missing.
   엔진 default 전환(USE_GOVERNANCE_BENCHMARKS)은 임계정책 결정 후. 이 서비스는 그 전까지 read-only로 사용.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.benchmark_seed import kpi_definition_index
from app.db.models.benchmark import Benchmark, KpiDefinition
from app.engine.benchmark_thresholds import severity_for

_FIREABLE_COMPARISON = {"exact", "compatible", "normalized"}
_VERIFIED = {"verified", "normalized_verified"}
# 조회 우선순위 (높을수록 우선) — 같은 (country,kpi)에 여러 행이면 최상위 채택
_STATUS_RANK = {"verified": 5, "normalized_verified": 4, "global_fallback": 3, "provisional": 2, "missing": 1}


@dataclass
class ResolvedBenchmark:
    # 식별/trace (§7)
    benchmark_id: int | None
    country_code: str
    kpi_code: str
    definition_id: str | None
    population_scope: str | None
    benchmark_status: str
    comparison_status: str | None
    source_obs_id: int | None
    obs_group_id: str | None
    direction: str | None
    value_scale: str | None
    # 값/임계
    transformed_value: float | None
    warning_min: float | None
    warning_max: float | None
    critical_min: float | None
    critical_max: float | None
    target: float | None
    # 판정
    can_fire: bool
    is_global_fallback: bool
    insufficient_reason: str | None
    threshold_used: str | None = None   # 발화 시 사용한 칸 설명

    def trace(self) -> dict:
        return asdict(self)


def _thresholds_valid(direction: str | None, b: Benchmark) -> bool:
    """direction별 발화에 필요한 칸이 있는지 (§3.1)."""
    if direction == "higher_better":
        return b.warning_min is not None or b.critical_min is not None
    if direction == "lower_better":
        return b.warning_max is not None or b.critical_max is not None
    if direction == "range_target":
        # 4-bound 모두 필요
        return None not in (b.warning_min, b.warning_max, b.critical_min, b.critical_max)
    return False


def _evaluate_gate(b: Benchmark, kdef: dict | None) -> tuple[bool, bool, str | None]:
    """(can_fire, is_global_fallback, insufficient_reason)."""
    direction = kdef["direction"] if kdef else None
    kdef_scale = kdef["value_scale"] if kdef else None
    is_gf = b.benchmark_status == "global_fallback"

    # value_scale 일치 (§6) — None(미설정)도 비교 불가로 본다
    if b.value_scale is None or kdef_scale is None or b.value_scale != kdef_scale:
        return False, is_gf, "value_scale_mismatch"

    # comparison_status 게이트 (§4)
    if b.comparison_status not in _FIREABLE_COMPARISON:
        return False, is_gf, f"comparison_status={b.comparison_status}"

    # benchmark_status 게이트 (§4) — verified류 또는 global_fallback만
    if b.benchmark_status in _VERIFIED:
        pass
    elif b.benchmark_status == "global_fallback":
        pass  # §4.2 — threshold 검사로 이어짐
    else:
        return False, is_gf, f"benchmark_status={b.benchmark_status}"

    # direction별 threshold 유효성 (§3.1)
    if not _thresholds_valid(direction, b):
        return False, is_gf, "threshold_missing"

    return True, is_gf, None


def _to_resolved(b: Benchmark, kdef: dict | None) -> ResolvedBenchmark:
    can_fire, is_gf, reason = _evaluate_gate(b, kdef)
    return ResolvedBenchmark(
        benchmark_id=b.bench_id, country_code=b.country_code, kpi_code=b.kpi_code,
        definition_id=b.definition_id, population_scope=b.population_scope,
        benchmark_status=b.benchmark_status, comparison_status=b.comparison_status,
        source_obs_id=b.source_obs_id, obs_group_id=b.obs_group_id,
        direction=(kdef["direction"] if kdef else None),
        value_scale=b.value_scale,
        transformed_value=float(b.transformed_value) if b.transformed_value is not None else None,
        warning_min=float(b.warning_min) if b.warning_min is not None else None,
        warning_max=float(b.warning_max) if b.warning_max is not None else None,
        critical_min=float(b.critical_min) if b.critical_min is not None else None,
        critical_max=float(b.critical_max) if b.critical_max is not None else None,
        target=float(b.target) if b.target is not None else None,
        can_fire=can_fire, is_global_fallback=is_gf, insufficient_reason=reason,
    )


async def resolve_benchmark(
    db: AsyncSession, country_code: str, kpi_code: str, *, population_scope: str | None = None,
) -> ResolvedBenchmark | None:
    """
    (country, kpi[, population])에 대한 최적 governance benchmark를 조회·판정.
    여러 행이면 status 우선순위로 1개 채택. 행이 없으면 None(= 미시드, 발화 안 함).
    default_metric_values는 보지 않는다(§5).
    """
    rows = await _fetch_rows(db, country_code, kpi_code, population_scope)
    if not rows:
        return None
    rows = sorted(rows, key=lambda b: _STATUS_RANK.get(b.benchmark_status, 0), reverse=True)
    kdefs = kpi_definition_index()
    best = rows[0]
    return _to_resolved(best, kdefs.get(best.kpi_code))


async def _fetch_rows(db: AsyncSession, country_code: str, kpi_code: str, population_scope: str | None):
    stmt = select(Benchmark).where(
        Benchmark.country_code == country_code,
        Benchmark.kpi_code == kpi_code,
        Benchmark.is_active.is_(True),
    )
    if population_scope is not None:
        stmt = stmt.where(Benchmark.population_scope == population_scope)
    return (await db.scalars(stmt)).all()


@dataclass
class BenchmarkContext:
    """T1-4 — insight에 붙이는 '비교 맥락' (발화 결정과 무관, §5)."""
    available: bool
    benchmark_value: float | None
    value_scale: str | None
    benchmark_id: int | None
    benchmark_status: str | None
    comparison_status: str | None
    source_obs_id: int | None
    obs_group_id: str | None
    population_scope: str | None
    is_global_fallback: bool
    unavailable_reason: str | None   # none|provisional|missing|benchmark_value_scale_mismatch

    def trace(self) -> dict:
        return asdict(self)


_CONTEXT_OK = {"verified", "normalized_verified", "global_fallback"}


async def resolve_benchmark_context(
    db: AsyncSession, country_code: str, kpi_code: str, *, population_scope: str | None = None,
) -> BenchmarkContext:
    """
    verified/normalized 평균을 비교 맥락으로 해소(§5). **발화 결정 아님.**
    - verified/normalized_verified/global_fallback + value_scale 일치 → 맥락 첨부.
    - provisional/missing → 맥락 금지(사용자 노출 안 함), reason 기록.
    - value_scale mismatch → 맥락만 강등(benchmark_value_scale_mismatch), 발화는 막지 않음(threshold 담당).
    """
    def _none(reason: str) -> BenchmarkContext:
        return BenchmarkContext(False, None, None, None, None, None, None, None, None, False, reason)

    rows = await _fetch_rows(db, country_code, kpi_code, population_scope)
    if not rows:
        return _none("none")
    kdefs = kpi_definition_index()
    b = sorted(rows, key=lambda r: _STATUS_RANK.get(r.benchmark_status, 0), reverse=True)[0]
    kdef = kdefs.get(b.kpi_code)
    is_gf = b.benchmark_status == "global_fallback"

    if b.benchmark_status not in _CONTEXT_OK:
        # provisional / missing → 맥락도 노출 금지
        return _none(b.benchmark_status)

    kdef_scale = kdef["value_scale"] if kdef else None
    if b.value_scale is None or kdef_scale is None or b.value_scale != kdef_scale:
        # value_scale 불일치 → 맥락만 강등(발화는 별개)
        return BenchmarkContext(
            False, None, b.value_scale, b.bench_id, b.benchmark_status, b.comparison_status,
            b.source_obs_id, b.obs_group_id, b.population_scope, is_gf, "benchmark_value_scale_mismatch")

    return BenchmarkContext(
        available=True,
        benchmark_value=float(b.transformed_value) if b.transformed_value is not None else None,
        value_scale=b.value_scale, benchmark_id=b.bench_id, benchmark_status=b.benchmark_status,
        comparison_status=b.comparison_status, source_obs_id=b.source_obs_id, obs_group_id=b.obs_group_id,
        population_scope=b.population_scope, is_global_fallback=is_gf, unavailable_reason=None)


def evaluate_severity(rb: ResolvedBenchmark, value: float) -> str | None:
    """발화 적격이면 severity(ok/warning/critical), 아니면 None(발화 안 함)."""
    if not rb.can_fire or rb.direction is None:
        return None
    sev = severity_for(
        rb.direction, value,
        warning_min=rb.warning_min, warning_max=rb.warning_max,
        critical_min=rb.critical_min, critical_max=rb.critical_max,
    )
    rb.threshold_used = rb.direction
    return sev


# 룰 KPI 코드(대문자 legacy) → governance kpi_code(소문자). 매핑 없으면 맥락 없음.
RULE_KPI_TO_GOVERNANCE = {
    "PSY": "psy", "MSY": "msy", "FARROWING_RATE": "farrowing_rate", "WEANED_COUNT": "weaned_per_litter",
    "NPD": "npd", "STILLBORN_RATE": "stillbirth_rate", "MUMMIFIED_RATE": "mummy_rate",
    "SOW_MORTALITY": "sow_mortality", "FCR": "fcr", "WSI": "wsi", "CULLING_RATE": "culling_rate",
}


async def enrich_findings_with_governance(db: AsyncSession, country_code: str, findings: list) -> None:
    """
    T1-5: flag ON일 때만 호출. 각 finding.detail["governance_trace"]에 §7 trace + 비교 맥락 첨부.
    benchmark context는 §5(verified/normalized만 첨부). 매핑 없는 룰 KPI는 benchmark_source=none.
    발화는 이미 끝난 상태 — 여기선 맥락/감사 trace만 붙인다(발화 변경 없음).
    """
    from app.engine.rule_engine import Severity  # noqa
    for f in findings:
        gov_kpi = RULE_KPI_TO_GOVERNANCE.get(f.kpi)
        bc = None
        if gov_kpi is not None:
            bc = await resolve_benchmark_context(db, country_code, gov_kpi)
        sev = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
        f.detail["governance_trace"] = {
            "rule_id": f.rule_id, "kpi_code": f.kpi, "governance_kpi": gov_kpi, "severity": sev,
            "current_value": f.current_value, "target_value": f.target_value,
            "benchmark_source": "governance_benchmark" if (bc and bc.available) else "none",
            "benchmark_value": bc.benchmark_value if bc else None,
            "benchmark_id": bc.benchmark_id if bc else None,
            "benchmark_status": bc.benchmark_status if bc else None,
            "comparison_status": bc.comparison_status if bc else None,
            "source_obs_id": bc.source_obs_id if bc else None,
            "obs_group_id": bc.obs_group_id if bc else None,
            "is_global_fallback": bool(bc.is_global_fallback) if bc else False,
            "benchmark_unavailable_reason": bc.unavailable_reason if bc else "no_mapping",
        }


async def list_benchmarks(
    db: AsyncSession, *, country_code: str | None = None, kpi_code: str | None = None,
) -> list[Benchmark]:
    stmt = select(Benchmark)
    if country_code:
        stmt = stmt.where(Benchmark.country_code == country_code)
    if kpi_code:
        stmt = stmt.where(Benchmark.kpi_code == kpi_code)
    stmt = stmt.order_by(Benchmark.country_code, Benchmark.kpi_code)
    return list((await db.scalars(stmt)).all())


async def list_kpi_definitions(db: AsyncSession) -> list[KpiDefinition]:
    return list((await db.scalars(select(KpiDefinition).order_by(KpiDefinition.kpi_code))).all())
