# Plan: Basic Login User API

**Feature file:** `tests/features/auth/20260408_basic_login_user_api.feature`
**Module(s) affected:** `app/auth/`, `app/core/exceptions.py` (message-only change)
**Date:** 2026-04-16
**Status:** FROZEN

---

## 1. Feature Summary

Implements the `POST /auth/login` endpoint — the first iteration of user authentication. Users provide email and password; the service verifies credentials, manages failed login attempt tracking with automatic account lockout after 5 failures (30-minute lock), and returns a JWT access token on success. Locked accounts with expired locks are auto-unlocked on successful login.

---

## 2. Scope Confirmation

- Feature type: API
- MVP: Yes — `docs/SCOPE.md` Module 1: "User login (email + password)", "Failed login tracking + account lockout", "JWT token generation, validation, revocation"
- Scenarios count: 5
- Modules touched: `app/auth/` (primary), `app/core/exceptions.py` (message update only — approved by developer)

---

## 3. API Endpoints

| Method | Path | Auth required | Role required | Description |
|--------|------|---------------|---------------|-------------|
| POST | /auth/login | No | None | Authenticate user, return JWT access token |

This is the only public endpoint besides `/auth/register` — no `get_current_user` dependency.

---

## 3b. API Dependencies *(UI features only — omit for API features)*

N/A — API feature.

---

## 4. Database Changes

### New tables
None.

### Modified tables
None — the `users` table already has `failed_login_attempts` (Integer, default=0), `locked_until` (DateTime, nullable), `status` (Enum including `locked`), and `last_activity_at` (DateTime, nullable). All fields needed by this feature exist per `docs/DATA_MODELS.md`.

### Alembic migration required?
No.

---

## 5. Module Breakdown

### app/auth/

- **router.py:** Add `POST /login` endpoint. No auth dependencies. Uses `get_correlation_id` and `get_db`. Returns `ApiResponse[LoginData]` with status 200.
- **service.py:** Add `login_user(db, request, correlation_id) -> LoginData` function. Full login flow: user lookup, password verification, lock/status check, counter management, token generation.
- **models.py:** No changes — `User` model already has all required fields.
- **schemas.py:** Add `LoginRequest` (email, password — no password policy validation on login) and `LoginData` (access_token, token_type). `LoginRequest` uses plain `str` for email — no `EmailStr` validator. Login must accept any string and let the DB lookup determine validity (prevents 422 on malformed emails — feature file Scenario 2 depends on this).
- **jwt_handler.py (NEW):** `create_access_token(user_id, role) -> str`. PyJWT HS256 with claims: `sub`, `role`, `exp`, `iat`, `jti`. 15-minute expiry. Secret from `JWT_SECRET_KEY` env var via `app/core/config.py`.

### app/core/

- **exceptions.py:** Update `InvalidCredentialsError` message from `"Invalid credentials"` to `"Login failed. You must have used an incorrect email address or password."`. No structural changes. Verify `AccountLockedError` message matches feature file expectation: `"Account is locked due to multiple failed login attempts."` — if it already matches, no change needed; if not, update.

---

## 6. Security Considerations

- Does any endpoint require JWT auth? No — `/auth/login` is a public endpoint (per `docs/SECURITY.md` Section 4).
- Does any endpoint require a specific role? No.
- Are there rate limiting requirements? Yes — 5 per minute per IP (`docs/SECURITY.md` Section 7). **Out of scope for this feature file** — no scenarios test rate limiting. Will be implemented with the rate limiting feature.
- Does this feature handle passwords or tokens? Yes:
  - Passwords: verified via `verify_password()` from `app/auth/password.py` (already exists, not yet called). Raw passwords are NEVER logged.
  - Tokens: JWT access token generated and returned in response body. Token secret from env var, never hardcoded.
- Does this feature require CSRF protection? No — login uses email/password in request body, not cookies.
- What security events must be logged (`docs/SECURITY.md` Section 12):
  - Successful login — INFO
  - Failed login attempt — WARNING
  - Account locked (auto) — WARNING

---

## 7. Audit Logging

| Action | Table | action_type | Notes |
|--------|-------|-------------|-------|
| Successful login | users | — | Logged via `logger.info` with correlation_id, user_id. No audit_logs table entry for login (it's a read operation, not a data mutation). Field updates (failed_login_attempts reset, status change, last_activity_at) are DB writes but tracked via security event logging, not the formal audit_logs table. |
| Failed login | users | — | Logged via `logger.warning` with correlation_id, email domain (not full email — avoid PII). |
| Account locked | users | — | Logged via `logger.warning` with correlation_id, user_id. |

Note: The `audit_logs` table is for data mutations (CREATE/UPDATE/DELETE of business entities). Login events are security events logged to the application logger per `docs/SECURITY.md` Section 12. Formal audit log entries for user field updates (status, failed_login_attempts) are deferred to when the audit logging service is implemented.

---

## 8. Test Scenarios Breakdown

### Scenario 1: Successful login
- **Test type:** BDD step def
- **Fixtures needed:** registered user (active, failed_login_attempts=0) — created inline via `db_session` + `hash_password()` from `app/auth/password.py`
- **What it verifies:** 200 response, ApiResponse envelope, valid JWT in data.access_token, message "Login successful.", valid UUID correlation_id, failed_login_attempts remains 0
- **Token verification:** Step def imports `jwt` (PyJWT) to decode the access token and verify claims (sub, role, exp, iat, jti)
- **Expected HTTP status:** 200

### Scenario 2: User is not logged in when using incorrect email and password combination
- **Test type:** BDD step def
- **Fixtures needed:** registered user (active, failed_login_attempts=2) — created inline via `db_session` + `hash_password()`
- **What it verifies:** 401 response, error envelope, error_code "INVALID_CREDENTIALS", message "Login failed. You must have used an incorrect email address or password.", valid UUID correlation_id, empty details, failed_login_attempts incremented by 1
- **DB verification:** Step def queries `db_session` after the HTTP request to assert `failed_login_attempts` was incremented from 2 to 3
- **Expected HTTP status:** 401

### Scenario 3: Lock user account when failed_login_attempts counter reaches 5 failed logins
- **Test type:** BDD step def
- **Fixtures needed:** registered user (active, failed_login_attempts=4) — created inline via `db_session` + `hash_password()`
- **What it verifies:** failed_login_attempts reaches 5, status set to "locked", locked_until set to now+30min, 403 response, error_code "ACCOUNT_LOCKED", message "Account is locked due to multiple failed login attempts.", valid UUID correlation_id, empty details
- **DB verification:** Step def queries `db_session` after the HTTP request to assert `failed_login_attempts=5`, `status="locked"`, and `locked_until` is approximately now+30min (UTC)
- **Expected HTTP status:** 403

### Scenario 4: Reset failed_login_attempts counter and set user account status to active on successful login
- **Test type:** BDD step def
- **Fixtures needed:** registered user (locked, locked_until in the past, failed_login_attempts=3) — created inline via `db_session` + `hash_password()`
- **What it verifies:** 200 response, ApiResponse envelope, valid JWT, message "Login successful.", failed_login_attempts reset to 0, status set to "active"
- **Token verification:** Step def imports `jwt` (PyJWT) to decode the access token and verify claims
- **DB verification:** Step def queries `db_session` after the HTTP request to assert `failed_login_attempts=0` and `status="active"`
- **Structural note:** The feature file places the login action in a Given/And step ("And the user successfuly logs in with the correct details") — the HTTP request must happen there, storing the response in `context`. The When step ("When the user is successfully logged in") is a state confirmation, not the action trigger.
- **Expected HTTP status:** 200

### Scenario 5: Login with correct credentials fails when account is locked and lock duration did not expire
- **Test type:** BDD step def
- **Fixtures needed:** registered user (locked, locked_until in the future) — created inline via `db_session` + `hash_password()`
- **What it verifies:** 403 response, error_code "ACCOUNT_LOCKED", message "Account is locked due to multiple failed login attempts.", valid UUID correlation_id
- **Expected HTTP status:** 403

---

## 9. Success Criteria

### Automated verification
- [x] `pytest tests/bdd/step_defs/test_20260408_basic_login_user_api.py -v` — all 5 scenarios pass
- [x] `black . --check` passes (pre-existing issues in unrelated files only)
- [x] `flake8 .` passes (pre-existing E402 in alembic/env.py only)

### Manual verification
- [ ] JWT token returned in successful login can be decoded and contains expected claims (sub, role, exp, iat, jti)
- [ ] Account lockout timing: locked_until is approximately 30 minutes after the failed attempt (UTC)

---

## 10. Implementation Order

**Red-green note:** BDD tests hit the HTTP endpoint, so all 5 phases must be implemented before any test turns GREEN. Tests are written first (RED) and remain RED until all phases complete. No intermediate GREEN checkpoints exist for individual phases.

- [x] **Phase 1: Pydantic schemas** — `app/auth/schemas.py`
  - Add `LoginRequest` (email: str, password: str) — no `EmailStr`, no format validation (Scenario 2 sends malformed email, expects 401 not 422)
  - Add `LoginData` (access_token: str, token_type: str = "bearer")
  - Test signal: Scenarios 1-5 (every request validates LoginRequest deserialization; Scenarios 1/4 validate LoginData in the response)

- [x] **Phase 2: JWT handler** — `app/auth/jwt_handler.py` (NEW FILE)
  - `create_access_token(user_id: int, role: str) -> str`
  - PyJWT, HS256, claims: sub, role, exp, iat, jti (jti generated via `uuid4().hex`)
  - 15-minute expiry from `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` config
  - Secret from `JWT_SECRET_KEY` config
  - **Config dependency:** If `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, or `JWT_ALGORITHM` are not yet in the Settings class in `app/core/config.py`, add them. This `app/core/*` modification is pre-approved (adversarial review, developer-approved 2026-04-16).
  - Test signal: Scenarios 1/4 (step defs decode the returned JWT using PyJWT and verify claims: sub, role, exp, iat, jti)

- [x] **Phase 3: Exception update** — `app/core/exceptions.py`
  - Update `InvalidCredentialsError` message to: "Login failed. You must have used an incorrect email address or password."
  - Test signal: Scenarios 2/3/5 assert exact error messages (2: InvalidCredentialsError, 3/5: AccountLockedError)

- [x] **Phase 4: Service function** — `app/auth/service.py`
  - Add `login_user(db, request, correlation_id) -> LoginData`
  - Flow (matches `docs/SECURITY.md` Section 4 ordering):
    1. Look up user by email → raise `InvalidCredentialsError` if not found
    2. Verify password via `verify_password()` — always runs to eliminate timing side-channels
    3. If password WRONG:
       - Increment `failed_login_attempts`, flush
       - If `failed_login_attempts >= 5`: set `status=locked`, set `locked_until=now+30min`, flush → raise `AccountLockedError`
       - Else: raise `InvalidCredentialsError`
    4. If password CORRECT:
       - Check if status is `locked` and `locked_until >= now` → raise `AccountLockedError`
       - Check if status allows login (`active`, or `locked` with expired `locked_until`) → raise appropriate error if not (deferred to future feature — only active and locked statuses are covered by this feature file)
       - Reset `failed_login_attempts=0`
       - If status was `locked` (expired lock): set `status=active`
       - Update `last_activity_at=now` (**driven by `docs/SECURITY.md` step 6, not tested by feature file** — needed for future session timeout on `/auth/refresh`)
       - Generate access token via `create_access_token()`
       - Return `LoginData`
  - Security event logging at each decision point
  - Test signal: All 5 scenarios exercise this function

- [x] **Phase 5: Router endpoint** — `app/auth/router.py`
  - `POST /login`, `response_model=ApiResponse[LoginData]`, `status_code=200`
  - Dependencies: `get_db`, `get_correlation_id` (no auth)
  - Wraps service result in `ApiResponse` envelope
  - Test signal: All 5 scenarios hit this endpoint

---

## 11. Edge Cases and Error Conditions

| Condition | HTTP status | error_code | Notes |
|-----------|-------------|------------|-------|
| Invalid credentials (wrong password or email not found) | 401 | INVALID_CREDENTIALS | Same response for both to prevent email enumeration |
| Account locked, lock not expired | 403 | ACCOUNT_LOCKED | Applies to both correct and incorrect credentials |
| 5th failed login attempt (triggers lock) | 403 | ACCOUNT_LOCKED | Counter incremented first, then lock applied |
| Locked account, lock expired, correct password | 200 | — | Auto-unlock: status→active, counter→0 |

**Not covered by this feature file (deferred):**
- Non-existent email (handled: returns INVALID_CREDENTIALS — same as wrong password)
- Account in suspended/inactive/pending status (future feature file)
- Rate limiting (future feature file)
- Refresh token / cookie handling (future feature file)

---

## 12. Out of Scope

- Refresh token generation and storage — deferred to refresh/logout feature
- HTTP-only cookie and CSRF cookie setting — deferred to refresh/logout feature
- Rate limiting on `/auth/login` — deferred to rate limiting feature
- Login for suspended/inactive/pending accounts — deferred to future feature file
- Token decode/validation (`get_current_user` dependency) — separate feature
- Password reset — separate feature per `docs/SCOPE.md`

---

## 13. Codebase Analysis Reference

Full analysis: `tests/bdd/plans/auth_20260408_basic_login_user_api.analysis.md`

### Key findings (from analysis doc synthesis)
- `app/auth/` module exists with router, service, models, schemas, password utilities — this is an extension, not a new module
- `User` model already has `failed_login_attempts`, `locked_until`, `status` (including `locked` enum value) — no migration needed
- `verify_password()` exists in `app/auth/password.py` but is not yet called — built for this feature
- `InvalidCredentialsError` (401) and `AccountLockedError` (403) already defined in `app/core/exceptions.py`
- No JWT token generation exists yet — `jwt_handler.py` must be created
- Existing `POST /register` endpoint provides the template for router/service/test structure
- BDD step defs use synchronous `_run()` wrappers around async calls and pass state via `context` dict

### Patterns to follow
- **Endpoint pattern:** `app/auth/router.py:33-52` — POST /register structure
- **Service function pattern:** `app/auth/service.py:61-158` — register_user structure (logger on entry, warning on rejection, info on success, db.flush not commit)
- **Schema pattern:** `app/auth/schemas.py:59-122` — request/response with field validators
- **Exception pattern:** `app/core/exceptions.py:60-103` — AppException subclasses with hardcoded messages
- **BDD test pattern:** `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` — scenarios(), _run(), context dict, datatable parsing
- **Conftest fixtures:** `tests/bdd/conftest.py` — clean_tables, db_session, client, context (all reusable)

---

## 14. File Manifest

### Files to READ before writing tests

| File | Why |
|------|-----|
| `tests/features/auth/20260408_basic_login_user_api.feature` | The contract — all scenarios |
| This plan file | Scenarios breakdown, fixtures, success criteria |
| `tests/bdd/conftest.py` | Reuse existing fixtures (clean_tables, db_session, client, context) |
| `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` | Pattern for step defs (_run, context, datatable, scenarios import) |
| `app/auth/models.py` | User model fields for fixture setup |
| `app/auth/password.py` | hash_password for creating test users |

### Files to READ before implementing

| File | Why |
|------|-----|
| `tests/features/auth/20260408_basic_login_user_api.feature` | The contract |
| This plan file | Implementation order, phases, service flow |
| `tests/bdd/step_defs/test_20260408_basic_login_user_api.py` | What tests expect |
| `app/auth/router.py` | Existing endpoint pattern to follow |
| `app/auth/service.py` | Existing service function pattern, exception pattern |
| `app/auth/schemas.py` | Existing schema pattern |
| `app/auth/password.py` | verify_password function signature |
| `app/auth/models.py` | User model (fields, enums) |
| `app/core/exceptions.py` | InvalidCredentialsError, AccountLockedError |
| `app/core/schemas.py` | ApiResponse[T] envelope |
| `app/core/config.py` | JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM — READ first, MODIFY if settings not yet declared (see Phase 2) |
| `app/core/dependencies.py` | get_correlation_id dependency |
| `docs/SECURITY.md` | JWT claims spec, login flow, security event logging |

### Files to CREATE

| File | Agent | Purpose |
|------|-------|---------|
| `tests/bdd/step_defs/test_20260408_basic_login_user_api.py` | write-tests | BDD step definitions for all 5 scenarios |
| `app/auth/jwt_handler.py` | implement | JWT access token creation (PyJWT, HS256) |

### Files to MODIFY

| File | Agent | What changes |
|------|-------|--------------|
| `app/auth/schemas.py` | implement | Add LoginRequest, LoginData |
| `app/auth/service.py` | implement | Add login_user() function |
| `app/auth/router.py` | implement | Add POST /login endpoint |
| `app/core/exceptions.py` | implement | Update InvalidCredentialsError message |
| `app/core/config.py` | implement | (conditional) Add JWT settings to Settings class if not present — pre-approved in adversarial review |

### Files NOT touched

Everything not listed above. No broad exploration needed.

---

## 15. Changelog

| Date | Phase | Scope | Changes |
|------|-------|-------|---------|
| 2026-04-16 | draft | — | Initial plan created. Approach A chosen: access token only, defer refresh token infrastructure. |
| 2026-04-16 | iterate | adversarial | Reordered service flow: password verification before lock check (matches updated SECURITY.md). Added conditional config.py modification to Phase 2 + file manifest. Added SECURITY.md attribution for last_activity_at update. |
| 2026-04-16 | iterate | enrich | Added no-EmailStr constraint to LoginRequest (Sections 5, 10). Added AccountLockedError message verification to Section 5. Replaced vague "correct message" with exact strings in Section 8 Scenarios 2/3/5. Replaced range-based fixtures with concrete values in Scenarios 2/4. Added jti generation method to Phase 2. |
| 2026-04-16 | iterate | testability | Replaced "N/A" test signals in Phases 1/2/3 with specific scenario references. Added red-green note (all phases must complete before GREEN). Added DB verification, token verification, hash_password, and Scenario 4 structural notes to Section 8. |
| 2026-04-16 | freeze | — | Plan frozen for implementation |
