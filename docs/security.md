# Security Specifications — PurrfectReqs

> **Purpose:** This file defines security **behavior and constraints** — what the system must do to be secure, and the rules it must enforce. It does not define data structures.
>
> **Data model authority:** For table definitions (fields, types, constraints, indexes), see `docs/DATA_MODELS.md`. This file references those tables but does not redefine them.
>
> **Code patterns:** For implementation patterns (function signatures, code examples), see `docs/GUIDE.md`. This file specifies *what* must happen, not *how* the code looks.
>
> **Related files:**
> - `docs/DATA_MODELS.md` → table structures for `users`, `refresh_tokens`
> - `docs/GUIDE.md` → code patterns, standard implementations
> - `CLAUDE.md` → agent behavior rules (takes precedence over this file)

---

## Architecture Overview

All security logic lives in `app/auth/`. Other modules import auth dependencies — they never implement their own auth logic.

```
app/auth/
├── router.py        # Auth endpoints (/login, /register, /refresh, /logout)
├── service.py       # Auth business logic (login, register, refresh, revoke)
├── models.py        # SQLAlchemy models (must match docs/DATA_MODELS.md exactly)
├── schemas.py       # Pydantic request/response models + input validation
├── dependencies.py  # get_current_user, require_role, get_correlation_id
├── jwt_handler.py   # PyJWT encode/decode/refresh logic
├── password.py      # passlib hashing utilities
└── rate_limit.py    # Rate limiting config for auth endpoints
```

---

## 1. User & Token Models

For complete table definitions, see `docs/DATA_MODELS.md` → Module 1: Auth.

This section defines only the **security-relevant behavior** of these models.

### Password storage

- Algorithm: argon2 (preferred), bcrypt as automatic fallback via passlib
- Raw passwords are NEVER stored — only the argon2/bcrypt hash
- Library: `passlib` with argon2 backend

### Account lockout

- Trigger: 5 consecutive failed login attempts (`failed_login_attempts` field)
- Duration: 30 minutes (stored in `locked_until`)
- Reset: successful login resets `failed_login_attempts` to 0
- Locked accounts return HTTP 423 on login attempts

### Account status behavior

| Status | Can login? | Description |
|--------|-----------|-------------|
| `active` | Yes | Normal operational state |
| `pending` | No | Self-registered, awaiting admin approval |
| `suspended` | No | Admin-suspended account |
| `locked` | No | Automatically locked after failed login attempts |
| `inactive` | No | Deactivated account |

### Refresh token security

- Raw refresh tokens are NEVER stored in the database — only the SHA-256 hash
- On rotation: old token is revoked (`is_revoked = True`), `replaced_by` points to new token's ID
- On logout: ALL refresh tokens for the user are revoked (single-session enforcement)
- Expired tokens are eligible for hard delete (not soft delete)

---

## 2. Password Policy

### Requirements (enforced in Pydantic schema validation)

- Minimum 8 characters
- At least one letter
- At least one number
- At least one allowed special characters: `@$!%*#?&`

---

## 3. JWT Token Handling

**Library:** `PyJWT`

### Access Token

| Property | Value |
|----------|-------|
| Algorithm | HS256 |
| Secret | From `JWT_SECRET_KEY` env var (never hardcoded) |
| Expiry | 15 minutes |
| Claims | `sub` (user ID as string), `role`, `exp`, `iat`, `jti` (unique token ID — UUID) |
| Delivery | Response body (JSON) |
| Client storage | In-memory only (NOT localStorage, NOT sessionStorage) |

### Refresh Token

| Property | Value |
|----------|-------|
| Format | Opaque cryptographically random string (NOT a JWT) |
| Expiry | 7 days |
| Storage (server) | SHA-256 hash stored in `refresh_tokens` table (see `docs/DATA_MODELS.md`) |
| Delivery | HTTP-only, Secure, SameSite=Strict cookie |
| Rotation | New token issued on each `/auth/refresh` call; old token revoked |

---

## 4. Auth Endpoints — `app/auth/router.py`

### POST `/auth/register`

- **Auth required:** No (public endpoint)
- **Input:** email, username, password
- **Behavior:**
  1. Validate input against password policy and field constraints
  2. Check that email and username are not already taken
  3. Hash password
  4. Create user with role = `super_user`, status = `active`
  5. Log registration event
  6. Return 201 with confirmation message
- **Error responses:**
  - 409 if email or username already exists
  - 422 if input validation fails (password policy, missing fields, invalid email format)
- **Rate limit:** 5 per minute per IP

### POST `/auth/login`

- **Auth required:** No (public endpoint)
- **Input:** email, password
- **Behavior:**
  1. Look up user by email
  2. Check if account is locked → return 423 if locked
  3. Check if account status allows login (only `active` status) → return 403 if not
  4. Verify password
  5. On failure: increment `failed_login_attempts`, lock after 5 failures (30-min lockout) → return 401
  6. On success: reset `failed_login_attempts`, update `last_activity_at`, revoke any existing refresh tokens (single-session), create new access token + refresh token
  7. Store hashed refresh token in DB
  8. Return access token in body, set refresh token in HTTP-only cookie, set CSRF token in readable cookie
- **Rate limit:** 5 per minute per IP

### POST `/auth/refresh`

- **Auth required:** Refresh token cookie (not JWT)
- **Input:** Refresh token from HTTP-only cookie + CSRF token header
- **Behavior:**
  1. Extract refresh token from cookie
  2. Hash it and look up in DB
  3. Validate: not revoked, not expired
  4. Check `last_activity_at` — if more than 30 minutes ago, reject (session timeout)
  5. Revoke current refresh token
  6. Issue new access token + new refresh token (rotation)
  7. Store new hashed refresh token in DB
  8. Update `last_activity_at`
  9. Return new access token in body, set new refresh token cookie
- **Rate limit:** 10 per minute per user
- **CSRF:** Required (double-submit cookie pattern)

### POST `/auth/logout`

- **Auth required:** JWT access token
- **Input:** Access token (Authorization header) + refresh token from cookie
- **Behavior:**
  1. Validate access token to identify user
  2. Revoke ALL refresh tokens for this user (enforces single-session)
  3. Clear refresh token cookie
  4. Clear CSRF cookie
  5. Return 200 OK
- **Rate limit:** 10 per minute per user

---

## 5. RBAC — Role-Based Access Control

### System Roles & Permissions

| Role | DB value | Permissions |
|------|----------|------------|
| Admin | `admin` | Full system access: manage all users, manage all projects, all CRUD, view audit logs |
| Super-user | `super_user` | Manage users (limited), same as `user` for everything else (MVP) |
| User | `user` | Basic access: CRUD own projects/requirements, upload documents, run analysis |

> **Naming convention:** The database stores `super_user` (underscore — Python/DB convention). The UI displays "Super-user" (hyphen — human-readable). All code, schemas, and feature files must use `super_user`.

### Auth Dependencies

The following FastAPI dependencies are provided by `app/auth/dependencies.py` for use in all modules:

- **`get_current_user`** — Extracts JWT from Authorization header, decodes and validates it, loads User from DB. Returns the User object. Returns 401 if token is missing, expired, or invalid.
- **`require_role(*roles)`** — Checks that the current user's role is one of the specified roles. Returns 403 if not. Must be used after `get_current_user` in the dependency chain.
- **`get_correlation_id`** — Extracts correlation ID from `X-Correlation-ID` request header, or generates a new UUID if absent.

### Integration Pattern

```python
# In any module's router.py:
from app.auth.dependencies import get_current_user, require_role

@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_role("admin")),
):
    ...
```

---

## 6. Session Management

| Rule | Value |
|------|-------|
| Session timeout | 30 minutes of inactivity (tracked via `last_activity_at` on `users` table) |
| Automatic logout | Yes — `/auth/refresh` rejects if `last_activity_at` > 30 min ago |
| Single session per user | Yes — on new login, revoke all existing refresh tokens |
| Concurrent sessions | NOT allowed (MVP) |

---

## 7. Rate Limiting

**Library:** `fastapi-limiter` with Redis backend.

| Endpoint | Limit |
|----------|-------|
| `POST /auth/register` | 5 per minute per IP |
| `POST /auth/login` | 5 per minute per IP |
| `POST /auth/refresh` | 10 per minute per user |
| `POST /auth/logout` | 10 per minute per user |
| Admin password reset | 3 per hour per IP |
| General API endpoints | 100 per minute per user |

---

## 8. Security Headers

Apply via FastAPI middleware on ALL responses:

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | `default-src 'self'` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

---

## 9. CSRF Protection

- **Method:** Double-submit cookie pattern
- **Apply to:** All cookie-authenticated endpoints (`/auth/refresh`)
- **Flow:**
  1. On login, set a CSRF token in a readable (non-HTTP-only) cookie
  2. Client reads CSRF cookie and sends it as a request header (`X-CSRF-Token`)
  3. Server compares cookie value to header value
  4. Reject with 403 if mismatch

---

## 10. CORS Policy

- **Library:** `starlette.middleware.cors.CORSMiddleware` (included with FastAPI)
- **Apply to:** All responses via FastAPI middleware
- **Configuration:**

| Setting | Development | Production |
|---------|------------|------------|
| `allow_origins` | `["http://localhost:8000"]` | `["https://<production-domain>"]` |
| `allow_methods` | `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` | Same |
| `allow_headers` | `["Authorization", "Content-Type", "X-CSRF-Token", "X-Correlation-ID"]` | Same |
| `allow_credentials` | `True` | `True` |
| `max_age` | `600` (10 minutes) | `600` |

- **`allow_credentials: True`** is required because the refresh token 
  is delivered via HTTP-only cookie. Without this, the browser will not 
  send cookies on cross-origin requests.
- **NEVER use `allow_origins: ["*"]`** when `allow_credentials` is `True` — 
  browsers reject this combination. Always specify exact origins.
- Origins are configured via environment variable `CORS_ALLOWED_ORIGINS` 
  (comma-separated list) in `app/core/config.py`.

---

## 11. Honeypot Bot Protection

- **Apply to:** All public-facing forms (registration, any future public forms)
- **Mechanism:**
  1. Template includes a hidden form field (e.g., `website` or `company`) 
     styled with `display: none` via CSS class
  2. Real users never see or fill this field
  3. Bots auto-fill all fields, including the hidden one
  4. Server checks: if honeypot field has a value, reject silently
- **Server behavior on bot detection:**
  - Return the same response as a successful submission (e.g., 201) 
    — do not reveal detection to the bot
  - Log the event at WARNING level with correlation ID
  - Do NOT create the account
- **Template implementation:** Hidden field in Jinja2 template, 
  CSS class in `pico.min.css` override or inline style in `base.html`
- **Validation:** Pydantic schema accepts the field as `Optional[str]`, 
  service.py checks if populated before processing

---
## 12. Security Event Logging

Log ALL of the following to the unified logging system with correlation ID:

| Event | Log Level |
|-------|-----------|
| Successful registration | INFO |
| Successful login | INFO |
| Failed login attempt | WARNING |
| Account locked (auto) | WARNING |
| Account unlocked (admin) | INFO |
| Account status changed (admin) | WARNING |
| Token refreshed | INFO |
| Token revoked | INFO |
| Logout | INFO |
| Password changed | INFO |
| Role changed | WARNING |
| Authorization denied (403) | WARNING |
| Invalid token presented | WARNING |
| Rate limit exceeded | WARNING |
| CSRF validation failed | WARNING |
| Honeypot triggered (bot detected) | WARNING |

**NEVER log:** passwords (plain or hashed), full tokens, PII beyond user ID.

---

## 13. Error Responses for Auth

All auth errors use the standard error format (see `docs/GUIDE.md` → Error Response Format) with these specific codes.

All auth success responses use the `ApiResponse[T]` envelope (see `docs/GUIDE.md` → Success Response Format) which includes `correlation_id` for traceability.

| Scenario | HTTP Status | Error Code |
|----------|-------------|------------|
| Invalid credentials | 401 | `INVALID_CREDENTIALS` |
| Token expired | 401 | `TOKEN_EXPIRED` |
| Token invalid | 401 | `TOKEN_INVALID` |
| Account not active | 403 | `ACCOUNT_NOT_ACTIVE` |
| Insufficient permissions | 403 | `INSUFFICIENT_PERMISSIONS` |
| CSRF token mismatch | 403 | `CSRF_VALIDATION_FAILED` |
| Email already exists | 409 | `EMAIL_ALREADY_EXISTS` |
| Username already exists | 409 | `USERNAME_ALREADY_EXISTS` |
| Validation error | 422 | `VALIDATION_ERROR` |
| Account locked | 423 | `ACCOUNT_LOCKED` |
| Rate limit exceeded | 429 | `RATE_LIMIT_EXCEEDED` |

---

## [nr]. Transport Security

### HTTPS

- **Enforcement:** All production/beta deployments MUST use HTTPS. 
  HTTP is acceptable only in local development (`APP_ENV=development`).
- **Certificate management:** Handled by reverse proxy (Caddy with 
  automatic Let's Encrypt, or Nginx with certbot). The FastAPI 
  application does NOT terminate TLS.
- **Secure cookies:** The `Secure` flag on cookies (refresh token, CSRF) 
  is set conditionally:
  - `APP_ENV=development` → `Secure=False` (allows HTTP on localhost)
  - `APP_ENV=production` or `APP_ENV=beta` → `Secure=True`

### Reverse Proxy Requirements (production/beta)

- Only port 443 (HTTPS) exposed publicly
- HTTP (port 80) redirects to HTTPS — handled by proxy, not by app
- Proxy sets `X-Forwarded-For`, `X-Forwarded-Proto` headers
- App trusts proxy headers only from known proxy IPs 
  (configured via `TRUSTED_PROXY_IPS` env var)
- All internal services (PostgreSQL, Redis, Grafana, Loki) are 
  accessible only within the Docker network — NOT exposed on host

### Service Authentication

| Service | Development | Production/Beta |
|---------|------------|-----------------|
| Redis | No password | Password required (`REDIS_PASSWORD` env var) |
| Grafana | Default admin/admin | Password from `GF_SECURITY_ADMIN_PASSWORD` env var, unique per deployment |
| PostgreSQL | Password from env var | Same (already configured) |
| Ollama | No auth (localhost only) | Not deployed on public VM (runs locally on dev machine only) |

---

## Seed Data for Testing

Create these users via Alembic data migration (guarded by `APP_ENV=development`):

| Email | Username | Role | Status | Password | Purpose |
|-------|----------|------|--------|----------|---------|
| `admin@purrfectreqs.local` | `admin` | `admin` | `active` | `Admin123!` | Full access testing |
| `super@purrfectreqs.local` | `superuser` | `super_user` | `active` | `Super123!` | Elevated access testing |
| `user@purrfectreqs.local` | `testuser` | `user` | `active` | `User1234!` | Basic access testing |

> **Note:** These are for development/testing only. Never deploy with default credentials.
> Seed data users are created with status `active` to enable immediate testing. Self-registered users get status `active` by default.
