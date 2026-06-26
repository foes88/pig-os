"""비밀번호 재설정 — request/confirm 서비스 통합 테스트 (PASSWORD_RESET_DRAFT 구현).

검증: 토큰 발급·열거방지, confirm 성공(비번갱신+refresh폐기), 만료/재사용/무효 차단.
"""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.security import verify_password
from app.db.models.platform import PasswordResetToken, RefreshToken, User
from app.services import auth_service


async def test_request_returns_token_for_existing_user(db: AsyncSession, test_user: User):
    raw = await auth_service.request_password_reset(db, test_user.email)
    assert raw, "활성 유저는 토큰 발급돼야"
    # DB엔 해시만 저장(평문 토큰 없음)
    prt = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id))
    assert prt is not None and prt.token_hash != raw and prt.used_at is None


async def test_request_none_for_unknown_email_no_enumeration(db: AsyncSession):
    raw = await auth_service.request_password_reset(db, "nobody-xyz@pigos.io")
    assert raw is None  # 라우터는 그래도 204 → 계정 존재 여부 노출 안 함


async def test_confirm_updates_password_and_revokes_refresh(db: AsyncSession, test_user: User):
    # refresh 토큰 하나 심어 두고 → confirm 시 폐기되는지
    db.add(RefreshToken(user_id=test_user.id, token_hash="rt-hash-1",
                        expires_at=datetime.now(UTC) + timedelta(days=7)))
    await db.flush()
    raw = await auth_service.request_password_reset(db, test_user.email)

    await auth_service.confirm_password_reset(db, raw, "NewPass123!")

    refreshed = await db.get(User, test_user.id)
    assert verify_password("NewPass123!", refreshed.password_hash)          # 새 비번 적용
    assert not verify_password("Test1234!", refreshed.password_hash)        # 옛 비번 무효
    # refresh 전부 폐기(강제 재로그인)
    assert await db.scalar(select(RefreshToken).where(RefreshToken.user_id == test_user.id)) is None
    # 토큰 1회용 소진
    prt = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id))
    assert prt.used_at is not None


async def test_confirm_rejects_reused_token(db: AsyncSession, test_user: User):
    raw = await auth_service.request_password_reset(db, test_user.email)
    await auth_service.confirm_password_reset(db, raw, "NewPass123!")
    with pytest.raises(ValidationError):
        await auth_service.confirm_password_reset(db, raw, "Another123!")   # 재사용 차단


async def test_confirm_rejects_garbage_token(db: AsyncSession):
    with pytest.raises(ValidationError):
        await auth_service.confirm_password_reset(db, "not-a-real-token", "NewPass123!")


async def test_confirm_rejects_expired_token(db: AsyncSession, test_user: User):
    raw = await auth_service.request_password_reset(db, test_user.email)
    prt = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.user_id == test_user.id))
    prt.expires_at = datetime.now(UTC) - timedelta(minutes=1)             # 만료시킴
    await db.flush()
    with pytest.raises(ValidationError):
        await auth_service.confirm_password_reset(db, raw, "NewPass123!")
