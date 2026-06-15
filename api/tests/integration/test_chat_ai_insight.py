"""
Addon #1 (AI Insight) 구독 게이팅 테스트.

handle_query 안에서 use_llm을 결정하는 _has_ai_insight() 가 과금 게이트이므로
구독 상태(없음/활성/비활성)별로 정확히 판정되는지 검증한다.
(handle_query 전체 경로는 effective_metric_values DB 함수에 의존 — 별도 KPI 테스트 영역)
"""
import pytest

from app.db.models.platform import AddonSubscription
from app.services import chat_service


@pytest.mark.asyncio
async def test_no_subscription(db, test_farm):
    assert await chat_service._has_ai_insight(db, test_farm.id) is False


@pytest.mark.asyncio
async def test_active_subscription_detected(db, test_farm):
    db.add(AddonSubscription(
        farm_id=test_farm.id,
        addon_code=chat_service.AI_INSIGHT_ADDON_CODE,
        is_active=True,
    ))
    await db.flush()
    assert await chat_service._has_ai_insight(db, test_farm.id) is True


@pytest.mark.asyncio
async def test_inactive_subscription_ignored(db, test_farm):
    db.add(AddonSubscription(
        farm_id=test_farm.id,
        addon_code=chat_service.AI_INSIGHT_ADDON_CODE,
        is_active=False,
    ))
    await db.flush()
    assert await chat_service._has_ai_insight(db, test_farm.id) is False


@pytest.mark.asyncio
async def test_other_addon_does_not_enable_insight(db, test_farm):
    db.add(AddonSubscription(
        farm_id=test_farm.id,
        addon_code="ADDON_FCR",
        is_active=True,
    ))
    await db.flush()
    assert await chat_service._has_ai_insight(db, test_farm.id) is False
