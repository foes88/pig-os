"""#4 — 중복판정 시각차 계산이 타임존 안전한지 + None 방어."""
from datetime import UTC, datetime, timedelta, timezone

from app.services.sync_service import _dup_time_diff_seconds


def test_aware_offset_converted_not_relabeled():
    # 클라가 +09:00 aware로 30분 전 시각 → UTC 변환 후 실제 차이 1800초여야 함
    # (과거 .replace(tzinfo=UTC)는 9h 어긋나게 했음).
    kst = timezone(timedelta(hours=9))
    server = datetime(2026, 6, 1, 0, 0, 0, tzinfo=UTC)
    client = datetime(2026, 6, 1, 9, 30, 0, tzinfo=kst)  # = 00:30 UTC
    diff = _dup_time_diff_seconds(client, server)
    assert diff == 1800.0


def test_naive_client_assumed_utc():
    server = datetime(2026, 6, 1, 0, 0, 0, tzinfo=UTC)
    client = datetime(2026, 6, 1, 0, 10, 0)  # naive → UTC 간주
    assert _dup_time_diff_seconds(client, server) == 600.0


def test_none_server_time_returns_none():
    # 같은 배치 직전 삽입(server_default 미반영) → None → 비교 불가(크래시 아님)
    assert _dup_time_diff_seconds(datetime(2026, 6, 1, tzinfo=UTC), None) is None
