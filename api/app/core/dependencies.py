"""
FastAPI dependency injection layer.

Dependency hierarchy:
  get_db          → raw async DB session
  get_current_user → verify JWT, load User row
  get_farm_context → validate user ↔ farm membership, return Farm row
  require_addon    → verify farm has active Addon subscription (factory)
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AddonNotSubscribedError, ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.core.permissions import can_access_farm, effective_system_role
from app.db.session import AsyncSessionLocal
from app.db.models.platform import AddonSubscription, Farm, User, UserFarm

_bearer = HTTPBearer()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise UnauthorizedError("Invalid or expired token")

    user = await db.get(User, user_id)
    if not user or not user.active:
        raise UnauthorizedError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_farm_context(
    farm_id: Annotated[UUID, Path(description="Farm UUID")],
    db: DbDep,
    current_user: CurrentUser,
) -> Farm:
    """
    Validates that the current user has access to the requested farm.
    ADMIN role can access any farm. Others must be in user_farms.
    """
    farm = await db.get(Farm, farm_id)
    if not farm or not farm.active:
        raise ForbiddenError("Farm not found or inactive")

    role = effective_system_role(current_user)

    # SUPER_ADMIN은 모든 농장 접근
    if role == "SUPER_ADMIN":
        return farm

    # ORG 레벨 롤(VENDOR/DISTRIBUTOR/DEALER_ADMIN): 트리 기반 접근
    # FARM 레벨 롤: user_farms 기반 접근
    if not await can_access_farm(current_user, farm_id, db):
        raise ForbiddenError("No access to this farm")

    return farm


FarmDep = Annotated[Farm, Depends(get_farm_context)]


def require_addon(addon_code: str):
    """
    Dependency factory. Injects after get_farm_context.
    Raises AddonNotSubscribedError (HTTP 402) if not subscribed.

    Usage:
        @router.get("/analysis", dependencies=[Depends(require_addon("ADDON_FCR"))])
    """
    async def _check(
        farm: FarmDep,
        db: DbDep,
    ) -> None:
        result = await db.execute(
            select(AddonSubscription).where(
                AddonSubscription.farm_id == farm.id,
                AddonSubscription.addon_code == addon_code,
                AddonSubscription.is_active.is_(True),
            )
        )
        if not result.scalar_one_or_none():
            raise AddonNotSubscribedError(addon_code)

    return Depends(_check)


def require_role(*roles: str):
    """Guard that ensures current user has one of the specified roles."""
    async def _check(current_user: CurrentUser) -> None:
        if current_user.role not in roles:
            raise ForbiddenError(f"Required role: {' or '.join(roles)}")
    return Depends(_check)
