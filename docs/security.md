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
├── dependencies.py  # get_current_user, require_role (auth-specific dependencies)
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
- Locked accounts return HTTP 403 on login attempts

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
| Delivery (browser, `Accept: text/html`) | HTTP-only cookie `access_token`; `HttpOnly; Secure; SameSite=Lax; Path=/` |
| Delivery (API, `Accept: application/json`) | Response body (JSON) |
| Client storage (browser) | Cookie only — inaccessible to JavaScript |
| Client storage (API) | In-memory only (NOT localStorage, NOT sessionStorage, NOT disk unless using an OS keychain) |

### Refresh Token

| Property | Value |
|----------|-------|
| Format | Opaque cryptographically random string (NOT a JWT) |
| Expiry | 7 days |
| Storage (server) | SHA-256 hash stored in `refresh_tokens` table (see `docs/DATA_MODELS.md`) |
| Delivery (browser) | HTTP-only cookie `refresh_token`; `HttpOnly; Secure; SameSite=Lax; Path=/auth/refresh` |
| Delivery (API) | Response body (JSON) alongside the access token |
| Client storage (browser) | Cookie only — inaccessible to JavaScript |
| Client storage (API) | Client-managed (keychain, secrets manager, or equivalent — never localStorage/sessionStorage) |
| Rotation | New token issued on each `/auth/refresh` call; old token revoked |

---

## 4. Auth Endpoints — `app/auth/router.py`

### POST `/auth/register`

- **Auth required:** No (public endpoint)
- **Input:** email, username, password
- **Content negotiation:** `Accept: text/html` (browser) → 303 redirect on success. `Accept: application/json` (API) → JSON body.
- **Behavior (both paths):**
  1. Validate input against password policy and field constraints
  2. Check that email and username are not already taken
  3. Hash password
  4. Create user with role = `super_user`, status = `active`
  5. Log registration event
- **Response (browser, `Accept: text/html`):** HTTP **303 See Other** with `Location: /auth/login` (user logs in separately; registration does not issue tokens).
- **Response (API, `Accept: application/json`):** 201 with confirmation message in JSON body.
- **Error responses (both paths):**
  - 409 if email or username already exists
  - 422 if input validation fails (password policy, missing fields, invalid email format)
- **Rate limit:** 5 per minute per IP

### POST `/auth/login`

- **Auth required:** No (public endpoint)
- **Input:** email, password
- **Content negotiation:** The response shape is determined by the `Accept` request header. `Accept: text/html` (browser) → cookies + 303 redirect. `Accept: application/json` (API) → JSON body with tokens.
- **Behavior (both paths):**
  1. Look up user by email
  2. Verify password
  3. Check if account is locked → return 403 if locked in the last 30 minutes
  4. Check if account status allows login (only `active`, or `locked` status after `locked_until` has passed) → return 403 if not
  5. On failure: increment `failed_login_attempts`, lock after 5 failures (30-min lockout) → return 401
  6. On success: reset `failed_login_attempts`, update `last_activity_at`, revoke any existing refresh tokens (single-session), create new access token + refresh token, store hashed refresh token in DB
- **Response (browser, `Accept: text/html`):**
  - Set cookie `access_token` (`HttpOnly; Secure; SameSite=Lax; Path=/`; Max-Age = 15 minutes)
  - Set cookie `refresh_token` (`HttpOnly; Secure; SameSite=Lax; Path=/auth/refresh`; Max-Age = 7 days)
  - Return HTTP **303 See Other** with `Location` set to env var `POST_LOGIN_REDIRECT_URL` (default `/`)
- **Response (API, `Accept: application/json`):**
  - Return 200 with `access_token` and `refresh_token` in the JSON body (wrapped in the standard `ApiResponse[T]` envelope)
  - No cookies set
- **Rate limit:** 5 per minute per IP

### POST `/auth/refresh`

- **Auth required:** Refresh token only (no access token needed; this endpoint exists to obtain a new one)
- **Input:** Refresh token sourced per client type — cookie `refresh_token` for browser, request body field for API
- **Content negotiation:** `Accept: text/html` (browser) → new cookies, 200 OK. `Accept: application/json` (API) → JSON body with new tokens.
- **Behavior (both paths):**
  1. Extract refresh token (cookie for browser, body for API)
  2. Hash it and look up in DB
  3. Validate: not revoked, not expired
  4. Check `last_activity_at` — if more than 30 minutes ago, reject (session timeout)
  5. Revoke current refresh token
  6. Issue new access token + new refresh token (rotation)
  7. Store new hashed refresh token in DB
  8. Update `last_activity_at`
- **Response (browser):** Set new `access_token` and `refresh_token` cookies with the same attributes as `/auth/login`. Return 200 OK (no redirect — this endpoint is called from inside the authenticated app, typically via fetch/HTMX).
- **Response (API):** Return 200 with the new `access_token` and `refresh_token` in the JSON body.
- **Rate limit:** 10 per minute per user
- **CSRF:** Not required. See §9.

### POST `/auth/logout`

- **Auth required:** Access token, sourced per client type — cookie `access_token` for browser, `Authorization: Bearer` header for API. Resolved by `get_current_user` (see §5).
- **Content negotiation:** `Accept: text/html` (browser) → clear cookies, 303 redirect. `Accept: application/json` (API) → JSON confirmation.
- **Behavior (both paths):**
  1. Validate access token to identify user
  2. Revoke ALL refresh tokens for this user (enforces single-session)
- **Response (browser):**
  - Clear `access_token` cookie (set with `Max-Age=0` and the same attributes as at login, so the browser evicts it)
  - Clear `refresh_token` cookie (set with `Max-Age=0` and the same attributes as at login)
  - Return HTTP **303 See Other** with `Location: /auth/login`
- **Response (API):** Return 200 with JSON confirmation.
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

- **`get_current_user`** — Resolves the current user from either the `Authorization: Bearer` header (API clients) or the `access_token` cookie (browser clients). Resolution order: **header first, cookie second.** Decodes and validates the JWT, loads User from DB. Returns the User object. Returns 401 if both sources are absent, or the token is expired/invalid. Header-first order ensures API clients are never affected by a stray browser cookie present on the same host.
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
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'` |
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

### CSP and Alpine.js

The CSP above must **not** include `'unsafe-eval'` in `script-src`. This is only possible because Alpine.js is used via the `@alpinejs/csp` build, which replaces runtime `Function()` evaluation with a restricted expression parser. If `'unsafe-eval'` ever appears in `script-src`, either the default `alpinejs` build has crept in or the CSP build has been bypassed — both are blocking issues and must be rejected in review.

Likewise, `'unsafe-inline'` must not appear in `script-src`. Alpine component registration (`Alpine.data('name', () => ({...}))`) lives in files under `app/static/js/` loaded via `<script src="...">`, never in inline `<script>` blocks. See `docs/TECH_STACK.md` → Alpine.js Security Constraints for the full ruleset (CSP-build-only, static `x-*` attributes, `x-html` forbidden on user data).

---

## 9. CSRF Protection

**Strategy:** `SameSite=Lax` on all auth cookies, combined with a hard rule that state-changing actions never use GET. No CSRF tokens, no CSRF library.

### Why this is sufficient

`SameSite=Lax` instructs the browser to omit the auth cookies on cross-site POST/PUT/PATCH/DELETE requests and on cross-site subresource fetches. The browser itself blocks the classic CSRF attack before the request reaches the server, so no server-side token check is needed.

### Preconditions — if any of these stops being true, revisit this decision

1. **No state-changing GET endpoints.** See the hard rule below. `SameSite=Lax` still attaches cookies on top-level GET navigation — this is intentional, because it is what allows inbound email/IM links to land the user logged in — so any GET that mutates state is a CSRF hole.
2. **Single origin.** The application is served from one origin. No untrusted subdomains share the cookie domain. `SameSite=Lax` protects against *cross-site* requests; subdomains are treated as same-site.
3. **HTTPS in all non-development environments.** Enforced via the `Secure` cookie attribute; see Transport Security.
4. **Modern browsers only.** All major browsers have enforced `SameSite=Lax` as the default since 2020. Users on browsers predating this enforcement are not protected.

### Hard rule: state-changing actions are POST / PUT / PATCH / DELETE only

GET requests are display-only. A GET endpoint MUST NOT mutate database state, revoke tokens, send emails, or trigger side effects of any kind.

**Rationale:** inbound links from email, IM, or notifications land as top-level GET navigations. `SameSite=Lax` sends the user's cookie on these requests. If a GET endpoint performs an action, an attacker who tricks a user into clicking a crafted link completes that action with the user's credentials.

**Pattern for action links in emails:** the email link points to a GET endpoint that renders a confirmation page. The user clicks a button on that page, which submits a POST to perform the action. The GET is safe to repeat; the POST carries intent.

### What replaces CSRF tokens

Nothing. The browser is doing the enforcement via `SameSite=Lax`. There is no token to generate, embed, or verify.

---

## 10. CORS Policy

- **Library:** `starlette.middleware.cors.CORSMiddleware` (included with FastAPI)
- **Apply to:** All responses via FastAPI middleware
- **Configuration:**

| Setting | Development | Production |
|---------|------------|------------|
| `allow_origins` | `["http://localhost:8000"]` | `["https://<production-domain>"]` |
| `allow_methods` | `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` | Same |
| `allow_headers` | `["Authorization", "Content-Type", "X-Correlation-ID"]` | Same |
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
  hidden via inline style in `base.html` or a small rule in `app/static/css/app.css`
  (do not edit the vendored `pico.min.css`)
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
| Email already exists | 409 | `EMAIL_ALREADY_EXISTS` |
| Username already exists | 409 | `USERNAME_ALREADY_EXISTS` |
| Validation error | 422 | `VALIDATION_ERROR` |
| Account locked | 403 | `ACCOUNT_LOCKED` |
| Rate limit exceeded | 429 | `RATE_LIMIT_EXCEEDED` |

---

## 14. Browser vs API Auth Flows — Summary

This table is the quick-reference index. Full behavior for each endpoint lives in §4.

| Aspect | Browser (HTML UI) | API client (scripts, integrations) |
|--------|-------------------|-------------------------------------|
| Detected by | `Accept: text/html` request header | `Accept: application/json` request header |
| Access token delivery | `access_token` HTTP-only cookie | JSON response body |
| Access token attachment | Automatic (browser sends cookie) | Manual — client adds `Authorization: Bearer <token>` header |
| Refresh token delivery | `refresh_token` HTTP-only cookie (`Path=/auth/refresh`) | JSON response body alongside access token |
| Refresh token storage (client) | Cookie only | Client-managed (keychain, secrets manager) |
| `/auth/login` success response | 303 redirect to `POST_LOGIN_REDIRECT_URL` | 200 with tokens in JSON body |
| `/auth/refresh` success response | New cookies + 200 OK | 200 with new tokens in JSON body |
| `/auth/logout` success response | Cleared cookies + 303 to `/auth/login` | 200 with confirmation |
| CSRF defense | `SameSite=Lax` cookie + no-state-changing-GET rule (§9) | Not applicable — attacker cannot forge `Authorization` header from another origin |
| XSS risk to token | Low — `HttpOnly` hides token from JS | N/A at browser; API client must protect its own token |

### Configuration

| Env var | Purpose | Default |
|---------|---------|---------|
| `POST_LOGIN_REDIRECT_URL` | Where the browser is redirected after successful login | `/` |

---

## 15. Transport Security

### HTTPS

- **Enforcement:** All production/beta deployments MUST use HTTPS. 
  HTTP is acceptable only in local development (`APP_ENV=development`).
- **Certificate management:** Handled by reverse proxy (Caddy with 
  automatic Let's Encrypt, or Nginx with certbot). The FastAPI 
  application does NOT terminate TLS.
- **Secure cookies:** The `Secure` flag on auth cookies (access token, refresh token) 
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
