# Plan: New User Account Registration

**Feature file:** `tests/features/auth/20260407_basic_register_user_api.feature`
**Module(s) affected:** `app/auth/`
**Date:** 2026-04-07
**Status:** APPROVED — ready for test writing

---

## 1. Feature Summary

This feature provides a public API endpoint for new visitors to create an account by submitting their email, username, password, first name, and last name. The endpoint validates input (password complexity, email format, required fields), checks for duplicate email/username, hashes the password, and creates the user with role `super_user` and status `active`. This is the first entry point into the system for new users.

---

## 2. Scope Confirmation

- Feature type: API
- MVP: Yes — `docs/SCOPE.md` Module 1, "User self-registration via registration form"
- Scenarios count: 11
- Modules touched: `app/auth/` only — no cross-module escalation

---

## 3. API Endpoints

| Method | Path | Auth required | Role required | Description |
|--------|------|---------------|---------------|-------------|
| POST | `/auth/register` | No | None | Register a new user account |

---

## 4. Database Changes

### New tables

- **`users`** — see `docs/DATA_MODELS.md` → Module 1: Auth. Required because this is the first feature touching the auth module; no tables exist yet.

### Modified tables

None

### Alembic migration required?

Yes — create the `users` table with all fields defined in `DATA_MODELS.md`:
- `id`, `email`, `username`, `hashed_password`, `role`, `status`
- `failed_login_attempts`, `locked_until`, `last_password_change`, `last_activity_at`
- `first_name`, `last_name`
- Audit fields: `created_at`, `updated_at`, `created_by`, `updated_by`
- Indexes: `ix_users_email`, `ix_users_username`, `ix_users_status`
- Unique constraints: `uq_users_email`, `uq_users_username`

Note: The `users` table does NOT have soft delete fields — it is not user-created content. This is correct per `DATA_MODELS.md`.

---

## 5. Module Breakdown

### app/auth/

- **router.py:** Add `POST /auth/register` endpoint. Accepts `UserRegisterRequest`, delegates to service, returns `UserRegisterResponse` with 201 status.
- **service.py:** Add `register_user()` function — validates uniqueness (email, username), hashes password via passlib argon2, creates user record with role=`super_user` and status=`active`, writes audit log entry, returns response with confirmation message.
- **models.py:** Define `User` SQLAlchemy model matching `DATA_MODELS.md` users table exactly.
- **schemas.py:** Define:
  - `UserRegisterRequest` — email (validated format), username (required, non-empty), password (validated against policy: min 8 chars, at least one letter, at least one number, at least one special character from `@$!%*#?&`), first_name, last_name
  - `UserRegisterResponse` — confirmation message, user status, user role
- **password.py:** Add `hash_password()` utility using passlib with argon2 backend.
- **dependencies.py:** No changes needed for this feature (registration is public, no auth dependency required).

---

## 6. Security Considerations

- Does any endpoint require JWT auth? **No** — `POST /auth/register` is a public endpoint per `SECURITY.md` Section 4.
- Does any endpoint require a specific role? **No**
- Are there rate limiting requirements? **Yes** — 5 per minute per IP (`SECURITY.md` Section 7). Note: rate limiting infrastructure (fastapi-limiter + Redis) may not be set up yet. If not, implement the endpoint without rate limiting and flag it as a follow-up. Do NOT block the feature on rate limiting setup.
- Does this feature handle passwords? **Yes** — passwords must be hashed with argon2 via passlib before storage (`SECURITY.md` Section 1). Raw passwords must NEVER be stored or logged.
- Does this feature require CSRF protection? **No** — CSRF applies to cookie-authenticated endpoints only (`SECURITY.md` Section 9). Registration uses no cookies.
- What security events must be logged?
  - Successful registration → INFO (`SECURITY.md` Section 12)

---

## 7. Audit Logging

| Action | Table | action_type | Notes |
|--------|-------|-------------|-------|
| New user registers | users | CREATE | Log new user ID, email (no password). `created_by` will be NULL (self-registration — no authenticated user). |

---

## 8. Test Scenarios Breakdown

### Scenario 1: Successful registration with valid credentials that do not exist in the DB
- **Test type:** BDD step def
- **Fixtures needed:** Clean database (no existing user with test email/username), async HTTP client
- **What it verifies:** User created with status `active` and role `super_user`, 201 response, confirmation message "Congrats! Your account has been successfully created."
- **Expected HTTP status:** 201

### Scenario 2: Registration failure when email already exists
- **Test type:** BDD step def
- **Fixtures needed:** Pre-existing user with email `john.doe@example.com`
- **What it verifies:** Account not created, 409 response, message "Email address already in use. Please login with your existing account!"
- **Expected HTTP status:** 409

### Scenario 3: Registration failure when username already exists
- **Test type:** BDD step def
- **Fixtures needed:** Pre-existing user with username `john.doe`
- **What it verifies:** Account not created, 409 response, message "Username already in use. Please choose a different username!"
- **Expected HTTP status:** 409

### Scenario 4: Registration failure when password is too short
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client (no DB setup needed)
- **What it verifies:** Account not created, 422 response, message "Password does not meet the complexity requirements. Please fix it."
- **Expected HTTP status:** 422

### Scenario 5: Registration failure when missing required fields from registration payload
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** Account not created, 422 response, message "Missing required registration details. Please fix it!"
- **Expected HTTP status:** 422

### Scenario 6: Registration failure when password has no letters and special characters
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** All-numeric password rejected, 422 response, password complexity message
- **Expected HTTP status:** 422

### Scenario 7: Registration failure when password has no special characters
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** Password without special chars rejected (`Weak1234`), 422 response, password complexity message
- **Expected HTTP status:** 422

### Scenario 8: Registration failure when password has no letters
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** Numbers + special chars only rejected (`1234!!!!!!`), 422 response, password complexity message
- **Expected HTTP status:** 422

### Scenario 9: Registration failure when password has no numbers and special characters
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** Letters-only password rejected (`WeakWeakWeakWeakWeak`), 422 response, password complexity message
- **Expected HTTP status:** 422

### Scenario 10: Registration failure when email is missing the domain
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** Email `john.doe9@` rejected, 422 response, message "Incorrect email address format. Please fix it."
- **Expected HTTP status:** 422

### Scenario 11: Registration failure when email is missing the domain suffix
- **Test type:** BDD step def
- **Fixtures needed:** Async HTTP client
- **What it verifies:** Email `john.doe9@example` rejected (no TLD), 422 response, message "Incorrect email address format. Please fix it."
- **Expected HTTP status:** 422

---

## 9. Success Criteria

### Automated verification
- [x] `pytest tests/bdd/step_defs/test_20260407_basic_register_user_api.py -v` — all 11 scenarios pass
- [x] `pytest tests/unit/auth/ -v` — all unit tests pass (password hashing, password validation, email validation)
- [ ] `alembic upgrade head` runs cleanly (creates users table)
- [ ] `alembic downgrade -1` runs cleanly (drops users table)
- [x] `black . --check` passes
- [x] `flake8 .` passes

### Manual verification
- [ ] Send a valid registration request via curl/httpx and confirm 201 response with correct message
- [ ] Send a duplicate email registration and confirm 409 with correct message
- [ ] Confirm the password is stored as an argon2 hash in the database (not plain text)
- [ ] Confirm no password appears in application logs after a registration request
- [ ] Confirm the `created_by` field is NULL for self-registered users

---

## 10. Implementation Order

**API feature track:**

- [x] **Phase 1: Alembic migration** — `alembic/versions/` — Create `users` table with all fields, indexes, and constraints from `DATA_MODELS.md`
- [x] **Phase 2: SQLAlchemy model** — `app/auth/models.py` — Define `User` model matching `DATA_MODELS.md` exactly
- [x] **Phase 3: Pydantic schemas** — `app/auth/schemas.py` — Define `UserRegisterRequest` (with password policy + email format validators) and `UserRegisterResponse`
- [x] **Phase 4: Password utility** — `app/auth/password.py` — `hash_password()` and `verify_password()` using passlib argon2
- [x] **Phase 5: Service function** — `app/auth/service.py` — `register_user()` with duplicate checks, hashing, audit log, correlation ID
- [x] **Phase 6: Router endpoint** — `app/auth/router.py` — `POST /auth/register` wired to service, returns 201

---

## 11. Edge Cases and Error Conditions

| Condition | HTTP status | error_code | Feature file scenario |
|-----------|-------------|------------|-----------------------|
| Email already exists | 409 | `EMAIL_ALREADY_EXISTS` | Scenario 2 |
| Username already exists | 409 | `USERNAME_ALREADY_EXISTS` | Scenario 3 |
| Password too short (< 8 chars) | 422 | `VALIDATION_ERROR` | Scenario 4 |
| Missing required fields | 422 | `VALIDATION_ERROR` | Scenario 5 |
| Password has no letters or special chars | 422 | `VALIDATION_ERROR` | Scenario 6 |
| Password has no special characters | 422 | `VALIDATION_ERROR` | Scenario 7 |
| Password has no letters | 422 | `VALIDATION_ERROR` | Scenario 8 |
| Password has no numbers or special chars | 422 | `VALIDATION_ERROR` | Scenario 9 |
| Invalid email format (no domain) | 422 | `VALIDATION_ERROR` | Scenario 10 |
| Invalid email format (no TLD) | 422 | `VALIDATION_ERROR` | Scenario 11 |

---

## 12. Out of Scope

Explicitly excluded from this plan — do not implement:

- **User login** — separate feature file (`POST /auth/login`)
- **Token generation (JWT + refresh)** — part of login feature
- **User logout** — separate feature file
- **Admin user management** — separate feature file (admin creates/edits/removes users)
- **Password reset** — separate feature file
- **Account lockout** — part of login feature
- **Rate limiting on registration** — requires fastapi-limiter + Redis infrastructure setup; will be added when infrastructure is in place
- **Honeypot bot protection** — requires UI form (this is API only); will be covered in the UI registration feature
- **Email verification/confirmation** — not in MVP scope
- **`refresh_tokens` table** — not needed until login feature is implemented
- **CORS middleware** — infrastructure concern, not specific to this feature
- **Security headers middleware** — infrastructure concern, not specific to this feature
