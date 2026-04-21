# app/core/exceptions.py
"""
Shared exception classes and HTTP exception handlers.

Define domain exceptions here. Register their HTTP handlers in app/main.py.
Never return raw Python exceptions to the client.
Always use the standardised error response format.
"""

import logging
import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def error_response(
    error_code: str,
    message: str,
    correlation_id: str | None = None,
    details: dict[str, Any] | None = None,
    status_code: int = 400,
) -> JSONResponse:
    """
    Build a standardised error response.

    Format: {"error_code": "...", "message": "...", "correlation_id": "", "details": {}}
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": error_code,
            "message": message,
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "details": details or {},
        },
    )


class AppException(Exception):
    """Base exception class for the application."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details  # must be set explicitly — handler accesses exc.details
        super().__init__(message)


class InvalidCredentialsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Login failed. You must have used an incorrect email address or password.",
            error_code="INVALID_CREDENTIALS",
            status_code=401,
        )


class TokenExpiredError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Token expired",
            error_code="TOKEN_EXPIRED",
            status_code=401,
        )


class TokenInvalidError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Token invalid",
            error_code="TOKEN_INVALID",
            status_code=401,
        )


class InsufficientPermissionsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="You do not have permissions to perform this action.",
            error_code="INSUFFICIENT_PERMISSIONS",
            status_code=403,
        )


class AccountLockedError(AppException):

    def __init__(self) -> None:
        super().__init__(
            message="Account is locked due to multiple failed login attempts.",
            error_code="ACCOUNT_LOCKED",
            status_code=403,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle AppException and return a standardised error response."""
    correlation_id = request.headers.get("X-Correlation-ID")
    logger.warning(
        "AppException caught: %s",
        exc.error_code,
        extra={"correlation_id": correlation_id, "error_code": exc.error_code},
    )
    return error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unexpected exceptions.

    Logs the full error internally but never returns internal details to the client.
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        extra={"correlation-id": correlation_id},
    )
    return error_response(
        error_code="INTERNAL_ERROR",
        message="An internal server error occurred.",
        correlation_id=correlation_id,
        status_code=500,
    )
