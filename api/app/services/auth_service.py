import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.config import FarmConfig
from app.db.models.platform import (
    Farm,
    Organization,
    PasswordResetToken,
    RefreshToken,
    User,
    UserFarm,
)
from app.schemas.auth import (
    LoginResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services.farm_service import _generate_farm_code


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def register(db: AsyncSession, req: RegisterRequest) -> tuple[User, Organization]:
    existing = await db.scalar(select(User).where(User.email == req.email))
    if existing:
        raise ConflictError("Email already registered")

    org = Organization(
        name=req.org_name,
        country=req.country,
        timezone=req.timezone,
    )
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=req.email,
        name=req.name,
        password_hash=hash_password(req.password),
        role="FARM_OWNER",
        language=req.language,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, org


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email, User.active.is_(True)))
    if not user or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")

    user.last_login_at = datetime.now(UTC)
    await db.commit()
    return user


async def issue_tokens(db: AsyncSession, user: User) -> LoginResponse:
    farm_rows = await db.scalars(select(UserFarm).where(UserFarm.user_id == user.id))
    farm_ids = [str(uf.farm_id) for uf in farm_rows]

    access = create_access_token(user.id, user.org_id, [user.role])
    refresh = create_refresh_token(user.id)

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh),
        expires_at=expires_at,
    ))
    await db.commit()

    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
        user_id=str(user.id),
        name=user.name,
        email=user.email or "",
        role=user.role,
        farm_ids=farm_ids,
    )


async def complete_onboarding(
    db: AsyncSession, req: OnboardingCompleteRequest
) -> OnboardingCompleteResponse:
    existing = await db.scalar(select(User).where(User.email == req.email))
    if existing:
        raise ConflictError("Email already registered")

    org = Organization(name=req.org_name, country=req.country, timezone=req.timezone)
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=req.email,
        name=req.name,
        password_hash=hash_password(req.password),
        role="FARM_OWNER",
        language="en",
    )
    db.add(user)
    await db.flush()

    farm = Farm(
        org_id=org.id,
        farm_code=_generate_farm_code(req.country, org.id),
        name=req.farm_name,
        country=req.country,
        timezone=req.timezone,
    )
    db.add(farm)
    await db.flush()

    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override="FARM_OWNER"))

    db.add(FarmConfig(farm_id=farm.id, config_key="FARM_TYPE", config_value=req.farm_type))
    if req.sow_count is not None:
        db.add(FarmConfig(farm_id=farm.id, config_key="SOW_CAPACITY", config_value=str(req.sow_count)))

    await db.flush()  # ensure UserFarm is visible to issue_tokens' farm_ids query
    tokens = await issue_tokens(db, user)

    return OnboardingCompleteResponse(
        org_id=str(org.id),
        farm_id=str(farm.id),
        user_id=str(user.id),
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    try:
        user_id_str = decode_refresh_token(refresh_token)
        user_id = UUID(user_id_str)
    except Exception:
        raise UnauthorizedError("Invalid refresh token")

    token_hash = _hash_token(refresh_token)
    stored = await db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    if not stored:
        raise UnauthorizedError("Refresh token revoked or expired")

    # Rotate: revoke old, issue new
    stored.revoked = True
    await db.flush()

    user = await db.get(User, user_id)
    if not user or not user.active:
        raise UnauthorizedError("User not found")

    return await issue_tokens(db, user)


async def logout(db: AsyncSession, refresh_token: str) -> None:
    token_hash = _hash_token(refresh_token)
    stored = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if stored:
        stored.revoked = True
        await db.commit()


# ── 비밀번호 재설정 (PASSWORD_RESET_DRAFT.md 구현, 2026-06-26) ─────────────────
logger = logging.getLogger("pigos.auth.reset")
RESET_TTL = timedelta(minutes=30)


def _hash_reset_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def _deliver_reset_token(email: str, raw: str) -> None:
    """토큰 전달 — 현재는 로그(운영자 중개 임시). TODO: SMTP/SES/SMS로 교체.
    운영(production)에선 raw 토큰을 평문 로그에 남기지 않는다(운영자 콘솔/메일 채널 필요)."""
    if settings.is_production:
        logger.warning("[PASSWORD-RESET] 토큰 발급(%s) — 전달 채널 미설정(운영자 조치 필요)", email)
    else:
        logger.warning("[PASSWORD-RESET][dev] %s 토큰=%s (TTL 30분, 1회용)", email, raw)


async def request_password_reset(db: AsyncSession, email: str) -> str | None:
    """유저 존재·active면 1회용 토큰 생성·반환(라우터가 전달). 없으면 None. 라우터는 항상 204(열거 방지).
    반환된 raw 토큰은 라우터의 _deliver_reset_token으로만 전달 — 응답엔 절대 노출 안 함."""
    user = await db.scalar(select(User).where(User.email == email, User.active.is_(True)))
    if not user:
        return None
    raw = secrets.token_urlsafe(32)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_reset_token(raw),
        expires_at=datetime.now(UTC) + RESET_TTL,
    ))
    await db.flush()
    return raw


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    """토큰 검증(해시·미만료·미사용) → 비번 갱신 + 토큰 소진 + 해당 유저 refresh 전부 폐기."""
    prt = await db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash_reset_token(token))
    )
    now = datetime.now(UTC)
    if not prt or prt.used_at is not None or prt.expires_at < now:
        raise ValidationError("토큰이 유효하지 않거나 만료되었습니다.")
    user = await db.get(User, prt.user_id)
    if not user:
        raise ValidationError("토큰이 유효하지 않습니다.")
    user.password_hash = hash_password(new_password)
    prt.used_at = now
    # 같은 유저의 다른 미사용 reset 토큰 무효 + refresh 토큰 전부 삭제(강제 재로그인)
    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.flush()
