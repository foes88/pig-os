#!/usr/bin/env python
"""
파일럿 후속 Phase A — 조직 계층 + 멀티팜 계정 구성 (멱등).

계층: VENDOR "피그플랜 시범사업단"
        ├ DEALER "동부지사" → 농장 2807, 4448
        └ DEALER "서부지사" → 농장 848, 978
계정: vendor_admin(4농장) · dealer_east(2) · dealer_west(2) · owner_*(각1)
      → RBAC 서브트리(get_accessible_farm_ids) 검증용.

전제: import_pigplan.py로 4농장 적재 완료. 로컬 Docker pigos DB.
실행: cd api && uv run python -m scripts.setup_pilot_orgs
필수 env: PIGPLAN_PILOT_PASSWORD
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.platform import Farm, Organization, User, UserFarm
from app.db.session import AsyncSessionLocal
from scripts.pilot_common import (
    ACCOUNTS,
    FARM_ORG,
    ORG_SPECS,
    PILOT_PASSWORD_ENV,
    farm_uuid,
    get_pilot_password,
    user_uuid,
)


async def main():
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    async with AsyncSessionLocal() as db:
        # 1) 조직 계층 (멱등)
        for oid, otype, name, parent, level in ORG_SPECS:
            o = await db.get(Organization, oid)
            if not o:
                db.add(Organization(id=oid, name=name, org_type=otype, parent_org_id=parent,
                                    org_level=level, country="KR", timezone="Asia/Seoul"))
            else:
                o.org_type, o.name, o.parent_org_id, o.org_level = otype, name, parent, level
        await db.flush()

        # 2) 농장 → DEALER 재배정 (2농장씩)
        reassigned = 0
        for fn, org in FARM_ORG.items():
            farm = await db.get(Farm, farm_uuid(fn))
            if farm and farm.org_id != org:
                farm.org_id = org
                reassigned += 1
        await db.flush()

        # 3) 계정 + 멤버십 (멱등)
        pw = hash_password(get_pilot_password())
        made = []
        for account in ACCOUNTS:
            uid = user_uuid(account.uuid_tag)
            u = await db.get(User, uid)
            if not u:
                u = User(id=uid, org_id=account.org_id, username=account.username,
                         email=f"{account.username}@pilot.local",
                         name=account.username, password_hash=pw, role="FARM_OWNER",
                         system_role=account.system_role, language="ko")
                db.add(u)
                made.append(account.username)
            else:
                u.org_id = account.org_id
                u.system_role = account.system_role
                u.password_hash = pw
            await db.flush()
            # FARM_OWNER는 user_farms 멤버십 필요(비-admin은 서브트리 아닌 멤버십으로 접근)
            if account.farm_no is not None:
                exists = await db.scalar(select(UserFarm).where(
                    UserFarm.user_id == uid, UserFarm.farm_id == farm_uuid(account.farm_no)))
                if not exists:
                    db.add(UserFarm(user_id=uid, farm_id=farm_uuid(account.farm_no),
                                    role_override="FARM_OWNER"))
        await db.commit()

        print("=== Phase A 완료 ===")
        print(f"조직 3개(VENDOR→DEALER×2), 농장 재배정 {reassigned}, 신규계정 {len(made)}")
        print(f"계정({len(ACCOUNTS)}) 초기비번: ${PILOT_PASSWORD_ENV}")
        for account in ACCOUNTS:
            scope = "4농장(서브트리)" if account.system_role == "VENDOR_ADMIN" else (
                "2농장(서브트리)" if account.system_role == "DEALER_ADMIN" else f"농장 {account.farm_no}"
            )
            print(f"  {account.username:14s} {account.system_role:14s} → {scope}")


if __name__ == "__main__":
    asyncio.run(main())
