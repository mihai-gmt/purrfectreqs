# Codebase Analysis: Search users

**Feature file:** `tests/features/auth/20260407_basic_search_users_api.feature`
**Target module:** `app/auth/`
**Date:** 2026-04-07
**Feature type:** API

---

## Synthesis: What This Means for the Upcoming Feature

- The auth module already exists with all required files (router, service, models, schemas, password utilities)
- The register endpoint pattern (router.py:43-63) can be followed directly for the search endpoint - same structure, different service call
- The existing service function pattern (service.py:61-158) shows how to implement database operations with proper error handling
- The User model already exists and is fully defined with all required fields
- The exception handling pattern (service.py:31-54) shows how to create custom exceptions with proper status codes
- The existing test patterns (step_defs/test_20260407_basic_register_user_api.py) show the BDD approach for testing
- The auth module is already wired into app/main.py
- No new database migrations needed - users table already exists
- The search endpoint should return user information in a similar structure to the registration response

---

## 1. File Locations

1. TARGET MODULE STATUS
- `app/auth/` exists with files: app/auth/__init__.py, app/auth/password.py, app/auth/router.py, app/auth/schemas.py, app/auth/models.py, app/auth/service.py
- No other files in auth module

2. APP WIRING
- `app/main.py` imports auth router (grep shows "from app.auth.router import router")
- `app/core/` has no files referencing auth

3. DATABASE
- Alembic migration files mentioning users: alembic/versions/467079342047_create_users_table.py
- `docs/DATA_MODELS.md` exists

4. TESTS
- `tests/bdd/step_defs/` has no auth files
- `tests/unit/auth/` has test files
- `tests/bdd/conftest.py` exists
- `tests/bdd/plans/` has auth plan files

5. RELATED MODULES
- Other modules: app/core/, app/main.py, app/auth/
- No modules reference auth in imports

---

## 2. Existing Implementation

### ROUTER (app/auth/router.py)
- Contains `/register` endpoint (POST) with response_model `UserRegisterResponse` and status_code 201
- Uses dependency `get_db` for database session
- Injects `Request` for correlation_id extraction
- Correlation_id obtained via `_get_correlation_id()` function reading `request.state.correlation_id` (line 40)

### SERVICE (app/auth/service.py)
- Defines `register_user()` function with signature `async def register_user(db: AsyncSession, request: UserRegisterRequest, correlation_id: str) -> UserRegisterResponse` (line 61)
- Defines two exceptions: `EmailAlreadyExistsError` (line 31) and `UsernameAlreadyExistsError` (line 45), both with status_code 409
- Uses `db.flush()` to get user.id after adding (line 139) but relies on `get_db` for session commit
- Implements audit logging via `logger.info()` calls with correlation_id (lines 86-92, 146-154)

### MODELS (app/auth/models.py)
- Defines `User` SQLAlchemy model (line 50) with fields: id (int), email (str), username (str), hashed_password (str), role (UserRole enum), status (UserStatus enum), failed_login_attempts (int), locked_until (datetime), last_password_change (datetime), last_activity_at (datetime), first_name (str), last_name (str), created_at (datetime), updated_at (datetime), created_by (int), updated_by (int)
- Defines `UserRole` enum with values: admin, super_user, user (line 32)
- Defines `UserStatus` enum with values: active, suspended, locked, inactive, pending (line 40)
- Has indexes on email, username, and status columns (lines 117-119)

### SCHEMAS (app/auth/schemas.py)
- Defines `UserRegisterRequest` Pydantic model with fields: email, password, username, first_name, last_name (line 59)
- Defines `UserRegisterResponse` Pydantic model with field: message (line 112)
- Includes validators for email (line 73), password (line 81), and username (line 98)

### OTHER FILES
- `app/auth/password.py` exports `hash_password()` and `verify_password()` functions
- `app/auth/__init__.py` is empty

### DATA FLOW
Registration flow: Router (`register_user` endpoint) → Service (`register_user` function) → DB (SQLAlchemy User model). Errors propagate through exceptions (`EmailAlreadyExistsError`, `UsernameAlreadyExistsError`) back to router which returns appropriate HTTP status codes.

---

## 3. Patterns and Examples

## 1. ENDPOINT PATTERN
From `/app/auth/router.py` lines 43-63:
```python
@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register_user(
    request_body: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    ...
    """
    correlation_id = _get_correlation_id(request)
    return await auth_service.register_user(db, request_body, correlation_id)
```

## 2. SERVICE FUNCTION PATTERN
From `/app/auth/service.py` lines 61-158:
```python
async def register_user(
    db: AsyncSession,
    request: UserRegisterRequest,
    correlation_id: str,
) -> UserRegisterResponse:
    """
    Register a new user account.
    ...
    """
    logger.info(
        "Registration attempt",
        extra={
            "correlation_id": correlation_id,
            "email_domain": request.email.split("@")[-1],
        },
    )
    # Check for duplicate email
    existing_email = await db.execute(select(User).where(User.email == request.email))
    if existing_email.scalars().first() is not None:
        logger.warning(
            "Registration rejected: email already exists",
            extra={"correlation_id": correlation_id},
        )
        raise EmailAlreadyExistsError()

    # Check for duplicate username
    existing_username = await db.execute(
        select(User).where(User.username == request.username)
    )
    if existing_username.scalars().first() is not None:
        logger.warning(
            "Registration rejected: username already exists",
            extra={"correlation_id": correlation_id},
        )
        raise UsernameAlreadyExistsError()

    # Create user record
    hashed = hash_password(request.password)
    user = User(
        email=request.email,
        username=request.username,
        hashed_password=hashed,
        role=UserRole.super_user,
        status=UserStatus.active,
        first_name=request.first_name,
        last_name=request.last_name,
        created_by=None,
        updated_by=None,
    )
    db.add(user)
    await db.flush()

    # Log successful creation
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
```

## 3. SCHEMA PATTERN
From `/app/auth/schemas.py` lines 59-105:
```python
class UserRegisterRequest(BaseModel):
    """
    Payload for POST /auth/register.
    ...
    """

    email: str
    password: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Reject email addresses that do not match the expected format."""
        if not _EMAIL_PATTERN.match(v):
            raise ValueError(MSG_EMAIL_FORMAT)
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Enforce the password policy from docs/SECURITY.md Section 2.
        ...
        """
        if not _PASSWORD_PATTERN.match(v):
            raise ValueError(MSG_PASSWORD_COMPLEXITY)
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Reject empty or whitespace-only usernames."""
        if not v or not v.strip():
            raise ValueError(MSG_MISSING_FIELDS)
        return v
```

## 4. EXCEPTION PATTERN
From `/app/auth/service.py` lines 31-54:
```python
class EmailAlreadyExistsError(AppException):
    """Raised when a registration attempt uses an email already in the system."""

    def __init__(self) -> None:
        super().__init__(
            message=(
                "Email address already in use. "
                "Please login with your existing account!"
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
```

## 5. MIGRATION PATTERN
From `/alembic/versions/20260407153113_create_users_table.py`:
```python
def upgrade() -> None:
    """Create users table with enums, indexes, and constraints."""
    # Create enum types first
    userrole = sa.Enum("admin", "super_user", "user", name="userrole", create_type=True)
    userstatus = sa.Enum(
        "active",
        "suspended",
        "locked",
        "inactive",
        "pending",
        name="userstatus",
        create_type=True,
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        # ... other columns
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
        # ... constraints
    )

    # Indexes
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_status", "users", ["status"])
```

## 6. TEST PATTERNS
From `/tests/bdd/step_defs/test_20260407_basic_register_user_api.py`:
a. `scenarios("../../features/auth/20260407_basic_register_user_api.feature")`
b. `@given(parsers.parse("no user account exist for the following user registration data:"))`
c. `@when("I register with the following details:")`
d. `@then('my account is created with status "active" and role "super_user"')`

## 7. CONFTEST PATTERNS
From `/tests/bdd/conftest.py` lines 141-161:
```python
@pytest_asyncio.fixture
async def client(db_session):
    """
    Async HTTP client pointed at the FastAPI test app.
    ...
    """

    async def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
```