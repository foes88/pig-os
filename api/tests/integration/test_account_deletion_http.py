"""계정 삭제 — **HTTP 계층** 종단 검증.

`test_account_deletion.py` 는 서비스 함수를 직접 부른다. 그것만으로는
**라우터 배선·요청 스키마·상태코드·본문 파싱**이 실제로 맞는지 알 수 없다.
독립검증(2026-08-25)에서 BLOCKER 가 정확히 그 층(화면 → API 호출)에 있었다 —
서비스는 멀쩡한데 아무도 부르지 않는 상태였다.

★ 이 파일이 잠그는 것
  1) `DELETE /api/v1/auth/me` 가 **실재하고** 스펙대로 응답한다 (204/401/403/422)
  2) 삭제 후 **기존 access token 이 즉시 거부**된다 (플래그만 세우고 끝나면 안 된다)
  3) 삭제 후 로그인이 불가능하다
  4) 같은 이메일로 **재가입이 가능**하다

특히 (2)는 구조 검사(소스에 "active" 가 있는지)로는 부족하다 — 실제 요청으로 확인한다.
"""
import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio

PW = "Test1234!"
V1 = "/api/v1/auth"


def _identity() -> tuple[str, str, str]:
    tag = uuid.uuid4().hex[:8]
    return f"e2e{tag}", f"e2e{tag}@pigos.io", f"E2E Org {tag}"


async def _register(client: AsyncClient) -> tuple[str, str, str]:
    """가입 후 (username, email, access_token)."""
    user, email, org = _identity()
    r = await client.post(f"{V1}/register", json={
        "name": "E2E", "username": user, "email": email, "password": PW,
        "org_name": org, "country": "KR"})
    assert r.status_code == 201, r.text
    return user, email, r.json()["access_token"]


async def test_delete_endpoint_exists_and_follows_the_contract(client: AsyncClient):
    """★ 계약 그대로 — 이전에는 이 경로가 405 였다(엔드포인트 자체가 없었다)."""
    _user, _email, token = await _register(client)
    auth = {"Authorization": f"Bearer {token}"}

    # 비밀번호 누락 → 422
    r = await client.request("DELETE", f"{V1}/me", headers=auth)
    assert r.status_code == 422, f"비밀번호 누락이 {r.status_code}: {r.text}"

    # 토큰 없음 → 401 (비밀번호가 맞아도 인증이 먼저다)
    r = await client.request("DELETE", f"{V1}/me", json={"password": PW})
    assert r.status_code == 401

    # 비밀번호 불일치 → 403 (권한 없음이 아니라 재인증 실패)
    r = await client.request("DELETE", f"{V1}/me", json={"password": "wrong"}, headers=auth)
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "FORBIDDEN"

    # 정상 삭제 → 204 (본문 없음)
    r = await client.request("DELETE", f"{V1}/me", json={"password": PW}, headers=auth)
    assert r.status_code == 204, r.text
    assert not r.content


async def test_existing_token_is_rejected_right_after_deletion(client: AsyncClient):
    """★★ 삭제 직후 **기존 access token** 으로 API 를 못 쓴다.

    refresh token 은 지우지만 access token 은 서명된 JWT 라 만료 전까지 유효하다.
    매 요청 계정 상태를 확인하지 않으면 **토큰 수명만큼 삭제된 계정이 살아 있다.**
    구조 검사가 아니라 실제 요청으로 확인한다."""
    _user, _email, token = await _register(client)
    auth = {"Authorization": f"Bearer {token}"}

    assert (await client.get(f"{V1}/me", headers=auth)).status_code == 200, "삭제 전엔 정상"

    r = await client.request("DELETE", f"{V1}/me", json={"password": PW}, headers=auth)
    assert r.status_code == 204

    r = await client.get(f"{V1}/me", headers=auth)
    assert r.status_code == 401, (
        f"삭제된 계정의 토큰이 아직 통한다({r.status_code}) — 토큰 수명만큼 접근이 남는다")


async def test_login_impossible_and_email_reusable(client: AsyncClient):
    """삭제 후 로그인 불가 + 같은 이메일 재가입 가능 — 익명화를 택한 이유."""
    user, email, token = await _register(client)

    r = await client.request("DELETE", f"{V1}/me", json={"password": PW},
                             headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204

    r = await client.post(f"{V1}/login", json={"username": user, "password": PW})
    assert r.status_code == 401, "삭제된 계정으로 로그인됐다"

    r = await client.post(f"{V1}/register", json={
        "name": "again", "username": user, "email": email, "password": PW,
        "org_name": "Again Org", "country": "KR"})
    assert r.status_code == 201, (
        f"같은 이메일 재가입이 막혔다({r.status_code}) — 자리표시값 치환이 안 됐을 수 있다: {r.text}")
