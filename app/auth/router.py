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

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.schemas import LoginData, LoginRequest, UserRegisterRequest, UserRegisterResponse
from app.core.schemas import ApiResponse
from app.core.database import get_db
from app.core.dependencies import get_correlation_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register_user(
    request_body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    """
    Register a new user account.

    Public endpoint — no authentication required.

    Validates the payload (password policy, email format, required fields),
    checks for duplicate email/username, hashes the password, and creates
    the user with role=super_user and status=active.

    Returns 201 with a confirmation message on success.
    Returns 409 if the email or username is already registered.
    Returns 422 if the payload fails validation.
    """
    return await auth_service.register_user(db, request_body, correlation_id)


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
