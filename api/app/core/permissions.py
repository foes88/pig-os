"""
PigOS 권한 계층 유틸리티

조직 계층: VENDOR → DISTRIBUTOR → DEALER → INDEPENDENT(농가 직가입)
사용자 시스템 롤:
  SUPER_ADMIN       — 전체 접근 (WiseLake 내부)
  VENDOR_ADMIN      — 자기 Vendor 하위 전체 농가
  DISTRIBUTOR_ADMIN — 자기 Distributor 하위 전체 농가
  DEALER_ADMIN      — 자기 Dealer 소속 농가
  FARM_OWNER        — 자기 농장(들)
  FARM_MANAGER      — 배정된 농장
  FARM_WORKER       — 배정된 농장 (기록 입력 전용)
  VET               — 배정된 농장 (건강 이벤트 전용)
"""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform import Farm, User, UserFarm

# 조직 레벨 롤 (farm_id 없이 상위에서 접근)
ORG_LEVEL_ROLES = {
    "SUPER_ADMIN",
    "VENDOR_ADMIN",
    "DISTRIBUTOR_ADMIN",
    "DEALER_ADMIN",
}

# 농장 레벨 롤 (user_farms 필요)
FARM_LEVEL_ROLES = {
    "FARM_OWNER",
    "FARM_MANAGER",
    "FARM_WORKER",
    "VET",
}

# 쓰기 가능 롤 (기록 추가/수정)
WRITE_ROLES = {
    "SUPER_ADMIN", "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN",
    "FARM_OWNER", "FARM_MANAGER", "FARM_WORKER",
}

# 읽기 전용 롤
READ_ONLY_ROLES = {"VET"}


def effective_system_role(user: User) -> str:
    """system_role이 설정돼 있으면 사용, 아니면 legacy role 사용."""
    return user.system_role if user.system_role else user.role


async def get_accessible_farm_ids(user: User, db: AsyncSession) -> list[UUID]:
    """
    사용자가 접근 가능한 모든 farm_id 목록 반환.

    - SUPER_ADMIN: 전체
    - VENDOR/DISTRIBUTOR/DEALER_ADMIN: 조직 트리 하위 모든 농장 (recursive CTE)
    - FARM_*: user_farms 테이블에 등록된 농장만
    """
    role = effective_system_role(user)

    if role == "SUPER_ADMIN":
        result = await db.execute(
            text("SELECT id FROM farms WHERE active = TRUE")
        )
        return [row[0] for row in result.fetchall()]

    if role in ("VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN"):
        # Recursive CTE: 내 org부터 모든 하위 org의 farm 조회
        result = await db.execute(
            text("""
                WITH RECURSIVE org_tree AS (
                    SELECT id FROM organizations WHERE id = :root_org_id
                    UNION ALL
                    SELECT o.id FROM organizations o
                    INNER JOIN org_tree ot ON o.parent_org_id = ot.id
                )
                SELECT f.id FROM farms f
                INNER JOIN org_tree ot ON f.org_id = ot.id
                WHERE f.active = TRUE
            """),
            {"root_org_id": user.org_id},
        )
        return [row[0] for row in result.fetchall()]

    # FARM_OWNER / FARM_MANAGER / FARM_WORKER / VET → user_farms
    result = await db.execute(
        text("SELECT farm_id FROM user_farms WHERE user_id = :uid"),
        {"uid": user.id},
    )
    return [row[0] for row in result.fetchall()]


async def can_access_farm(user: User, farm_id: UUID, db: AsyncSession) -> bool:
    """특정 farm_id에 접근 가능한지 확인."""
    accessible = await get_accessible_farm_ids(user, db)
    return farm_id in accessible


def is_org_admin(user: User) -> bool:
    return effective_system_role(user) in ORG_LEVEL_ROLES


def is_write_allowed(user: User) -> bool:
    return effective_system_role(user) in WRITE_ROLES
