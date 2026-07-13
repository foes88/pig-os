#!/usr/bin/env python
"""
파일럿 후속 Phase B — UAT (실 API 왕복).

각 계정 로그인 → /me farm_ids 세트(RBAC 서브트리) → 대시보드/리포트/알림 데이터
→ 접근불가 농장 403/404 격리 검증.
전제: import_pigplan(적재) + setup_pilot_orgs(계정) 완료.
실행: cd api && uv run python -m scripts.uat_pilot
필수 env: PIGPLAN_PILOT_PASSWORD
선택 env: PIGPLAN_PILOT_API_BASE=http://127.0.0.1:8000 (/api/v1 제외)
"""
from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from httpx import ASGITransport, AsyncClient

from scripts.pilot_common import (
    ACCOUNTS,
    PILOT_API_BASE_ENV,
    farm_uuid_str,
    get_pilot_password,
)

V1 = "/api/v1"
REPORT_PARAMS = {
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "period": "monthly",
    "group_by": "period",
}


@dataclass(frozen=True)
class UatCheck:
    account: str
    check: str
    ok: bool
    detail: str


@asynccontextmanager
async def _client() -> AsyncIterator[AsyncClient]:
    base = os.getenv(PILOT_API_BASE_ENV)
    if base:
        async with AsyncClient(base_url=base.rstrip("/"), timeout=60.0) as client:
            yield client
        return

    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://pilot.local",
        timeout=60.0,
    ) as client:
        yield client


def _nonzero_number(value: object) -> bool:
    return isinstance(value, int | float) and value != 0


def _add(rows: list[UatCheck], account: str, check: str, ok: bool, detail: str) -> None:
    rows.append(UatCheck(account, check, ok, detail))


async def run_uat() -> list[UatCheck]:
    password = get_pilot_password()
    rows: list[UatCheck] = []

    async with _client() as client:
        for account in ACCOUNTS:
            login = await client.post(
                f"{V1}/auth/login",
                json={"username": account.username, "password": password},
            )
            login_ok = login.status_code == 200
            if login_ok:
                body = login.json()
                role_ok = body.get("system_role") == account.system_role
                _add(rows, account.username, "login", role_ok,
                     f"HTTP {login.status_code}, system_role={body.get('system_role')}")
                token = body["access_token"]
            else:
                _add(rows, account.username, "login", False, f"HTTP {login.status_code}: {login.text[:160]}")
                continue

            headers = {"Authorization": f"Bearer {token}"}
            me = await client.get(f"{V1}/auth/me", headers=headers)
            if me.status_code == 200:
                got_ids = set(me.json().get("farm_ids", []))
                expected_ids = account.expected_farm_ids
                _add(
                    rows,
                    account.username,
                    "farm_ids",
                    got_ids == expected_ids,
                    f"got={sorted(got_ids)} expected={sorted(expected_ids)}",
                )
            else:
                _add(rows, account.username, "farm_ids", False, f"HTTP {me.status_code}: {me.text[:160]}")

            for farm_no in account.expected_farms:
                farm_id = farm_uuid_str(farm_no)
                dash = await client.get(f"{V1}/farms/{farm_id}/kpi/dashboard", headers=headers)
                if dash.status_code == 200:
                    data = dash.json()
                    ok = _nonzero_number(data.get("psy")) and _nonzero_number(data.get("npd"))
                    detail = f"HTTP 200 psy={data.get('psy')} npd={data.get('npd')} fr={data.get('farrowing_rate')}"
                else:
                    ok = False
                    detail = f"HTTP {dash.status_code}: {dash.text[:160]}"
                _add(rows, account.username, f"dashboard:{farm_no}", ok, detail)

                report = await client.get(
                    f"{V1}/farms/{farm_id}/reports/reproduction",
                    headers=headers,
                    params=REPORT_PARAMS,
                )
                if report.status_code == 200:
                    report_rows = report.json()
                    has_activity = any(
                        (row.get("total_matings", 0) or row.get("total_farrowings", 0) or row.get("total_weanings", 0))
                        for row in report_rows
                    )
                    ok = bool(report_rows) and has_activity
                    detail = f"HTTP 200 rows={len(report_rows)} activity={has_activity}"
                else:
                    ok = False
                    detail = f"HTTP {report.status_code}: {report.text[:160]}"
                _add(rows, account.username, f"report:{farm_no}", ok, detail)

                alerts = await client.get(f"{V1}/farms/{farm_id}/alerts/overdue", headers=headers)
                if alerts.status_code == 200:
                    data = alerts.json()
                    ok = isinstance(data.get("items"), list) and isinstance(data.get("counts"), dict)
                    detail = f"HTTP 200 total={data.get('total')}"
                else:
                    ok = False
                    detail = f"HTTP {alerts.status_code}: {alerts.text[:160]}"
                _add(rows, account.username, f"alerts:{farm_no}", ok, detail)

            if account.denied_farm is not None:
                denied_id = farm_uuid_str(account.denied_farm)
                denied = await client.get(f"{V1}/farms/{denied_id}/kpi/dashboard", headers=headers)
                _add(
                    rows,
                    account.username,
                    f"deny:{account.denied_farm}",
                    denied.status_code in (403, 404),
                    f"HTTP {denied.status_code}",
                )

    return rows


def print_matrix(rows: list[UatCheck]) -> None:
    print("=== Phase B UAT 매트릭스 ===")
    current = None
    for row in rows:
        if row.account != current:
            current = row.account
            print(f"\n[{current}]")
        verdict = "PASS" if row.ok else "FAIL"
        print(f"  {verdict:4s}  {row.check:18s} {row.detail}")
    passed = sum(1 for row in rows if row.ok)
    print(f"\n결과: {passed}/{len(rows)} checks PASS")


async def main() -> int:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    rows = await run_uat()
    print_matrix(rows)
    return 0 if rows and all(row.ok for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
