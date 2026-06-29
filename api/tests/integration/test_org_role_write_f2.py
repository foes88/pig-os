"""F2 — 조직롤(총판/대리점)이 자기 서브트리 농장에 입력(write) 가능, 외부는 403.

요구사항: 총판이 하위 농장으로 전환하면 그 농장으로 데이터 입력 → 다른 농장 전환 후 또 입력.
F1(effective_farm_role 서브트리 강제)이 안전망 — 외부 농장엔 write 불가.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Farm, Organization, User

pytestmark = pytest.mark.anyio


def _h(u: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


async def _distributor(db, org) -> User:
    u = User(org_id=org.id, username=f"dist_{uuid.uuid4().hex[:6]}",
             email=f"dist-{uuid.uuid4().hex[:6]}@pigos.io", name="Distributor",
             password_hash=hash_password("Test1234!"), role="DISTRIBUTOR_ADMIN",
             system_role="DISTRIBUTOR_ADMIN")
    db.add(u)
    await db.flush()
    return u


async def test_distributor_can_write_subtree_farm(client: AsyncClient, db: AsyncSession, test_org):
    # 총판 org 하위 농장
    child = Organization(name="Child Co", country="KR", timezone="Asia/Seoul", parent_org_id=test_org.id)
    db.add(child)
    await db.flush()
    farm = Farm(org_id=child.id, farm_code=f"SUB-{uuid.uuid4().hex[:5].upper()}",
                name="Sub", country="KR", timezone="Asia/Seoul", active=True)
    db.add(farm)
    dist = await _distributor(db, test_org)
    await db.flush()

    # 하위 농장에 모돈 등록(입력) → 허용
    r = await client.post(f"/api/v1/farms/{farm.id}/sows", headers=_h(dist),
                          json={"ear_tag": "DIST-SOW-1", "entry_date": "2024-01-01", "entry_type": "GILT"})
    assert r.status_code == 201, r.text


async def test_distributor_blocked_on_other_org_farm(client: AsyncClient, db: AsyncSession, test_org):
    # 무관한 조직의 농장 — 총판 서브트리 밖
    other = Organization(name="Other Co", country="KR", timezone="Asia/Seoul")
    db.add(other)
    await db.flush()
    foreign = Farm(org_id=other.id, farm_code=f"FOR-{uuid.uuid4().hex[:5].upper()}",
                   name="Foreign", country="KR", timezone="Asia/Seoul", active=True)
    db.add(foreign)
    dist = await _distributor(db, test_org)
    await db.flush()

    r = await client.post(f"/api/v1/farms/{foreign.id}/sows", headers=_h(dist),
                          json={"ear_tag": "X-1", "entry_date": "2024-01-01", "entry_type": "GILT"})
    assert r.status_code == 403, r.text  # 서브트리 밖 → 접근/입력 불가
