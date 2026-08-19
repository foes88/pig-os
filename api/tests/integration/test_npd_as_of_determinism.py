"""WEI/NPD as_of 계약 — 계산 기준일은 호출자가 준 as_of 다(벽시계 아님).

깨졌던 계약:
    호출 계약  service(as_of) 기준 계산
    실제 계산  v_sow_npd 의 CURRENT_DATE 기준 계산
2026-08-19 에 test_npd_idle_cap 이 처음 깨진 것이 이 위반의 증상이었다
(fixture 의 C 모돈이 실제 경과일 기준으로 60일선을 넘어버림).

★ 이 파일의 테스트는 어느 날짜에 실행해도 결과가 같아야 한다.
  상대날짜(date.today() 기반) fixture 를 쓰지 않는다 — 그렇게 하면 결함이 숨는다.
"""
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.repositories import npd_repo
from app.services.kpi_service import calculate_npd

pytestmark = pytest.mark.anyio


async def _weaned_sow(db, farm, weaning_date: date, *, remate_after: int | None = None) -> Sow:
    """이유 1건을 가진 모돈. remate_after 를 주면 이유 n일 후 재교배."""
    s = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=2,
            status="OPEN", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    m0 = Mating(farm_id=farm.id, sow_id=s.id, mating_date=weaning_date - timedelta(days=150),
                mating_type="AI", mating_number=1)
    db.add(m0)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=s.id, mating_id=m0.id,
                  farrowing_date=weaning_date - timedelta(days=25), total_born=12, born_alive=12,
                  stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    db.add(Weaning(farm_id=farm.id, sow_id=s.id, farrowing_id=f.id,
                   weaning_date=weaning_date, weaned_count=11))
    if remate_after is not None:
        db.add(Mating(farm_id=farm.id, sow_id=s.id,
                      mating_date=weaning_date + timedelta(days=remate_after),
                      mating_type="AI", mating_number=2))
    await db.flush()
    return s


async def _wei(db, farm, as_of: date) -> float | None:
    return await npd_repo.avg_wei_days(
        db, farm.id, start=as_of - timedelta(days=365), end=as_of, as_of=as_of)


# ── 유휴 경계 59 / 60 / 61 ────────────────────────────────────────────────────
# 기준일을 고정한다. 실행 날짜가 2026년이든 2030년이든 결과가 같아야 한다.
AS_OF = date(2026, 6, 30)


@pytest.mark.parametrize(("idle_days", "expected"), [
    (59, None),   # 아직 정상 WEI 구간 → 평균에서 제외
    (60, 60.0),   # 경계 포함 → cap
    (61, 60.0),   # 초과 → cap
])
async def test_idle_boundary_59_60_61(db: AsyncSession, test_farm: Farm, idle_days, expected):
    await _weaned_sow(db, test_farm, AS_OF - timedelta(days=idle_days))
    assert await _wei(db, test_farm, AS_OF) == expected


async def test_remated_sow_uses_actual_interval(db: AsyncSession, test_farm: Farm):
    """재교배 완료 → 실제 WEI(60 초과분은 cap)."""
    await _weaned_sow(db, test_farm, AS_OF - timedelta(days=90), remate_after=7)
    assert await _wei(db, test_farm, AS_OF) == 7.0


async def test_remate_beyond_60_is_capped(db: AsyncSession, test_farm: Farm):
    """60일 넘겨 재교배해도 60 으로 cap — 기존 뷰 의미 보존."""
    await _weaned_sow(db, test_farm, AS_OF - timedelta(days=120), remate_after=75)
    assert await _wei(db, test_farm, AS_OF) == 60.0


# ── ★ 핵심 계약 ──────────────────────────────────────────────────────────────

async def test_same_as_of_is_independent_of_wall_clock(db: AsyncSession, test_farm: Farm):
    """★ 같은 as_of 면 실행 날짜가 언제든 결과가 같다.

    벽시계 의존이 남아 있으면 이 fixture 는 시간이 지나며 값이 변한다.
    (기존 결함: 이유 06-20 모돈이 2026-08-19 부터 60 cap 으로 바뀌어 33.5 → 42.3)
    """
    await _weaned_sow(db, test_farm, date(2026, 4, 1))                    # 90일 유휴 → 60
    await _weaned_sow(db, test_farm, date(2026, 6, 1), remate_after=7)    # → 7
    await _weaned_sow(db, test_farm, date(2026, 6, 20))                   # 10일 유휴 → NULL
    # AVG(60, 7) = 33.5 — 이 값은 실행 시점과 무관한 상수여야 한다.
    assert await _wei(db, test_farm, date(2026, 6, 30)) == pytest.approx(33.5, abs=0.1)


async def test_different_as_of_changes_value_as_intended(db: AsyncSession, test_farm: Farm):
    """동일 fixture + 다른 as_of → 의도한 대로 값이 변한다.

    06-20 이유 모돈은 as_of 가 60일 이상 지난 뒤에야 cap 대상이 된다.
    """
    await _weaned_sow(db, test_farm, date(2026, 4, 1))
    await _weaned_sow(db, test_farm, date(2026, 6, 1), remate_after=7)
    await _weaned_sow(db, test_farm, date(2026, 6, 20))

    # 06-20 + 60 = 08-19 → 그 전날까지는 제외
    assert await _wei(db, test_farm, date(2026, 8, 18)) == pytest.approx(33.5, abs=0.1)
    # 08-19 부터 포함 → AVG(60, 7, 60) = 42.3
    assert await _wei(db, test_farm, date(2026, 8, 19)) == pytest.approx(42.3, abs=0.1)


async def test_mating_after_as_of_is_not_visible(db: AsyncSession, test_farm: Farm):
    """as_of 이후의 교배는 아직 일어나지 않은 사건 — 과거시점 재계산에 섞이면 안 된다."""
    await _weaned_sow(db, test_farm, date(2026, 6, 1), remate_after=40)  # 재교배 07-11
    # 06-30 시점에는 아직 재교배 전이고 유휴 29일(<60) → 평균 산출 대상 없음
    assert await _wei(db, test_farm, date(2026, 6, 30)) is None
    # 07-31 시점에는 재교배가 보인다 → 40
    assert await _wei(db, test_farm, date(2026, 7, 31)) == 40.0


async def test_calculate_npd_passes_as_of_down_to_repository(db: AsyncSession, test_farm: Farm):
    """as_of 가 service → repository 까지 실제로 전달되는지(서비스 경유 확인)."""
    await _weaned_sow(db, test_farm, date(2026, 4, 1))
    await _weaned_sow(db, test_farm, date(2026, 6, 1), remate_after=7)
    await _weaned_sow(db, test_farm, date(2026, 6, 20))

    early = await calculate_npd(db, test_farm.id, date(2026, 8, 18))
    late = await calculate_npd(db, test_farm.id, date(2026, 8, 19))
    assert early is not None and late is not None
    assert early.weaning_to_mating_days == pytest.approx(33.5, abs=0.1)
    assert late.weaning_to_mating_days == pytest.approx(42.3, abs=0.1)


async def test_calculation_sql_has_no_current_date(db: AsyncSession):
    """계산 SQL 에 CURRENT_DATE 가 없다.

    docstring/주석의 설명은 허용하고 실제 SQL 문자열만 본다 — AST 로 docstring 을
    걸러내고, 남은 문자열 리터럴에서 SQL 라인 주석을 제거한 뒤 검사한다."""
    import ast
    import re
    from pathlib import Path

    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    for f in ("app/repositories/npd_repo.py", "app/services/kpi_service.py"):
        tree = ast.parse(Path(f).read_text(encoding="utf-8"))
        docstrings = set()
        for node in ast.walk(tree):
            if not isinstance(node, holders):
                continue
            body = getattr(node, "body", [])
            if not body or not isinstance(body[0], ast.Expr):
                continue
            first = body[0].value
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                docstrings.add(id(first))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if id(node) in docstrings:
                continue
            sql = re.sub(r"--.*", "", node.value)  # SQL 라인 주석 제거
            assert not re.search(r"\bCURRENT_DATE\b", sql, re.IGNORECASE), (
                f"{f}:{node.lineno} 계산 SQL 에 CURRENT_DATE"
            )
