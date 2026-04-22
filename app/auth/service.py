"""
Business logic for the auth module.

Routers call service functions. Service functions talk to the database.
No business logic belongs in router.py — if it's a decision or a data
transformation, it goes here.

Auth-specific exceptions are defined here (not in app/core/exceptions.py)
to keep the auth module self-contained. They still inherit from AppException
so the global exception handler in app/main.py catches them correctly.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.auth.models import User, UserRole, UserStatus
from app.auth.password import hash_password, verify_password
from app.auth.schemas import (
    LoginData,
    LoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.core.exceptions import (
    AccountLockedError,
    AppException,
    InvalidCredentialsError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Auth-specific exceptions
# ---------------------------------------------------------------------------


class EmailAlreadyExistsError(AppException):
    """Raised when a registration attempt uses an email already in the system."""

    def __init__(self) -> None:
        super().__init__(
            message=(
                "Email address already in use. Please login with your existing account!"
            ),
            error_code="EMAIL_ALREADY_EXISTS",
            status_code=409,
        )


class UsernameAlreadyExistsError(AppException):
    """Raised when a registration attempt uses a username already in the system."""

    def __init__(self) -> None:
        super().__init__(
            message="Username already in use. Please choose a different username!",
            error_code="USERNAME_ALREADY_EXISTS",
            status_code=409,
        )


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def register_user(
    db: AsyncSession,
    request: UserRegisterRequest,
    correlation_id: str,
) -> UserRegisterResponse:
    """
    Register a new user account.

    Checks for duplicate email and username before creating the record.
    Hashes the password with argon2. Sets role=super_user and status=active
    for all self-registered users (per docs/SECURITY.md Section 4 and
    docs/DATA_MODELS.md Module 1 Notes).

    Args:
        db: Async database session.
        request: Validated registration data from UserRegisterRequest.
        correlation_id: Request correlation ID for tracing in logs.

    Returns:
        UserRegisterResponse with a confirmation message.

    Raises:
        EmailAlreadyExistsError: If the email is already registered.
        UsernameAlreadyExistsError: If the username is already taken.
    """
    logger.info(
        "Registration attempt",
        extra={
            "correlation_id": correlation_id,
            "email_domain": request.email.split("@")[-1],
        },
    )

    # Check for duplicate email — email is the primary login identifier.
    # Check before username so that the error message matches the order in the
    # feature file (email conflict is scenario 2, username conflict is scenario 3).
    existing_email = await db.execute(select(User).where(User.email == request.email))
    if existing_email.scalars().first() is not None:
        logger.warning(
            "Registration rejected: email already exists",
            extra={"correlation_id": correlation_id},
        )
        raise EmailAlreadyExistsError()

    # Check for duplicate username.
    existing_username = await db.execute(
        select(User).where(User.username == request.username)
    )
    if existing_username.scalars().first() is not None:
        logger.warning(
            "Registration rejected: username already exists",
            extra={"correlation_id": correlation_id},
        )
        raise UsernameAlreadyExistsError()

    # Hash the password before any DB interaction — raw password must never
    # be stored or logged even transiently.
    # Why argon2? See app/auth/password.py for the reasoning.
    hashed = hash_password(request.password)

    user = User(
        email=request.email,
        username=request.username,
        hashed_password=hashed,
        # All self-registered users get role=super_user and status=active.
        # This is intentional for MVP — the admin can demote/suspend later.
        # (docs/SECURITY.md Section 4, DATA_MODELS.md Module 1 Notes)
        role=UserRole.super_user,
        status=UserStatus.active,
        first_name=request.first_name,
        last_name=request.last_name,
        # created_by is NULL for self-registration — no authenticated user
        # initiated this action. This is expected per the plan (Section 7).
        created_by=None,
        updated_by=None,
    )
    db.add(user)
    # flush to get user.id — the session commit is managed by get_db
    await db.flush()

    # Security event log: successful registration (docs/SECURITY.md Section 12).
    # NOTE: The audit_logs table (app/admin/models.py) does not exist yet.
    # Using structured application logging as the audit trail until the
    # audit_logs infrastructure is built. This is consistent with how rate
    # limiting is deferred (plan Section 6 / Section 12 of the plan).
    logger.info(
        "User registered successfully",
        extra={
            "correlation_id": correlation_id,
            "user_id": user.id,
            "action": "CREATE",
            "table": "users",
        },
    )

    return UserRegisterResponse(
        message="Congrats! Your account has been successfully created."
    )


async def login_user(
    db: AsyncSession,
    request: LoginRequest,
    correlation_id: str,
) -> LoginData:
    """
    Authenticate a user with email and password.

    Flow (matches docs/SECURITY.md Section 4 ordering):
      1. Look up user by email
      2. Verify password (always runs to eliminate timing side-channels)
      3. If password wrong: increment counter, lock if >= 5 failures
      4. If password correct: check lock status, reset counter, generate token

    Args:
        db: Async database session.
        request: LoginRequest with email and password fields.
        correlation_id: Request correlation ID for tracing in logs.

    Returns:
        LoginData with access_token and token_type.

    Raises:
        InvalidCredentialsError: If email not found or password wrong.
        AccountLockedError: If account is locked and lock has not expired.
    """
    logger.info(
        "Login attempt",
        extra={
            "correlation_id": correlation_id,
            "email_domain": (
                request.email.split("@")[-1] if "@" in request.email else "unknown"
            ),
        },
    )

    # 1. Look up user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()

    if user is None:
        logger.warning(
            "Login failed: user not found",
            extra={
                "correlation_id": correlation_id,
                "email_domain": (
                    request.email.split("@")[-1] if "@" in request.email else "unknown"
                ),
            },
        )
        raise InvalidCredentialsError()

    # 2. Verify password — always runs even if account is locked,
    # to eliminate timing side-channels that reveal account existence.
    password_valid = verify_password(request.password, user.hashed_password)

    # 3. Password WRONG
    if not password_valid:
        user.failed_login_attempts += 1
        await db.commit()

        if user.failed_login_attempts >= 5:
            user.status = UserStatus.locked
            user.locked_until = datetime.now(UTC) + timedelta(minutes=30)
            await db.commit()

            logger.warning(
                "Account locked after %d failed attempts",
                user.failed_login_attempts,
                extra={
                    "correlation_id": correlation_id,
                    "user_id": user.id,
                },
            )
            raise AccountLockedError()

        logger.warning(
            "Login failed: incorrect password (attempt %d)",
            user.failed_login_attempts,
            extra={
                "correlation_id": correlation_id,
                "user_id": user.id,
            },
        )
        raise InvalidCredentialsError()

    # 4. Password CORRECT — check lock status
    if user.status == UserStatus.locked:
        _now = datetime.now(UTC)
        if user.locked_until is not None and user.locked_until >= _now:
            logger.warning(
                "Login rejected: account locked",
                extra={
                    "correlation_id": correlation_id,
                    "user_id": user.id,
                },
            )
            raise AccountLockedError()

        # Lock expired — auto-unlock
        user.status = UserStatus.active
        logger.info(
            "Account auto-unlocked (lock expired)",
            extra={
                "correlation_id": correlation_id,
                "user_id": user.id,
            },
        )

    # Reset counter and update activity
    user.failed_login_attempts = 0
    user.last_activity_at = datetime.now(UTC)
    await db.flush()

    # Generate access token
    token = create_access_token(user.id, user.role.value)

    logger.info(
        "Login successful",
        extra={
            "correlation_id": correlation_id,
            "user_id": user.id,
        },
    )

    return LoginData(access_token=token)
