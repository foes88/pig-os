from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


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
    """Raised when trying to modify data in a locked period."""
    status_code = 409
    code = "PERIOD_LOCKED"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PigOSError)
    async def pigos_error_handler(request: Request, exc: PigOSError) -> JSONResponse:
        body: dict = {"code": exc.code, "detail": exc.detail}
        if isinstance(exc, AddonNotSubscribedError):
            body["addon_code"] = exc.addon_code
        return JSONResponse(status_code=exc.status_code, content=body)
