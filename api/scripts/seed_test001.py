"""계약 테스트 계정 시드: test001@pigos.io / 123123 (FARM_OWNER).
API onboarding/complete는 password min 8자라 6자 계약 비번을 못 받음 → DB 직접 시드.
실행: cd api; uv run python scripts/seed_test001.py
"""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.config import FarmConfig
from app.db.models.platform import Farm, Organization, User, UserFarm
from app.db.session import AsyncSessionLocal
from app.services.farm_service import _generate_farm_code

EMAIL = "test001@pigos.io"
PASSWORD = "123123"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == EMAIL))
        if existing:
            print(f"이미 존재: {EMAIL} (user_id={existing.id})")
            return

        org = Organization(name="Test Org", country="KR", timezone="Asia/Seoul")
        db.add(org)
        await db.flush()

        user = User(
            org_id=org.id,
            username="test001",
            email=EMAIL,
            name="Test Owner",
            password_hash=hash_password(PASSWORD),
            role="FARM_OWNER",
            language="en",
        )
        db.add(user)
        await db.flush()

        farm = Farm(
            org_id=org.id,
            farm_code=_generate_farm_code("KR", org.id),
            name="Test Farm",
            country="KR",
            timezone="Asia/Seoul",
        )
        db.add(farm)
        await db.flush()

        db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override="FARM_OWNER"))
        db.add(FarmConfig(farm_id=farm.id, config_key="FARM_TYPE", config_value="FARROW_TO_FINISH"))
        await db.commit()
        print(f"시드 완료: {EMAIL} / {PASSWORD}  farm_id={farm.id}")


if __name__ == "__main__":
    asyncio.run(main())
