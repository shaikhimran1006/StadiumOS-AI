from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class StadiumOSException(Exception):
    status_code: int = 500
    detail: str = "An internal error occurred"
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class NotFoundException(StadiumOSException):
    status_code = 404
    detail = "Resource not found"
    error_code = "NOT_FOUND"


class BadRequestException(StadiumOSException):
    status_code = 400
    detail = "Bad request"
    error_code = "BAD_REQUEST"


class UnauthorizedException(StadiumOSException):
    status_code = 401
    detail = "Unauthorized"
    error_code = "UNAUTHORIZED"


class ForbiddenException(StadiumOSException):
    status_code = 403
    detail = "Forbidden"
    error_code = "FORBIDDEN"


class ConflictException(StadiumOSException):
    status_code = 409
    detail = "Resource conflict"
    error_code = "CONFLICT"


class InternalServerException(StadiumOSException):
    status_code = 500
    detail = "Internal server error"
    error_code = "INTERNAL_SERVER_ERROR"


class ValidationException(StadiumOSException):
    status_code = 422
    detail = "Validation error"
    error_code = "VALIDATION_ERROR"


class AIServiceException(StadiumOSException):
    status_code = 502
    detail = "AI service error"
    error_code = "AI_SERVICE_ERROR"


async def _stadiumos_exception_handler(
    request: Request, exc: StadiumOSException
) -> JSONResponse:
    logger.error(
        "StadiumOSException: %s (code=%s, status=%d, path=%s)",
        exc.detail,
        exc.error_code,
        exc.status_code,
        request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "path": request.url.path,
            }
        },
    )


async def _unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "path": request.url.path,
            }
        },
    )


async def _validation_exception_handler(
    request: Request, exc: Any
) -> JSONResponse:
    errors: list[dict[str, Any]] = []
    if hasattr(exc, "errors"):
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            errors.append({
                "field": loc,
                "message": err.get("msg", "Validation error"),
                "type": err.get("type", "unknown"),
            })

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "path": request.url.path,
                "details": errors,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    app.add_exception_handler(
        StadiumOSException, _stadiumos_exception_handler  # type: ignore
    )
    app.add_exception_handler(
        RequestValidationError, _validation_exception_handler  # type: ignore
    )
    app.add_exception_handler(
        StarletteHTTPException, _starlette_http_exception_handler  # type: ignore
    )
    app.add_exception_handler(
        Exception, _unhandled_exception_handler  # type: ignore
    )


async def _starlette_http_exception_handler(
    request: Request, exc: Any
) -> JSONResponse:
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "HTTP error")
    logger.warning(
        "HTTPException %d on %s: %s", status_code, request.url.path, detail
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": f"HTTP_{status_code}",
                "message": detail,
                "path": request.url.path,
            }
        },
    )
