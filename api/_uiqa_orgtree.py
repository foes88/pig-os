"""업체/총판(조직계층) 스코핑 테스트용 셋업 — Vendor→Distributor→Dealer 트리 + org-admin + 농장.
QA 셋업(UIQA 접두어). ORM 사용(마이그레이션 후 username 컬럼 존재). 결과 ID를 JSON으로 출력.
실행: api/.venv python _uiqa_orgtree.py
"""
import asyncio
import json
import os
import uuid

from app.core.security import hash_password
from app.db.models.platform import Farm, Organization, User, UserFarm  # noqa: F401
from app.db.session import AsyncSessionLocal

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "..", "pigos-android", "scripts", "overnight", "results", "uiqa_orgtree.json")


async def main():
    sfx = uuid.uuid4().hex[:6]
    h = hash_password("123123")
    async with AsyncSessionLocal() as db:
        # 계층: VENDOR(0) → DISTRIBUTOR(1) → DEALER(2)
        v = Organization(name=f"UIQA Vendor {sfx}", org_type="VENDOR", org_level=0,
                         parent_org_id=None, country="KR", timezone="Asia/Seoul")
        db.add(v); await db.flush()
        d = Organization(name=f"UIQA Dist {sfx}", org_type="DISTRIBUTOR", org_level=1,
                         parent_org_id=v.id, country="KR", timezone="Asia/Seoul")
        db.add(d); await db.flush()
        e = Organization(name=f"UIQA Dealer {sfx}", org_type="DEALER", org_level=2,
                         parent_org_id=d.id, country="KR", timezone="Asia/Seoul")
        db.add(e); await db.flush()

        # 농장: org 레벨마다 1개
        fv = Farm(org_id=v.id, farm_code=f"UIQA-V-{sfx}", name="Vendor Farm", country="KR", timezone="Asia/Seoul")
        fd = Farm(org_id=d.id, farm_code=f"UIQA-D-{sfx}", name="Dist Farm", country="KR", timezone="Asia/Seoul")
        fe = Farm(org_id=e.id, farm_code=f"UIQA-E-{sfx}", name="Dealer Farm", country="KR", timezone="Asia/Seoul")
        db.add_all([fv, fd, fe]); await db.flush()

        # org-admin (system_role = 조직레벨 역할, org_id 연결)
        va = User(org_id=v.id, username=f"uiqa_vendor_{sfx}", email=f"uiqa_vendor_{sfx}@pigos.io",
                  name="Vendor Admin", password_hash=h, role="VENDOR_ADMIN", system_role="VENDOR_ADMIN")
        da = User(org_id=d.id, username=f"uiqa_dist_{sfx}", email=f"uiqa_dist_{sfx}@pigos.io",
                  name="Dist Admin", password_hash=h, role="DISTRIBUTOR_ADMIN", system_role="DISTRIBUTOR_ADMIN")
        ea = User(org_id=e.id, username=f"uiqa_dealer_{sfx}", email=f"uiqa_dealer_{sfx}@pigos.io",
                  name="Dealer Admin", password_hash=h, role="DEALER_ADMIN", system_role="DEALER_ADMIN")
        db.add_all([va, da, ea]); await db.commit()

        data = {
            "sfx": sfx,
            "vendor": {"user": va.username, "org": str(v.id), "farm": str(fv.id)},
            "dist": {"user": da.username, "org": str(d.id), "farm": str(fd.id)},
            "dealer": {"user": ea.username, "org": str(e.id), "farm": str(fe.id)},
        }
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("saved:", os.path.normpath(OUT))


asyncio.run(main())
