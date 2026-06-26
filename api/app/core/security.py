from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def _make_token(data: dict, expires_delta: timedelta) -> str:
    # jti(고유 토큰 ID): 같은 유저·같은 초에 발급해도 토큰이 유일 → RefreshToken.token_hash
    # (UNIQUE) 충돌 방지. jti 없으면 동시/연속 로그인·즉시 refresh가 동일 토큰을 만들어
    # IntegrityError 500(P0 refresh·P1 로그인 동시성)의 근인. (2026-06-24 수정)
    payload = {**data, "exp": datetime.now(UTC) + expires_delta, "jti": str(uuid4())}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: UUID, org_id: UUID, roles: list[str]) -> str:
    return _make_token(
        {"sub": str(user_id), "org": str(org_id), "roles": roles, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: UUID) -> str:
    return _make_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_access_token(token: str) -> dict:
    """Returns payload dict or raises JWTError."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload


def decode_refresh_token(token: str) -> str:
    """Returns user_id string or raises JWTError."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    if payload.get("type") != "refresh":
        raise JWTError("Not a refresh token")
    return payload["sub"]
