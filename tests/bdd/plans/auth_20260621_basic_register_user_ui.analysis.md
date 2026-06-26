# Codebase Analysis: 20260621 Basic Register User UI

**Feature file:** `tests/features/auth/20260621_basic_register_user_ui.feature`
**Target module:** `app/auth/`
**Date:** 2026-06-21
**Feature type:** UI

---

## Synthesis: What This Means for the Upcoming Feature

- The target module is existing: `app/auth/` contains router, service, models, schemas, JWT, and password utilities.
- The feature is a browser/server-rendered HTML registration flow for `GET /auth/register` and form submission to registration handling.
- The feature contract covers three UI outcomes: successful registration redirects to `/auth/login`, duplicate email returns HTTP 409 and re-renders the registration page with an exact error message, and honeypot-filled submissions silently redirect like success without creating an account.
- Existing API registration already creates `users` records with `role=super_user`, `status=active`, optional `first_name`/`last_name`, and no creator/updater user for self-registration.
- Existing `POST /auth/register` is JSON-oriented: it accepts a Pydantic body and returns `UserRegisterResponse` with HTTP 201.
- Existing browser template infrastructure is present only as `app/templates/base.html`; no `app/templates/auth/` templates were found.
- Static frontend assets are vendored under `app/static/vendor/` for PicoCSS, HTMX, and Alpine.js CSP build.
- Existing BDD tests use `pytest-bdd` step definitions with synchronous wrappers around async HTTP/database operations.
- Existing test fixtures provide `client`, `db_session`, automatic users-table cleanup, and database dependency overrides for FastAPI.
- The existing users migration is `alembic/versions/20260407153113_create_users_table.py`; no migration for this feature is implied by the feature text because it uses existing `users` fields.

---

## 1. File Locations

### 1.1 Feature extraction

- Module from path: `auth`
- Feature type from comment: `UI`
- Feature summary: Browser users can register through a server-rendered registration page. Registration creates an active `super_user` account on the happy path, rejects duplicate email submissions with a rendered error, and silently rejects honeypot bot submissions with the same redirect as success.
- Key entities:
  - Table: `users`
  - Endpoint paths mentioned/implied: `GET /auth/register`, `POST /auth/register`, `/auth/login`
  - Schemas/classes implied by existing implementation: `UserRegisterRequest`, `UserRegisterResponse`, `User`, `UserRole`, `UserStatus`
  - Domain terms: unauthenticated visitor, registration form, hidden honeypot field, HTTP 303 redirect, Location header, auth tokens/cookies, status `active`, role `super_user`, correlation ID
- Search keywords used:
  - `auth`, `register`, `login`, `/auth/register`, `/auth/login`
  - `users`, `email`, `username`, `refresh_tokens`
  - `UserRegisterRequest`, `UserRegisterResponse`, `register_user`
  - `honeypot`, `website`, `company`, `templates/auth`

### 1.2 Target module status

`app/auth/` exists.

Files found:

- `app/auth/__init__.py`
- `app/auth/jwt_handler.py`
- `app/auth/models.py`
- `app/auth/password.py`
- `app/auth/router.py`
- `app/auth/schemas.py`
- `app/auth/service.py`

### 1.3 App wiring

- `app/main.py:24` imports the auth router: `from app.auth.router import router as auth_router`
- `app/main.py:200` wires the auth router: `app.include_router(auth_router, prefix="/auth", tags=["auth"])`
- `app/core/dependencies.py` references auth in a comment/docstring context only: correlation ID extraction is described as needed by every module, not just auth.

### 1.4 Database

Alembic migrations mentioning relevant user/auth table terms:

- `alembic/versions/20260407153113_create_users_table.py`

Data model documentation:

- `docs/DATA_MODELS.md` exists.

### 1.5 Tests and plans

BDD step definition files for this module/feature area:

- `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`
- `tests/bdd/step_defs/test_20260408_basic_login_user_api.py`

Unit tests for this module:

- `tests/unit/auth/__init__.py`
- `tests/unit/auth/test_password_validation.py`

Shared BDD conftest:

- `tests/bdd/conftest.py` exists.

Existing auth plan/analysis/review files:

- `tests/bdd/plans/auth_20260407_basic_register_user_api.plan.md`
- `tests/bdd/plans/auth_20260407_basic_search_users_api.analysis.md`
- `tests/bdd/plans/auth_20260407_basic_search_users_api.plan.md`
- `tests/bdd/plans/auth_20260408_basic_login_user_api.analysis.md`
- `tests/bdd/plans/auth_20260408_basic_login_user_api.plan.md`
- `tests/bdd/plans/auth_20260408_basic_login_user_api.review.md`

### 1.6 Related modules and directories

Other module directories under `app/`:

- `app/admin/`
- `app/documents/`
- `app/gherkin/`
- `app/nlp/`
- `app/projects/`
- `app/traceability/`

Shared/non-domain directories under `app/`:

- `app/core/`
- `app/static/`
- `app/templates/`

Imports referencing `app.auth` were found in:

- `app/main.py`
- `app/auth/router.py`
- `app/auth/service.py`
- `tests/bdd/conftest.py`
- `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`
- `tests/bdd/step_defs/test_20260408_basic_login_user_api.py`
- `tests/unit/auth/test_password_validation.py`

---

## 2. Existing Implementation

### 2.1 Router: `app/auth/router.py`

The auth router declares `router = APIRouter()` and currently exposes two POST endpoints.

#### `POST /auth/register`

File reference: `app/auth/router.py`

- Decorator: `@router.post("/register", response_model=UserRegisterResponse, status_code=201)`
- Request input: `request_body: UserRegisterRequest`
- Dependencies:
  - `db: AsyncSession = Depends(get_db)`
  - `correlation_id: str = Depends(get_correlation_id)`
- Authentication: public endpoint; no `get_current_user` dependency.
- Behavior in router: delegates directly to `auth_service.register_user(db, request_body, correlation_id)`.
- Response model: `UserRegisterResponse`
- Status code: 201
- Correlation ID: injected through dependency and passed to service.

#### `POST /auth/login`

File reference: `app/auth/router.py`

- Decorator: `@router.post("/login", response_model=ApiResponse[LoginData], status_code=200)`
- Request input: `request_body: LoginRequest`
- Dependencies:
  - `db: AsyncSession = Depends(get_db)`
  - `correlation_id: str = Depends(get_correlation_id)`
- Authentication: public endpoint; no `get_current_user` dependency.
- Behavior in router: calls `auth_service.login_user(db, request_body, correlation_id)` and wraps returned data in `ApiResponse`.
- Response model: `ApiResponse[LoginData]`
- Status code: 200
- Correlation ID: injected through dependency, passed to service, and included in success response envelope.

### 2.2 Service: `app/auth/service.py`

#### Exceptions

File reference: `app/auth/service.py`

- `EmailAlreadyExistsError(AppException)`
  - `message`: `Email address already in use. Please login with your existing account!`
  - `error_code`: `EMAIL_ALREADY_EXISTS`
  - `status_code`: 409
- `UsernameAlreadyExistsError(AppException)`
  - `message`: `Username already in use. Please choose a different username!`
  - `error_code`: `USERNAME_ALREADY_EXISTS`
  - `status_code`: 409

The service also imports shared auth-related exceptions from `app.core.exceptions`:

- `AccountLockedError`
- `AppException`
- `InvalidCredentialsError`

#### `register_user`

Signature:

```python
async def register_user(
    db: AsyncSession,
    request: UserRegisterRequest,
    correlation_id: str,
) -> UserRegisterResponse:
```

Observed behavior:

1. Logs a registration attempt at INFO level with `correlation_id` and email domain.
2. Checks duplicate email with `select(User).where(User.email == request.email)`.
3. If duplicate email exists, logs at WARNING level with `correlation_id` and raises `EmailAlreadyExistsError`.
4. Checks duplicate username with `select(User).where(User.username == request.username)`.
5. If duplicate username exists, logs at WARNING level with `correlation_id` and raises `UsernameAlreadyExistsError`.
6. Hashes the password via `hash_password(request.password)`.
7. Creates a `User` model instance with:
   - `email=request.email`
   - `username=request.username`
   - `hashed_password=hashed`
   - `role=UserRole.super_user`
   - `status=UserStatus.active`
   - `first_name=request.first_name`
   - `last_name=request.last_name`
   - `created_by=None`
   - `updated_by=None`
8. Adds the user to the session and flushes with `await db.flush()`.
9. Logs successful registration at INFO level with `correlation_id`, `user_id`, `action=CREATE`, and `table=users`.
10. Returns `UserRegisterResponse(message="Congrats! Your account has been successfully created.")`.

Commit behavior is handled by the `get_db` dependency in normal request flow and by the test override in `tests/bdd/conftest.py`.

#### `login_user`

Signature:

```python
async def login_user(
    db: AsyncSession,
    request: LoginRequest,
    correlation_id: str,
) -> LoginData:
```

Observed behavior:

1. Logs login attempt with `correlation_id` and email domain.
2. Looks up the user by email.
3. Raises `InvalidCredentialsError` if no user exists.
4. Verifies password with `verify_password`.
5. On wrong password, increments `failed_login_attempts`, commits, and locks at five failed attempts.
6. On successful password, checks locked status and locked-until timestamp.
7. Resets failed attempts and updates `last_activity_at`.
8. Generates access token with `create_access_token(user.id, user.role.value)`.
9. Logs successful login with `correlation_id` and `user_id`.
10. Returns `LoginData(access_token=token)`.

### 2.3 Models: `app/auth/models.py`

#### Enums

`UserRole(str, enum.Enum)` values:

- `admin = "admin"`
- `super_user = "super_user"`
- `user = "user"`

`UserStatus(str, enum.Enum)` values:

- `active = "active"`
- `suspended = "suspended"`
- `locked = "locked"`
- `inactive = "inactive"`
- `pending = "pending"`

#### `User` SQLAlchemy model

- Table name: `users`
- Primary key:
  - `id: Integer`, primary key, autoincrement
- Identity fields:
  - `email: String(255)`, unique, not nullable
  - `username: String(100)`, unique, not nullable
  - `hashed_password: String(255)`, not nullable
- RBAC/account fields:
  - `role: Enum(UserRole, name="userrole")`, not nullable, default `UserRole.user`
  - `status: Enum(UserStatus, name="userstatus")`, not nullable, default `UserStatus.pending`
- Login/session fields:
  - `failed_login_attempts: Integer`, not nullable, default `0`
  - `locked_until: DateTime(timezone=True)`, nullable
  - `last_password_change: DateTime(timezone=True)`, nullable
  - `last_activity_at: DateTime(timezone=True)`, nullable
- Name fields:
  - `first_name: String(50)`, nullable
  - `last_name: String(50)`, nullable
- Audit fields:
  - `created_at: DateTime(timezone=True)`, not nullable, default `func.now()`
  - `updated_at: DateTime(timezone=True)`, not nullable, default `func.now()`, onupdate `func.now()`
  - `created_by: Integer`, nullable, FK to `users.id`
  - `updated_by: Integer`, nullable, FK to `users.id`
- Indexes:
  - `ix_users_email`
  - `ix_users_username`
  - `ix_users_status`

### 2.4 Schemas: `app/auth/schemas.py`

#### Validation constants

- `_PASSWORD_PATTERN`: enforces minimum 8 characters, at least one letter, at least one digit, at least one special character from `@$!%*#?&`, and no characters outside the allowed set.
- `_EMAIL_PATTERN`: validates a simple local-part/domain/TLD email shape.
- Error message constants:
  - `MSG_PASSWORD_COMPLEXITY = "Password does not meet the complexity requirements. Please fix it."`
  - `MSG_MISSING_FIELDS = "Missing required registration details. Please fix it!"`
  - `MSG_EMAIL_FORMAT = "Incorrect email address format. Please fix it."`

#### `UserRegisterRequest`

Fields:

- `email: str`
- `password: str`
- `username: str`
- `first_name: str | None = None`
- `last_name: str | None = None`

Validators:

- `validate_email`: raises `ValueError(MSG_EMAIL_FORMAT)` if `_EMAIL_PATTERN` does not match.
- `validate_password`: raises `ValueError(MSG_PASSWORD_COMPLEXITY)` if `_PASSWORD_PATTERN` does not match.
- `validate_username`: raises `ValueError(MSG_MISSING_FIELDS)` if username is empty or whitespace-only.

#### `UserRegisterResponse`

- `model_config = ConfigDict(from_attributes=True)`
- Field:
  - `message: str`

#### `LoginRequest`

Fields:

- `email: str`
- `password: str`

#### `LoginData`

- `model_config = ConfigDict(from_attributes=True)`
- Fields:
  - `access_token: str`
  - `token_type: str = "bearer"`

### 2.5 Other auth files

#### `app/auth/password.py`

Exports:

- `hash_password(plain_password: str) -> str`
- `verify_password(plain_password: str, hashed_password: str) -> bool`

Implementation uses `passlib.context.CryptContext(schemes=["argon2"], deprecated="auto")`.

#### `app/auth/jwt_handler.py`

Exports:

- `create_access_token(user_id: int, role: str) -> str`

Observed JWT claims:

- `sub`
- `role`
- `exp`
- `iat`
- `jti`

Settings are read from `app.core.config.settings`.

#### `app/auth/__init__.py`

No text exports were present when read.

### 2.6 Existing frontend files

#### `app/templates/base.html`

- Loads PicoCSS from `/static/vendor/pico/2.1.1/pico.min.css`.
- Provides `{% block title %}`, `{% block extra_css %}`, `{% block flash %}`, `{% block content %}`, and `{% block extra_js %}`.
- Contains a nav with a Login link for unauthenticated visitors.
- Loads HTMX from `/static/vendor/htmx/2.0.9/htmx.min.js`.
- Loads Alpine.js CSP build from `/static/vendor/alpinejs/3.15.11/cspAlpine.min.js` with `defer`.

No `app/templates/auth/` directory or auth-specific templates were found in the locator pass.

### 2.7 Data flow: existing API registration path

Existing request path for `POST /auth/register` JSON registration:

1. Client sends `POST /auth/register`.
2. FastAPI validates JSON body into `UserRegisterRequest`.
3. `get_db` provides an `AsyncSession`.
4. `get_correlation_id` reads the request correlation ID from middleware state.
5. Router function `register_user` calls `auth_service.register_user(db, request_body, correlation_id)`.
6. Service checks duplicate email and duplicate username against the `users` table.
7. Service raises `EmailAlreadyExistsError` or `UsernameAlreadyExistsError` for conflicts.
8. App-level exception handler converts `AppException` into standardized JSON error response.
9. If no conflict, service hashes the password and creates a `User` record.
10. Service flushes the session, logs the create event, and returns `UserRegisterResponse`.
11. The database session commits after the request through dependency management.
12. Router returns the response body with HTTP 201.

---

## 3. Patterns and Examples

### 3.1 Endpoint pattern

#### Existing registration endpoint

File reference: `app/auth/router.py`

```python
@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register_user(
    request_body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    return await auth_service.register_user(db, request_body, correlation_id)
```

#### Existing login endpoint with `ApiResponse`

File reference: `app/auth/router.py`

```python
@router.post("/login", response_model=ApiResponse[LoginData], status_code=200)
async def login_user(
    request_body: LoginRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    login_data = await auth_service.login_user(db, request_body, correlation_id)
    return ApiResponse(
        data=login_data,
        message="Login successful.",
        correlation_id=correlation_id,
    )
```

#### Router wiring pattern

File reference: `app/main.py`

```python
from app.auth.router import router as auth_router

app.include_router(auth_router, prefix="/auth", tags=["auth"])
```

### 3.2 Service function pattern

File reference: `app/auth/service.py`

```python
async def register_user(
    db: AsyncSession,
    request: UserRegisterRequest,
    correlation_id: str,
) -> UserRegisterResponse:
    logger.info(
        "Registration attempt",
        extra={
            "correlation_id": correlation_id,
            "email_domain": request.email.split("@")[-1],
        },
    )
```

Duplicate email handling pattern:

```python
existing_email = await db.execute(select(User).where(User.email == request.email))
if existing_email.scalars().first() is not None:
    logger.warning(
        "Registration rejected: email already exists",
        extra={"correlation_id": correlation_id},
    )
    raise EmailAlreadyExistsError()
```

User creation pattern:

```python
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
```

### 3.3 Schema pattern

File reference: `app/auth/schemas.py`

```python
class UserRegisterRequest(BaseModel):
    email: str
    password: str
    username: str
    first_name: str | None = None
    last_name: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_PATTERN.match(v):
            raise ValueError(MSG_EMAIL_FORMAT)
        return v
```

Response schema pattern:

```python
class UserRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
```

Shared success envelope pattern:

File reference: `app/core/schemas.py`

```python
class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: str
    correlation_id: str
```

### 3.4 Exception pattern

Auth-specific exception pattern:

File reference: `app/auth/service.py`

```python
class EmailAlreadyExistsError(AppException):
    """Raised when a registration attempt uses an email already in the system."""

    def __init__(self) -> None:
        super().__init__(
            message=("Email address already in use. Please login with your existing account!"),
            error_code="EMAIL_ALREADY_EXISTS",
            status_code=409,
        )
```

Shared exception response pattern:

File reference: `app/core/exceptions.py`

```python
class AppException(Exception):
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
        self.details = details
        super().__init__(message)
```

Exception handler pattern:

File reference: `app/core/exceptions.py`

```python
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
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
```

### 3.5 Migration pattern

File reference: `alembic/versions/20260407153113_create_users_table.py`

Revision identifiers:

```python
revision = "20260407153113"
down_revision = None
branch_labels = None
depends_on = None
```

Upgrade pattern:

```python
def upgrade() -> None:
    """Create users table with enums, indexes, and constraints."""
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
        sa.Column("role", userrole, nullable=False, server_default="user"),
        sa.Column("status", userstatus, nullable=False, server_default="pending"),
    )
```

Index pattern:

```python
op.create_index("ix_users_email", "users", ["email"])
op.create_index("ix_users_username", "users", ["username"])
op.create_index("ix_users_status", "users", ["status"])
```

Downgrade pattern:

```python
def downgrade() -> None:
    """Drop users table and its enum types."""
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    sa.Enum(name="userstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
```

### 3.6 Test patterns

#### `scenarios()` usage

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../../features/auth/20260407_basic_register_user_api.feature")
```

File reference: `tests/bdd/step_defs/test_20260408_basic_login_user_api.py`

```python
scenarios("../../features/auth/20260408_basic_login_user_api.feature")
```

#### Async helper pattern for sync BDD steps

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
def _run(coro):
    """Run an async coroutine from a sync step function."""
    return asyncio.get_event_loop().run_until_complete(coro)
```

#### Datatable parsing pattern

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
def _table_to_dict(datatable: list[list[str]]) -> dict:
    headers = datatable[0]
    values = datatable[1]
    return dict(zip(headers, values, strict=True))
```

#### Given setup pattern

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
@given(parsers.parse('an account already exists with the email address "{email}"'))
def account_exists_with_email(email: str, db_session: AsyncSession, context: dict):
    from sqlalchemy import func as sa_func

    from app.auth.models import User
    from app.auth.password import hash_password

    user = User(
        email=email,
        username="existing.user",
        hashed_password=hash_password("Existing1!"),
        role="super_user",
        status="active",
        created_by=None,
    )
    db_session.add(user)
    _run(db_session.commit())
    _run(db_session.refresh(user))
```

#### When HTTP request pattern

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
@when("I register with the following details:")
def register_with_details(
    datatable: list[list[str]],
    client: AsyncClient,
    context: dict,
):
    payload = _table_to_dict(datatable)
    context["attempted_email"] = payload.get("email", "")
    clean_payload = {k: v for k, v in payload.items() if v != ""}
    response = _run(client.post("/auth/register", json=clean_payload))
    context["response"] = response
```

#### Then status assertion pattern

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
@then(parsers.parse("I receive a {status_code:d} response"))
def assert_status_code(context: dict, status_code: int):
    assert context["response"].status_code == status_code, (
        f"Expected HTTP {status_code}, got {context['response'].status_code}. Body: {context['response'].text}"
    )
```

#### Then database assertion pattern

File reference: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`

```python
@then('my account is created with status "active" and role "super_user"')
def account_created_with_correct_status_and_role(
    context: dict,
    db_session: AsyncSession,
):
    from app.auth.models import User

    email = context["attempted_email"]
    result = _run(db_session.execute(select(User).where(User.email == email)))
    user = result.scalars().first()

    assert user is not None
    assert user.status.value == "active"
    assert user.role.value == "super_user"
```

#### Unit test schema-validation pattern

File reference: `tests/unit/auth/test_password_validation.py`

```python
def make_request(**overrides) -> dict:
    data = {
        "email": "test@example.com",
        "password": "Valid1234!",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
    }
    data.update(overrides)
    return data
```

```python
def test_valid_registration_data():
    request = UserRegisterRequest(**make_request())
    assert request.email == "test@example.com"
    assert request.username == "testuser"
    assert request.password == "Valid1234!"
```

### 3.7 Conftest patterns

#### Loading environment and model imports

File reference: `tests/bdd/conftest.py`

```python
load_dotenv()
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.auth.models  # noqa: F401, E402
from app.core.database import Base, get_db  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
```

#### Test engine fixture

File reference: `tests/bdd/conftest.py`

```python
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

#### Database session fixture

File reference: `tests/bdd/conftest.py`

```python
@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()
```

#### Cleanup fixture

File reference: `tests/bdd/conftest.py`

```python
@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    try:
        from sqlalchemy import delete

        from app.auth.models import User

        async with test_engine.begin() as conn:
            await conn.execute(delete(User))
    except ImportError:
        pass

    yield
```

#### Client fixture and dependency override

File reference: `tests/bdd/conftest.py`

```python
@pytest_asyncio.fixture
async def client(test_engine, db_session):  # noqa: ARG001
    app_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with app_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
```

#### Scenario context fixture

File reference: `tests/bdd/conftest.py`

```python
@pytest.fixture
def context() -> dict:
    return {}
```
