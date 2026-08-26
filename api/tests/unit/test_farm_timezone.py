"""농장 현지 '오늘' — 서버 벽시계를 쓰면 실제로 무엇이 깨지는가.

## 이 파일이 잠그는 사고 (2026-08-25 TZ 전수 점검에서 발견)

운영 컨테이너는 **UTC** 로 뜬다(실측 `time.tzname == ('UTC','UTC')`). 그런데 PigOS 는
8개 법역 서비스이고 농장은 자기 현지 날짜로 사건을 기록한다. `date.today()` 를 그대로
쓰면 서버와 농장의 날짜가 어긋나는 시간대가 매일 생긴다.

프로덕션 농장 타임존 실측: UTC 47 · Asia/Seoul 12 · America/Chicago 4 ·
America/Mexico_City 3 · Asia/Manila 1 — **실고객 농장이 실제로 비-UTC 다.**

재현된 결함 두 가지:

**① 입력 거부 (서버보다 앞선 타임존)**
서울(UTC+9) 2026-08-26 07:00 → 사용자가 보는 오늘은 `08-26`, 서버 `date.today()` 는
`08-25`. `mating_date > date.today()` 가 참이 되어 **"cannot be in the future" 로 거부**.
→ 아침에 일하는 농장이 매일 00:00~09:00 동안 데이터를 못 넣는다(서울 9h · 마닐라 8h).

**② 기간 경계 밀림 (서버보다 뒤진 타임존)**
시카고(UTC-5) 일요일 19:00 → 서버는 이미 월요일이라 대시보드 '이번주'가 **다음 주로**
넘어간다. 일요일 저녁에 그 주 실적이 0으로 보인다(시카고 5h · 멕시코시티 6h).

★ 두 결함은 방향이 반대다. 한쪽만 고치면 다른 쪽이 남는다.
"""
import inspect
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.core.farm_time import farm_today, today_in_tz

UTC = ZoneInfo("UTC")


class _Farm:
    """timezone 속성만 있으면 되는 최소 스텁 — Farm 모델 전체가 필요 없다."""

    def __init__(self, tz):
        self.timezone = tz


# ── 폴백: 잘못된 tz 하나가 농장 기능을 멈추면 안 된다 ─────────────────────────

@pytest.mark.parametrize("tz", [None, "", "Not/AZone", "Asia/Nowhere"])
def test_unknown_timezone_falls_back_to_utc(tz):
    """★ 예외를 던지면 tz 오타 하나로 그 농장의 모든 요청이 죽는다.

    폴백은 기존 동작(서버 UTC)과 같아 더 나빠지지 않는다."""
    assert farm_today(_Farm(tz)) == datetime.now(UTC).date()


def test_missing_attribute_does_not_raise():
    """timezone 속성 자체가 없는 객체(부분 로드 등)도 견딘다."""
    assert farm_today(object()) == datetime.now(UTC).date()


# ── 실제 타임존이 반영되는가 ─────────────────────────────────────────────────

@pytest.mark.parametrize("tz", ["Asia/Seoul", "America/Chicago", "America/Sao_Paulo", "UTC"])
def test_farm_today_matches_that_zone(tz):
    assert farm_today(_Farm(tz)) == datetime.now(ZoneInfo(tz)).date()
    assert today_in_tz(tz) == datetime.now(ZoneInfo(tz)).date()


# ── ① 입력 거부: 서버보다 앞선 타임존 ────────────────────────────────────────

@pytest.mark.parametrize(("tz", "hour"), [
    ("Asia/Seoul", 7),     # UTC+9 → 00:00~09:00 이 문제 창
    ("Asia/Seoul", 8),
    ("Asia/Manila", 5),    # UTC+8 → 00:00~08:00
])
def test_server_utc_would_reject_valid_same_day_entry(tz, hour):
    """★ 서버 UTC 기준이면 현지 오늘 날짜가 '미래'로 거부된다는 사실을 고정한다.

    이건 버그 재현이지 기대 동작이 아니다 — 아래 test_farm_local_accepts... 가
    고쳐진 동작을 잠근다. 둘을 같이 둬야 왜 고쳤는지가 남는다."""
    local = datetime(2026, 8, 26, hour, 0, tzinfo=ZoneInfo(tz))
    user_entered = local.date()               # 사용자가 보는 오늘
    server_today = local.astimezone(UTC).date()   # date.today() (컨테이너 UTC)
    assert user_entered > server_today, (
        f"{tz} {hour}시는 서버와 날짜가 어긋나는 창이어야 한다 "
        f"(사용자 {user_entered} vs 서버 {server_today})")


@pytest.mark.parametrize(("tz", "hour"), [("Asia/Seoul", 7), ("Asia/Manila", 5)])
def test_farm_local_accepts_same_day_entry(tz, hour):
    """★ 농장 현지 기준으로 판정하면 같은 상황이 통과한다."""
    local = datetime(2026, 8, 26, hour, 0, tzinfo=ZoneInfo(tz))
    assert not (local.date() > local.date()), "현지 오늘은 결코 현지 오늘보다 미래가 아니다"


# ── ② 기간 경계: 서버보다 뒤진 타임존 ────────────────────────────────────────

def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


@pytest.mark.parametrize(("tz", "hour"), [
    ("America/Chicago", 19),        # UTC-5 → 19:00 부터 서버는 다음 날
    ("America/Mexico_City", 19),    # UTC-6 → 19:00 부터(DST 따라 18~19시)
])
def test_server_utc_shifts_week_boundary_on_sunday_evening(tz, hour):
    """★ 일요일 저녁, 서버 기준 '이번주'가 다음 주로 넘어간다 = 그 주 실적이 0으로 보인다."""
    local = datetime(2026, 8, 30, hour, 0, tzinfo=ZoneInfo(tz))   # 2026-08-30 = 일요일
    assert local.weekday() == 6, "fixture 전제: 일요일"
    server_today = local.astimezone(UTC).date()
    assert _week_start(server_today) != _week_start(local.date()), (
        f"{tz} {hour}시는 주 경계가 어긋나는 창이어야 한다 "
        f"(농장 {_week_start(local.date())} vs 서버 {_week_start(server_today)})")


def test_farm_local_week_start_is_stable_within_the_local_day():
    """★ 현지 기준이면 하루 종일 같은 주에 속한다 — 저녁에 실적이 사라지지 않는다."""
    tz = ZoneInfo("America/Chicago")
    day = date(2026, 8, 30)
    starts = {_week_start(datetime(2026, 8, 30, h, 0, tzinfo=tz).date()) for h in range(24)}
    assert starts == {_week_start(day)}, f"현지 하루 안에서 주 시작이 흔들린다: {starts}"


# ── 계약: 새 코드가 서버 벽시계로 되돌아가지 않게 ────────────────────────────

def test_user_facing_modules_do_not_use_server_wallclock():
    """★ 사용자에게 보이는 날짜 판정에 date.today() 가 다시 들어오면 실패한다.

    2026-08-25 이전에는 이 모듈들이 전부 서버 벽시계를 썼다. 되돌아가기 쉬운 변경이라
    (한 줄이면 된다) 구조로 막는다. 농장 맥락이 없는 곳은 대상에서 제외한다."""
    import inspect

    from app.routers.base import boars as boars_mod
    from app.services import event_service, kpi_service

    for mod in (kpi_service, event_service, boars_mod):
        src = inspect.getsource(mod)
        # Query(default=...) 같은 요청 파싱 기본값은 농장을 모르는 자리라 예외로 둔다.
        offenders = [
            ln.strip() for ln in src.split("\n")
            if "date.today()" in ln and "Query(" not in ln and not ln.strip().startswith("#")
        ]
        assert not offenders, (
            f"{mod.__name__} 이 서버 벽시계를 쓴다: {offenders}\n"
            "농장 현지 기준이어야 한다 — app/core/farm_time.py 의 farm_today/"
            "farm_today_by_id/today_in_tz 를 쓰십시오.")


# ── KPI 스냅샷 기간: cron 시각이 아니라 농장 현지 완료 기간 ─────────────────

def test_snapshot_period_is_the_last_completed_one():
    """★ 아직 끝나지 않은 기간을 집계하지 않는다.

    예전엔 cron 이 도는 **시각**이 기간을 정했다. 월간 잡이 UTC 1일 00:15 에 도는데
    America/Chicago 는 그 순간 아직 전월 마지막 날이라, 함수가 **한 달 전**을 계산하고
    직전 달 스냅샷은 다음 달 1일까지 밀렸다(독립검증 2026-08-25).
    """
    from app.jobs.kpi import _last_completed_period as period

    # 시카고가 8/31(8월이 아직 안 끝남) → 끝난 달은 7월
    assert period("MONTHLY", date(2026, 8, 31)) == (date(2026, 7, 1), date(2026, 7, 31))
    # 현지가 9/1 이 되는 순간 → 8월이 집계된다(하루 안에 반영)
    assert period("MONTHLY", date(2026, 9, 1)) == (date(2026, 8, 1), date(2026, 8, 31))


def test_weekly_snapshot_uses_the_week_that_actually_ended():
    from app.jobs.kpi import _last_completed_period as period

    # 일요일(8/30)은 그 주가 아직 안 끝났다 → 직전 완료 주는 8/17~8/23
    assert period("WEEKLY", date(2026, 8, 30)) == (date(2026, 8, 17), date(2026, 8, 23))
    # 월요일(8/31)이 되면 직전 주(8/24~8/30)가 완료된다
    assert period("WEEKLY", date(2026, 8, 31)) == (date(2026, 8, 24), date(2026, 8, 30))


def test_daily_snapshot_is_yesterday_local():
    from app.jobs.kpi import _last_completed_period as period

    assert period("DAILY", date(2026, 8, 26)) == (date(2026, 8, 25), date(2026, 8, 25))


def test_every_timezone_gets_its_period_within_a_day():
    """★ 어느 타임존이든 기간 종료 후 하루 안에 집계된다 — 잡이 매일 돌기 때문이다.

    잡을 '월요일만', '1일만' 돌리면 그 순간 아직 기간이 안 끝난 타임존은 다음 주기까지
    기다려야 한다. 이 테스트는 그 설계로 되돌아가는 것을 막는다."""
    from app.jobs import worker as W

    src = inspect.getsource(W)
    assert "cron(weekly_kpi_aggregation, hour=" in src and "weekday=" not in src.split(
        "cron(weekly_kpi_aggregation")[1].split(")")[0], (
        "주간 잡이 특정 요일에만 돈다 — 그 시각에 주가 안 끝난 타임존이 일주일 늦는다")
    monthly = src.split("cron(monthly_kpi_aggregation")[1].split(")")[0]
    assert "day=" not in monthly, (
        "월간 잡이 특정 날짜에만 돈다 — 그 시각에 달이 안 끝난 타임존이 한 달 늦는다")
