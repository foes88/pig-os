"""WEI 뷰 fast-path 등가성 — as_of=오늘일 때만 v_sow_npd 를 쓴다.

## 왜 이 파일이 필요한가

`test_npd_as_of_determinism.py` 는 "계산 경로에서 v_sow_npd 를 쓰지 않는다"를 전제로
쓰였다. 뷰가 내부적으로 `CURRENT_DATE` 를 쓰기 때문에 as_of 계약을 깨뜨렸기 때문이다.

그런데 2026-08-25 대시보드 지연 대응에서 **as_of == 오늘인 핫패스에 한해** 뷰를
다시 쓰기로 했다(인라인 서브쿼리보다 훨씬 빠르다). 즉 전제에 예외가 생겼다.

★ 그 예외가 안전한 이유는 "as_of=오늘이면 뷰의 CURRENT_DATE 와 기준일이 같다"인데,
  이건 **가정이지 보장이 아니다.** 가정이 깨지면 값이 조용히 달라진다 — 예외를 만든
  쪽이 그 등가성을 테스트로 고정해야 한다. 이 파일이 그 역할이다.

## 등가성이 성립하는 근거와 그 조건

|  | 인라인(WEI_ROWS_SQL) | 뷰(v_sow_npd) |
|---|---|---|
| cap 판정 | `weaning_date <= (:as_of) - 60` | `weaning_date <= CURRENT_DATE - 60` |
| 다음 교배 상한 | `LEAST(weaning_date + 60, :as_of)` | `weaning_date + 60` |
| 이유 상한 | `weaning_date <= :as_of` | 없음 |

as_of = 오늘이면 1행은 같다. 2·3행의 차이는 **미래 날짜 데이터가 없을 때만** 무해하다.

- 미래 이유(3행): 바깥 쿼리의 `weaning_date BETWEEN :s AND :e`(e=as_of)가 이미 막는다.
- 미래 교배(2행): **DB 에 미래 교배가 있으면 두 경로가 갈린다.**
  현재는 `event_service.record_mating`/PATCH 가 미래 교배일을 거부해서 성립한다
  (프로덕션 실측 2026-08-25: 미래 날짜 matings/weanings/farrowings 0건).
  아래 `test_future_mating_is_the_condition...` 이 이 의존을 못 박는다 — 서비스
  가드를 없애거나 우회 경로(sync·harvest import)가 생기면 이 테스트가 이유를 알려준다.
"""
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.repositories import npd_repo

pytestmark = pytest.mark.anyio

TODAY = date.today()          # ★ 여기서만 상대날짜를 쓴다 — fast-path 조건 자체가 "오늘"이다
WINDOW = timedelta(days=365)


async def _weaned_sow(db, farm, weaning_date: date, *, remate_after: int | None = None) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=f"V-{uuid.uuid4().hex[:6].upper()}", parity=2,
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


async def _inline_avg(db, farm_id, *, start, end, as_of):
    """fast-path 를 우회하고 인라인 경로를 직접 실행(비교 기준)."""
    row = (await db.execute(
        npd_repo._AVG, {"farm_id": str(farm_id), "s": start, "e": end, "as_of": as_of},
    )).fetchone()
    return float(row.w) if row and row.w is not None else None


async def _inline_sum(db, farm_id, *, start, end, as_of):
    return float((await db.execute(
        npd_repo._SUM, {"farm_id": str(farm_id), "s": start, "e": end, "as_of": as_of},
    )).scalar() or 0)


async def _mixed_population(db, farm: Farm) -> None:
    """cap·정상·미판정을 모두 포함하는 모집단 — 한 종류만 넣으면 차이가 숨는다."""
    await _weaned_sow(db, farm, TODAY - timedelta(days=200))                      # 60 cap
    await _weaned_sow(db, farm, TODAY - timedelta(days=120), remate_after=5)      # 5
    await _weaned_sow(db, farm, TODAY - timedelta(days=90), remate_after=40)      # 40
    await _weaned_sow(db, farm, TODAY - timedelta(days=100), remate_after=80)     # 60 cap(초과)
    await _weaned_sow(db, farm, TODAY - timedelta(days=30))                       # NULL(59일 미만)


# ── 등가성 ────────────────────────────────────────────────────────────────────

async def test_avg_fastpath_matches_inline_today(db: AsyncSession, test_farm: Farm):
    """★ as_of=오늘: 뷰 경로와 인라인 경로가 같은 평균을 낸다."""
    await _mixed_population(db, test_farm)
    kw = {"start": TODAY - WINDOW, "end": TODAY}
    fast = await npd_repo.avg_wei_days(db, test_farm.id, as_of=TODAY, **kw)
    inline = await _inline_avg(db, test_farm.id, as_of=TODAY, **kw)
    assert fast is not None, "모집단이 비면 등가성 검증이 무의미하다"
    assert fast == pytest.approx(inline), (
        f"뷰 {fast} != 인라인 {inline} — fast-path 등가성이 깨졌다. "
        "미래 날짜 데이터가 유입됐는지, 뷰 정의가 바뀌었는지 확인하십시오."
    )


async def test_sum_fastpath_matches_inline_today(db: AsyncSession, test_farm: Farm):
    """합계 경로(손실 추정)도 동일해야 한다 — 평균만 맞추면 sum 이 조용히 어긋난다."""
    await _mixed_population(db, test_farm)
    kw = {"start": TODAY - WINDOW, "end": TODAY}
    fast = await npd_repo.sum_wei_days(db, test_farm.id, as_of=TODAY, **kw)
    inline = await _inline_sum(db, test_farm.id, as_of=TODAY, **kw)
    assert fast > 0
    assert fast == pytest.approx(inline)


async def test_past_as_of_does_not_use_view(db: AsyncSession, test_farm: Farm):
    """★ 과거 as_of 는 인라인 경로여야 한다 — 뷰를 쓰면 as_of 계약이 깨진다.

    뷰는 CURRENT_DATE 로 cap 을 판정하므로, 과거 시점 재계산에 뷰를 쓰면
    '그때는 아직 유휴가 아니었던' 모돈이 cap 60 으로 잡힌다."""
    # 오늘 기준 200일 전 이유 + 재교배 없음.
    # as_of=이유 30일 후 시점에서는 아직 유휴 판정 전(NULL) 이어야 한다.
    weaning = TODAY - timedelta(days=200)
    await _weaned_sow(db, test_farm, weaning)
    as_of = weaning + timedelta(days=30)

    got = await npd_repo.avg_wei_days(
        db, test_farm.id, start=as_of - WINDOW, end=as_of, as_of=as_of)
    assert got is None, (
        f"as_of={as_of} 시점엔 유휴 60일 미달이라 평균 대상이 없어야 하는데 {got} 이 나왔다 — "
        "과거 as_of 에 뷰(CURRENT_DATE) 경로가 쓰였을 가능성이 크다."
    )


# ── 등가성이 기대는 조건 ──────────────────────────────────────────────────────

async def test_future_mating_is_the_condition_fastpath_depends_on(
    db: AsyncSession, test_farm: Farm,
):
    """★ 미래 교배가 들어오면 두 경로가 갈린다 — 그래서 서비스 가드가 필요하다.

    이 테스트는 버그를 잡는 게 아니라 **의존 관계를 문서로 고정**한다.
    ORM 으로 직접 넣어 event_service 가드를 우회한다(sync·import 우회 경로 모사).
    실패하면 등가성 전제가 사라진 것이므로 fast-path 를 재검토해야 한다.
    """
    weaning = TODAY - timedelta(days=10)
    s = await _weaned_sow(db, test_farm, weaning)
    # 이유 후 20일 = 오늘 기준 미래. 뷰는 보고(20), 인라인은 as_of 상한에 걸려 못 본다.
    db.add(Mating(farm_id=test_farm.id, sow_id=s.id,
                  mating_date=weaning + timedelta(days=20),
                  mating_type="AI", mating_number=2))
    await db.flush()

    kw = {"start": TODAY - WINDOW, "end": TODAY}
    fast = await npd_repo.avg_wei_days(db, test_farm.id, as_of=TODAY, **kw)
    inline = await _inline_avg(db, test_farm.id, as_of=TODAY, **kw)

    assert fast == pytest.approx(20.0), "뷰는 미래 교배를 본다"
    assert inline is None, "인라인은 as_of 상한으로 미래 교배를 배제한다(아직 60일 미달 → NULL)"
    assert fast != inline, (
        "미래 교배가 있으면 두 경로가 달라야 한다 — 이 차이가 사라졌다면 "
        "뷰나 인라인 정의가 바뀐 것이니 fast-path 전제를 다시 확인하십시오."
    )


async def test_service_layer_rejects_future_mating(db: AsyncSession, test_farm: Farm):
    """위 조건을 실제로 지켜주는 가드가 살아 있는지 — 없어지면 fast-path 가 위험해진다.

    문서가 아니라 **동작**으로 확인한다. 주석에 "검증층이 막는다"고 적어두고
    실제로는 안 막는 상태가 되면 fast-path 가 조용히 틀린 값을 낸다."""
    from app.core.exceptions import ValidationError
    from app.schemas.events import MatingCreate
    from app.services import event_service

    sow = await _weaned_sow(db, test_farm, TODAY - timedelta(days=100), remate_after=5)
    req = MatingCreate(sow_id=sow.id, mating_date=TODAY + timedelta(days=1),
                       mating_type="AI", mating_number=3)
    with pytest.raises((ValidationError, ValueError)) as exc:
        await event_service.record_mating(
            db, farm_id=test_farm.id, user_id=uuid.uuid4(), req=req)
    assert "future" in str(exc.value).lower(), (
        f"미래 교배일이 아닌 다른 이유로 거부됐다: {exc.value} — "
        "가드가 실제로 미래일을 막고 있는지 확인하십시오."
    )
