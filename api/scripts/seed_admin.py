"""플랫폼 관리자(SUPER_ADMIN) 시드 — 한국어 노출 + 관리용 로그인.

한국어는 플랫폼 관리자만 선택 가능(해외 출시: 일반/고객 FARM_OWNER엔 숨김).
이 계정으로 로그인하면 Topbar에서 한국어 선택 가능. e2e 농장에 연결해 같은 데이터를 봄.
멱등: 이미 있으면 farm_id만 출력. 실행: cd api; PYTHONPATH=. uv run python scripts/seed_admin.py

크리덴셜:
  EMAIL=admin@pigos.io  PASSWORD=admin!2026pw  role=SUPER_ADMIN
"""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.platform import Farm, User, UserFarm
from app.db.session import AsyncSessionLocal

EMAIL = "admin@pigos.io"
PASSWORD = "admin!2026pw"
E2E_EMAIL = "e2e@pigos.io"


async def main() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == EMAIL))
        if existing:
            uf = await db.scalar(select(UserFarm).where(UserFarm.user_id == existing.id))
            print(f"이미 존재: {EMAIL}  role={existing.role}  farm_id={uf.farm_id if uf else None}")
            return

        # e2e 농장/조직에 합류 → 같은 데이터 공유
        e2e = await db.scalar(select(User).where(User.email == E2E_EMAIL))
        if not e2e:
            print("e2e 계정이 없습니다. 먼저 scripts/seed_e2e.py 실행하세요.")
            return
        uf = await db.scalar(select(UserFarm).where(UserFarm.user_id == e2e.id))
        farm = await db.scalar(select(Farm).where(Farm.id == uf.farm_id)) if uf else None
        if not farm:
            print("e2e 농장을 찾지 못했습니다.")
            return

        user = User(
            org_id=e2e.org_id,
            email=EMAIL,
            name="Platform Admin",
            password_hash=hash_password(PASSWORD),
            role="SUPER_ADMIN",
            language="ko",
        )
        db.add(user)
        await db.flush()
        db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override="FARM_OWNER"))
        await db.commit()
        print(f"시드 완료: {EMAIL} / {PASSWORD}  role=SUPER_ADMIN  farm_id={farm.id}")


if __name__ == "__main__":
    asyncio.run(main())
