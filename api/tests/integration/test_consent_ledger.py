"""동의 원장 기록/철회 통합 (CONSENT_SPEC §5 원장 불변식).

- 가입 기록: 고지형(①②⑥)=NOTICE_GIVEN, 옵트인(③④⑤)=granted 만 GRANTED
- 현재상태: 목적별 최신 1행
- 철회/이의/제외: append-only, 최신이 현재
- 필수 동의 미체크 → 422
- CONSENT 근거인데 evidence 없음 → DB CheckConstraint 위반 방지(서비스가 evidence 합성)
"""
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.consent import ConsentRecord
from app.db.models.platform import Farm, User
from app.schemas.consent import ConsentChoice, RecordConsentRequest, WithdrawRequest
from app.services import consent_service as cs

pytestmark = pytest.mark.anyio


async def _record(db, user, farm, *, country="KR", choices=None, terms=True, privacy=True):
    req = RecordConsentRequest(
        farm_id=farm.id, selected_country=country, farm_country=country,
        terms_ack=terms, privacy_ack=privacy,
        choices=choices or [],
    )
    return await cs.record_consents(db, user_id=user.id, req=req)


async def test_signup_records_notice_and_optin(db: AsyncSession, test_user: User, test_farm: Farm):
    out = await _record(db, test_user, test_farm, country="KR", choices=[
        ConsentChoice(purpose_code="AI_MODEL_TRAINING", granted=True),
        ConsentChoice(purpose_code="NAMED_RESEARCH", granted=False),
    ])
    by = {o.purpose_code: o for o in out}
    # 고지형: ① 서비스운영, ② 익명, ⑥ 외부처리 → NOTICE_GIVEN
    assert by["SERVICE_OPERATION"].consent_status == "NOTICE_GIVEN"
    assert by["ANON_AGG_STATS"].consent_status == "NOTICE_GIVEN"
    assert by["EXTERNAL_AI_PROCESSING"].consent_status == "NOTICE_GIVEN"
    # 옵트인: 켠 것만 GRANTED, 끈 건 미기록
    assert by["AI_MODEL_TRAINING"].consent_status == "GRANTED"
    assert "NAMED_RESEARCH" not in by


async def test_optin_granted_has_consent_basis_and_evidence(db: AsyncSession, test_user, test_farm):
    await _record(db, test_user, test_farm, country="KR", choices=[
        ConsentChoice(purpose_code="AI_MODEL_TRAINING", granted=True),
    ])
    row = (await db.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == test_user.id,
            ConsentRecord.purpose_code == "AI_MODEL_TRAINING",
        )
    )).scalars().one()
    assert row.lawful_basis == "CONSENT"
    assert row.evidence_ref  # 증적 필수(§5.2) — 서비스가 합성


async def test_required_ack_missing_is_422(db: AsyncSession, test_user, test_farm):
    with pytest.raises(Exception) as ei:
        await _record(db, test_user, test_farm, terms=False)
    assert "422" in str(ei.value) or "TERMS" in str(ei.value)


async def test_cn_signup_blocked_451(db: AsyncSession, test_user, test_farm):
    with pytest.raises(Exception) as ei:
        await _record(db, test_user, test_farm, country="CN")
    assert "451" in str(ei.value) or "BLOCKED" in str(ei.value)


async def test_current_returns_latest_per_purpose(db: AsyncSession, test_user, test_farm):
    await _record(db, test_user, test_farm, country="KR", choices=[
        ConsentChoice(purpose_code="AI_MODEL_TRAINING", granted=True),
    ])
    cur = await cs.current_consents(db, user_id=test_user.id, farm_id=test_farm.id)
    codes = {c.purpose_code for c in cur}
    assert "AI_MODEL_TRAINING" in codes and "SERVICE_OPERATION" in codes


async def test_withdraw_optin_appends_and_becomes_current(db: AsyncSession, test_user, test_farm):
    await _record(db, test_user, test_farm, country="KR", choices=[
        ConsentChoice(purpose_code="AI_MODEL_TRAINING", granted=True),
    ])
    await cs.withdraw(db, user_id=test_user.id,
                      req=WithdrawRequest(purpose_code="AI_MODEL_TRAINING", farm_id=test_farm.id, action="WITHDRAWN"))
    cur = await cs.current_consents(db, user_id=test_user.id, farm_id=test_farm.id)
    ai = next(c for c in cur if c.purpose_code == "AI_MODEL_TRAINING")
    assert ai.consent_status == "WITHDRAWN"
    # append-only: 원장에 2행 이상 남음
    n = (await db.execute(
        select(func.count()).select_from(ConsentRecord).where(
            ConsentRecord.user_id == test_user.id,
            ConsentRecord.purpose_code == "AI_MODEL_TRAINING",
        )
    )).scalar()
    assert n >= 2


async def test_exclusion_request_on_anon(db: AsyncSession, test_user, test_farm):
    await _record(db, test_user, test_farm, country="KR")
    out = await cs.withdraw(db, user_id=test_user.id,
                            req=WithdrawRequest(purpose_code="ANON_AGG_STATS", farm_id=test_farm.id,
                                                action="EXCLUSION_REQUESTED"))
    assert out.consent_status == "EXCLUSION_REQUESTED"


async def test_us_ne_written_optin_recorded_with_evidence(db: AsyncSession, test_user, test_farm):
    req = RecordConsentRequest(
        farm_id=test_farm.id, selected_country="US", farm_country="US", farm_state="NE",
        terms_ack=True, privacy_ack=True,
        choices=[ConsentChoice(purpose_code="ANON_AGG_STATS", granted=True, evidence_ref="e-signature:abc")],
    )
    out = await cs.record_consents(db, user_id=test_user.id, req=req)
    anon = next(o for o in out if o.purpose_code == "ANON_AGG_STATS")
    # NE 는 ②가 서면 옵트인 → granted 시 GRANTED(고지형 아님)
    assert anon.consent_status == "GRANTED"
    assert anon.jurisdiction == "US-NE"
