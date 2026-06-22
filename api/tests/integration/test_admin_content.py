"""운영자 콘솔 Phase 2 — 공지/문의 백오피스 검증."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Organization, User

pytestmark = pytest.mark.anyio


async def _mk_user(db: AsyncSession, org: Organization, role: str) -> User:
    u = User(
        org_id=org.id, email=f"{role.lower()}-{uuid.uuid4().hex[:6]}@pigos.io",
        name=f"{role} User", password_hash=hash_password("Test1234!"), role=role, system_role=role,
    )
    db.add(u)
    await db.flush()
    return u


def _auth(u: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(u.id), str(u.org_id), [u.system_role])}"}


# ── 공지 ──────────────────────────────────────────────────────────────────────
async def test_announcement_crud_and_gate(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    owner = await _mk_user(db, test_org, "FARM_OWNER")
    await db.flush()

    # 비관리자 작성 차단
    assert (await client.post("/api/v1/admin/announcements", headers=_auth(owner),
            json={"title": "x", "body": "y"})).status_code == 403

    # 작성
    r = await client.post("/api/v1/admin/announcements", headers=_auth(admin),
                          json={"title": "Launch", "body": "PigOS launches", "category": "UPDATE", "pinned": True})
    assert r.status_code == 201, r.text
    ann_id = r.json()["id"]

    # 잘못된 category
    assert (await client.post("/api/v1/admin/announcements", headers=_auth(admin),
            json={"title": "a", "body": "b", "category": "NOPE"})).status_code == 422

    # 수정(노출 토글)
    up = await client.put(f"/api/v1/admin/announcements/{ann_id}", headers=_auth(admin),
                          json={"published": False})
    assert up.status_code == 200 and up.json()["published"] is False

    # 고객 읽기 — 미게시는 안 보임
    cust = await client.get("/api/v1/announcements", headers=_auth(owner))
    assert cust.status_code == 200
    assert all(a["id"] != ann_id for a in cust.json())

    # 재게시 → 고객에게 보임
    await client.put(f"/api/v1/admin/announcements/{ann_id}", headers=_auth(admin), json={"published": True})
    cust2 = await client.get("/api/v1/announcements", headers=_auth(owner))
    assert any(a["id"] == ann_id for a in cust2.json())

    # 삭제
    assert (await client.delete(f"/api/v1/admin/announcements/{ann_id}", headers=_auth(admin))).status_code == 204


# ── 문의 ──────────────────────────────────────────────────────────────────────
async def test_support_ticket_flow(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    owner = await _mk_user(db, test_org, "FARM_OWNER")
    other = await _mk_user(db, test_org, "FARM_OWNER")
    await db.flush()

    # 고객 문의 등록
    cr = await client.post("/api/v1/support/tickets", headers=_auth(owner),
                           json={"subject": "Cannot login", "body": "help me"})
    assert cr.status_code == 201, cr.text
    tid = cr.json()["id"]
    assert cr.json()["status"] == "OPEN"

    # 내 문의 목록
    mine = await client.get("/api/v1/support/tickets", headers=_auth(owner))
    assert any(t["id"] == tid for t in mine.json())

    # 남의 문의 접근 차단
    assert (await client.get(f"/api/v1/support/tickets/{tid}", headers=_auth(other))).status_code == 403

    # 비관리자 admin 문의함 차단
    assert (await client.get("/api/v1/admin/support", headers=_auth(owner))).status_code == 403

    # 운영자 목록·답변
    lst = await client.get("/api/v1/admin/support", headers=_auth(admin))
    assert lst.status_code == 200 and lst.json()["meta"]["total"] >= 1
    rep = await client.post(f"/api/v1/admin/support/{tid}/reply", headers=_auth(admin),
                            json={"body": "Try resetting your password"})
    assert rep.status_code == 200, rep.text
    assert rep.json()["status"] == "ANSWERED"
    assert any(r["is_staff"] for r in rep.json()["replies"])

    # 고객이 답변 확인
    det = await client.get(f"/api/v1/support/tickets/{tid}", headers=_auth(owner))
    assert det.json()["status"] == "ANSWERED"
    assert len(det.json()["replies"]) == 1
