# Plan: 20260621 Basic Register User UI

**Feature file:** `tests/features/auth/20260621_basic_register_user_ui.feature`
**Module(s) affected:** `auth`
**Date:** 2026-06-21
**Status:** FROZEN

---

## 1. Feature Summary

This feature adds the browser/server-rendered HTML registration flow for unauthenticated visitors. It renders a registration page, accepts form submission, creates an active `super_user` account on success, handles duplicate email errors by re-rendering the page, and silently rejects honeypot bot submissions without creating an account.

The UI flow is the browser counterpart to the existing JSON registration API. The API behavior must remain unchanged for JSON clients while `Accept: text/html` receives browser-appropriate redirects or rendered HTML.

---

## 2. Scope Confirmation

- Feature type: UI
- MVP: Yes — user self-registration via registration form is MVP in `docs/SCOPE.md` Module 1.
- Scenarios count: 3
- Modules touched: `auth` only — no cross-module escalation expected.

---

## 3. API Endpoints

N/A for UI feature — see Section 3b and the UI route list below.

UI routes/endpoints involved:

| Method | Path | Auth required | Role required | Description |
|--------|------|---------------|---------------|-------------|
| GET | `/auth/register` | No | None | Render browser registration page |
| POST | `/auth/register` | No | None | Existing endpoint; add `Accept: text/html` form behavior while preserving JSON API behavior |
| GET | `/auth/login` | No | None | Minimal placeholder login page stub returning 200 after registration redirect |

---

## 3b. API Dependencies *(UI features only — omit for API features)*

| Method | Path | Purpose in this UI feature |
|--------|------|---------------------------|
| POST | `/auth/register` | Existing JSON registration endpoint will be extended with content negotiation for browser form submission. |

The existing `POST /auth/register` API is implemented and tested for JSON behavior. This plan must preserve the JSON path and add only the browser `Accept: text/html` branch required by the feature.

---

## 4. Database Changes

### New tables
None.

### Modified tables
None.

### Alembic migration required?
No. The feature uses existing `users` fields: `email`, `username`, `hashed_password`, `role`, `status`, `first_name`, `last_name`, and audit fields.

---

## 5. Module Breakdown

### app/auth/
- **router.py:** Add `GET /register` HTML page route. Modify existing `POST /register` to branch by `Accept` header: if `Accept` contains `text/html`, use the HTML/form branch; otherwise use the JSON branch by default. The router may perform content negotiation, request extraction, and HTTP/HTML response shaping only. It must preserve JSON API behavior for non-HTML requests. Add `GET /login` minimal HTML stub with a clear `# STUB: replaced by login UI feature` code comment.
- **service.py:** Add `register_browser_user(...)` for browser registration service handling that keeps registration decisions out of the router. Contract: return the success-shaped redirect outcome for successful browser registrations; raise the existing `EmailAlreadyExistsError` on duplicate email; when the UI-only honeypot field is populated, check it before duplicate checks/user creation, create no account, log WARNING with the correlation ID, and return the same success-shaped redirect outcome. It must make all duplicate/honeypot/registration decisions and raise domain errors for router response shaping. Reuse existing registration logic for valid submissions.
- **models.py:** No changes.
- **schemas.py:** Add a UI-only form schema, e.g. `UserRegisterFormRequest`, with `email`, `password`, `username`, `first_name`, `last_name`, and optional honeypot field such as `website: str | None = None`. Do not change `UserRegisterRequest`.
- **dependencies.py:** No changes.

**UI features only:**

### app/templates/auth/
- **register.html:** Full registration page template. It renders the form, posts to `/auth/register`, includes required fields, displays the exact duplicate-email error message when present, and includes the hidden honeypot field.
- **login.html:** Minimal placeholder page for `/auth/login`, only enough for the browser to land on a 200 HTML page after redirect. It is not a real login UI.
- **_register_form.html:** Optional partial to keep duplicate-error form rendering reusable. Use only if it simplifies 409 re-rendering; otherwise render the form directly in `register.html`.

### app/static/css/
- **app.css:** Add only the CSP-safe honeypot hiding class, e.g. `.hp-field { display: none; }`. Do not add unrelated CSS, do not use inline styles, and do not edit vendored PicoCSS.

### app/templates/
- **base.html:** Modify only if `/static/css/app.css` is not already loaded after PicoCSS, as required by `docs/FRONTEND.md` loading order. Do not change app-shell/navigation behavior or unrelated shared layout.

---

## 6. Security Considerations

- Does any endpoint require JWT auth? No. `POST /auth/register` and `POST /auth/login` are public exceptions in `docs/SECURITY.md`; this feature uses public registration and a public login-page stub.
- Does any endpoint require a specific role? No.
- Are there rate limiting requirements? Yes. `docs/SECURITY.md` §4 and §7 specify `POST /auth/register` rate limit of 5 per minute per IP. If rate limiting infrastructure is not currently implemented, do not invent it in this UI feature; flag separately.
- Does this feature handle passwords or tokens? Yes, passwords are submitted and must be validated/hashed only through existing auth schema/service patterns. Registration must issue no authentication tokens and no cookies. Never log plain or hashed passwords.
- Does this feature require CSRF protection? No separate CSRF token. `docs/SECURITY.md` §9 uses `SameSite=Lax` cookies and the no-state-changing-GET rule. The registration form must submit with POST.
- What security events must be logged?
  - Successful registration: INFO with correlation ID.
  - Duplicate email rejection: existing WARNING path with correlation ID.
  - Honeypot triggered/bot detected: WARNING with correlation ID; do not log submitted PII beyond allowed fields.

Honeypot requirements from `docs/SECURITY.md` §11 and `docs/FRONTEND.md`:
- Hidden field rendered in the Jinja template.
- Hidden via `app/static/css/app.css` class, not inline `style`.
- `tabindex="-1"`, `aria-hidden="true"`, and `autocomplete="off"`.
- Server checks the field before normal registration processing.
- Populated honeypot returns success-shaped browser response: HTTP 303 `Location: /auth/login`, creates no user, and logs WARNING with correlation ID.

---

## 7. Audit Logging

| Action | Table | action_type | Notes |
|--------|-------|-------------|-------|
| Browser self-registration creates user | users | CREATE | Existing service currently logs successful creation with `action=CREATE` and `table=users`; preserve correlation ID. Do not add admin audit table work in this feature unless already present. |
| Honeypot triggered | None | N/A | Security event log only: WARNING with correlation ID, no database mutation. |

---

## 8. Test Scenarios Breakdown

Testability notes for all UI BDD scenarios:
- All browser/UI requests MUST send `Accept: text/html` so tests exercise the HTML content-negotiation branch. Existing JSON API tests intentionally do not send this header; JSON remains the default branch.
- Database assertions MUST follow `tests/bdd/conftest.py` transaction-boundary discipline: the test `db_session` is separate from the app request session; `@given` writes call `commit()`; `@then` reads call `expire_all()` before asserting committed app writes, mirroring the existing `_get_user_from_db` pattern in `test_20260407_basic_register_user_api.py`.
- Redirect assertions MUST inspect the HTTP 303 response before following `Location: /auth/login`.

### Scenario: Successful registration redirects the visitor to the login page
- **Test type:** BDD step definition
- **Fixtures needed:** unauthenticated `client`, `db_session`, clean users table, `context`
- **What it verifies:** registration page renders HTML form with honeypot field; posting valid form data creates one user with status `active` and role `super_user`; no auth cookies/tokens are issued; response is HTTP 303 with `Location: /auth/login`; following the redirect lands on placeholder login page.
- **Expected HTTP status:** 303 for registration submission; 200 for final login page GET.

### Scenario: Registration is rejected when the email is already registered
- **Test type:** BDD step definition
- **Fixtures needed:** unauthenticated `client`, `db_session`, existing user with same email, `context`
- **What it verifies:** duplicate email form submission creates no new user; response is HTTP 409; returned HTML remains the registration page; exact error message is displayed: `Email address already in use. Please login with your existing account!`.
- **Expected HTTP status:** 409.

### Scenario: Registration is silently rejected when the honeypot field is filled
- **Test type:** BDD step definition
- **Fixtures needed:** unauthenticated `client`, `db_session`, clean users table, `caplog`, `context`
- **What it verifies:** populated hidden honeypot field creates no user; response is indistinguishable from successful browser registration: HTTP 303 with `Location: /auth/login`; bot detection event is logged at WARNING level with the correlation ID.
- **Expected HTTP status:** 303.

---

## 9. Success Criteria

### Automated verification
- [ ] `pytest tests/bdd/step_defs/test_20260621_basic_register_user_ui.py -v` — all scenarios pass
- [ ] `pytest tests/bdd/step_defs/test_20260407_basic_register_user_api.py -v` — existing JSON API registration behavior remains passing
- [ ] `pytest tests/unit/auth/ -v` — auth unit tests pass
- [ ] `ruff check app/auth/router.py app/auth/service.py app/auth/schemas.py tests/bdd/step_defs/test_20260621_basic_register_user_ui.py` passes
- [ ] `ruff format --check app/auth/router.py app/auth/service.py app/auth/schemas.py tests/bdd/step_defs/test_20260621_basic_register_user_ui.py` passes

### Manual verification
- [ ] Visit `/auth/register` in a browser and confirm a server-rendered registration form appears.
- [ ] Submit valid registration and confirm redirect to `/auth/login` placeholder without auth cookies being set.
- [ ] Inspect rendered HTML and confirm the honeypot field is hidden via CSS class, not inline style.

---

## 10. Implementation Order

Each phase is a checkbox. The implementation agent ticks each as it completes.

**API feature track:**

- [ ] **Phase 1: Alembic migration** (if needed) — N/A
  - Test signal: N/A — no DB schema changes.
- [ ] **Phase 2: SQLAlchemy model(s)** — N/A
  - Test signal: N/A — existing `users` table only.
- [ ] **Phase 3: Pydantic schemas** — `app/auth/schemas.py`
  - Test signal: BDD form submissions parse valid fields indirectly through the UI form submission path; no separate unit test is required by this plan. API schema tests continue passing.
- [ ] **Phase 4: Service browser registration decision function(s)** — `app/auth/service.py`
  - Test signal: honeypot scenario creates no account and logs WARNING with correlation ID; duplicate email raises the existing domain error; normal registration still creates active `super_user`.
- [ ] **Phase 5: Templates and CSS** — `app/templates/auth/register.html`, `app/templates/auth/login.html`, optional `app/templates/auth/_register_form.html`, `app/static/css/app.css`, and `app/templates/base.html` only if needed for app.css loading
  - Test signal: BDD background confirms server-rendered HTML form and hidden honeypot field; 409 duplicate email response renders exact error while remaining on registration page.
- [ ] **Phase 6: Router endpoints and content negotiation** — `app/auth/router.py`
  - Test signal: `GET /auth/register` returns HTML form; `GET /auth/login` returns 200 stub; JSON API tests remain green; UI BDD receives 303/409 responses as specified. All UI BDD requests MUST send `Accept: text/html` and must therefore use the HTML branch; all other requests, including existing JSON API tests that intentionally omit this header, use the JSON branch by default.

Note: UI feature depends on the existing API registration behavior remaining implemented and tested first. This plan extends the existing auth endpoint by content negotiation rather than replacing it.

---

## 11. Edge Cases and Error Conditions

| Condition | HTTP status | error_code |
|-----------|-------------|------------|
| Duplicate email in browser form | 409 | `EMAIL_ALREADY_EXISTS` conceptually; browser response renders HTML page with exact error message, not JSON. |
| Honeypot field populated | 303 | None exposed; intentionally indistinguishable from browser success. |
| Invalid password/email/missing fields in browser form | 422 | Out of scope for this UI feature; already covered by API feature. Do not add scenarios or extra UI behavior beyond existing validation path unless needed by framework mechanics. |
| Duplicate username in browser form | 409 | Out of scope for this UI feature; existing service behavior should not be broken. |

---

## 12. Out of Scope

- Full login UI implementation. `/auth/login` is only a minimal placeholder stub for redirect landing and must be marked as such.
- Login form submission, cookie issuance, refresh tokens, logout, and browser session management.
- Password policy, invalid email, missing field, and duplicate username UI scenarios.
- Rate limiting implementation if not already present.
- Changes to authentication/authorization dependencies.
- Database schema changes or Alembic migrations.
- App shell/navigation redesign.

---

## 13. Codebase Analysis Reference

Full analysis: `tests/bdd/plans/auth_20260621_basic_register_user_ui.analysis.md`

### Key findings (from analysis doc synthesis)
- The target module is existing: `app/auth/` contains router, service, models, schemas, JWT, and password utilities.
- The feature is a browser/server-rendered HTML registration flow for `GET /auth/register` and form submission to registration handling.
- Existing API registration already creates `users` records with `role=super_user`, `status=active`, optional `first_name`/`last_name`, and no creator/updater user for self-registration.
- Existing `POST /auth/register` is JSON-oriented: it accepts a Pydantic body and returns `UserRegisterResponse` with HTTP 201.
- Existing browser template infrastructure is present only as `app/templates/base.html`; no `app/templates/auth/` templates were found.
- Existing BDD tests use `pytest-bdd` step definitions with synchronous wrappers around async HTTP/database operations.
- Existing test fixtures provide `client`, `db_session`, automatic users-table cleanup, and database dependency overrides for FastAPI.
- No migration is implied because the feature uses existing `users` fields.

### Patterns to follow
- Existing registration endpoint pattern: `app/auth/router.py` existing `POST /register` delegates to `auth_service.register_user(db, request_body, correlation_id)`.
- Existing login endpoint pattern: `app/auth/router.py` wraps service result in `ApiResponse` for JSON.
- Existing registration service pattern: `app/auth/service.py` checks duplicate email/username, hashes password, creates `User` with `role=UserRole.super_user` and `status=UserStatus.active`, logs with correlation ID.
- Existing exception pattern: `EmailAlreadyExistsError` in `app/auth/service.py` has exact message required by the feature.
- Existing schema pattern: `app/auth/schemas.py` validates registration fields with Pydantic validators.
- Existing BDD patterns: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` for `scenarios()`, `_run()`, datatable parsing, HTTP request steps, and database assertions.
- Existing BDD fixtures: `tests/bdd/conftest.py` for `client`, `db_session`, `clean_tables`, dependency overrides, and `context`.

---

## 14. File Manifest

Explicit file lists that `/write-tests` and `/implement` MUST follow.
These agents should read ONLY the files listed here — no broad codebase exploration.

### Files to READ before writing tests

| File | Why |
|------|-----|
| `tests/features/auth/20260621_basic_register_user_ui.feature` | The executable feature contract. |
| `tests/bdd/plans/auth_20260621_basic_register_user_ui.plan.md` | Scenarios, fixtures, success criteria, file boundaries. |
| `tests/bdd/plans/auth_20260621_basic_register_user_ui.analysis.md` | Existing codebase facts and patterns; avoids broad code exploration. |
| `tests/bdd/conftest.py` | Reuse existing BDD fixtures and async client/session patterns. |
| `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` | Reuse BDD registration setup, datatable parsing, and DB assertion patterns. |
| `docs/SECURITY.md` | Registration content negotiation, honeypot, token/cookie, logging requirements. |
| `docs/FRONTEND.md` | Template/CSP/honeypot UI rules. |
| `docs/GUIDE.md` | Correlation ID, testing, response/error patterns. |

### Files to READ before implementing

| File | Why |
|------|-----|
| `tests/features/auth/20260621_basic_register_user_ui.feature` | The executable feature contract. |
| `tests/bdd/plans/auth_20260621_basic_register_user_ui.plan.md` | Approved implementation order and boundaries. |
| `tests/bdd/plans/auth_20260621_basic_register_user_ui.analysis.md` | Existing auth implementation facts and patterns. |
| `tests/bdd/step_defs/test_20260621_basic_register_user_ui.py` | BDD expectations from `/write-tests`. |
| `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` | Existing API behavior expectations to preserve. |
| `app/auth/router.py` | Add/modify auth routes and content negotiation. |
| `app/auth/service.py` | Add browser registration/honeypot business logic. |
| `app/auth/schemas.py` | Add UI-only form schema without changing `UserRegisterRequest`. |
| `app/templates/base.html` | Confirm/load `app.css` after PicoCSS if needed; do not change shell/navigation. |
| `docs/SECURITY.md` | Honeypot, registration, password/token/cookie, and logging requirements. |
| `docs/FRONTEND.md` | CSP-safe template and CSS rules. |
| `docs/GUIDE.md` | Router/service/correlation ID patterns. |
| `docs/DATA_MODELS.md` | Confirm no schema changes and correct `users` fields/enums. |

### Files to CREATE

| File | Agent | Purpose |
|------|-------|---------|
| `tests/bdd/step_defs/test_20260621_basic_register_user_ui.py` | write-tests | BDD step definitions for the three UI registration scenarios. |
| `app/templates/auth/register.html` | implement | Full server-rendered registration page with form and honeypot field. |
| `app/templates/auth/login.html` | implement | Minimal placeholder login page stub for redirect landing. |
| `app/templates/auth/_register_form.html` | implement | Optional reusable form partial for 409 re-rendering; create only if used. |
| `app/static/css/app.css` | implement | CREATE if absent / MODIFY if present; contains CSP-safe `.hp-field` honeypot hiding rule and only sanctioned app.css rules. |

### Files to MODIFY

| File | Agent | What changes |
|------|-------|--------------|
| `app/auth/router.py` | implement | Add `GET /register`, add `GET /login` stub, extend `POST /register` with HTML content negotiation while preserving JSON behavior. |
| `app/auth/service.py` | implement | Add browser registration/honeypot handling; preserve existing API registration behavior. |
| `app/auth/schemas.py` | implement | Add UI-only form schema with optional honeypot field; do not alter `UserRegisterRequest`. |
| `app/templates/base.html` | implement | Modify only if `/static/css/app.css` is not already loaded after PicoCSS; no shell/navigation or unrelated shared layout changes. |
| `docs/PROJECT_STATUS.md` | implement | Update only if implementation completes the feature and project workflow requires status update. |

### Files NOT touched

Everything not listed above. No broad exploration needed. Specifically, do not modify `app/auth/models.py` or `app/auth/dependencies.py`. Do not modify `.feature` files, `app/core/*`, Alembic migrations, vendored frontend assets, other modules, or unrelated tests.

---

## 15. Changelog

| Date | Phase | Scope | Changes |
|------|-------|-------|---------|
| 2026-06-21 | draft | auth UI registration | Initial plan created with Approach A content negotiation, full honeypot handling, and minimal login-page stub. |
| 2026-06-21 | iterate | adversarial | Clarified router/service responsibilities, Accept negotiation default, shared UI file limits, and linear implementation order. |
| 2026-06-21 | iterate | enrich | Named browser registration service contract and resolved app.css manifest ambiguity. |
| 2026-06-21 | iterate | testability | Clarified HTML Accept header requirements, transaction-boundary DB assertions, redirect assertion order, and indirect form-schema test signal. |
| 2026-06-21 | iterate | freeze-fix | Added explicit no-touch entries for unchanged auth module files referenced in Section 5. |
| 2026-06-21 | freeze | — | Plan frozen for implementation |
