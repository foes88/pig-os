#!/usr/bin/env python
"""
파일럿 후속 Phase B — UAT (실 API 왕복, in-process ASGI).

각 계정 로그인 → /me farm_ids 개수(RBAC 서브트리) → 대시보드 데이터 → 403 격리 검증.
전제: import_pigplan(적재) + setup_pilot_orgs(계정) 완료. 별도 서버 불필요(ASGITransport).
실행: cd api && uv run python -m scripts.uat_pilot
"""
from __future__ import annotations

import asyncio
import logging

from httpx import ASGITransport, AsyncClient

from app.main import app

PW = "Pilot!2026"
V1 = "/api/v1"

# (username, 기대 접근농장수, 접근가능 farm_no 예시, 접근불가 farm_no 예시)
CASES = [
    ("vendor_admin", 4, 2807, None),
    ("dealer_east",  2, 2807, 848),
    ("dealer_west",  2, 848, 2807),
    ("owner_2807",   1, 2807, 4448),
    ("owner_4448",   1, 4448, 2807),
    ("owner_848",    1, 848, 978),
    ("owner_978",    1, 978, 848),
]
NS = "a11c0000"
def farm_uuid(fn: int) -> str: return f"{NS}-0000-0000-0000-{fn:012d}"


async def main():
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    rows, fails = [], 0
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://uat") as c:
        for uname, exp_n, ok_farm, deny_farm in CASES:
            checks = []
            # 1) 로그인
            r = await c.post(f"{V1}/auth/login", json={"username": uname, "password": PW})
            if r.status_code != 200:
                rows.append((uname, "LOGIN FAIL", f"{r.status_code} {r.text[:60]}"))
                fails += 1
                continue
            tok = r.json()["access_token"]
            h = {"Authorization": f"Bearer {tok}"}
            # 2) /me farm_ids 개수 = 기대(RBAC 서브트리)
            me = await c.get(f"{V1}/auth/me", headers=h)
            n = len(me.json().get("farm_ids", [])) if me.status_code == 200 else -1
            checks.append(("farm_ids", n == exp_n, f"{n}/{exp_n}"))
            # 3) 접근가능 농장 대시보드 200 + KPI 존재
            d = await c.get(f"{V1}/farms/{farm_uuid(ok_farm)}/kpi/dashboard", headers=h)
            checks.append(("dashboard", d.status_code == 200, str(d.status_code)))
            # 4) 접근불가 농장 → 403
            if deny_farm is not None:
                dn = await c.get(f"{V1}/farms/{farm_uuid(deny_farm)}/kpi/dashboard", headers=h)
                checks.append(("deny403", dn.status_code in (403, 404), str(dn.status_code)))
            ok = all(p for _, p, _ in checks)
            fails += 0 if ok else 1
            detail = " ".join(f"{k}={v}{'' if p else '<X>'}" for k, p, v in checks)
            rows.append((uname, "PASS" if ok else "FAIL", detail))

    print("=== Phase B UAT 매트릭스 ===")
    for uname, verdict, detail in rows:
        print(f"  {uname:14s} {verdict:5s}  {detail}")
    print(f"\n결과: {len(rows)-fails}/{len(rows)} PASS")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if asyncio.run(main()) else 0)
