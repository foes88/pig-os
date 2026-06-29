"""
username 기반 로그인 검증 (email→username 전환).
- username 로그인 성공 / email로는 로그인 불가
- username 중복 가입 실패 / email 중복 가입 실패
- password reset은 여전히 email 기준
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.schemas.auth import RegisterRequest
from app.services import auth_service

pytestmark = pytest.mark.anyio


def _reg(username="farmer1", email="farmer1@pigos.io"):
    return RegisterRequest(name="Kim", username=username, email=email, password="Test1234!",
                           org_name="Kim Farm", country="KR")


async def test_username_login_success(db: AsyncSession):
    user, _ = await auth_service.register(db, _reg())
    got = await auth_service.authenticate(db, "farmer1", "Test1234!")
    assert got.id == user.id and got.username == "farmer1"


async def test_email_is_not_login_id(db: AsyncSession):
    """email로는 로그인 불가(username 인증)."""
    await auth_service.register(db, _reg())
    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate(db, "farmer1@pigos.io", "Test1234!")


async def test_wrong_password_fails(db: AsyncSession):
    await auth_service.register(db, _reg())
    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate(db, "farmer1", "wrong")


async def test_duplicate_username_rejected(db: AsyncSession):
    await auth_service.register(db, _reg(username="dup", email="a@pigos.io"))
    with pytest.raises(ConflictError):
        await auth_service.register(db, _reg(username="dup", email="b@pigos.io"))


async def test_duplicate_email_rejected(db: AsyncSession):
    await auth_service.register(db, _reg(username="user1", email="same@pigos.io"))
    with pytest.raises(ConflictError):
        await auth_service.register(db, _reg(username="user2", email="same@pigos.io"))


async def test_username_case_insensitive_login(db: AsyncSession):
    """H3: 대문자/공백 섞어 가입해도 소문자로 정규화 → 어떤 케이스로도 로그인."""
    user, _ = await auth_service.register(db, _reg(username="Farmer1", email="c@pigos.io"))
    assert user.username == "farmer1"  # 저장 시 정규화
    # 입력 케이스 무관 로그인
    for attempt in ("farmer1", "FARMER1", "  Farmer1  "):
        got = await auth_service.authenticate(db, attempt, "Test1234!")
        assert got.id == user.id


async def test_username_case_insensitive_duplicate(db: AsyncSession):
    """H3: 'Admin'과 'admin'은 같은 계정 — 대소문자만 다른 중복 차단."""
    await auth_service.register(db, _reg(username="Owner", email="d@pigos.io"))
    with pytest.raises(ConflictError):
        await auth_service.register(db, _reg(username="owner", email="e@pigos.io"))


def test_login_schema_requires_username():
    """LoginRequest는 username 기반(email EmailStr 강제 제거)."""
    from app.schemas.auth import LoginRequest
    lr = LoginRequest(username="admin", password="x")
    assert lr.username == "admin"
    # email 필드는 더이상 LoginRequest에 없다
    assert "email" not in LoginRequest.model_fields


def test_register_requires_username():
    """RegisterRequest에 username 필수 + email도 필수."""
    from app.schemas.auth import RegisterRequest as RR
    assert "username" in RR.model_fields and "email" in RR.model_fields
    with pytest.raises(Exception):
        RR(name="x", email="x@pigos.io", password="Test1234!", org_name="o", country="KR")  # username 누락
