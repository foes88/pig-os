"""운영자 콘솔 Phase 3 — AI 규칙 설정 + 엔진 반영 검증."""
import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.db.models.platform import Organization, User
from app.engine import RuleContext, RuleEngine
from app.engine.rules import reproduction as _r  # noqa: F401  (register rules)

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


def _ctx(rule_configs: dict | None = None) -> RuleContext:
    return RuleContext(
        farm_id=uuid.uuid4(), country="KR",
        kpi={"WSI": 16.0},  # 기본 임계(warn10/crit14) 기준 CRITICAL
        benchmarks={}, sow_counts={}, as_of=date(2026, 6, 23),
        extra={"rule_configs": rule_configs or {}},
    )


# ── API ───────────────────────────────────────────────────────────────────────
async def test_rules_list_gate_and_content(client: AsyncClient, db: AsyncSession, test_org: Organization):
    owner = await _mk_user(db, test_org, "FARM_OWNER")
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    await db.flush()
    assert (await client.get("/api/v1/admin/rules", headers=_auth(owner))).status_code == 403
    r = await client.get("/api/v1/admin/rules", headers=_auth(admin))
    assert r.status_code == 200
    ids = {x["rule_id"] for x in r.json()}
    assert "wsi.overdue" in ids  # 번식 규칙 등록 확인


async def test_rule_update_validation_and_persist(client: AsyncClient, db: AsyncSession, test_org: Organization):
    admin = await _mk_user(db, test_org, "SUPER_ADMIN")
    await db.flush()
    # above형(WSI): warning >= critical 차단
    bad = await client.patch("/api/v1/admin/rules/wsi.overdue", headers=_auth(admin),
                             json={"warning": 20, "critical": 10})
    assert bad.status_code == 422
    # above형 동일값도 차단
    same = await client.patch("/api/v1/admin/rules/wsi.overdue", headers=_auth(admin),
                              json={"warning": 10, "critical": 10})
    assert same.status_code == 422
    # below형(PSY, higher-is-better): warning > critical 이 정상 → 허용 (BUG-011)
    below_ok = await client.patch("/api/v1/admin/rules/psy.below_target", headers=_auth(admin),
                                  json={"warning": 24, "critical": 20})
    assert below_ok.status_code == 200, below_ok.text
    assert below_ok.json()["warning"] == 24 and below_ok.json()["critical"] == 20
    # below형에서 warning < critical 은 방향 위반 → 차단
    below_bad = await client.patch("/api/v1/admin/rules/psy.below_target", headers=_auth(admin),
                                   json={"warning": 20, "critical": 24})
    assert below_bad.status_code == 422
    # 정상 upsert (above형)
    ok = await client.patch("/api/v1/admin/rules/wsi.overdue", headers=_auth(admin),
                            json={"enabled": False, "warning": 8, "critical": 12})
    assert ok.status_code == 200
    assert ok.json()["enabled"] is False and ok.json()["warning"] == 8
    # 미등록 규칙
    assert (await client.patch("/api/v1/admin/rules/nope.rule", headers=_auth(admin),
                               json={"enabled": False})).status_code == 404
    # ADM-RULES-NULLCLEAR: 명시적 null로 임계값을 코드 기본(null)으로 클리어 가능
    cleared = await client.patch("/api/v1/admin/rules/wsi.overdue", headers=_auth(admin),
                                 json={"warning": None, "critical": None})
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["warning"] is None and cleared.json()["critical"] is None


# ── 엔진 반영 ───────────────────────────────────────────────────────────────────
async def test_engine_default_fires_wsi():
    res = await RuleEngine.evaluate(_ctx(), intent="wsi")
    assert any(f.rule_id == "wsi.overdue" for f in res.findings)


async def test_engine_disabled_rule_skipped():
    res = await RuleEngine.evaluate(_ctx({"wsi.overdue": {"enabled": False}}), intent="wsi")
    assert all(f.rule_id != "wsi.overdue" for f in res.findings)


async def test_engine_threshold_override_changes_severity():
    # WSI=16. 기본(10/14)=CRITICAL. 운영자가 크게 올리면(20/30) 발동 안 함.
    res = await RuleEngine.evaluate(
        _ctx({"wsi.overdue": {"enabled": True, "warning": 20.0, "critical": 30.0}}), intent="wsi"
    )
    assert all(f.rule_id != "wsi.overdue" for f in res.findings)
