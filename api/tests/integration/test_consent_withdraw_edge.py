"""동의 철회 엣지 (CONSENT_SPEC §5) — 기존 test_consent_ledger 미커버분.

- 기록 없는 목적 철회 → 404
- 허용되지 않은 action → 422
- 철회 후 재동의 → current 가 다시 GRANTED (append-only, 최신 우선)
- 철회 레코드는 이전 근거·법역·버전 승계 + reason 을 evidence 로 보존
"""
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.consent import ConsentRecord
from app.db.models.platform import Farm, User
from app.schemas.consent import ConsentChoice, RecordConsentRequest, WithdrawRequest
from app.services import consent_service as cs

pytestmark = pytest.mark.anyio


async def _grant_ai(db, user, farm):
    req = RecordConsentRequest(
        farm_id=farm.id, selected_country="KR", farm_country="KR",
        terms_ack=True, privacy_ack=True,
        choices=[ConsentChoice(purpose_code="AI_MODEL_TRAINING", granted=True)],
    )
    return await cs.record_consents(db, user_id=user.id, req=req)


async def test_withdraw_without_prior_record_is_404(db: AsyncSession, test_user: User, test_farm: Farm):
    with pytest.raises(Exception) as ei:
        await cs.withdraw(db, user_id=test_user.id,
                          req=WithdrawRequest(purpose_code="AI_MODEL_TRAINING", farm_id=test_farm.id, action="WITHDRAWN"))
    assert "404" in str(ei.value) or "NO_CONSENT_RECORD" in str(ei.value)


async def test_invalid_withdraw_action_is_422(db: AsyncSession, test_user, test_farm):
    await _grant_ai(db, test_user, test_farm)
    with pytest.raises(Exception) as ei:
        await cs.withdraw(db, user_id=test_user.id,
                          req=WithdrawRequest(purpose_code="AI_MODEL_TRAINING", farm_id=test_farm.id, action="BOGUS"))
    assert "422" in str(ei.value) or "INVALID_ACTION" in str(ei.value)


async def test_regrant_after_withdraw_becomes_current(db: AsyncSession, test_user, test_farm):
    await _grant_ai(db, test_user, test_farm)
    await cs.withdraw(db, user_id=test_user.id,
                      req=WithdrawRequest(purpose_code="AI_MODEL_TRAINING", farm_id=test_farm.id, action="WITHDRAWN"))
    # 재동의
    await _grant_ai(db, test_user, test_farm)
    cur = await cs.current_consents(db, user_id=test_user.id, farm_id=test_farm.id)
    ai = next(c for c in cur if c.purpose_code == "AI_MODEL_TRAINING")
    assert ai.consent_status == "GRANTED"  # 최신이 재동의
    # 원장은 3행(grant→withdraw→grant) 이상 보존
    n = (await db.execute(
        select(func.count()).select_from(ConsentRecord).where(
            ConsentRecord.user_id == test_user.id,
            ConsentRecord.purpose_code == "AI_MODEL_TRAINING",
        )
    )).scalar()
    assert n >= 3


async def test_withdraw_inherits_basis_and_stores_reason(db: AsyncSession, test_user, test_farm):
    await _grant_ai(db, test_user, test_farm)
    out = await cs.withdraw(db, user_id=test_user.id,
                            req=WithdrawRequest(purpose_code="AI_MODEL_TRAINING", farm_id=test_farm.id,
                                                action="WITHDRAWN", reason="user-request-42"))
    # 이전 근거·법역 승계
    assert out.lawful_basis == "CONSENT"
    assert out.jurisdiction == "KR"
    # reason 이 철회 레코드 evidence 로 보존
    row = (await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == test_user.id,
            ConsentRecord.purpose_code == "AI_MODEL_TRAINING",
            ConsentRecord.consent_status == "WITHDRAWN",
        )
    )).scalars().one()
    assert row.evidence_ref == "user-request-42"
