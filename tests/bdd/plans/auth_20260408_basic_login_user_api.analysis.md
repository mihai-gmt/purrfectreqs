# Codebase Analysis: Basic Login User API

**Feature file:** `tests/features/auth/20260408_basic_login_user_api.feature`
**Target module:** `app/auth/`
**Date:** 2026-04-16
**Feature type:** API

---

## Synthesis: What This Means for the Upcoming Feature

- The `app/auth/` module already exists with router, service, models, schemas, and password utilities. This is an **extension**, not a new module.
- The `User` model already has `failed_login_attempts` (Integer, default=0), `locked_until` (DateTime, nullable), and `status` (Enum including `locked`). No schema migration needed for these fields.
- `verify_password` exists in `app/auth/password.py` but is **not yet called** anywhere — it was built for this feature.
- `InvalidCredentialsError` (401) and `AcocuntLockedError` (403) are already defined in `app/core/exceptions.py`. However, the feature file specifies status `423` for locked accounts and `error_code="ACCOUNT_LOCKED"`, while the existing `AccountLockedError` uses status `403`. The feature file also specifies different message text. These will need to be reconciled — the `.feature` file takes precedence per CLAUDE.md. Also note the existing class has a typo: `AccountLockedError` (missing 'c').
- The feature file specifies error_code `"UNAUTHORIZED"` for bad credentials. The existing `InvalidCredentialsError` in `core/exceptions.py` needs to be checked for matching error_code and message.
- No JWT token generation exists yet — the feature requires returning "a valid authorization token" in `response.data`. Token generation/signing infrastructure will need to be built.
- The existing `POST /register` endpoint and its BDD tests provide a complete template for the router/service/test structure.
- The `conftest.py` already has `clean_tables`, `db_session`, `client`, and `context` fixtures. The login tests can reuse all of them.
- BDD step defs use synchronous wrappers (`_run()`) around async calls and pass state via the `context` dict fixture.
- The `ApiResponse` envelope pattern (`{"data": ..., "message": ..., "correlation_id": ...}`) is referenced in the feature but needs to be verified against `app/core/schemas.py` for exact structure.
- The router delegates immediately to service — no business logic in router. Login must follow the same pattern.

---

## 1. File Locations

### Target Module Status
`app/auth/` exists with 6 files:
- `app/auth/__init__.py`
- `app/auth/models.py`
- `app/auth/password.py`
- `app/auth/router.py`
- `app/auth/schemas.py`
- `app/auth/service.py`

### App Wiring
- `app/main.py:24` — imports auth router: `from app.auth.router import router as auth_router`
- `app/main.py:204` — wires router: `app.include_router(auth_router, prefix="/auth", tags=["auth"])`
- `app/core/dependencies.py` — references auth

### Database
- Migration: `alembic/versions/20260407153113_create_users_table.py`
- `docs/DATA_MODELS.md` — exists

### Tests
- BDD step defs: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py`
- Unit tests: `tests/unit/auth/test_password_validation.py`
- `tests/bdd/conftest.py` — exists
- Existing plans: `tests/bdd/plans/auth_20260407_basic_register_user_api.plan.md`, `tests/bdd/plans/auth_20260407_basic_search_users_api.plan.md`, `tests/bdd/plans/auth_20260407_basic_search_users_api.analysis.md`

### Related Modules
- Other modules under `app/`: `admin`, `core`, `documents`, `gherkin`, `nlp`, `projects`, `traceability`
- Auth is imported in: `app/auth/router.py`, `app/auth/service.py`, `app/main.py`

---

## 2. Existing Implementation

### Router (`app/auth/router.py`)
- Single endpoint: `POST /register` at line 33, `response_model=UserRegisterResponse`, `status_code=201`
- Dependencies: `db: AsyncSession = Depends(get_db)`, `correlation_id: str = Depends(get_correlation_id)`
- Delegates immediately to `auth_service.register_user(db, request_body, correlation_id)` at line 52

### Service (`app/auth/service.py`)
- Custom exceptions (inherit `AppException`):
  - `EmailAlreadyExistsError` (line 31) — status 409, error_code `"EMAIL_ALREADY_EXISTS"`
  - `UsernameAlreadyExistsError` (line 45) — status 409, error_code `"USERNAME_ALREADY_EXISTS"`
- `register_user(db, request, correlation_id) -> UserRegisterResponse` (line 61):
  - Logs attempt with `correlation_id` and email domain (lines 86-92)
  - Checks email uniqueness via `select(User).where(User.email == ...)` (lines 97-103)
  - Checks username uniqueness (lines 106-114)
  - Calls `hash_password()`, constructs `User()`, `db.add()`, `await db.flush()` (lines 119-139)
  - Commit managed by `get_db` dependency
  - Audit via `logger.info()` with `user_id`, `action="CREATE"`, `table="users"` (lines 146-154)

### Models (`app/auth/models.py`)
- `UserRole` enum (line 32): `admin`, `super_user`, `user`
- `UserStatus` enum (line 40): `active`, `suspended`, `locked`, `inactive`, `pending`
- `User` table `"users"` (line 50):
  - `id` — Integer, PK, autoincrement (line 68)
  - `email` — String(255), unique, not null (line 71)
  - `username` — String(100), unique, not null (line 72)
  - `hashed_password` — String(255), not null (line 73)
  - `role` — Enum(UserRole), not null (lines 76-78)
  - `status` — Enum(UserStatus), not null (lines 81-83)
  - `failed_login_attempts` — Integer, not null, default=0 (lines 86-88)
  - `locked_until` — DateTime, nullable (line 89)
  - `last_password_change`, `last_activity_at` — DateTime, nullable (lines 90-93)
  - `first_name`, `last_name` — String(50), nullable (lines 96-97)
  - `created_at`, `updated_at` — DateTime, not null (lines 100-105)
  - `created_by`, `updated_by` — Integer, self-referential FK, nullable (lines 107-112)
  - Indexes: `ix_users_email`, `ix_users_username`, `ix_users_status` (lines 116-120)

### Schemas (`app/auth/schemas.py`)
- `UserRegisterRequest` (line 59): `email`, `password`, `username`, `first_name`, `last_name`
  - Validators: `validate_email` (regex), `validate_password` (min 8, letter+digit+special), `validate_username`
- `UserRegisterResponse` (line 112): `message: str`, `ConfigDict(from_attributes=True)`

### Other Files
- `app/auth/password.py`: exports `hash_password(plain_password) -> str` (line 30) and `verify_password(plain_password, hashed_password) -> bool` (line 46). Uses `passlib.CryptContext` with Argon2. `verify_password` is defined but **not yet called** anywhere.

### Data Flow — POST /auth/register
1. Request → `router.py:34` → FastAPI injects `db` and `correlation_id`
2. `UserRegisterRequest` Pydantic validation (422 on invalid)
3. `auth_service.register_user()` called
4. DB queries for uniqueness → `AppException` subclass on conflict
5. `hash_password()` → `User()` → `db.add()` → `db.flush()`
6. `get_db` commits/rolls back after route returns
7. `UserRegisterResponse` returned with status 201
8. On `AppException`, global handler in `app/main.py` converts to HTTP error

---

## 3. Patterns and Examples

### Endpoint Pattern
`app/auth/router.py:33-52`
```python
@router.post("/register", response_model=UserRegisterResponse, status_code=201)
async def register_user(
    request_body: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(get_correlation_id),
):
    return await auth_service.register_user(db, request_body, correlation_id)
```

### Service Function Pattern
`app/auth/service.py:61-158`
```python
async def register_user(
    db: AsyncSession,
    request: UserRegisterRequest,
    correlation_id: str,
) -> UserRegisterResponse:
    logger.info(
        "Registration attempt",
        extra={"correlation_id": correlation_id, "email_domain": request.email.split("@")[-1]},
    )
    existing_email = await db.execute(select(User).where(User.email == request.email))
    if existing_email.scalars().first() is not None:
        logger.warning("Registration rejected: email already exists",
                       extra={"correlation_id": correlation_id})
        raise EmailAlreadyExistsError()
    # ... create user, db.add(user), await db.flush() ...
    logger.info("User registered successfully",
                extra={"correlation_id": correlation_id, "user_id": user.id,
                       "action": "CREATE", "table": "users"})
    return UserRegisterResponse(message="Congrats! Your account has been successfully created.")
```
Pattern: `logger.info` on entry, `logger.warning` on rejection, `logger.info` on success. `await db.flush()` (not commit). Commit managed by `get_db`.

### Schema Pattern
`app/auth/schemas.py:59-122`
```python
class UserRegisterRequest(BaseModel):
    email: str
    password: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_PATTERN.match(v):
            raise ValueError(MSG_EMAIL_FORMAT)
        return v

class UserRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message: str
```
Error messages are module-level string constants.

### Exception Pattern
`app/core/exceptions.py:43-103`
```python
class AppException(Exception):
    def __init__(self, message: str, error_code: str,
                 status_code: int = 400, details: dict[str, Any] | None = None):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
```

Auth-specific exceptions in `app/auth/service.py:31-53`:
```python
class EmailAlreadyExistsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Email address already in use. Please login with your existing account!",
            error_code="EMAIL_ALREADY_EXISTS",
            status_code=409,
        )
```

Pre-existing in `app/core/exceptions.py`: `InvalidCredentialsError` (401) and `AccountLockedError` (403, note typo).

### Migration Pattern
`alembic/versions/20260407153113_create_users_table.py`
```python
revision = "20260407153113"   # timestamp-based: YYYYMMDDHHMMSS
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    userrole = sa.Enum("admin", "super_user", "user", name="userrole", create_type=True)
    op.create_table("users", sa.Column(...), ...)
    op.create_index("ix_users_email", "users", ["email"])

def downgrade() -> None:
    op.drop_index(...)
    op.drop_table("users")
    sa.Enum(name="userstatus").drop(op.get_bind(), checkfirst=True)
```
Hand-written. Enums created before `op.create_table`. Index naming: `ix_<table>_<column>`.

### BDD Test Pattern
`tests/bdd/step_defs/test_20260407_basic_register_user_api.py:34`
```python
scenarios("../../features/auth/20260407_basic_register_user_api.feature")
```

```python
@given(parsers.parse('an account already exists with the email address "{email}"'))
def account_exists_with_email(email: str, db_session: AsyncSession, context: dict):
    user = User(email=email, username="existing.user", ...)
    db_session.add(user)
    _run(db_session.commit())

@when("I register with the following details:")
def register_with_details(datatable, client: AsyncClient, context: dict):
    payload = _table_to_dict(datatable)
    response = _run(client.post("/auth/register", json=clean_payload))
    context["response"] = response

@then(parsers.parse("I receive a {status_code:d} response"))
def assert_status_code(context: dict, status_code: int):
    assert context["response"].status_code == status_code
```
Steps are synchronous; async calls use `_run(coro)` = `asyncio.get_event_loop().run_until_complete(coro)`. State passes via `context` dict.

### Conftest Patterns
`tests/bdd/conftest.py`
```python
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(autouse=True)
async def clean_tables(test_engine):
    async with test_engine.begin() as conn:
        await conn.execute(delete(User))
    yield
    async with test_engine.begin() as conn:
        await conn.execute(delete(User))

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    fastapi_app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def context() -> dict:
    return {}
```
