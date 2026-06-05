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


def is_org_admin(user: User) -> bool:
    return effective_system_role(user) in ORG_LEVEL_ROLES


def is_write_allowed(user: User) -> bool:
    return effective_system_role(user) in WRITE_ROLES
