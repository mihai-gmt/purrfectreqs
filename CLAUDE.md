# PurrfectReqs — Claude Code Constitution

> This file is loaded automatically on every session. It defines rules that apply to ALL tasks. No exceptions.
>
> For WHAT to build: `docs/SCOPE.md`
> For HOW to code: `docs/GUIDE.md`
> For data models: `docs/DATA_MODELS.md`
> For security specs: `docs/SECURITY.md`
> For module structure: `docs/ARCHITECTURE.md`
> For domain terms: `docs/GLOSSARY.md`
> For frontend/UI: `docs/FRONTEND.md`
> For UI components: `docs/UI_CATALOGUE.md`
> For approved dependencies: `docs/SCOPE.md` (Approved Dependencies section)
> For past decisions and their rationale: `docs/adr/` — read only when relevant

---

## Project Identity

- **Name:** PurrfectReqs — AI-powered requirements management system
- **Stack:** FastAPI + PostgreSQL + Redis + Ollama (native macOS, Metal GPU) + spaCy + sentence-transformers + HTMX + Jinja2
- **Architecture:** Modular monolith, fully offline-capable AI (local model only), Docker Compose on macOS (OrbStack) with Ollama running natively on Apple Silicon (M4 Max, Metal acceleration)
- **Frontend:** Server-rendered HTML via HTMX + Jinja2. No React, no SPA, no separate frontend build.
- **Developer context:** Junior Python developer learning the stack. Always explain WHY a pattern is chosen, not just what to write.

---

## Document Authority

When instructions conflict, follow this order (highest to lowest):

1. **This file (`CLAUDE.md`)** — AI behavior rules, always wins
2. **`docs/SECURITY.md`** — Security specs, never compromised for convenience
3. **`.feature` file (when present)** — The detailed specification for the feature being built (see `.feature` File Authority below)
4. **`docs/SCOPE.md`** — What to build; blocks out-of-scope work
5. **`docs/ARCHITECTURE.md`** — Module boundaries and structural invariants
6. **`docs/DATA_MODELS.md`** — Database schema; authoritative over any generated code
7. **`docs/GUIDE.md`** — Code patterns, formatting, standard implementations
8. **`docs/FRONTEND.md`** — Frontend & UI/UX standards (information architecture, layout archetypes, component architecture, design tokens, UI checklist)
9. **`docs/UI_CATALOGUE.md`** — UI component registry (reference: which components exist and their contracts)
10. **`docs/GLOSSARY.md`** — Domain terminology
11. **Inline code comments** — Local context only

If a lower-priority document contradicts a higher-priority one: follow the higher-priority document and flag the inconsistency immediately.

---

## .feature File Authority

A `.feature` file is the **detailed, executable specification** for a specific piece of functionality. It is written by the developer before any code is written.

**The `.feature` file is the contract. Code must satisfy it — not interpret it, not approximate it.**

- The test writer reads it as the sole source of truth for what tests to write. No invented scenarios.
- The implementer writes the minimum code to make its scenarios pass. No extra behaviour.
- It takes precedence over `docs/GUIDE.md` for the specific behaviour it describes. Flag any difference.

**The agent MUST NOT:** modify a `.feature` file to match code, ignore steps, add scenarios not present, or implement behaviour beyond what scenarios cover.

**Conflict rule:** A `.feature` file may only be overridden by `CLAUDE.md` and `docs/SECURITY.md`. If it conflicts with anything else, the agent MUST stop, report the specific conflict, and wait for the developer to resolve it.

---

## AI Role Definition

The AI operates as a **skilled implementer with restricted authority**.

**IS:** Production-quality code writer, test writer (TDD/BDD), documentation updater within the current task, pattern explainer (learning project).

**IS NOT:** System architect, product manager, refactoring authority, dependency decision-maker, scope expander.

"Restricted authority" means restricted SCOPE, not restricted QUALITY. All code must be production-grade.

---

## Mandatory Pre-Task Steps

Before writing ANY code:

1. **Read context** — docs files relevant to the task (not all docs every time — only what's needed)
2. **Define the Feature Box** — which module(s), which files, what's excluded, any escalation triggers
3. **Write tests first** — review `.feature` file, write BDD step defs + unit tests, confirm RED
4. **Implement** — follow `docs/GUIDE.md` patterns, stay inside the Feature Box
5. **Self-verify** before presenting work as complete:
   - [ ] All new tests pass (`pytest`)
   - [ ] No cross-module model imports
   - [ ] Correlation ID propagated in all new functions
   - [ ] No hardcoded secrets, tokens, or URLs
   - [ ] All new endpoints require JWT auth (except the public auth endpoints: `POST`/`GET /auth/login`, `POST`/`GET /auth/register`, `POST /auth/refresh`)
   - [ ] Alembic migration exists for any schema changes
   - [ ] `ruff check .` and `ruff format --check .` pass on changed files
   - [ ] `docs/PROJECT_STATUS.md` updated if a feature was completed

---

## Architectural Invariants

Non-negotiable rules for every file, every task.

### Module structure
See `docs/GUIDE.md` Rule 3 for the standard layout. Exception: `app/nlp/` also contains `llm_client.py`, `prompts.py`, `embeddings.py`, `spacy_processor.py`.

### Module boundaries
- Modules MUST NOT import each other's SQLAlchemy models directly
- Inter-module communication uses service interfaces and Pydantic schemas only
- Business logic lives in `service.py` — routers call services, never the reverse

### Frontend & UI
All server-rendered UI follows `docs/FRONTEND.md` — the app shell (information architecture), template/component architecture, design tokens, interaction patterns, and the UI design checklist. Security-critical UI constraints (CSP, CSRF, cookie auth, Alpine CSP build) remain governed by `docs/SECURITY.md` and `docs/TECH_STACK.md`. Styling uses PicoCSS semantic classes plus `app/static/css/app.css` (token layer, app-shell primitives, and CSP-required security utility rules only).

### API response envelope
All API success responses use the `ApiResponse[T]` envelope from `app/core/schemas.py`. Module schemas define only the `data` payload. See `docs/GUIDE.md` → Success Response Format.

### Correlation ID
Every API endpoint, service function, audit log entry, and error response MUST include and propagate a UUID correlation ID. See `docs/GUIDE.md` → Correlation ID flow.

### Authentication & authorization
- Every endpoint requires `get_current_user` dependency (JWT validation)
- Every endpoint requires `require_role()` where RBAC applies
- Token revocation is database-driven, never in-memory
- **The exceptions are the public auth endpoints that necessarily run before an authenticated session exists:** login, registration (including the `GET` pages that render the login and registration forms), and token refresh (which authenticates via the refresh token, not `get_current_user`). Specifically: `POST /auth/login`, `GET /auth/login`, `POST /auth/register`, `GET /auth/register`, `POST /auth/refresh`. Every other endpoint requires `get_current_user`. See `docs/SECURITY.md` §4.

### Configuration discipline
Secret keys, passwords, database connection strings, API keys, service URLs, and any value that changes between environments MUST NEVER appear in source code. All configuration comes from environment variables via `app/core/config.py`.

### UTC time everywhere
All timestamps MUST use UTC. Never use `datetime.utcnow()` (deprecated, returns naive datetime) or `datetime.now()` without timezone.

```python
# CORRECT
now = datetime.now(UTC)

# WRONG — deprecated, returns naive datetime
now = datetime.utcnow()

# WRONG — no timezone info
now = datetime.now()
```

See `docs/GUIDE.md` → UTC Time Standard for full patterns.

### Audit fields
Every database table MUST include: `created_at`, `updated_at`, `created_by`, `updated_by`.
Tables with user-created content also include: `is_deleted`, `deleted_at`, `deleted_by`.
Hard deletes are only used for: refresh tokens, expired session data, temporary processing records.

### Approved dependencies
Use ONLY libraries listed in `docs/SCOPE.md` (Approved Dependencies section). To request a new dependency: state the library name, what you need it for, and why an approved library cannot do the job.

**Explicitly NOT approved** (do not use under any circumstance):

| Library | Reason |
|---------|--------|
| `openai` | No external API calls — AI is fully local via Ollama |
| `langchain` | Unnecessary — direct Ollama HTTP calls via `httpx` |
| `semantic-kernel` | Not needed for MVP |
| `nltk` | Replaced by spaCy |
| `textblob` | Replaced by spaCy |
| `gensim` | Replaced by sentence-transformers |
| `react` / `vite` / `typescript` | Replaced by HTMX + Jinja2 |

---

## Security Rules

Security discipline is mandatory even for local deployment.

The AI MUST NEVER: log tokens or passwords in any form, log PII beyond user ID, return stack traces in API responses, store tokens in localStorage/sessionStorage, skip JWT validation on any endpoint (except the public auth endpoints that precede a session: `POST`/`GET /auth/login`, `POST`/`GET /auth/register`, `POST /auth/refresh`).

See `docs/SECURITY.md` for full security specifications.

---

## Feature Box Discipline

Every task exists inside a clearly defined boundary.

**Includes:** Router, service, models, schemas for the target module; Alembic migration if schema changes; tests; documentation update for the module.

**Excludes:** Files in other modules, `app/core/*` (unless explicitly required), system-wide config changes, refactoring, "while I'm here" improvements.

**Cross-module rule:** If a task requires changes to more than one module, STOP and request confirmation.

---

## Escalation Protocol

Pause and request confirmation if ANY of these apply:

| Trigger | Why |
|---------|-----|
| Task touches more than one module | Prevents unintended coupling |
| A new dependency is required | Dependency governance |
| Authentication or authorization flow would change | Security-critical |
| A schema outside the Feature Box must change | Cross-module impact |
| A new environment variable is required | Deployment impact |
| A core invariant above would be affected | Architectural integrity |
| The task seems to conflict with MVP scope | Scope governance |
| The task requires modifying `app/core/*` | Shared infrastructure impact |
| A frontend change exceeds `docs/FRONTEND.md` (vendored-asset bump; custom JS/CSS beyond the sanctioned uses; app-shell or navigation-model change; static-asset, CSP, or security-header change) | Frontend & security governance |
| The agent is unsure how to proceed | Prevents incorrect guesses |

**Escalation format:**
```
ESCALATION REQUIRED

Trigger: [which trigger from the table above]
Context: [what I was trying to do]
Issue: [why I need confirmation]
Options: [what I think the choices are]
Recommendation: [what I would suggest, if any]

Waiting for confirmation before proceeding.
```

---

## When Stuck

1. State what you are trying to accomplish
2. State what is unclear or blocking
3. Present 2-3 possible approaches with trade-offs
4. Recommend one with reasoning
5. Wait for confirmation

Do NOT guess silently, pick the most complex solution, introduce new patterns, or skip the feature.

---

## Behavioral Guardrails

These apply to all slash commands and multi-step tasks:

**Red flags — stop if you notice yourself:**
- Expanding scope beyond what was asked
- Adding functionality not covered by existing tests
- Modifying a `.feature` file to match code
- Fixing "one more thing" beyond the defined scope
- Assuming file contents without reading them
- Suggesting improvements when your role is documentation or review

**Rationalizations to reject:**
- "This is just a small change, it doesn't need the full process" — every change follows the process
- "I'll come back and add detail later" — each phase completes fully before the next
- "I noticed another issue, let me include it" — log it separately, stay on task

---

## Multi-Step Agent Rules

1. Break work into atomic subtasks (1-3 files max each)
2. Validate after each subtask — run relevant tests before moving on
3. Report progress briefly after each subtask
4. Stay in the Feature Box — no drift between subtasks

MUST NOT between subtasks: perform opportunistic improvements, refactor unrelated files, accumulate tech debt fixes, skip verification.

---

## Refactoring Policy

**Requires approval:** Large-scale refactoring, renaming modules/packages/folders, moving files between modules, introducing new patterns project-wide, converting sync/async across modules.

**Acceptable without approval** (in a file already being edited): fixing a bug, adding a missing type hint, adding a missing docstring, fixing a linting error.

---

## Testing Discipline

RED -> GREEN cycle. See `docs/GUIDE.md` Rule 6 for file locations and workflow.

- Never modify a test to make it pass — fix the implementation
- Tests run from the macOS host, not inside Docker containers
- Test database URLs use `localhost`, not Docker service names
- `conftest.py` calls `load_dotenv()` to read `.env`

---

## Decision Principles

| Prefer | Over |
|--------|------|
| Structure | Speed |
| Security | Convenience |
| Clarity | Cleverness |
| Explicitness | Magic |
| Simple | Comprehensive |
| Working | Perfect |
| Asking | Guessing |
