"""에러 응답 계약 — 프론트가 분기할 수 있는 code 를 항상 준다.

## 왜 필요한가

2026-08-25 장애에서 사용자가 본 것은 전부 `Server error. Please try again.` 하나였다.
로그인 500·가입 실패·대시보드 오류가 같은 문구였고, 그래서
  "다시 하면 되나?"  "내가 뭘 잘못했나?"  "문의해야 하나?"
를 구분할 수 없었다. 원인은 프론트 문구가 아니라 **백엔드가 분기 근거를 안 준 것**이다
— 예상 못 한 예외에는 code 가 아예 없었다(FastAPI 기본 500).

★ 이 파일이 고정하는 계약:
   1) 모든 에러 응답에 `code` 가 있다 (프론트 분기 키)
   2) 재시도 가능(503)과 코드 결함(500)을 **다른 code 로** 구분한다
   3) 500/503 에는 `request_id` 가 있다 — 없으면 "아까 에러났어요"를 추적할 수 없다
   4) 내부 예외 메시지를 detail 로 노출하지 않는다 (정보 누출 + 사용자에게 무의미)
"""
import pytest
from asyncpg.exceptions import PostgresConnectionError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PeriodLockedError,
    PigOSError,
    UnauthorizedError,
    ValidationError,
    register_exception_handlers,
)

SECRET = "table pigos_secret column password_hash"   # 노출되면 안 되는 내부 문자열


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom/{kind}")
    async def boom(kind: str):  # noqa: ANN202
        raise {
            "notfound": NotFoundError("Sow not found"),
            "forbidden": ForbiddenError("no access"),
            "unauthorized": UnauthorizedError("bad credentials"),
            "conflict": ConflictError("duplicate"),
            "validation": ValidationError("bad input"),
            "locked": PeriodLockedError("period closed"),
            "integrity": IntegrityError(SECRET, {}, Exception(SECRET)),
            "dbdown": OperationalError(SECRET, {}, Exception(SECRET)),
            "pgconn": PostgresConnectionError(SECRET),
            "bug": RuntimeError(SECRET),
        }[kind]

    # raise_server_exceptions=False: catch-all 핸들러의 응답을 실제로 받아본다
    # (기본값이면 TestClient 가 예외를 그대로 올려버려 계약을 검증할 수 없다).
    return TestClient(app, raise_server_exceptions=False)


# ── 1) 모든 에러에 code 가 있다 ───────────────────────────────────────────────

@pytest.mark.parametrize(("kind", "status", "code"), [
    ("notfound", 404, "NOT_FOUND"),
    ("forbidden", 403, "FORBIDDEN"),
    ("unauthorized", 401, "UNAUTHORIZED"),
    ("conflict", 409, "CONFLICT"),
    ("validation", 422, "VALIDATION_ERROR"),
    ("locked", 423, "PERIOD_LOCKED"),
    ("integrity", 409, "CONFLICT"),
    ("dbdown", 503, "DB_UNAVAILABLE"),
    ("pgconn", 503, "DB_UNAVAILABLE"),
    ("bug", 500, "INTERNAL_ERROR"),
])
def test_every_error_carries_a_code(client: TestClient, kind, status, code):
    r = client.get(f"/boom/{kind}")
    assert r.status_code == status
    assert r.json().get("code") == code, (
        f"{kind}: code 가 없거나 다르다 → 프론트가 분기할 수 없다. 응답={r.json()}")


# ── 2) 재시도 가능 vs 코드 결함 구분 ─────────────────────────────────────────

def test_db_outage_is_retryable_not_a_bug(client: TestClient):
    """★ DB 장애(503)와 코드 결함(500)은 사용자 행동이 다르다 — 같은 code 면 안 된다.

    503 → "잠시 후 다시" / 500 → "문의" 로 안내가 갈려야 한다."""
    down = client.get("/boom/dbdown")
    bug = client.get("/boom/bug")
    assert down.json()["code"] != bug.json()["code"]
    assert down.status_code == 503 and bug.status_code == 500
    assert down.headers.get("Retry-After"), "503 은 재시도 시점을 알려줘야 한다"


# ── 3) 추적 ID ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kind", ["dbdown", "bug"])
def test_server_errors_carry_request_id(client: TestClient, kind):
    """서버측 실패에는 추적 ID가 있어야 한다 — 없으면 사용자 신고를 로그와 못 잇는다."""
    rid = client.get(f"/boom/{kind}").json().get("request_id")
    assert rid and len(rid) >= 8, f"request_id 누락({rid})"


def test_request_ids_are_unique_per_request(client: TestClient):
    """같은 값이 재사용되면 추적에 쓸 수 없다."""
    a = client.get("/boom/bug").json()["request_id"]
    b = client.get("/boom/bug").json()["request_id"]
    assert a != b


# ── 4) 내부 정보 비노출 ───────────────────────────────────────────────────────

@pytest.mark.parametrize("kind", ["integrity", "dbdown", "pgconn", "bug"])
def test_internal_details_are_not_leaked(client: TestClient, kind):
    """★ 예외 메시지에 스키마·쿼리가 들어 있다. 사용자에게 보내지 않는다."""
    body = client.get(f"/boom/{kind}").text
    assert SECRET not in body, f"{kind}: 내부 정보가 응답에 노출됐다"
    assert "Traceback" not in body


# ── 계약 자체 ─────────────────────────────────────────────────────────────────

def test_all_pigos_errors_define_code_and_status():
    """새 예외를 추가할 때 code 를 빠뜨리면 프론트에서 조용히 기본 문구로 떨어진다."""
    subs = []
    stack = [PigOSError]
    while stack:
        c = stack.pop()
        subs.append(c)
        stack.extend(c.__subclasses__())
    for c in subs:
        assert isinstance(c.code, str) and c.code, f"{c.__name__}.code 미정의"
        assert isinstance(c.status_code, int), f"{c.__name__}.status_code 미정의"
        if c is not PigOSError:
            assert c.code != PigOSError.code, (
                f"{c.__name__} 이 기본 code(INTERNAL_ERROR)를 그대로 쓴다 — "
                "프론트가 코드 결함과 구분하지 못한다")
