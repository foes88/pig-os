"""resolve_display_kpis 쿼리 횟수 고정 (N+1 회귀 방지).

배경: 원래 구현은 KPI 1개당 정책·표현을 각각 조회해서 KPI 14개면 왕복 29회였다.
Supabase Supavisor 세션 모드는 동시 클라이언트 15가 한도라, 왕복이 길면 커넥션을
그만큼 오래 물고 있어 마이그레이션·모니터링이 슬롯을 못 잡는다(2026-08-20 장애).
KPI 가 늘어도 왕복이 늘지 않아야 한다.
"""
import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.kpi_policy import CountryKpiPolicy
from app.db.models.kpi_presentation import CountryKpiPresentation
from app.services.kpi_policy_resolver import resolve_display_kpis

pytestmark = pytest.mark.anyio


def _global(kpi, **kw):
    base = dict(scope_level="GLOBAL", kpi_code=kpi, compute_enabled=True, display_role="PRIMARY",
                rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
                api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="test")
    base.update(kw)
    return CountryKpiPolicy(**base)


class _Counter:
    """이 세션이 실제로 던진 SELECT 수를 센다."""

    def __init__(self, sync_conn):
        self.n = 0
        self._conn = sync_conn
        event.listen(sync_conn, "before_cursor_execute", self._hit)

    def _hit(self, conn, cursor, statement, params, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            self.n += 1

    def stop(self):
        event.remove(self._conn, "before_cursor_execute", self._hit)


async def _count_queries(db: AsyncSession, **kw) -> tuple[int, int]:
    await db.flush()  # 카운트 전에 보류 INSERT 를 비운다
    raw = await db.connection()
    counter = await raw.run_sync(lambda c: _Counter(c))
    try:
        rows = await resolve_display_kpis(db, **kw)
    finally:
        await raw.run_sync(lambda c: counter.stop())
    return counter.n, len(rows)


async def _seed(db: AsyncSession, n: int) -> None:
    for i in range(n):
        db.add(_global(f"QK{i:02d}"))
        db.add(CountryKpiPresentation(
            scope_level="GLOBAL", kpi_code=f"QK{i:02d}", display_order=i * 10,
            display_order_override=True, decision_status="APPROVED"))
    await db.flush()


async def test_query_count_is_two(db: AsyncSession):
    """★ KPI 개수와 무관하게 SELECT 2회(정책 1 + 표현 1)."""
    await _seed(db, 12)
    n, got = await _count_queries(db, country="BR")
    assert got == 12
    assert n == 2, f"KPI 12개에 SELECT {n}회 — N+1 이 되살아났다(기대 2)"


async def test_query_count_does_not_grow_with_kpi_count(db: AsyncSession):
    """KPI 를 3배로 늘려도 왕복 수가 그대로여야 한다."""
    await _seed(db, 6)
    small, n_small = await _count_queries(db, country="BR")
    await _seed(db, 18)
    large, n_large = await _count_queries(db, country="BR")
    assert n_large > n_small, "픽스처가 실제로 늘어나야 의미 있는 비교"
    assert large == small, f"KPI {n_small}→{n_large} 인데 쿼리 {small}→{large} 로 증가"
