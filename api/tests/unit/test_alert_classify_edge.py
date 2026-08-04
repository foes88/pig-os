"""alert 분류기 엣지 (기존 test_alert_service 미커버) — None 견고성·경계·임계 주입.

classify_overdue / classify_cull 순수함수의 방어적 동작을 고정:
불완전 데이터(날짜 None)에도 크래시 없이 None, 임계 '초과' strict 경계, farm_config 임계 주입.
"""
from datetime import date, timedelta

from app.services.alert_service import AlertThresholds, classify_cull, classify_overdue

TODAY = date(2026, 6, 10)
TH = AlertThresholds()


def test_missing_dates_return_none_not_crash():
    # 상태는 있으나 관련 날짜가 없는 불완전 레코드 → None (예외 없이)
    assert classify_overdue(status="PREGNANT", today=TODAY, last_mating=None) is None
    assert classify_overdue(status="LACTATING", today=TODAY, last_farrowing=None) is None
    assert classify_overdue(status="OPEN", today=TODAY, last_weaning=None) is None
    assert classify_overdue(status="ACCIDENT", today=TODAY, last_rts=None) is None


def test_exact_threshold_not_overdue_open_lact_accident():
    # '초과(strictly greater)'만 과기한 → 임계 정확히 = 정상
    assert classify_overdue(status="OPEN", today=TODAY, last_weaning=TODAY - timedelta(days=TH.wsi_days)) is None
    assert classify_overdue(status="LACTATING", today=TODAY, last_farrowing=TODAY - timedelta(days=TH.lactation_days)) is None
    assert classify_overdue(status="ACCIDENT", today=TODAY, last_rts=TODAY - timedelta(days=TH.wsi_days)) is None


def test_one_day_over_threshold_is_overdue():
    r = classify_overdue(status="OPEN", today=TODAY, last_weaning=TODAY - timedelta(days=TH.wsi_days + 1))
    assert r == ("open_overdue_mating", 1)


def test_gilt_exactly_first_mating_age_is_no_estrus_not_overdue_mating():
    # age == 240 은 >240 아니므로 gilt_overdue_mating 아님. 무발정(>=180)으로 분류
    r = classify_overdue(status="GILT", today=TODAY, age_days=TH.gilt_first_mating_age, has_heat=False)
    assert r is not None and r[0] == "gilt_no_estrus"
    # 발정 확인되면 정상
    assert classify_overdue(status="GILT", today=TODAY, age_days=TH.gilt_first_mating_age, has_heat=True) is None


def test_unknown_status_returns_none():
    for st in ("CULLED", "DEAD", "", "WEANED"):
        assert classify_overdue(status=st, today=TODAY, last_mating=date(2020, 1, 1)) is None


def test_custom_gestation_threshold_plumbed():
    mating = TODAY - timedelta(days=105)
    # 기본 114 → 105일은 정상
    assert classify_overdue(status="PREGNANT", today=TODAY, last_mating=mating) is None
    # 임신기간 100 로 낮추면 105일은 과기한(초과 5일)
    short = AlertThresholds(gestation_days=100)
    r = classify_overdue(status="PREGNANT", today=TODAY, last_mating=mating, th=short)
    assert r == ("pregnant_overdue_farrowing", 5)


def test_custom_cull_parity_threshold_plumbed():
    # 기본 7 → parity 6 은 도태권고 아님
    assert "aged_low_performer" not in classify_cull(status="OPEN", parity=6, last_weaned_count=8)
    # 임계 5 로 낮추면 parity 6 + 저성적 → 권고
    low = AlertThresholds(cull_parity_threshold=5)
    assert "aged_low_performer" in classify_cull(status="OPEN", parity=6, last_weaned_count=8, th=low)
