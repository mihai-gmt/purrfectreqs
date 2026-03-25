# Security Specifications — PurrfectReqs

> **Purpose:** This file defines the security requirements and implementation specs. For the task backlog, see `docs/security_work.md`. For general agent rules, see `docs/guide.md`.

---

## Architecture Overview

All security logic lives in `app/auth/`. Other modules import auth dependencies — they never implement their own auth logic.

```
app/auth/
├── router.py        # /login, /refresh, /logout endpoints
├── service.py       # Auth business logic (login, refresh, revoke)
├── models.py        # User model, RefreshToken model
├── schemas.py       # LoginRequest, TokenResponse, UserResponse, etc.
├── dependencies.py  # get_current_user, require_role
├── jwt_handler.py   # PyJWT encode/decode/refresh logic
├── password.py      # passlib hashing utilities
└── rate_limit.py    # Rate limiting config for auth endpoints
```

---

## 1. User Model — `app/auth/models.py`

### User Table Fields

| Field | Type | Description |
|-------|------|-------------|
| id | Integer, PK | Auto-increment |
| email | String, unique, indexed | Login identifier |
| username | String, unique | Display name |
| hashed_password | String | passlib hash (argon2 or bcrypt) |
| role | Enum: `admin`, `super-user`, `user` | RBAC role |
| status | Enum: `active`, `suspended`, `locked`, `inactive`, `pending` | Account status |
| failed_login_attempts | Integer, default 0 | Counter for lockout logic |
| locked_until | DateTime, nullable | Lockout expiry timestamp |
| last_password_change | DateTime | For password age tracking |
| created_at | DateTime | Audit field |
| updated_at | DateTime | Audit field |
| created_by | Integer, FK → User | Audit field |
| updated_by | Integer, FK → User | Audit field |

### RefreshToken Table Fields

| Field | Type | Description |
|-------|------|-------------|
| id | Integer, PK | Auto-increment |
| user_id | Integer, FK → User | Token owner |
| token_hash | String | Hashed refresh token (never store raw) |
| is_revoked | Boolean, default False | Revocation flag |
| expires_at | DateTime | Token expiry |
| created_at | DateTime | When issued |
| replaced_by | Integer, FK → RefreshToken, nullable | Points to rotated replacement |

---

## 2. Password Security — `app/auth/password.py`

**Library:** `passlib` with argon2 (preferred) or bcrypt fallback.

### Password Requirements (validate in `app/auth/schemas.py`)

- Minimum 8 characters
- At least one letter
- At least one number
- Allowed special characters: `@$!%*#?&`

### Functions to Implement

| Function | Signature | Purpose |
|----------|-----------|---------|
| `hash_password` | `(plain: str) → str` | Hash a plaintext password |
| `verify_password` | `(plain: str, hashed: str) → bool` | Verify password against hash |

---

## 3. JWT Token Handling — `app/auth/jwt_handler.py`

**Library:** `PyJWT`

### Access Token

| Property | Value |
|----------|-------|
| Algorithm | HS256 |
| Secret | From `JWT_SECRET_KEY` env var |
| Expiry | 15 minutes |
| Claims | `sub` (user ID), `role`, `exp`, `iat`, `jti` (unique token ID) |
| Delivery | Response body (JSON) |
| Client storage | In-memory only (NOT localStorage) |

### Refresh Token

| Property | Value |
|----------|-------|
| Format | Opaque random string (NOT a JWT) |
| Expiry | 7 days |
| Storage (server) | Hashed in `refresh_tokens` DB table |
| Delivery | HTTP-only, Secure, SameSite=Strict cookie |
| Rotation | New token issued on each `/refresh` call; old token revoked |

### Functions to Implement

| Function | Signature | Purpose |
|----------|-----------|---------|
| `create_access_token` | `(user_id: int, role: str) → str` | Encode JWT with PyJWT |
| `decode_access_token` | `(token: str) → dict` | Decode and validate JWT |
| `create_refresh_token` | `() → str` | Generate cryptographically random string |
| `hash_refresh_token` | `(token: str) → str` | Hash for DB storage |

---

## 4. Auth Endpoints — `app/auth/router.py`

### POST `/auth/login`

- **Input:** `LoginRequest` (email, password)
- **Logic:**
  1. Look up user by email
  2. Check if account is locked → return 423 if locked
  3. Verify password
  4. On failure: increment `failed_login_attempts`, lock after 5 failures (30-min lockout) → return 401
  5. On success: reset `failed_login_attempts`, create access token + refresh token
  6. Store hashed refresh token in DB
  7. Return access token in body, set refresh token in HTTP-only cookie
- **Rate limit:** 5 attempts per minute per IP

### POST `/auth/refresh`

- **Input:** Refresh token from HTTP-only cookie + CSRF token
- **Logic:**
  1. Extract refresh token from cookie
  2. Hash it and look up in DB
  3. Validate: not revoked, not expired
  4. Revoke current refresh token
  5. Issue new access token + new refresh token (rotation)
  6. Store new hashed refresh token in DB
  7. Return new access token in body, set new refresh token cookie
- **Rate limit:** 10 per minute per user
- **CSRF:** Required (double-submit cookie pattern)

### POST `/auth/logout`

- **Input:** Access token (Authorization header) + refresh token from cookie
- **Logic:**
  1. Validate access token to identify user
  2. Revoke ALL refresh tokens for this user (enforces single-session)
  3. Clear refresh token cookie
  4. Return 200 OK
- **Rate limit:** 10 per minute per user

---

## 5. RBAC Dependencies — `app/auth/dependencies.py`

### Roles & Permissions

| Role | Permissions |
|------|------------|
| `admin` | Full system access: manage users, manage projects, all CRUD, view audit logs |
| `super-user` | Manage users (limited), same as `user` for everything else (MVP) |
| `user` | Basic access: CRUD own projects/requirements, upload documents, run analysis |

### Dependencies to Implement

| Dependency | Purpose | Usage |
|-----------|---------|-------|
| `get_current_user` | Extract + decode JWT → return User object | `Depends(get_current_user)` |
| `require_role(*roles)` | Check current user has one of the specified roles → 403 if not | `Depends(require_role("admin"))` |
| `get_correlation_id` | Extract or generate correlation ID from request headers | `Depends(get_correlation_id)` |

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
| Session timeout | 30 minutes of inactivity |
| Automatic logout | Yes — expired access tokens are not renewed if last activity > 30 min |
| Single session per user | Yes — on new login, revoke all existing refresh tokens |
| Concurrent sessions | NOT allowed (MVP) |

---

## 7. Rate Limiting — `app/auth/rate_limit.py`

**Library:** `fastapi-limiter` with Redis backend.

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5 per minute per IP |
| `/auth/refresh` | 10 per minute per user |
| `/auth/logout` | 10 per minute per user |
| Password reset | 3 per hour per IP |
| General API endpoints | 100 per minute per user |

---

## 8. Security Headers

Apply these via FastAPI middleware on ALL responses:

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
  4. Reject if mismatch

---

## 10. Security Event Logging

Log ALL of the following to the unified logging system with correlation ID:

| Event | Log Level |
|-------|-----------|
| Successful login | INFO |
| Failed login attempt | WARNING |
| Account locked | WARNING |
| Account unlocked | INFO |
| Token refreshed | INFO |
| Token revoked | INFO |
| Logout | INFO |
| Password changed | INFO |
| Role changed | WARNING |
| Authorization denied (403) | WARNING |
| Invalid token presented | WARNING |
| Rate limit exceeded | WARNING |

**NEVER log:** passwords (plain or hashed), full tokens, PII beyond user ID.

---

## 11. Error Responses for Auth

All auth errors use the standard error format with these specific codes:

| Scenario | HTTP Status | Error Code |
|----------|-------------|------------|
| Invalid credentials | 401 | `INVALID_CREDENTIALS` |
| Token expired | 401 | `TOKEN_EXPIRED` |
| Token invalid | 401 | `TOKEN_INVALID` |
| Insufficient permissions | 403 | `INSUFFICIENT_PERMISSIONS` |
| Account locked | 423 | `ACCOUNT_LOCKED` |
| Rate limit exceeded | 429 | `RATE_LIMIT_EXCEEDED` |

---

## Seed Data for Testing

Create these users when seeding the database (in `app/auth/service.py` or a seed script):

| Email | Role | Password | Purpose |
|-------|------|----------|---------|
| `admin@purrfectreqs.local` | admin | `Admin123!` | Full access testing |
| `super@purrfectreqs.local` | super-user | `Super123!` | Elevated access testing |
| `user@purrfectreqs.local` | user | `User1234!` | Basic access testing |

> **Note:** These are for development/testing only. Never deploy with default credentials.
