# Review: Basic Login User API

**Feature file:** `tests/features/auth/20260408_basic_login_user_api.feature`
**Plan:** `tests/bdd/plans/auth_20260408_basic_login_user_api.plan.md`
**Date:** 2026-04-16
**Test result:** 5/5 passed

---

## Compliance Check

### A: Test integrity
- [x] PASS — All 5 `.feature` scenarios have corresponding step definitions
- [x] PASS — No test was modified to make it pass
- [x] PASS — Tests cover happy path (scenarios 1, 4), validation failure (scenario 2), lockout (scenarios 3, 5)
- [x] PASS — No trivially passing tests — all steps assert concrete values and DB state

### B: Module structure
- [x] PASS — Code in correct module (`app/auth/`)
- [x] PASS — No business logic in `router.py` — delegates to `auth_service.login_user()`, wraps in `ApiResponse`
- [x] PASS — No direct SQLAlchemy model imports from other modules
- [x] PASS — `from_attributes=True` on `LoginData` and `UserRegisterResponse`
- [x] PASS — No catch-all `utils.py`

### C: Function quality
- [x] PASS — Type hints on all parameters and return values
- [x] PASS — Docstrings on all new functions
- [x] PASS — `correlation_id: str` on `login_user` service function (`service.py:159`)
- [x] PASS — No `print()` — logging only

### D: Security
- [x] PASS — `POST /auth/login` correctly exempt from `get_current_user` (per `docs/SECURITY.md` Section 4)
- [x] N/A — `require_role(...)` — login is a public endpoint, no RBAC
- [x] PASS — No secrets/tokens/passwords logged — log entries use `email_domain` not full email
- [x] PASS — No stack traces in API responses
- [x] PASS — `ApiResponse[LoginData]` envelope with `correlation_id` on success (`router.py:56,75-79`)
- [x] PASS — No hardcoded secrets — JWT secret from `settings.jwt_secret_key` (`jwt_handler.py:48-49`)
- [x] N/A — Tokens in HTTP-only cookies — deferred to refresh token feature (per plan Section 12)
- [x] N/A — Password hashing — login uses `verify_password()`, not hashing

### E: Database
- [x] N/A — No schema changes, no Alembic migration needed (per plan Section 4)
- [x] N/A — No migration
- [x] PASS — Existing `User` model has all mandatory audit fields (`models.py:104-116`)
- [x] N/A — No new models

### F: Observability
- [x] PASS — Correlation ID in every log entry (`service.py:183-272`)
- [x] N/A — Audit log for CREATE/UPDATE/DELETE — login is not a data mutation; security event logging used instead (per plan Section 7)
- [x] PASS — Correct log levels: INFO for attempt/success/auto-unlock, WARNING for failed/locked/rejected

### G: Code quality
- [x] PASS — `black --check` passes on all changed files
- [x] PASS — `flake8` passes on all changed files
- [x] PASS — Import order correct: stdlib -> third-party -> local
- [x] PASS — No unused imports

### H: UI/Template quality
- [x] N/A — API feature only

---

## Compliance Summary

```
PASSED:  22
FAILED:  0
N/A:     8

All compliance checks passed. Safe to commit.
```

---

## Learning Notes

### 1. Timing side-channel mitigation via password verification order
**What:** `service.py:206` always verifies the password before checking lock status, even when the account is locked.
**Why:** If password verification were skipped for locked accounts, an attacker could detect locked (existing) accounts by measuring response time — hashing is slow, so a faster response reveals the account exists. By always running `verify_password()`, all code paths take roughly the same time.
**What if done differently:** Checking lock status first and returning early would be faster for locked accounts, but creates a timing oracle that leaks account existence information to attackers.

### 2. Plain `str` for LoginRequest.email instead of EmailStr or regex validation
**What:** `LoginRequest` (`schemas.py:126-137`) uses `email: str` with no format validation, unlike `UserRegisterRequest` which validates email format.
**Why:** Login must return 401 ("invalid credentials") for any input that doesn't match a DB record, including malformed emails. If Pydantic rejected bad emails with a 422, that would tell an attacker the email format was wrong vs. the account not existing — and the feature file explicitly tests this (Scenario 2 expects 401, not 422).
**What if done differently:** Using `EmailStr` or the `_EMAIL_PATTERN` regex would trigger a 422 validation error before the service layer runs, leaking information about email format validity and breaking the `.feature` contract.

### 3. `db.flush()` instead of `db.commit()` in the service
**What:** `service.py:211,215,264` uses `await db.flush()` to write changes to the database without committing.
**Why:** The `get_db` dependency manages the transaction lifecycle — it commits on success and rolls back on exception. If the service called `commit()`, a later error in the same request would leave partial writes in the database (e.g., counter incremented but exception handler hasn't sent the response). `flush()` sends the SQL to the DB engine so subsequent queries in the same transaction see the changes, but the actual commit waits for the request to complete successfully.
**What if done differently:** Calling `commit()` in the service would work in the happy path but break atomicity. In .NET terms, this is similar to `SaveChanges()` inside a `TransactionScope` — you want the scope (the request lifecycle) to control when the transaction completes.

### 4. `app_exception_handler` reads correlation ID from request header, not `request.state`
**What:** `exceptions.py:108` reads `request.headers.get("X-Correlation-ID")` to include in error responses, while the `get_correlation_id` dependency reads from `request.state.correlation_id`.
**Why:** This is a pre-existing pattern, not introduced by this feature. It works when the client sends the header, but if the middleware generates a UUID (no client header), the error response will still have a correlation ID because `error_response()` falls back to generating a new UUID (`exceptions.py:37`). However, that fallback UUID won't match the one the middleware set on `request.state` — so the correlation ID in the error response may differ from what the middleware logged.
**What if done differently:** Reading from `request.state.correlation_id` (with a fallback) would ensure error responses always carry the same correlation ID that the middleware assigned. Worth fixing in a future cleanup, but out of scope for this feature.

### 5. `uuid4().hex` for JTI instead of `str(uuid4())`
**What:** `jwt_handler.py:45` uses `uuid4().hex` which produces a 32-character hex string without hyphens, not the standard `8-4-4-4-12` UUID format.
**Why:** The JTI claim just needs to be unique per token for future revocation lookup. The hex format is more compact (32 chars vs. 36) and avoids hyphens in the claim value. Both forms are equally unique — `.hex` is just the same 128 bits without formatting.
**What if done differently:** Using `str(uuid4())` would produce the hyphenated form, which is more recognizable as a UUID but wastes 4 bytes. Either works; the choice is cosmetic. The step def validates the token has a `jti` claim without checking its format, so this satisfies the contract.
