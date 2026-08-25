"""농장 현지 기준 '오늘' — 서버 벽시계를 그대로 쓰면 안 되는 이유.

## 문제

`date.today()` 는 **프로세스 타임존**의 오늘이다. 운영 컨테이너는 **UTC** 로 뜬다
(실측 2026-08-25: `time.tzname == ('UTC','UTC')`). 그런데 PigOS 는 8개 법역 서비스이고
농장은 자기 현지 날짜로 사건을 기록한다. 둘이 어긋나는 시간대가 매일 존재한다.

프로덕션 농장 타임존 실측(2026-08-25)과 어긋나는 창:

| 타임존 | 어긋남 | 증상 |
|---|---|---|
| Asia/Seoul (12 농장) | 9시간 | 00:00~09:00 에 **오늘 날짜 입력이 "미래"로 거부됨** |
| Asia/Manila (1) | 8시간 | 〃 |
| America/Chicago (4) | 5시간 | 19:00 부터 대시보드 '오늘·이번주'가 **하루 앞서감** |
| America/Mexico_City (3) | 6시간 | 〃 |

재현(서울, 2026-08-26 07:00 KST): 사용자 입력 `2026-08-26` vs `date.today()`(UTC)
`2026-08-25` → `mating_date > date.today()` 가 참 → ValidationError.
**아침에 일하는 농장이 오전 내내 데이터를 못 넣는다.**

## 규칙

- 사용자가 보는 날짜·기간(오늘, 이번주, KPI 기준일, 미래일 검증)은 **농장 현지**로 판정한다.
- 서버 벽시계(`date.today()`)는 **농장 맥락이 없는 곳에서만** 쓴다
  (예: 정책 발효일 게이트처럼 회사 기준으로 판단하는 것).
- 절대시각 비교(`created_at >= now() - interval '7 days'`)는 timestamptz 라 TZ 무관 — 그대로 둔다.

`reports.py` 에는 2026-06 부터 같은 취지의 `_farm_today` 가 있었지만 그 파일에서만 썼고,
주석은 "서버(KST)"를 전제하고 있었다(컨테이너는 UTC 다). 여기로 통합한다.
"""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

_UTC = ZoneInfo("UTC")


def farm_today(farm) -> date:
    """농장 타임존 기준 오늘. farm 은 `.timezone` 을 가진 객체(Farm 모델 등).

    tz 문자열이 비었거나 해석 불가면 UTC 로 폴백한다 — 예외를 던지면 잘못된 tz 하나가
    농장 전체 기능을 멈춘다. 폴백은 기존 동작(서버 UTC)과 같아 더 나빠지지 않는다.
    """
    return _today_in(getattr(farm, "timezone", None))


def today_in_tz(tz: str | None) -> date:
    """타임존 문자열만 있을 때(배치 잡이 farm_id·timezone 만 들고 도는 경우)."""
    return _today_in(tz)


def _today_in(tz: str | None) -> date:
    try:
        return datetime.now(ZoneInfo(tz)).date() if tz else datetime.now(_UTC).date()
    except Exception:  # noqa: BLE001 — 알 수 없는 tz 는 UTC 폴백
        return datetime.now(_UTC).date()


async def farm_today_by_id(db: AsyncSession, farm_id: UUID) -> date:
    """farm 객체 없이 farm_id 만 있는 경로(event_service 등)용.

    ★ 타임존 컬럼 하나만 읽는다 — 검증 한 줄 때문에 Farm 전체를 로드할 이유가 없다.
    """
    from app.db.models.platform import Farm  # 순환 import 회피

    tz = await db.scalar(select(Farm.timezone).where(Farm.id == farm_id))
    return _today_in(tz)
