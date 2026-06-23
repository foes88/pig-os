"""데모 조직 트리 시드 — 운영자 콘솔 /admin/orgs 드릴다운 확인용.

업체(VENDOR) → 총판(DISTRIBUTOR) → 대리점(DEALER) → 농장 체인 1벌 생성(멱등).
실행: cd api; PYTHONPATH=. uv run python scripts/seed_demo_org_tree.py
"""
import asyncio
import uuid

from sqlalchemy import select

from app.db.models.platform import Farm, Organization
from app.db.session import AsyncSessionLocal

VENDOR = "데모 사료(주) [업체]"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        if await db.scalar(select(Organization).where(Organization.name == VENDOR)):
            print("이미 존재:", VENDOR)
            return

        vendor = Organization(name=VENDOR, org_type="VENDOR", org_level=0, country="KR", timezone="Asia/Seoul")
        db.add(vendor); await db.flush()
        dist = Organization(name="서울총판 [총판]", org_type="DISTRIBUTOR", org_level=1,
                            parent_org_id=vendor.id, country="KR", timezone="Asia/Seoul")
        db.add(dist); await db.flush()
        dealer = Organization(name="경기대리점 [대리점]", org_type="DEALER", org_level=2,
                             parent_org_id=dist.id, country="KR", timezone="Asia/Seoul")
        db.add(dealer); await db.flush()

        for nm in ("행복농장", "푸른농장"):
            db.add(Farm(org_id=dealer.id, farm_code=f"FARM-KR-{uuid.uuid4().hex[:6].upper()}",
                        name=nm, country="KR", timezone="Asia/Seoul", active=True))
        await db.commit()
        print(f"시드 완료: {VENDOR} → 서울총판 → 경기대리점 → 행복농장·푸른농장")


if __name__ == "__main__":
    asyncio.run(main())
