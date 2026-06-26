from fastapi import APIRouter
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbDep
from app.db.models.platform import UserFarm
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(body: RegisterRequest, db: DbDep):
    """
    Create organization + user account. Returns tokens immediately.
    Next step: POST /onboarding/complete
    """
    user, org = await auth_service.register(db, body)
    return await auth_service.issue_tokens(db, user)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: DbDep):
    user = await auth_service.authenticate(db, body.username, body.password)
    return await auth_service.issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbDep):
    return await auth_service.refresh_tokens(db, body.refresh_token)


@router.post("/logout", status_code=204)
async def logout(body: RefreshRequest, db: DbDep):
    await auth_service.logout(db, body.refresh_token)


@router.post("/password-reset/request", status_code=204)
async def password_reset_request(body: PasswordResetRequest, db: DbDep):
    """비밀번호 재설정 요청 — 계정 존재 여부와 무관하게 항상 204(열거 방지). 존재 시 토큰 발급·전달."""
    raw = await auth_service.request_password_reset(db, body.email)
    if raw:
        await auth_service._deliver_reset_token(body.email, raw)  # 응답엔 노출 안 함
    await db.commit()


@router.post("/password-reset/confirm", status_code=204)
async def password_reset_confirm(body: PasswordResetConfirm, db: DbDep):
    """토큰 + 새 비번 → 검증 후 비번 갱신(+ refresh 전부 폐기). 무효/만료 토큰은 400."""
    await auth_service.confirm_password_reset(db, body.token, body.new_password)
    await db.commit()


@router.get("/me", response_model=MeResponse)
async def me(current_user: CurrentUser, db: DbDep):
    farm_rows = await db.scalars(
        select(UserFarm).where(UserFarm.user_id == current_user.id)
    )
    return MeResponse(
        id=str(current_user.id),
        name=current_user.name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        org_id=str(current_user.org_id) if current_user.org_id else None,
        language=current_user.language,
        farm_ids=[str(uf.farm_id) for uf in farm_rows],
    )
