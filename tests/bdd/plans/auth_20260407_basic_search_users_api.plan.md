# Plan: Search users

**Feature file:** `tests/features/auth/20260407_basic_search_users_api.feature`
**Module(s) affected:** app/auth/
**Date:** 2026-04-07
**Status:** APPROVED — ready for test writing

---

## 1. Feature Summary

This feature implements a basic search endpoint that allows authenticated users to find other users by their email address or username. The endpoint returns user information (email, username, first name, last name) when a match is found, and appropriate error responses when no match is found or when the user lacks proper authorization.

---

## 2. Scope Confirmation

- Feature type: API
- MVP: Yes
- Scenarios count: 2
- Modules touched: app/auth/ (only)

---

## 3. API Endpoints

**API features:** This feature adds a new search endpoint to the auth module.

| Method | Path | Auth required | Role required | Description |
|--------|------|---------------|---------------|-------------|
| POST | /auth/search-user | Yes | None | Search for users by email or username |

---

## 4. Database Changes

### New tables
None

### Modified tables
None

### Alembic migration required?
No

---

## 5. Module Breakdown

### app/auth/
- **router.py:** Add new POST endpoint `/auth/search-user` that accepts search parameters and returns user data
- **service.py:** Add `search_user()` function that queries the database for users by email or username
- **models.py:** No changes - existing User model already has required fields
- **schemas.py:** Add `UserSearchRequest` and `UserSearchResponse` Pydantic schemas
- **dependencies.py:** No changes - existing dependencies are sufficient

---

## 6. Security Considerations

- Does any endpoint require JWT auth? Yes - all endpoints in auth module require JWT auth
- Does any endpoint require a specific role? No - search is available to all authenticated users
- Are there rate limiting requirements? Yes - see docs/SECURITY.md Section 7
- Does this feature handle passwords or tokens? No - only user data is returned
- Does this feature require CSRF protection? No - this is not a cookie-authenticated endpoint
- What security events must be logged? Search attempts should be logged at INFO level

---

## 7. Audit Logging

List every action in this feature that must produce an audit log entry:

| Action | Table | action_type | Notes |
|--------|-------|-------------|-------|
| User search | users | READ | Security event log only, no audit_logs row |

---

## 8. Test Scenarios Breakdown

### Scenario: Successfully find user by email address
- **Test type:** BDD step def / unit test / both
- **Fixtures needed:** authenticated user, existing user record with email john.doe@example.com
- **What it verifies:** Search endpoint returns 200 status with correct user data when searching by email
- **Expected HTTP status:** 200 (Note: Feature file shows 201 but this is likely a mistake - search should return 200)

### Scenario: Successfully find user by username
- **Test type:** BDD step def / unit test / both
- **Fixtures needed:** authenticated user, existing user record with username john.doe
- **What it verifies:** Search endpoint returns 200 status with correct user data when searching by username
- **Expected HTTP status:** 200 (Note: Feature file shows 201 but this is likely a mistake - search should return 200)

---

## 9. Success Criteria

### Automated verification
- [ ] `pytest tests/bdd/step_defs/test_20260407_basic_search_users_api.py -v` — all scenarios pass
- [ ] `pytest tests/unit/auth/ -v` — all unit tests pass
- [ ] `alembic upgrade head` runs cleanly (if DB changes)
- [ ] `black . --check` passes
- [ ] `flake8 .` passes

### Manual verification
- [ ] Search endpoint returns correct user data when searching by email
- [ ] Search endpoint returns correct user data when searching by username
- [ ] Search endpoint returns 404 when user is not found
- [ ] Search endpoint requires valid JWT authentication

---

## 10. Implementation Order

**API feature track:**

- [ ] **Phase 1: Pydantic schemas** — `app/auth/schemas.py`
- [ ] **Phase 2: Service function(s)** — `app/auth/service.py`
- [ ] **Phase 3: Router endpoint(s)** — `app/auth/router.py`

---

## 11. Edge Cases and Error Conditions

Every error condition the implementation must handle:

| Condition | HTTP status | error_code |
|-----------|-------------|------------|
| User not found | 404 | USER_NOT_FOUND |
| Invalid search parameters | 422 | INVALID_SEARCH_PARAMETERS |
| Missing authentication | 401 | INVALID_CREDENTIALS |
| Invalid token | 401 | TOKEN_INVALID |

---

## 12. Out of Scope

Explicitly list what this plan does NOT cover:
- Fuzzy search or partial matching
- Search by first/last name
- Search by role or status
- Pagination of results
- Search by user ID
- Admin-only search functionality

---

## 13. Codebase Analysis Reference

Full analysis: `tests/bdd/plans/auth_20260407_basic_search_users_api.analysis.md`

### Key findings (from analysis doc synthesis)
- The auth module already exists with all required files (router, service, models, schemas, password utilities)
- The register endpoint pattern can be followed directly for the search endpoint
- The User model already exists and is fully defined with all required fields
- The existing service function pattern shows how to implement database operations with proper error handling
- No new database migrations needed - users table already exists

### Patterns to follow
- Follow the endpoint pattern from app/auth/router.py lines 43-63
- Follow the service function pattern from app/auth/service.py lines 61-158
- Follow the schema pattern from app/auth/schemas.py lines 59-105
- Follow the exception pattern from app/auth/service.py lines 31-54

---

## 14. File Manifest

Explicit file lists that `/write-tests` and `/implement` MUST follow.
These agents should read ONLY the files listed here — no broad exploration needed.

### Files to READ before writing tests

| File | Why |
|------|-----|
| `CLAUDE.md` | Behavioral rules |
| `tests/features/auth/20260407_basic_search_users_api.feature` | The contract |
| This plan file | Scenarios, fixtures, success criteria |
| `tests/bdd/conftest.py` | Reuse existing fixtures |
| `docs/GUIDE.md` | Error response format (only if testing error shapes) |
| `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` | Reuse existing patterns |

### Files to READ before implementing

| File | Why |
|------|-----|
| `CLAUDE.md` | Behavioral rules |
| `tests/features/auth/20260407_basic_search_users_api.feature` | The contract |
| This plan file | Implementation order, phases |
| `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` | Understand what tests expect |
| `docs/DATA_MODELS.md` | DB schema (only if DB changes needed) |
| `docs/SECURITY.md` | Security rules (only if auth/passwords involved) |
| `docs/GUIDE.md` | Code patterns |
| `app/auth/router.py` | Existing endpoint structure |
| `app/auth/service.py` | Existing service function structure |
| `app/auth/schemas.py` | Existing schema structure |

### Files to CREATE

| File | Agent | Purpose |
|------|-------|---------|
| `tests/bdd/step_defs/test_20260407_basic_search_users_api.py` | write-tests | BDD step definitions |
| `tests/unit/auth/test_search_user.py` | write-tests | Unit tests (if needed) |
| `app/auth/schemas.py` | implement | Add search schemas |
| `app/auth/service.py` | implement | Add search service function |
| `app/auth/router.py` | implement | Add search endpoint |

### Files to MODIFY

| File | Agent | What changes |
|------|-------|--------------|
| `app/auth/schemas.py` | implement | Add UserSearchRequest and UserSearchResponse schemas |
| `app/auth/service.py` | implement | Add search_user function |
| `app/auth/router.py` | implement | Add POST /auth/search-user endpoint |
| `app/main.py` | implement | No changes needed - auth router is already imported |