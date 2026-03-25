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

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

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

app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.project_version,
    docs_url="/docs" if settings.is_development else None,
    redoc_url=None,
)

# ---------------------------------------------------------------------------
# Static files and templates
# ---------------------------------------------------------------------------

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

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
    """
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = (
        "max-age=315366000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
async def health_check():
    """Returns 200 OK when the application is running."""
    return {"status": "ok", "environment": set.app_env}


# ---------------------------------------------------------------------------
# Routers — add here as modules are implemented
# ---------------------------------------------------------------------------

# from app.auth.router import router as auth_router
# app.include_router(auth_router, prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info(
        "Purrfectreqs starting",
        extra={"environment": settings.app_env, "debug": settings.app_debug},
    )
