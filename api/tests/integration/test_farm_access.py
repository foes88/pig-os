"""B1 — get_farm_access: 멀티팜 접근 농장 + 농장별 role 맵.

프론트 게이팅이 '활성 농장 기준 역할'로 판정하도록 로그인/me가 farm_roles를 제공.
"""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import get_farm_access
from app.db.models.platform import Farm, Organization, User, UserFarm

pytestmark = pytest.mark.anyio


async def test_farm_level_role_override(
    db: AsyncSession, test_farm: Farm, test_user: User
):
    """농장레벨 사용자: 멤버십 농장 → role_override 반영."""
    db.add(UserFarm(user_id=test_user.id, farm_id=test_farm.id, role_override="FARM_MANAGER"))
    await db.flush()
    ids, roles = await get_farm_access(test_user, db)
    assert str(test_farm.id) in ids
    assert roles[str(test_farm.id)] == "FARM_MANAGER"


async def test_no_membership_no_access(db: AsyncSession, test_farm: Farm, test_user: User):
    """멤버십 없으면 접근 농장 0 (role 맵도 비어 있음)."""
    ids, roles = await get_farm_access(test_user, db)
    assert ids == [] and roles == {}


async def test_super_admin_returns_empty(db: AsyncSession, test_org: Organization):
    """SUPER_ADMIN은 전 농장 동일권한 → 페이로드 비대화 방지로 빈 값(프론트 전역 role 폴백)."""
    from app.core.security import hash_password
    admin = User(
        org_id=test_org.id, username=f"sa_{uuid.uuid4().hex[:6]}",
        email=f"sa-{uuid.uuid4().hex[:6]}@pigos.io", name="SA",
        password_hash=hash_password("Test1234!"), role="SUPER_ADMIN",
        system_role="SUPER_ADMIN",
    )
    db.add(admin)
    await db.flush()
    ids, roles = await get_farm_access(admin, db)
    assert ids == [] and roles == {}


async def test_distributor_sees_subtree_farms(db: AsyncSession, test_org: Organization):
    """조직레벨(DISTRIBUTOR_ADMIN): org 서브트리 농장 전체를 동일 sys_role로 접근."""
    from app.core.security import hash_password
    child = Organization(name="Child Farm Co", country="KR", timezone="Asia/Seoul",
                         parent_org_id=test_org.id)
    db.add(child)
    await db.flush()
    farm = Farm(org_id=child.id, farm_code=f"SUB-{uuid.uuid4().hex[:5].upper()}",
                name="Sub Farm", country="KR", timezone="Asia/Seoul")
    db.add(farm)
    dist = User(org_id=test_org.id, username=f"dist_{uuid.uuid4().hex[:6]}",
                email=f"dist-{uuid.uuid4().hex[:6]}@pigos.io", name="Distributor",
                password_hash=hash_password("Test1234!"), role="DISTRIBUTOR_ADMIN",
                system_role="DISTRIBUTOR_ADMIN")
    db.add(dist)
    await db.flush()
    ids, roles = await get_farm_access(dist, db)
    assert str(farm.id) in ids
    assert roles[str(farm.id)] == "DISTRIBUTOR_ADMIN"
