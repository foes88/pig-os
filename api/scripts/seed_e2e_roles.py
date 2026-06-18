"""E2E 농장에 역할별 테스트 계정 시드 — RBAC 검증용.

e2e@pigos.io(FARM_OWNER, seed_e2e.py)와 같은 농장에 VIEWER/WORKER 계정 추가.
멱등. 실행: cd api; PYTHONPATH=. uv run python scripts/seed_e2e_roles.py

계정:
  viewer@pigos.io / e2e!2026pw  — VIEWER (조회만, 쓰기 403)
  worker@pigos.io / e2e!2026pw  — FARM_WORKER (일상 입력 가능, 도태/삭제/설정 불가)
"""
import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models.platform import Farm, User, UserFarm
from app.db.session import AsyncSessionLocal

PASSWORD = "e2e!2026pw"
ACCOUNTS = [
    ("viewer@pigos.io", "E2E Viewer", "VIEWER"),
    ("worker@pigos.io", "E2E Worker", "FARM_WORKER"),
]


async def main() -> None:
    async with AsyncSessionLocal() as db:
        owner = await db.scalar(select(User).where(User.email == "e2e@pigos.io"))
        if not owner:
            print("먼저 seed_e2e.py 실행 필요 (e2e@pigos.io 없음)")
            return
        uf = await db.scalar(select(UserFarm).where(UserFarm.user_id == owner.id))
        farm = await db.scalar(select(Farm).where(Farm.id == uf.farm_id))

        for email, name, role in ACCOUNTS:
            if await db.scalar(select(User).where(User.email == email)):
                print(f"이미 존재: {email}")
                continue
            u = User(org_id=owner.org_id, email=email, name=name,
                     password_hash=hash_password(PASSWORD), role=role, language="en")
            db.add(u)
            await db.flush()
            db.add(UserFarm(user_id=u.id, farm_id=farm.id, role_override=role))
            print(f"시드: {email} / {PASSWORD}  role={role}  farm={farm.id}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
