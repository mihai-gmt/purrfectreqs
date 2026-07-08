"""
FastAPI router for auth endpoints.

All endpoints in this file must:
  - Delegate immediately to service functions — no business logic here
  - Use the correct HTTP method and status code
  - Apply all required FastAPI dependencies

POST /auth/register is the only public endpoint in this module.
All future auth endpoints (/login, /logout, /refresh) are also defined here.

Why keep routing thin?
  The router is just a translation layer: HTTP request → Python function call.
  Keeping business logic in service.py makes it testable without HTTP overhead
  and prevents the router from becoming a dumping ground for one-off logic.
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.schemas import (
    LoginData,
    LoginRequest,
    UserRegisterFormRequest,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.core.database import get_db
from app.core.dependencies import get_correlation_id
from app.core.schemas import ApiResponse

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


def _wants_html(request: Request) -> bool:
    """Return True when a browser explicitly asks for server-rendered HTML."""
    return "text/html" in request.headers.get("accept", "").lower()


async def _parse_json_registration_request(request: Request) -> UserRegisterRequest:
    """
    Parse and validate the JSON API registration payload.

    The endpoint performs content negotiation manually, so it also validates the
    Pydantic model manually and re-raises FastAPI's validation exception type to
    preserve the existing global 422 error shape for API clients.
    """
    try:
        payload = await request.json()
        return UserRegisterRequest.model_validate(payload)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


async def _parse_html_registration_request(request: Request) -> UserRegisterFormRequest:
    """Parse and validate a browser form registration payload."""
    form = await request.form()
    try:
        return UserRegisterFormRequest.model_validate(
            {
                "email": form.get("email"),
                "password": form.get("password"),
                "username": form.get("username"),
                "first_name": form.get("first_name"),
                "last_name": form.get("last_name"),
                "website": form.get("website"),
            }
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    """Render the public, server-rendered registration page."""
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"error_message": None, "form": {}},
    )


@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
) -> Response | UserRegisterResponse:
    """
    Register a new user account.

    Public endpoint — no authentication required. JSON clients keep the existing
    201 response body. Browser clients (`Accept: text/html`) receive the UI flow:
    303 redirect on success, 409 rendered form on duplicate email, and silent
    success-shaped rejection for honeypot bot submissions.
    """
    if _wants_html(request):
        form_request = await _parse_html_registration_request(request)
        try:
            await auth_service.register_browser_user(db, form_request, correlation_id)
        except auth_service.EmailAlreadyExistsError as exc:
            return templates.TemplateResponse(
                request,
                "auth/register.html",
                {"error_message": exc.message, "form": form_request.model_dump()},
                status_code=exc.status_code,
            )
        return RedirectResponse(url="/auth/login", status_code=303)

    json_request = await _parse_json_registration_request(request)
    return await auth_service.register_user(db, json_request, correlation_id)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    """Render a minimal public login-page placeholder for registration redirects."""
    # STUB: replaced by login UI feature.
    return templates.TemplateResponse(request, "auth/login.html", {})


@router.post("/login", response_model=ApiResponse[LoginData], status_code=200)
async def login_user(
    request_body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Authenticate a user and return a JWT access token.

    Public endpoint — no authentication required.

    Verifies email and password, manages failed login tracking with
    automatic account lockout after 5 failures (30-minute lock).

    Returns 200 with access token on success.
    Returns 401 for invalid credentials.
    Returns 403 if the account is locked.
    """
    login_data = await auth_service.login_user(db, request_body, correlation_id)
    return ApiResponse(
        data=login_data,
        message="Login successful.",
        correlation_id=correlation_id,
    )
