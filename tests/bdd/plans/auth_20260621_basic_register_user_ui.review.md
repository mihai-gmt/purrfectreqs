# Review: 20260621 Basic Register User UI

Governance state: `REVIEWING` verified in `.pi/feature-box.json`; GREEN was already recorded there and re-verified during review.

Tests run first:

- `make test-file f=tests/bdd/step_defs/test_20260621_basic_register_user_ui.py` — PASSED (3 passed; pytest-bdd mark warnings for `ui` and `honeypot`)
- `make test-file f=tests/bdd/step_defs/test_20260407_basic_register_user_api.py` — PASSED (11 passed)
- `make lint-file f="app/auth/router.py app/auth/service.py app/auth/schemas.py tests/bdd/step_defs/test_20260621_basic_register_user_ui.py"` — PASSED

COMPLIANCE REVIEW: 20260621_basic_register_user_ui

PASSED: 31
FAILED (introduced by this feature): 1
N/A: 9
PRE-EXISTING (logged, not blocking): 1

## Compliance checklist

### A: Test integrity

- PASS — All `.feature` scenarios have corresponding step definitions.
- PASS — No test was modified to make it pass; the feature-specific BDD test file is newly created.
- PASS — Tests cover the applicable feature contract: happy path, duplicate-email failure, and honeypot rejection. Auth/role failures are not applicable because registration/login page routes are public exceptions.
- PASS — No trivially passing tests; the steps assert rendered HTML, persistence, redirects, cookies, and logs.

### B: Module structure

- PASS — Auth code is in `app/auth/`; templates are under `app/templates/auth/`; CSS is under `app/static/css/app.css` per the plan.
- PASS — Router logic is limited to HTTP/content negotiation, parsing, template response shaping, and service delegation.
- PASS — No introduced cross-module SQLAlchemy model imports in production code.
- PASS — Pydantic response schema already has `from_attributes=True`; the new form schema is request-only.
- PASS — No catch-all `utils.py` was introduced.

### C: Function quality

- FAIL — Type hints on all parameters and return values: `tests/bdd/step_defs/test_20260621_basic_register_user_ui.py:37`, `85`, `109`, `115`, `123`, `142`, `160`, `177`, `203`, `212`, `219`, `226`, `245`, `254`, `268`, `278`, `293`, `303`, `311`, `322`, `330`, `340`, `351`. Issue: new helper/step functions omit return annotations, and `_run` also omits a parameter type. Fix: add explicit return annotations (`-> None` for step/assertion helpers, precise return types for helpers such as `_run` and `_get_user_by_email`) without changing test behavior.
- PASS — New functions have docstrings.
- PASS — New service function `register_browser_user(..., correlation_id: str)` accepts and propagates correlation ID.
- PASS — No `print()` usage; logging is used.

### D: Security

- PASS — Public auth routes introduced/used by this feature (`GET /auth/register`, `POST /auth/register`, `GET /auth/login`) are allowed unauthenticated by `CLAUDE.md` and `docs/SECURITY.md`.
- N/A — `require_role(...)` is not applicable to public registration/login page routes.
- PASS — No secrets, tokens, or passwords are logged. Honeypot logging includes correlation ID only.
- PASS — No stack traces are returned in the reviewed implementation.
- PRE-EXISTING (note) — `app/auth/router.py:93` / existing `POST /auth/register` JSON response still uses `response_model=UserRegisterResponse` rather than `ApiResponse[UserRegisterResponse]`. Defect: this does not meet the project-wide API envelope invariant. Originates: the pre-existing JSON registration endpoint shape; this feature preserved it intentionally to avoid breaking the existing API contract/tests. Suggested: log to `Backlog.md` as a separate auth API response-envelope defect.
- PASS — No hardcoded secrets, DB URLs, or environment-specific config values were introduced. The literal `/auth/login` is feature-specified route behavior, not a secret/config value.
- PASS — Registration issues no auth tokens/cookies; browser token storage is not introduced.
- PASS — Password handling reuses existing registration service and `hash_password` path.

### E: Database

- N/A — No schema change; no Alembic migration required.
- N/A — No migration file required, so `upgrade()`/`downgrade()` are not applicable.
- N/A — No new models/tables.
- N/A — No new user-content models/tables.
- PASS — No raw SQL introduced; production code uses SQLAlchemy ORM/selects via existing service logic.

### F: Observability

- PASS — New honeypot warning log includes `correlation_id`.
- PASS — Browser registration creation reuses existing registration service logging with `action=CREATE` and `table=users`, as allowed by the plan while audit-log infrastructure is deferred.
- PASS — Log levels are appropriate: honeypot is WARNING; successful registration remains INFO.

### G: Code quality

- PASS — `make lint-file` passed on changed Python files.
- PASS — Import order follows ruff.
- PASS — No unused imports reported by ruff.

### H: UI/template quality

- PASS — HTML-only GET routes declare `response_class=HTMLResponse`; the dual-purpose POST route correctly retains the JSON `response_model` and returns HTML `Response` objects only in the HTML branch.
- N/A — No HTMX partial/full-page branching is required by this feature.
- PASS — Full pages `register.html` and `login.html` extend `base.html`.
- N/A — No partial template was created.
- N/A — No partial is used, and the plan made `_register_form.html` optional.
- PASS — Templates contain presentation and form markup only; business decisions stay in service/router layers.
- PASS — No custom JavaScript was introduced; the normal registration form POST is sufficient for this feature.
- N/A — Auth-failure redirect handling is not applicable to public registration routes.
- PASS — Templates use semantic HTML/Pico-compatible elements.
- PASS — `TemplateResponse` calls use the current Starlette signature with `request` as the first positional argument.

## ISSUES REQUIRING ATTENTION (introduced — must fix before commit)

1. C — Type hints on all parameters and return values: `tests/bdd/step_defs/test_20260621_basic_register_user_ui.py:37`, `85`, `109`, `115`, `123`, `142`, `160`, `177`, `203`, `212`, `219`, `226`, `245`, `254`, `268`, `278`, `293`, `303`, `311`, `322`, `330`, `340`, `351`. Issue: new helper/BDD step functions omit explicit return annotations, and `_run` omits a typed parameter. Fix: add explicit return annotations and a parameter type for `_run`; keep behavior unchanged.

## PRE-EXISTING DEFECTS (out of scope — recommend logging to Backlog.md)

1. D — `ApiResponse[T]` envelope with correlation ID on API success responses: `app/auth/router.py:93` / `register_user`. Defect: existing JSON registration success response is not wrapped in `ApiResponse[T]`. Originates: pre-existing auth API endpoint contract before this UI feature; the feature preserved JSON behavior by plan. Suggested: backlog.

Fix the INTRODUCED issues above, then clear context and re-run:

```text
/review tests/features/auth/20260621_basic_register_user_ui.feature
```

Do not re-run /implement. Fix the specific issues manually or ask for targeted help. Source fixes require `/phase set IMPLEMENTING`; test fixes require `/phase set WRITE_TESTS`; then return to `/phase set REVIEWING` to re-run. Pre-existing defects are NOT fixed here — log them to `Backlog.md`.

## Learning notes

### Content negotiation keeps one URL usable by browsers and APIs

**What:** `POST /auth/register` branches on `Accept: text/html` while leaving the JSON path as the default.
**Why:** This lets the browser form and API client share the same resource without forcing API clients to understand redirects or HTML.
**What if done differently:** A separate `/auth/register-ui` endpoint would be simpler internally, but it would duplicate registration behavior and increase the chance that browser/API rules drift apart.

### Honeypots must be checked before normal registration work

**What:** The browser service checks the `website` honeypot before duplicate lookups or user creation.
**Why:** Silent rejection works best when bots get the same visible response as success and no unnecessary database mutation occurs.
**What if done differently:** Checking duplicates first could leak behavior differences to bots and would do extra work for submissions you already know should be discarded.

### Reusing the API registration service avoids password-policy drift

**What:** Valid browser submissions are converted into `UserRegisterRequest` and passed through the existing `register_user` service.
**Why:** One registration path means hashing, duplicate checks, role/status defaults, and logging stay consistent.
**What if done differently:** Re-implementing browser registration separately might pass the UI tests but accidentally skip a security rule already enforced by the API path.

### HTML templates should hide honeypots with CSS classes, not inline styles

**What:** The honeypot is hidden through `.hp-field` in `app/static/css/app.css`.
**Why:** The CSP forbids inline styling, so class-based hiding keeps the UI compatible with security headers.
**What if done differently:** `style="display:none"` is quick, but it violates the CSP design and may stop working once strict headers are active.
