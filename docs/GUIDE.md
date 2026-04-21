# PurrfectReqs — Developer Guide

> **Purpose:** This file defines HOW to write code for PurrfectReqs — patterns, conventions, and standard implementations. For WHAT to build, see `docs/SCOPE.md`. For security specs, see `docs/SECURITY.md`. For module structure rules, see `docs/ARCHITECTURE.md`.

---

## Agent Behavior Rules

### Rule 1: Understand Before Acting

- Before generating code, confirm you understand which module, file, and function is being affected.
- If the request is ambiguous (e.g., "add validation"), ask ONE clarifying question before proceeding.
- If the request is clear, proceed without asking.

### Rule 2: Respect the File Structure

- All new code MUST go in the correct module folder as defined in `docs/SCOPE.md` → Project File Structure.
- Do NOT create files outside the established structure without explicit approval.
- Do NOT create a `utils.py` catch-all. Utilities belong in the relevant module or in `app/core/`.

### Rule 3: Follow the Module Pattern

Every module follows this structure. Do not deviate:

```
app/<module_name>/
├── router.py        # FastAPI router with endpoints
├── service.py       # Business logic (called by router)
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic request/response models
└── dependencies.py  # Module-specific FastAPI dependencies (if needed)
```

- **router.py** calls **service.py**. Never put business logic in the router.
- **service.py** calls **models.py** for DB access. Never import models directly in the router.
- Modules must NOT import each other's models or internals. Use service interfaces and schemas.

### Rule 4: Every Function Must Include

- **Type hints** on all parameters and return values.
- **Docstring** explaining purpose, parameters, and return value.
- **Correlation ID (UUID)** as a parameter — generate one if not provided.
- **Logging** at appropriate levels (info for actions, warning for edge cases, error for failures).
- **Error handling** with standardized exceptions.

### Rule 5: Security Is Non-Negotiable

- Every endpoint MUST require JWT authentication (except `/auth/login`).
- Every endpoint MUST enforce RBAC via `require_role()` dependency.
- Every endpoint MUST propagate the correlation ID.
- Never hardcode secrets — always use `app/core/config.py` reading from environment variables.
- Always validate input with Pydantic models.
- See `docs/SECURITY.md` for full security specifications.

### Rule 6: Testing Comes First (TDD/BDD)

Every new feature follows the RED → GREEN cycle:

1. **Developer writes** a `.feature` file in `features/<module>/` with Gherkin acceptance criteria.
2. **Agent reviews** the `.feature` file against spec docs for consistency.
3. **Agent writes** BDD step definitions + unit tests. Runs `pytest` → confirms RED (all fail).
4. **Agent implements** the functional code. Runs `pytest` → confirms GREEN (all pass).

File locations:
- Gherkin feature files: `tests/bdd/features/<module>/<feature_name>.feature`
- BDD step definitions: `tests/bdd/step_defs/test_<feature_name>.py`
- Unit tests: `tests/unit/<module_name>/`
- Integration tests: `tests/integration/`

BDD step definitions use `pytest-bdd` to connect `.feature` files to Python test functions.
Tests must cover: success case, failure case, edge cases, and authorization.

### Rule 7: Database Changes Require Migrations

- All schema changes must have an Alembic migration in `alembic/versions/`.
- Never modify the database schema without a migration script.
- Include audit fields on every model: `created_at`, `updated_at`, `created_by`, `updated_by`.

### Rule 8: Explain Your Decisions

- This is a learning project. When choosing a pattern, library, or approach, include a brief comment or docstring explaining WHY.
- Example: `# Using argon2 over bcrypt because it won the Password Hashing Competition and is more resistant to GPU attacks.`

### Rule 9: Frontend Templates (HTMX + Jinja2)

- All HTML templates live in `app/templates/<module>/` — never in the module's Python folder.
- Every template extends `base.html` which provides shared layout, nav, footer, and HTMX script.
- Use HTMX attributes (`hx-get`, `hx-post`, `hx-target`, `hx-swap`) for dynamic interactions. No custom JavaScript unless HTMX cannot handle it.
- Partials (HTML fragments for HTMX targets) use underscore prefix: `_form.html`, `_list.html`, `_criteria.html`.
- Templates must NOT contain business logic — that stays in `service.py`.
- Auth tokens live in HTTP-only cookies. No localStorage, no sessionStorage, no JavaScript token handling.
- Static files (CSS, JS) go in `app/static/`. All assets are served locally — no CDN references allowed.
- HTMX is served from `app/static/vendor/htmx/<version>/htmx.min.js`. PicoCSS is served from `app/static/vendor/pico/<version>/pico.min.css`. Both files are vendored into the repository — no build-time downloads, no CDN. Current pinned versions and SHA256 checksums live in `docs/TECH_STACK.md`.
- Use PicoCSS semantic classes for all UI styling. Do not write custom CSS unless PicoCSS cannot achieve the required element.

### Rule 10: Startup and Migrations

- Database migrations run automatically on container startup via `scripts/start.sh`.
- Dev seed data (3 test users) is an Alembic data migration guarded by `APP_ENV=development`.
- Use the `Makefile` for common commands: `make test`, `make dev`, `make logs`, `make reset-db`.

---

## Code Style & Formatting

| Rule | Detail |
|------|--------|
| Formatter | `ruff format` (run `ruff format .` before committing) |
| Linter | `ruff check` (run `ruff check .` before committing; add `--fix` to auto-fix) |
| Style guide | PEP 8 |
| Import order | stdlib → third-party → local (enforced by ruff rule set `I`) |
| Line length | 120 characters (`line-length = 120` in `[tool.ruff]` in pyproject.toml) |
| Quotes | Double quotes (`quote-style = "double"` in `[tool.ruff.format]`) |
| Naming | snake_case for functions/variables, PascalCase for classes |

---

## Standard Patterns

### API Endpoint Pattern

```python
from app.core.dependencies import get_correlation_id

@router.post("/", response_model=ApiResponse[ItemData], status_code=201)
async def create_item(
    request: ItemCreateRequest,
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_role("admin")),
    correlation_id: str = Depends(get_correlation_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new item.

    Requires admin role. Returns the created item wrapped in ApiResponse.
    """
    logger.info(
        "Creating item",
        extra={"correlation_id": correlation_id, "user_id": current_user.id}
    )
    result = await item_service.create(db, request, current_user.id, correlation_id)
    return ApiResponse(
        data=result,
        message="Item created successfully.",
        correlation_id=correlation_id,
    )
```

**Correlation ID flow:** The `correlation_id_middleware` in `app/main.py` reads the `X-Correlation-ID` header from the incoming request (allowing frontends and API clients to pass their own ID for end-to-end tracing). If the header is absent (e.g. a Swagger request), the middleware generates a UUID. The `get_correlation_id` dependency in `app/core/dependencies.py` extracts this value from `request.state` so every endpoint can use it via `Depends(get_correlation_id)`. The same ID is returned in the `X-Correlation-ID` response header.

### Error Response Format

```json
{
    "error_code": "VALIDATION_ERROR",
    "message": "Human-readable description of what went wrong",
    "correlation_id": "uuid-string",
    "details": {}
}
```

### Success Response Format (Envelope Pattern)

All API success responses use the `ApiResponse[T]` envelope from `app/core/schemas.py`. The `data` field contains the endpoint-specific payload; the outer fields are consistent across every endpoint.

```json
{
    "data": { "id": 1, "email": "user@example.com" },
    "message": "Operation completed successfully",
    "correlation_id": "uuid-string"
}
```

```python
# app/core/schemas.py — generic envelope
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    data: T
    message: str
    correlation_id: str | None = None
```

Module schemas define only the `data` payload — not the envelope:

```python
# app/auth/schemas.py — data payload only
class UserRegisterData(BaseModel):
    id: int
    email: str

# Do NOT put message or correlation_id here — the envelope handles that.
```

The router wraps the service result in the envelope:

```python
# app/auth/router.py
@router.post("/register", response_model=ApiResponse[UserRegisterData], status_code=201)
async def register_user(...):
    result = await auth_service.register_user(db, request_body, correlation_id)
    return ApiResponse(
        data=result,
        message="User registered successfully.",
        correlation_id=correlation_id,
    )
```

**Key rules:**
- Module schemas define data payloads only — never duplicate `message` or `correlation_id`
- Routers are responsible for wrapping in `ApiResponse[T]`
- Error responses keep their existing shape (they already have a consistent format via `app/core/exceptions.py`)

### Audit Logging Pattern

```python
await audit_service.log(
    db=db,
    table_name="projects",
    record_id=project.id,
    action_type="CREATE",
    old_values=None,
    new_values=project.model_dump(),
    user_id=current_user.id,
    correlation_id=correlation_id,
)
```

### Service Function Pattern

```python
async def create_project(
    db: AsyncSession,
    request: ProjectCreateRequest,
    current_user_id: int,
    correlation_id: str,
) -> ProjectResponse:
    """
    Create a new project owned by the current user.

    Args:
        db: Async database session.
        request: Validated project creation request.
        current_user_id: ID of the user creating the project.
        correlation_id: Request correlation ID for tracing.

    Returns:
        The created project as a ProjectResponse schema.

    Raises:
        ProjectNameConflictError: If a project with this name already exists for the user.
    """
    logger.info(
        "Creating project",
        extra={"correlation_id": correlation_id, "user_id": current_user_id}
    )
    # ... implementation
```

---

## Dependency Injection Chain

Every request flows through this dependency chain:

```
Request
  → Correlation ID middleware (reads X-Correlation-ID header, or generates UUID)
  → OAuth2 token extraction (Authorization header)
  → get_correlation_id (app/core/dependencies.py — extracts ID from request.state)
  → get_current_user (decode JWT, load user from DB)
  → require_role (check RBAC)
  → get_db (database session)
  → Router → Service → Model
  → Response (X-Correlation-ID header echoed back)
```

---

## Environment Variables

All environment variables are declared in `.env.example`. Never commit `.env` to version control.

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@db:5432/purrfectreqs

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# Grafana (change from default in any non-local deployment)
GF_SECURITY_ADMIN_PASSWORD=admin

# JWT
JWT_SECRET_KEY=<generated-secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Ollama (native macOS, Metal GPU — not in Docker)
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:32b
OLLAMA_TIMEOUT_SECONDS=120

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# App
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=info

# File uploads
UPLOAD_DIR=/app/uploads
MAX_UPLOAD_SIZE_MB=10
ALLOWED_FILE_TYPES=.txt,.md,.docx,.doc

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:8000
```

---

## Logging Standards

- Use Python's built-in `logging` library, configured once in `app/core/logging.py`.
- Use structured logging (JSON format) for machine parsing.
- ALWAYS include `correlation_id` in log entries.
- NEVER log passwords, tokens, PII, or sensitive data.
- Log levels: `DEBUG` (development only), `INFO` (actions), `WARNING` (edge cases), `ERROR` (failures), `CRITICAL` (system failures).

---

## UTC Time Standard

All timestamps in the system MUST be UTC. No exceptions.

### Python code

```python
from datetime import datetime, UTC

# CORRECT — timezone-aware UTC datetime
now = datetime.now(UTC)

# WRONG — naive datetime, no timezone info
now = datetime.now()

# WRONG — deprecated in Python 3.12, returns naive datetime
now = datetime.utcnow()
```

When computing time deltas (e.g., account lockout expiry, token expiry):

```python
from datetime import datetime, timedelta, UTC

locked_until = datetime.now(UTC) + timedelta(minutes=30)
is_expired = datetime.now(UTC) > token.expires_at
```

### SQLAlchemy columns

```python
from sqlalchemy import Column, DateTime, func

# All timestamp columns must be timezone-aware
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

### API responses

Return ISO 8601 format: `"2026-04-09T14:30:00+00:00"`. Pydantic serializes aware datetimes correctly by default.

### Key rules

- Never create a naive `datetime` (one without timezone info)
- Never use `datetime.utcnow()` — it is deprecated and returns a naive datetime
- Never compare naive and aware datetimes — this raises a `TypeError`
- Always use `datetime.now(UTC)` for the current time
- Store all DB timestamps as `DateTime(timezone=True)`

---

## What NOT to Do

- Do NOT create code for NOT MVP features (see `docs/SCOPE.md` → Post-MVP Roadmap).
- Do NOT use `localStorage` or `sessionStorage` for tokens.
- Do NOT import between modules — use service interfaces and Pydantic schemas.
- Do NOT skip Alembic migrations for DB changes.
- Do NOT put business logic in routers.
- Do NOT hardcode any configuration values.
- Do NOT create separate microservices — this is a monolith for MVP.
- Do NOT skip correlation ID propagation on any function.
- Do NOT use `print()` statements — use the logger.
- Do NOT return raw exception messages or stack traces in API responses.
