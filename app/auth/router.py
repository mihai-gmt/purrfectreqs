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
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service as auth_service
from app.auth.schemas import UserRegisterRequest, UserRegisterResponse
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_correlation_id(request: Request) -> str:
    """
    Extract the correlation ID attached by the middleware.

    The correlation_id_middleware in app/main.py sets request.state.correlation_id
    on every incoming request. Reading it here propagates the same ID through
    service functions and log entries.
    """
    return getattr(request.state, "correlation_id", "unknown")


@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register_user(
    request_body: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
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
    correlation_id = _get_correlation_id(request)
    return await auth_service.register_user(db, request_body, correlation_id)
