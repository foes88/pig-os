"""Permission helpers for farm and organization access."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.platform import User

ORG_LEVEL_ROLES = {
    "SUPER_ADMIN",
    "VENDOR_ADMIN",
    "DISTRIBUTOR_ADMIN",
    "DEALER_ADMIN",
}

FARM_LEVEL_ROLES = {
    "FARM_OWNER",
    "FARM_MANAGER",
    "FARM_WORKER",
    "VET",
    "VIEWER",
    "API_CLIENT",
}

_KNOWN_ROLES = ORG_LEVEL_ROLES | FARM_LEVEL_ROLES

WRITE_ROLES = {
    "SUPER_ADMIN",
    "VENDOR_ADMIN",
    "DISTRIBUTOR_ADMIN",
    "DEALER_ADMIN",
    "FARM_OWNER",
    "FARM_MANAGER",
    "FARM_WORKER",
}

READ_ONLY_ROLES = {"VET", "VIEWER", "API_CLIENT"}
MAX_ORG_TREE_DEPTH = 8

LEGACY_SYSTEM_ROLE_MAP = {
    "ADMIN": "SUPER_ADMIN",
    "COMPANY": "VENDOR_ADMIN",
}

ORG_TREE_CTE = """
    WITH RECURSIVE org_tree(id, path, depth) AS (
        SELECT id, ARRAY[id], 0
        FROM organizations
        WHERE id = :root_org_id
        UNION ALL
        SELECT o.id, ot.path || o.id, ot.depth + 1
        FROM organizations o
        INNER JOIN org_tree ot ON o.parent_org_id = ot.id
        WHERE o.id <> ALL(ot.path)
          AND ot.depth < :max_depth
    )
"""


def effective_system_role(user: User) -> str:
    """Return the explicit system role, or map legacy roles safely.

    Unrecognized values fail-safe to FARM_OWNER; always returns from _KNOWN_ROLES.
    """
    system_role = (user.system_role or "").strip()
    if system_role:
        return system_role if system_role in _KNOWN_ROLES else "FARM_OWNER"

    legacy_role = (user.role or "").strip()
    mapped = LEGACY_SYSTEM_ROLE_MAP.get(legacy_role, legacy_role or "FARM_OWNER")
    return mapped if mapped in _KNOWN_ROLES else "FARM_OWNER"


async def get_accessible_org_ids(user: User, db: AsyncSession) -> set[UUID]:
    """Return organization ids visible to this user."""
    role = effective_system_role(user)

    if role == "SUPER_ADMIN":
        result = await db.execute(text("SELECT id FROM organizations"))
        return {row[0] for row in result.fetchall()}

    if role not in ORG_LEVEL_ROLES or user.org_id is None:
        return set()

    result = await db.execute(
        text(f"""
            {ORG_TREE_CTE}
            SELECT id FROM org_tree
        """),
        {"root_org_id": user.org_id, "max_depth": MAX_ORG_TREE_DEPTH},
    )
    return {row[0] for row in result.fetchall()}


async def get_accessible_farm_ids(user: User, db: AsyncSession) -> list[UUID]:
    """Return all active farm ids visible to this user."""
    role = effective_system_role(user)

    if role == "SUPER_ADMIN":
        result = await db.execute(text("SELECT id FROM farms WHERE active = TRUE"))
        return [row[0] for row in result.fetchall()]

    if role in ("VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN"):
        if user.org_id is None:
            return []
        result = await db.execute(
            text(f"""
                {ORG_TREE_CTE}
                SELECT f.id
                FROM farms f
                INNER JOIN org_tree ot ON f.org_id = ot.id
                WHERE f.active = TRUE
            """),
            {"root_org_id": user.org_id, "max_depth": MAX_ORG_TREE_DEPTH},
        )
        return [row[0] for row in result.fetchall()]

    result = await db.execute(
        text("""
            SELECT uf.farm_id
            FROM user_farms uf
            INNER JOIN farms f ON f.id = uf.farm_id
            WHERE uf.user_id = :uid
              AND f.active = TRUE
        """),
        {"uid": user.id},
    )
    return [row[0] for row in result.fetchall()]


async def can_access_farm(user: User, farm_id: UUID, db: AsyncSession) -> bool:
    """Return whether the user can access a specific active farm."""
    role = effective_system_role(user)

    if role == "SUPER_ADMIN":
        result = await db.execute(
            text(
                "SELECT EXISTS("
                "SELECT 1 FROM farms WHERE id = :farm_id AND active = TRUE)"
            ),
            {"farm_id": farm_id},
        )
        return bool(result.scalar())

    if role in ("VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN"):
        if user.org_id is None:
            return False
        result = await db.execute(
            text(f"""
                {ORG_TREE_CTE}
                SELECT EXISTS(
                    SELECT 1
                    FROM farms f
                    INNER JOIN org_tree ot ON f.org_id = ot.id
                    WHERE f.id = :farm_id
                      AND f.active = TRUE
                )
            """),
            {
                "root_org_id": user.org_id,
                "farm_id": farm_id,
                "max_depth": MAX_ORG_TREE_DEPTH,
            },
        )
        return bool(result.scalar())

    result = await db.execute(
        text("""
            SELECT EXISTS(
                SELECT 1
                FROM user_farms uf
                INNER JOIN farms f ON f.id = uf.farm_id
                WHERE uf.user_id = :uid
                  AND uf.farm_id = :farm_id
                  AND f.active = TRUE
            )
        """),
        {"uid": user.id, "farm_id": farm_id},
    )
    return bool(result.scalar())


async def effective_farm_role(user: User, farm_id: UUID, db: AsyncSession) -> str | None:
    """농장별 유효 역할 (멀티팜 안전).

    - SUPER_ADMIN / 조직레벨 롤(VENDOR/DISTRIBUTOR/DEALER_ADMIN): 시스템 롤 그대로.
    - 그 외(농장레벨 사용자): 해당 농장의 user_farms.role_override 사용.
      멤버십이 없으면 None(권한 없음). role_override가 NULL이면 시스템 롤로 폴백(하위호환).

    전역 user.system_role만 보던 require_role의 멀티팜 역할 혼선(finding #2)을 해소한다.
    """
    sys_role = effective_system_role(user)
    if sys_role == "SUPER_ADMIN":
        return sys_role
    if sys_role in ORG_LEVEL_ROLES:
        # F1: 조직롤(총판/대리점/업체)은 '자기 org 서브트리' 농장에만 권한.
        # 과거엔 farm_id 무관하게 sys_role을 반환(타 조직 농장 접근 가능, FarmDep에만 의존).
        # 헬퍼 자체에서 서브트리를 강제해 require_farm_role 단독 사용 시에도 안전.
        return sys_role if await can_access_farm(user, farm_id, db) else None
    result = await db.execute(
        text(
            "SELECT role_override FROM user_farms "
            "WHERE user_id = :uid AND farm_id = :fid"
        ),
        {"uid": user.id, "fid": farm_id},
    )
    rows = result.fetchall()
    if not rows:
        return None  # 멤버십 없음 → 권한 없음 (FarmDep도 별도 차단)
    return rows[0][0] or sys_role  # role_override 우선, NULL이면 시스템 롤 폴백


async def get_farm_access(
    user: User, db: AsyncSession
) -> tuple[list[str], dict[str, str]]:
    """farm 앱용 (접근 가능 농장ID 목록, 농장별 유효 role 맵).

    - SUPER_ADMIN: ([], {}) — 전 농장 동일 권한 + 관리자 콘솔 사용. 전 농장 ID를
      토큰/응답에 싣지 않는다(페이로드 비대화 방지). 프론트는 전역 role로 폴백.
    - 조직레벨(VENDOR/DISTRIBUTOR/DEALER_ADMIN): org 서브트리 농장 전체 → 동일 sys_role.
      (총판/대리점이 하위 농장을 모두 전환·관리)
    - 농장레벨: user_farms 멤버십 농장 → role_override(없으면 sys_role).

    멀티팜에서 프론트 게이팅이 '활성 농장 기준 역할'로 판정하도록 farm_roles를 제공한다.
    """
    sys_role = effective_system_role(user)
    if sys_role == "SUPER_ADMIN":
        return [], {}
    accessible = await get_accessible_farm_ids(user, db)
    if not accessible:
        return [], {}
    ids = [str(f) for f in accessible]
    if sys_role in ORG_LEVEL_ROLES:
        return ids, {i: sys_role for i in ids}
    rows = await db.execute(
        text("SELECT farm_id, role_override FROM user_farms WHERE user_id = :uid"),
        {"uid": user.id},
    )
    override = {str(r[0]): r[1] for r in rows.fetchall()}
    return ids, {i: (override.get(i) or sys_role) for i in ids}


def is_org_admin(user: User) -> bool:
    return effective_system_role(user) in ORG_LEVEL_ROLES


def is_write_allowed(user: User) -> bool:
    return effective_system_role(user) in WRITE_ROLES
