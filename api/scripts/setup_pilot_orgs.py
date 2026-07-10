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
"""
from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.platform import Farm, Organization, User, UserFarm
from app.db.session import AsyncSessionLocal

PILOT_PW = "Pilot!2026"  # 테스트 전용 초기 비번(문서 기록). 운영 계정 아님.

NS = "a11c0000"
def _farm_uuid(fn: int) -> UUID: return UUID(f"{NS}-0000-0000-0000-{fn:012d}")
def _u(tag: str) -> UUID: return UUID(f"{NS}-0000-0000-00a1-{tag:>012s}".replace(" ", "0"))

VENDOR = UUID(f"{NS}-0000-0000-00b0-000000000001")
DEALER_E = UUID(f"{NS}-0000-0000-00b0-000000000002")
DEALER_W = UUID(f"{NS}-0000-0000-00b0-000000000003")

# (org_id, org_type, name, parent, level)
ORGS = [
    (VENDOR,   "VENDOR",   "피그플랜 시범사업단", None,   0),
    (DEALER_E, "DEALER",   "동부지사",           VENDOR, 2),
    (DEALER_W, "DEALER",   "서부지사",           VENDOR, 2),
]
FARM_ORG = {2807: DEALER_E, 4448: DEALER_E, 848: DEALER_W, 978: DEALER_W}

# (uuid_tag, username, system_role, org_id, farm_no|None)
ACCOUNTS = [
    ("vadmin",  "vendor_admin", "VENDOR_ADMIN", VENDOR,   None),
    ("deast",   "dealer_east",  "DEALER_ADMIN", DEALER_E, None),
    ("dwest",   "dealer_west",  "DEALER_ADMIN", DEALER_W, None),
    ("ow2807",  "owner_2807",   "FARM_OWNER",   DEALER_E, 2807),
    ("ow4448",  "owner_4448",   "FARM_OWNER",   DEALER_E, 4448),
    ("ow848",   "owner_848",    "FARM_OWNER",   DEALER_W, 848),
    ("ow978",   "owner_978",    "FARM_OWNER",   DEALER_W, 978),
]


async def main():
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    async with AsyncSessionLocal() as db:
        # 1) 조직 계층 (멱등)
        for oid, otype, name, parent, level in ORGS:
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
            farm = await db.get(Farm, _farm_uuid(fn))
            if farm and farm.org_id != org:
                farm.org_id = org
                reassigned += 1
        await db.flush()

        # 3) 계정 + 멤버십 (멱등)
        pw = hash_password(PILOT_PW)
        made = []
        for tag, uname, srole, org, fn in ACCOUNTS:
            uid = _u(tag)
            u = await db.get(User, uid)
            if not u:
                u = User(id=uid, org_id=org, username=uname, email=f"{uname}@pilot.local",
                         name=uname, password_hash=pw, role="FARM_OWNER", system_role=srole,
                         language="ko")
                db.add(u)
                made.append(uname)
            else:
                u.org_id, u.system_role = org, srole
            await db.flush()
            # FARM_OWNER는 user_farms 멤버십 필요(비-admin은 서브트리 아닌 멤버십으로 접근)
            if fn is not None:
                exists = await db.scalar(select(UserFarm).where(
                    UserFarm.user_id == uid, UserFarm.farm_id == _farm_uuid(fn)))
                if not exists:
                    db.add(UserFarm(user_id=uid, farm_id=_farm_uuid(fn), role_override="FARM_OWNER"))
        await db.commit()

        print("=== Phase A 완료 ===")
        print(f"조직 3개(VENDOR→DEALER×2), 농장 재배정 {reassigned}, 신규계정 {len(made)}")
        print(f"계정({len(ACCOUNTS)}) 초기비번: {PILOT_PW}")
        for tag, uname, srole, org, fn in ACCOUNTS:
            scope = "4농장(서브트리)" if srole == "VENDOR_ADMIN" else (
                "2농장(서브트리)" if srole == "DEALER_ADMIN" else f"농장 {fn}")
            print(f"  {uname:14s} {srole:14s} → {scope}")


if __name__ == "__main__":
    asyncio.run(main())
