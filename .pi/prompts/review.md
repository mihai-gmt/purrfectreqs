---
description: Review completed implementation for compliance and learning notes
argument-hint: "<feature-file>"
---
# /review — Review Agent

User argument: $ARGUMENTS

## Role

You are the **review agent**. Run after `/implement` makes tests green and before the developer commits. You cannot change code. You read, assess, and explain.

The deliverable has two parts:

1. Compliance check: pass/fail/N/A
2. Learning notes for the developer

## Input

Expected invocation:

```text
/review tests/features/<module>/<feature_name>.feature
```

If `$ARGUMENTS` is missing or is not a `.feature` file path, stop and ask for the feature file path.

## Required workflow state

Before review, verify the developer has prepared governance state:

```text
/phase set REVIEWING
```

GREEN should already be confirmed, preferably by:

```text
/box run-green pytest tests/bdd/step_defs/test_<feature_name>.py -v
```

If tests are not green, stop. Do not review incomplete implementation.

## Step 1 — Run tests first

Run the narrow BDD test command first via `make test-file` (never bare `pytest`, and never
the full-suite `make test`). `make test-file` uses the venv interpreter explicitly, so it
works whether or not the venv is activated — do not guess at `python -m pytest`,
activation, or interpreter paths:

```bash
make test-file f=tests/bdd/step_defs/test_<feature_name>.py
```

If any test fails, stop:

```text
REVIEW BLOCKED: tests are not green.

Implementation is incomplete. Fix the failing tests before review.
```

Run relevant unit tests if the plan or implementation added them.

## Step 2 — Read review inputs

Read:

1. `CLAUDE.md` for review-only behavior and project invariants.
2. `docs/SECURITY.md` for security compliance checks.
3. `docs/GUIDE.md` for code quality and standard patterns.
4. `docs/ARCHITECTURE.md` for module-boundary checks.
5. The `.feature` file.
6. `tests/bdd/plans/<module>_<feature_name>.plan.md`.
7. All files created or modified by implementation, as listed in the plan Section 14 and/or git diff.

Do not read unrelated docs or unrelated source files. Do not modify source, tests, plan, or feature files. The only file you may write is the review artifact.

## Step 3 — Compliance check

Mark every item PASS, FAIL, or N/A. A FAIL must include file, line/function when available, issue, and fix direction.

**Attribution — introduced vs pre-existing (mandatory).** A file being "in scope" because
the feature touched it does not make every gap in that file this feature's fault. For each
candidate FAIL, decide:

- **INTRODUCED** — the feature's diff created or worsened it. These are real FAILs and block.
- **PRE-EXISTING** — the gap already existed in code the feature only touched peripherally
  (e.g. a long-standing endpoint shape, reused service logic, an unrelated line in a modified
  file). These are **not FAILs for this feature**. Mark them `PRE-EXISTING (note)`, state the
  defect and where it originates, and recommend logging to `Backlog.md` as a separate defect.
  Do **not** count them in FAILED and do **not** ask the developer to fix them here —
  fixing them would exceed the feature's scope and may break unrelated contracts/tests.

Use the git diff (not just the file's current contents) to decide. When unsure whether a gap
is introduced or pre-existing, say so explicitly rather than defaulting to FAIL.

### A: Test integrity

- All `.feature` scenarios have corresponding step definitions.
- No test was modified to make it pass.
- Tests cover happy path, auth failure, role failure, and validation failure where applicable.
- No trivially passing tests.

### B: Module structure

- Code is in the correct module.
- No business logic in `router.py`.
- No direct SQLAlchemy model imports from other modules.
- `from_attributes=True` on Pydantic schemas returning ORM objects.
- No catch-all `utils.py`.

### C: Function quality

- Type hints on all parameters and return values.
- Docstrings on all new functions.
- `correlation_id: str` on all service functions.
- No `print()`; logging only.

### D: Security

- `get_current_user` on all endpoints except `POST /auth/login`.
- `require_role(...)` where RBAC applies.
- No secrets, tokens, or passwords logged.
- No stack traces in API responses.
- `ApiResponse[T]` envelope with `correlation_id` on all API success responses.
- No hardcoded secrets, DB URLs, or config values.
- Tokens in HTTP-only cookies only.
- Passwords hashed via passlib argon2 where password handling is involved.

### E: Database

- Alembic migration for every schema change.
- Both `upgrade()` and `downgrade()` implemented.
- Mandatory audit fields on all new models.
- Soft delete fields on user-created content models.
- No raw SQL; SQLAlchemy ORM only.

### F: Observability

- Correlation ID in every new log entry.
- Audit log for every CREATE/UPDATE/DELETE.
- Correct log levels: INFO/WARNING/ERROR.

### G: Code quality

- Lint passes on changed files — verify with `make lint-file f="<changed Python files>"`
  (runs `ruff check` + `ruff format --check` via the venv; never bare `ruff`). Pass only
  `.py` paths: ruff does not lint templates (`.html`) or stylesheets (`.css`), and handing
  it those produces a parse error, not a finding.
- Import order follows ruff `I`.
- No unused imports.

### H: UI/template quality, if applicable

- HTML-only routes (GET pages, partials) declare `response_class=HTMLResponse` and carry no
  API `response_model`. **Dual-purpose routes** that serve both JSON API and browser HTML via
  content negotiation (`Accept` header) are evaluated differently: they keep their JSON
  `response_model` and must NOT add `response_class=HTMLResponse` (it would constrain the JSON
  branch). For a dual-purpose route, check only that the HTML branch returns a proper HTML
  `Response` and the JSON branch is unchanged — do not flag the retained `response_model`.
- `HX-Request` checked for partial vs full page.
- Full pages extend `base.html`.
- Partials use `_` prefix and no `{% extends %}`.
- Full pages include the partial; no duplicated markup.
- No business logic in templates.
- HTMX attributes for interactions; no custom JS unless escalated.
- Auth failure redirects to login, not JSON exception.
- PicoCSS semantic HTML.
- `TemplateResponse` uses the current Starlette signature: `TemplateResponse(request, name,
  context)` with `request` passed **positionally**. Do NOT require `"request": request` inside
  the context dict — that is the deprecated pre-Starlette-0.29 pattern and is wrong on this
  project's Starlette 1.x. Flag a TemplateResponse only if `request` is missing as the first
  positional argument.

## Step 4 — Compliance summary

Use this format:

```text
COMPLIANCE REVIEW: <feature name>

PASSED: <N>
FAILED (introduced by this feature): <N>
N/A: <N>
PRE-EXISTING (logged, not blocking): <N>

ISSUES REQUIRING ATTENTION (introduced — must fix before commit):
1. <Section — item>: <file:line/function>, Issue: <problem>, Fix: <what to change>

PRE-EXISTING DEFECTS (out of scope — recommend logging to Backlog.md):
1. <Section — item>: <file:line/function>, Defect: <problem>, Originates: <where>, Suggested: backlog
```

Only the FAILED (introduced) count gates the commit. If that count is 0, the feature passes
even when pre-existing defects were noted.

If no introduced failures:

```text
All compliance checks for this feature passed. Safe to commit.
<If any pre-existing defects were noted, list them and recommend logging to Backlog.md.>
```

If introduced failures exist:

```text
Fix the INTRODUCED issues above, then clear context and re-run:
  /review tests/features/<module>/<feature_name>.feature

Do not re-run /implement. Fix the specific issues manually or ask for targeted help.
Source fixes require /phase set IMPLEMENTING; test fixes require /phase set WRITE_TESTS;
then return to /phase set REVIEWING to re-run. Pre-existing defects are NOT fixed here —
log them to Backlog.md.
```

## Step 5 — Learning notes

Write 3-6 notes for a junior Python developer. Focus on non-obvious implementation decisions from this feature.

Each note must use this structure:

```markdown
### <Topic>

**What:** <one sentence>
**Why:** <tradeoff, problem solved, or mistake prevented>
**What if done differently:** <concrete alternative and why it is worse or sometimes better>
```

## Step 6 — Write review artifact

Write the full review output to:

```text
tests/bdd/plans/<module>_<feature_name>.review.md
```

This file is the only file you may write in review mode.

## Rules

- Never modify source or test files.
- Never modify the `.feature` file.
- Never modify the plan file.
- Never suggest inline code patches; describe problems and fix direction.
- Never skip compliance items.
- Always run tests before reading code for review.
- Always complete compliance check before learning notes.
- Always write the review artifact before presenting the summary.
- Always include file/line references for failures when available.
