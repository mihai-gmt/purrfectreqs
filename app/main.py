"""
PurrfectReqs — FastAPI application entry point.

This file creates the FastAPI app and wires together:
- Logging configuration
- Exception handlers
- Middleware (security headers, correlation ID)
- Static files and templates
- Module routers (added here as modules are built)

Do not put business logic here. This file is configuration only.
"""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
)
from app.core.logging import configure_logging

# Configure logging before anything else

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: runs on startup and shutdown."""
    logger.info(
        "Purrfectreqs starting",
        extra={"environment": settings.app_env, "debug": settings.app_debug},
    )
    yield


app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.project_version,
    docs_url="/docs" if settings.is_development else None,
    redoc_url=None,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Static files and templates
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom handler for Pydantic validation errors (HTTP 422).

    FastAPI's default 422 response uses a 'detail' key with a list of error
    objects. Our API contract uses a 'message' key with a human-readable string.
    This handler bridges that gap.

    Priority order for the returned message:
      1. Missing required fields (type='missing') → generic missing-fields message.
         Checked first because a missing password is more actionable than a
         password complexity error on a password that doesn't exist.
      2. Field-level value errors → the exact message from our field validator.
         Pydantic v2 prefixes these with 'Value error, ' which is stripped here.

    This handler is registered globally so it applies to all endpoints.
    Each endpoint's Pydantic schema controls which messages are produced.
    """
    errors = exc.errors()
    correlation_id = getattr(request.state, "correlation_id", None)

    # Priority 1: any missing required field → missing-fields message
    for err in errors:
        if err.get("type") == "missing":
            return JSONResponse(
                status_code=422,
                content={
                    "error_code": "VALIDATION_ERROR",
                    "message": "Missing required registration details. Please fix it!",
                    "correlation_id": correlation_id,
                    "details": {},
                },
            )

    # Priority 2: first field-level error → extract its message
    if errors:
        msg = errors[0].get("msg", "Validation error")
        # Pydantic v2 prefixes ValueError messages with 'Value error, ' — strip it.
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": msg,
                "correlation_id": correlation_id,
                "details": {},
            },
        )

    # Fallback (should not be reached in practice)
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Validation error.",
            "correlation_id": correlation_id,
            "details": {},
        },
    )


app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """
    Attach a correlation ID to every request.

    Reads X-Correlation-ID header if present, otherwise generates a UUID.
    Adds it to the response header so clients can reference it when reporting issues.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security-related headers to all responses.

    In development mode, Swagger UI (/docs, /openapi.json) needs a relaxed
    Content-Security-Policy because FastAPI loads Swagger assets from a CDN
    and uses an inline script to initialize the UI.
    """
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=315366000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Swagger UI needs CDN assets + inline script to work
    swagger_paths = ("/docs", "/openapi.json", "/redoc")
    if settings.is_development and request.url.path in swagger_paths:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' https://fastapi.tiangolo.com"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """Returns 200 OK when the application is running."""
    return {"status": "ok", "environment": settings.app_env}


# ---------------------------------------------------------------------------
# Routers — add here as modules are implemented
# ---------------------------------------------------------------------------

app.include_router(auth_router, prefix="/auth", tags=["auth"])
