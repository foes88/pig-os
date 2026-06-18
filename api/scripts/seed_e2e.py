"""전용 E2E 테스트 농장 시드 — 실백엔드 CRUD/UAT 용 격리 계정.

test001(데모/계약)과 분리해 E2E가 데이터를 마음껏 만들어도 다른 데이터 오염 0.
멱등: 이미 있으면 farm_id만 출력. 실행: cd api; PYTHONPATH=. uv run python scripts/seed_e2e.py

크리덴셜(계약·핸드오프·E2E가 공유):
  EMAIL=e2e@pigos.io  PASSWORD=e2e!2026pw  country=KR
"""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.config import FarmConfig
from app.db.models.platform import Farm, Organization, User, UserFarm
from app.db.session import AsyncSessionLocal
from app.services.farm_service import _generate_farm_code

EMAIL = "e2e@pigos.io"
PASSWORD = "e2e!2026pw"  # min 8자 — API onboarding 경로로도 사용 가능


async def main() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == EMAIL))
        if existing:
            uf = await db.scalar(select(UserFarm).where(UserFarm.user_id == existing.id))
            print(f"이미 존재: {EMAIL}  user_id={existing.id}  farm_id={uf.farm_id if uf else None}")
            return

        org = Organization(name="E2E Test Org", country="KR", timezone="Asia/Seoul")
        db.add(org)
        await db.flush()

        user = User(
            org_id=org.id,
            email=EMAIL,
            name="E2E Tester",
            password_hash=hash_password(PASSWORD),
            role="FARM_OWNER",
            language="en",
        )
        db.add(user)
        await db.flush()

        farm = Farm(
            org_id=org.id,
            farm_code=_generate_farm_code("KR", org.id),
            name="E2E Test Farm",
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
