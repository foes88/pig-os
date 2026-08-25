"""계정 삭제(탈퇴) — Apple Guideline 5.1.1(v) 대응.

iOS 1.0 심사가 `DELETE /api/v1/auth/me` 하나로 막혀 있었다. 앱에서 계정을 만들 수 있으면
앱에서 삭제도 가능해야 하고, 고객센터 문의 방식은 인정되지 않는다.

★ 이 파일이 잠그는 계약 네 가지
  1) 삭제 후 **로그인이 실제로 불가능**하다 (플래그만 세우고 끝나면 안 된다)
  2) 개인식별정보가 남지 않는다 (이메일·아이디·이름·연락처)
  3) **같은 이메일로 재가입할 수 있다** — unique 제약이 풀려야 한다
  4) **타인의 데이터가 삭제되지 않는다** — 다른 구성원이 있는 농장은 건드리지 않는다

구현 근거(익명화를 택한 이유·농장 비활성화)는 app/services/account_deletion_service.py.
"""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError, ValidationError
from app.db.models.platform import Farm, RefreshToken, User, UserFarm
from app.schemas.auth import RegisterRequest
from app.services import account_deletion_service, auth_service

pytestmark = pytest.mark.anyio

PW = "Test1234!"


def _reg(username="owner1", email="owner1@pigos.io", org="Owner Farm"):
    return RegisterRequest(name="Kim", username=username, email=email, password=PW,
                           org_name=org, country="KR")


async def _register(db, **kw) -> User:
    user, _ = await auth_service.register(db, _reg(**kw))
    await db.flush()
    return user


async def _make_farm(db, user: User, name="Test Farm", role="FARM_OWNER") -> Farm:
    """가입은 조직만 만든다 — 농장은 온보딩 단계라 테스트에서 직접 만든다."""
    farm = Farm(org_id=user.org_id, farm_code=f"F-{uuid.uuid4().hex[:8]}", name=name,
                country="KR", timezone="Asia/Seoul")
    db.add(farm)
    await db.flush()
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override=role))
    await db.flush()
    return farm


# ── 재인증 ────────────────────────────────────────────────────────────────────

async def test_wrong_password_is_rejected(db: AsyncSession):
    """★ 방치된 세션·탈취 토큰만으로 실행되면 안 된다."""
    user = await _register(db)
    with pytest.raises(ForbiddenError):
        await account_deletion_service.delete_account(db, user, "not-my-password")
    assert user.active is True, "실패한 삭제가 계정 상태를 바꾸면 안 된다"
    assert user.email == "owner1@pigos.io"


async def test_empty_password_is_rejected(db: AsyncSession):
    user = await _register(db)
    with pytest.raises(ValidationError):
        await account_deletion_service.delete_account(db, user, "")


# ── 삭제 결과 ─────────────────────────────────────────────────────────────────

async def test_login_is_impossible_after_deletion(db: AsyncSession):
    """★ 계약의 핵심 — 삭제 후 실제로 못 들어온다."""
    user = await _register(db)
    await account_deletion_service.delete_account(db, user, PW)
    await db.flush()

    with pytest.raises(UnauthorizedError):
        await auth_service.authenticate(db, "owner1", PW)


async def test_identifying_fields_are_purged(db: AsyncSession):
    """이메일·아이디·이름·연락처가 남지 않는다."""
    user = await _register(db)
    original_email, original_username = user.email, user.username

    await account_deletion_service.delete_account(db, user, PW)
    await db.flush()

    assert user.email != original_email and original_email not in user.email
    assert user.username != original_username and original_username not in user.username
    assert user.name == "(deleted user)"
    assert user.phone is None
    assert user.active is False
    assert user.org_id is None


async def test_same_email_can_register_again(db: AsyncSession):
    """★ 익명화를 택한 이유 중 하나 — 재가입 경로가 막히면 안 된다.

    users.email 이 unique NOT NULL 이라, 자리표시값으로 치환하지 않으면 같은 사람이
    다시 가입할 수 없다."""
    user = await _register(db)
    await account_deletion_service.delete_account(db, user, PW)
    await db.flush()

    again = await _register(db)          # 같은 username·email
    assert again.id != user.id
    assert again.email == "owner1@pigos.io"


async def test_sessions_and_memberships_are_removed(db: AsyncSession):
    """세션·농장 멤버십이 실제로 지워진다 — 남으면 접근 경로가 남는다."""
    user = await _register(db)
    await db.flush()

    await account_deletion_service.delete_account(db, user, PW)
    await db.flush()

    assert (await db.scalars(
        select(RefreshToken).where(RefreshToken.user_id == user.id))).all() == []
    assert (await db.scalars(
        select(UserFarm).where(UserFarm.user_id == user.id))).all() == []


# ── 농장 처리 ─────────────────────────────────────────────────────────────────

async def test_solo_owned_farm_is_deactivated_not_deleted(db: AsyncSession):
    """단독 소유 농장은 비활성화된다 — 가축 생산기록을 되돌릴 수 없게 지우지 않는다."""
    user = await _register(db)
    farm = await _make_farm(db, user)

    result = await account_deletion_service.delete_account(db, user, PW)
    await db.flush()

    assert str(farm.id) in result.deactivated_farms
    assert await db.get(Farm, farm.id) is not None, "농장 행이 삭제되면 안 된다(생산기록 보존)"
    assert farm.active is False


async def test_shared_farm_is_left_untouched(db: AsyncSession):
    """★ 타인의 데이터는 지우지 않는다 — 다른 구성원이 있으면 농장을 건드리지 않는다."""
    owner = await _register(db)
    other = await _register(db, username="worker1", email="worker1@pigos.io", org="Other Org")
    farm = await _make_farm(db, owner, name="Shared Farm")
    db.add(UserFarm(user_id=other.id, farm_id=farm.id, role_override="FARM_WORKER"))
    await db.flush()

    result = await account_deletion_service.delete_account(db, owner, PW)
    await db.flush()

    assert farm.active is True, "다른 구성원이 있는 농장은 비활성화하면 안 된다"
    assert str(farm.id) not in result.deactivated_farms
    assert result.purged["shared_farms_kept"] >= 1
    # 남은 구성원의 멤버십은 그대로여야 한다
    assert (await db.scalars(select(UserFarm).where(
        UserFarm.user_id == other.id, UserFarm.farm_id == farm.id))).all()


async def test_worker_only_account_does_not_deactivate_the_farm(db: AsyncSession):
    """★ 소유자가 아닌 사용자가 탈퇴해도 농장은 그대로다 — 멤버십만 빠진다."""
    owner = await _register(db)
    worker = await _register(db, username="worker2", email="worker2@pigos.io", org="W Org")
    farm = await _make_farm(db, owner, name="Owner Farm")
    db.add(UserFarm(user_id=worker.id, farm_id=farm.id, role_override="FARM_WORKER"))
    await db.flush()

    result = await account_deletion_service.delete_account(db, worker, PW)
    await db.flush()

    assert result.deactivated_farms == []
    assert farm.active is True
