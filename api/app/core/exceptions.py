"""애플리케이션 예외 → HTTP 응답 매핑.

★ 응답 계약: 모든 에러는 `{"code": <불변 식별자>, "detail": <사람이 읽는 설명>}` 이다.
  프론트는 **code 로 분기**하고 detail 은 보조로만 쓴다 — detail 문구는 바뀔 수 있고
  번역 대상도 아니다(사용자 문구는 프론트 i18n 이 code 로 고른다).

2026-08-25 이전에는 예상 못 한 예외에 code 가 아예 없었다(FastAPI 기본 500). 그래서
프론트가 "일시적 장애"와 "진짜 버그"와 "네트워크 끊김"을 구분할 수 없어 전부
`Server error. Please try again.` 하나로 보여줬고, 사용자는 재시도해야 할지
문의해야 할지 알 수 없었다. 아래 catch-all 이 그 구멍을 막는다.
"""
import logging
import uuid

from asyncpg.exceptions import PostgresConnectionError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError

logger = logging.getLogger("pigos.error")


class PigOSError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.code


class NotFoundError(PigOSError):
    status_code = 404
    code = "NOT_FOUND"


class ForbiddenError(PigOSError):
    status_code = 403
    code = "FORBIDDEN"


class UnauthorizedError(PigOSError):
    status_code = 401
    code = "UNAUTHORIZED"


class ConflictError(PigOSError):
    status_code = 409
    code = "CONFLICT"


class ValidationError(PigOSError):
    status_code = 422
    code = "VALIDATION_ERROR"


class AddonNotSubscribedError(PigOSError):
    """Raised when a farm tries to access an Addon domain without subscription."""
    status_code = 402
    code = "ADDON_NOT_SUBSCRIBED"

    def __init__(self, addon_code: str):
        self.addon_code = addon_code
        self.detail = f"Addon '{addon_code}' is not subscribed for this farm"


class PeriodLockedError(PigOSError):
    """Raised when trying to modify data in a locked period. HTTP 423 Locked."""
    status_code = 423
    code = "PERIOD_LOCKED"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PigOSError)
    async def pigos_error_handler(request: Request, exc: PigOSError) -> JSONResponse:
        body: dict = {"code": exc.code, "detail": exc.detail}
        if isinstance(exc, AddonNotSubscribedError):
            body["addon_code"] = exc.addon_code
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        # DB 제약 위반(unique/FK/NOT NULL) backstop — 앱레벨 선검사 누락·동시성 TOCTOU 경합 시
        # 500(내부에러 노출) 대신 409 CONFLICT로 일관 응답(QA 온보딩 H2). 세션은 get_db 종료 시 롤백.
        return JSONResponse(
            status_code=409,
            content={"code": "CONFLICT", "detail": "Resource conflict or constraint violation"},
        )

    @app.exception_handler(OperationalError)
    @app.exception_handler(PostgresConnectionError)
    async def db_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
        """DB 에 못 붙거나 쿼리 도중 연결이 끊긴 경우 → 503.

        ★ 이걸 500 과 섞으면 안 된다. 503 은 **사용자가 다시 시도하면 되는 상황**이고
          500 은 **코드가 잘못된 상황**이다. 2026-08-25 장애 때 정확히 이 구분이 없어서
          풀러가 연결을 끊는 인프라 문제가 "서버 오류"로만 보였다.
        """
        rid = uuid.uuid4().hex[:12]
        logger.error("[%s] DB unavailable on %s %s: %s",
                     rid, request.method, request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"code": "DB_UNAVAILABLE", "detail": "Database temporarily unavailable",
                     "request_id": rid},
            headers={"Retry-After": "5"},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """예상 못 한 예외 — 프론트가 분기할 수 있게 code 를 준다.

        ★ detail 에 예외 메시지를 넣지 않는다. 내부 구조·쿼리·경로가 새어 나가고,
          사용자에게도 아무 의미가 없다. 대신 **request_id 를 준다** — 사용자가 그걸
          알려주면 로그에서 정확히 그 요청을 찾을 수 있다. 이게 없으면 "아까 에러났어요"
          를 추적할 방법이 없다(이번 장애 때 실제로 그랬다).
        """
        rid = uuid.uuid4().hex[:12]
        logger.exception("[%s] Unhandled on %s %s", rid, request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR",
                     "detail": "An unexpected error occurred", "request_id": rid},
        )
