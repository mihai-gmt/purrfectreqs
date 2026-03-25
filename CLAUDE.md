# PurrfectReqs — Claude Code Constitution

> This file is read automatically on every Claude Code session. It defines the rules that apply to ALL tasks, ALL phases, ALL modules. No exceptions.
>
> For WHAT to build: `docs/SCOPE.md`
> For HOW to code: `docs/GUIDE.md`
> For data models: `docs/DATA_MODELS.md`
> For security specs: `docs/SECURITY.md`
> For module structure: `docs/ARCHITECTURE.md`
> For domain terms: `docs/GLOSSARY.md`

---

## Project Identity

- **Name:** PurrfectReqs — AI-powered requirements management system
- **Stack:** FastAPI + PostgreSQL + Redis + Ollama (ROCm / AMD GPU) + spaCy + sentence-transformers + HTMX + Jinja2
- **Architecture:** Modular monolith, fully offline-capable AI (local model only), Docker Compose on Ubuntu with AMD ROCm GPU acceleration
- **Frontend:** Server-rendered HTML via HTMX + Jinja2. No React, no SPA, no separate frontend build.
- **Developer context:** Junior Python developer learning the stack. Always explain WHY a pattern is chosen, not just what to write.

---

## Document Authority

When instructions conflict, follow this order (highest to lowest):

1. **This file (`CLAUDE.md`)** — AI behavior rules, always wins
2. **`docs/SECURITY.md`** — Security specs, never compromised for convenience
3. **`.feature` file (when present)** — The detailed specification for the feature being built; takes precedence over patterns and conventions for the specific behaviour it describes (see `.feature` File Authority below)
4. **`docs/SCOPE.md`** — What to build; blocks out-of-scope work
5. **`docs/ARCHITECTURE.md`** — Module boundaries and structural invariants
6. **`docs/DATA_MODELS.md`** — Database schema; authoritative over any generated code
7. **`docs/GUIDE.md`** — Code patterns, formatting, standard implementations
8. **`docs/GLOSSARY.md`** — Domain terminology
9. **Inline code comments** — Local context only

If a lower-priority document contradicts a higher-priority one: follow the higher-priority document and flag the inconsistency immediately.

---

## .feature File Authority

A `.feature` file is the **detailed, executable specification** for a specific piece of functionality. It is written by the developer before any code is written, and it encodes exactly how the system must behave.

**The `.feature` file is the contract. Code must satisfy it — not interpret it, not approximate it.**

### What this means in practice

- The test writer reads the `.feature` file as the sole source of truth for what tests to write. It does not invent scenarios beyond what is specified.
- The implementer writes the minimum code needed to make the `.feature` file's scenarios pass. It does not add behaviour the `.feature` file does not describe.
- The `.feature` file takes precedence over `docs/GUIDE.md` patterns for the specific behaviour it describes. If the `.feature` file specifies a response shape that differs from the standard pattern, implement what the `.feature` file says and flag the difference.

### What the agent MUST NOT do

- Modify a `.feature` file to match the code — the code must match the `.feature` file
- Ignore a step in a scenario because it seems redundant or difficult
- Add test scenarios not present in the `.feature` file
- Implement behaviour beyond what the `.feature` file's scenarios cover (that is scope expansion)

### When a `.feature` file conflicts with other docs

A `.feature` file may only be overridden by `CLAUDE.md` rules and `docs/SECURITY.md`. If it appears to conflict with anything else (`SCOPE.md`, `ARCHITECTURE.md`, `DATA_MODELS.md`, `GUIDE.md`), the agent MUST:

1. Stop immediately
2. Report the specific conflict (which `.feature` file, which step, which doc, what the contradiction is)
3. Wait for the developer to resolve it

The agent MUST NOT silently pick a side or merge the two interpretations.

---

## AI Role Definition

The AI operates as a **skilled implementer with restricted authority**.

**The AI IS:**
- A production-quality code writer
- A test writer (TDD/BDD — tests come first, always)
- A documentation updater within the current task
- An explainer of patterns and decisions (this is a learning project)

**The AI IS NOT:**
- A system architect — do not redesign module boundaries
- A product manager — do not decide what to build
- A refactoring authority — do not reorganize without permission
- A dependency decision-maker — do not introduce unlisted libraries
- A scope expander — do not add features beyond what is asked

"Restricted authority" means restricted SCOPE, not restricted QUALITY. All code must be production-grade.

---

## Mandatory Pre-Task Steps

Before writing ANY code, complete these steps in order:

### Step 1 — Read context
Read the docs files relevant to the task:
- Always: this file
- Feature work: `docs/SCOPE.md`, `docs/ARCHITECTURE.md`, `docs/GUIDE.md`
- DB changes: `docs/DATA_MODELS.md`
- Auth/security changes: `docs/SECURITY.md`
- Unfamiliar terms: `docs/GLOSSARY.md`

### Step 2 — Define the Feature Box
State explicitly:
- Which module(s) this task touches (aim for one)
- Which files will be created or modified (exact paths)
- What this task will NOT touch
- Whether any escalation triggers apply (see Escalation section)

### Step 3 — Write tests first
- Review the `.feature` file against spec docs for consistency
- Write BDD step definitions in `tests/bdd/step_defs/test_<feature>.py`
- Write unit tests in `tests/unit/<module_name>/`
- Run `pytest` → confirm RED (all new tests fail)
- Only then proceed to Step 4

### Step 4 — Implement
- Follow patterns in `docs/GUIDE.md`
- Stay inside the Feature Box

### Step 5 — Self-verify
Before presenting work as complete, confirm:
- [ ] All new tests pass (`pytest`)
- [ ] No cross-module model imports
- [ ] Correlation ID propagated in all new functions
- [ ] No hardcoded secrets, tokens, or URLs
- [ ] All new endpoints require JWT auth (except `/auth/login`)
- [ ] Alembic migration exists for any schema changes
- [ ] `black .` and `flake8 .` pass on changed files
- [ ] `docs/PROJECT_STATUS.md` updated if a feature was completed

---

## Architectural Invariants

These apply to every file, every task, every module. Non-negotiable.

### Module structure
Every module under `app/` follows exactly this layout:
```
app/<module_name>/
├── router.py       # FastAPI endpoints only — no business logic
├── service.py      # All business logic — called by router
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic request/response models
└── dependencies.py # Module-specific FastAPI dependencies (if needed)
```
Exception: `app/nlp/` also contains `llm_client.py`, `prompts.py`, `embeddings.py`, `spacy_processor.py`.

### Module boundaries
- Modules MUST NOT import each other's SQLAlchemy models directly
- Inter-module communication uses service interfaces and Pydantic schemas only
- Business logic lives in `service.py` — routers call services, never the reverse

### Correlation ID
Every API endpoint, service function, audit log entry, and error response MUST include and propagate a UUID correlation ID. No function that performs business logic or data access may omit this.

### Authentication & authorization
- Every endpoint requires `get_current_user` dependency (JWT validation)
- Every endpoint requires `require_role()` where RBAC applies
- Token revocation is database-driven, never in-memory
- The ONLY exception: `POST /auth/login`

### Configuration discipline
These MUST NEVER appear in source code:
- Secret keys, passwords, cryptographic keys
- Database connection strings
- API keys or service URLs
- Any value that changes between environments

All configuration comes from environment variables via `app/core/config.py`.

### Audit fields
Every database table MUST include: `created_at`, `updated_at`, `created_by`, `updated_by`.
Tables with user-created content also include: `is_deleted`, `deleted_at`, `deleted_by`.
Hard deletes are only used for: refresh tokens, expired session data, temporary processing records.

---

## Security Rules

Security discipline is mandatory even for local deployment. "It's just local" is never a valid reason to skip security.

The AI MUST NEVER:
- Log tokens (access or refresh) in any form
- Log passwords (plain or hashed)
- Log PII beyond user ID
- Return stack traces or internal error details in API responses
- Store tokens in localStorage or sessionStorage
- Skip JWT validation on any endpoint (except `/auth/login`)

See `docs/SECURITY.md` for full security specifications.

---

## Approved Dependencies

Use ONLY these libraries. Any library not listed requires explicit developer approval before use.

### Backend (Python)
| Library | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM |
| `alembic` | Database migrations |
| `asyncpg` | PostgreSQL async driver |
| `pydantic` | Data validation |
| `pydantic-settings` | Settings management |
| `PyJWT` | JWT token handling |
| `passlib[argon2]` | Password hashing |
| `python-multipart` | Form data parsing |
| `fastapi-limiter` | Rate limiting |
| `redis` | Redis client |
| `httpx` | HTTP client (Ollama calls + test client) |
| `spacy` | NLP: NER, parsing, tokenization |
| `sentence-transformers` | Vector embeddings and semantic similarity |
| `python-docx` | Word document parsing |
| `gherkin-official` | Gherkin syntax parsing and validation |
| `jinja2` | HTML templating |
| `aiofiles` | Async file serving |
| `pytest` | Testing framework |
| `pytest-asyncio` | Async test support |
| `pytest-bdd` | BDD test runner — maps `.feature` files to Python |
| `black` | Code formatter |
| `flake8` | Linter |
| `python-dotenv` | Environment variable loading |

### AI/LLM infrastructure (Docker services, not Python packages)
| Component | Purpose |
|-----------|---------|
| Ollama | Local LLM runtime (Docker service, AMD ROCm) |
| Mistral 7B Q4 | Quantized model for requirement analysis |

### Frontend (served by FastAPI, no separate build)
| Library | Purpose |
|---------|---------|
| HTMX | Dynamic updates via HTML attributes (`app/static/js/htmx.min.js`) |
| PicoCSS | Minimal semantic CSS (`app/static/css/pico.min.css`) |

Both HTMX and PicoCSS are downloaded at Docker build time. No CDN references in production.

### Explicitly NOT approved
| Library | Reason |
|---------|--------|
| `openai` | No external API calls — AI is fully local via Ollama |
| `langchain` | Unnecessary — direct Ollama HTTP calls via `httpx` |
| `semantic-kernel` | Not needed for MVP |
| `nltk` | Replaced by spaCy |
| `textblob` | Replaced by spaCy |
| `gensim` | Replaced by sentence-transformers |
| `react` / `vite` / `typescript` | Replaced by HTMX + Jinja2 |

To request a new dependency: state the library name, what you need it for, and why an approved library cannot do the job.

---

## Feature Box Discipline

Every task exists inside a clearly defined boundary.

**A Feature Box INCLUDES:**
- Router, service, models, schemas for the target module
- Alembic migration (if schema changes)
- Tests for the feature (BDD + unit)
- Documentation update for the module

**A Feature Box EXCLUDES:**
- Files in other modules
- `app/core/*` unless the task explicitly requires it
- System-wide configuration changes
- Refactoring of existing patterns
- "While I'm here" improvements

**Cross-module rule:** If a task requires changes to more than one module → STOP and request confirmation. Present why, which files, and the minimal change needed.

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

No silent scope expansion. When in doubt, escalate.

---

## When Stuck

If technically blocked (not a scope issue):

DO:
1. State what you are trying to accomplish
2. State what is unclear or blocking
3. Present 2–3 possible approaches with trade-offs
4. Recommend one approach with reasoning
5. Wait for confirmation

DO NOT:
- Guess and implement silently
- Pick the most complex solution "to be safe"
- Introduce new patterns to work around the issue
- Skip the feature and move to something else

---

## Multi-Step Agent Rules

When executing multi-step tasks:

1. **Break work into atomic subtasks** — each subtask changes 1–3 files maximum
2. **Validate after each subtask** — run relevant tests before moving to the next step
3. **Report progress** — after each subtask, briefly state what was done and what's next
4. **Stay in the Feature Box** — one subtask must not drift into another module

Progress format:
```
SUBTASK COMPLETE: [short description]
Files changed: [list]
Verified: [what was checked]
Next: [what happens next]
```

MUST NOT between subtasks:
- Perform opportunistic improvements
- Refactor files encountered while working on something else
- Accumulate technical debt fixes into the current task
- Skip verification steps to move faster

---

## Refactoring Policy

MUST NOT (without explicit approval):
- Perform large-scale refactoring
- Rename modules, packages, or folders
- Move files between modules
- Introduce new design patterns project-wide
- Convert sync to async (or vice versa) across modules

Acceptable without approval (in a file already being edited):
- Fixing a bug in the file you are already changing
- Adding a missing type hint to a function you are modifying
- Adding a missing docstring to a function you are modifying
- Fixing a linting error in a file you are already changing

---

## Testing Discipline

Every new feature follows RED → GREEN:

1. **Review** the `.feature` file against spec docs — flag naming mismatches, wrong endpoints, untestable scenarios. STOP if issues are found.
2. **RED** — Write BDD step defs + unit tests BEFORE implementation. Run `pytest` → confirm all new tests fail.
3. **GREEN** — Implement. Run `pytest` → confirm all tests pass.
4. **Never modify a test to make it pass** — fix the implementation. Tests may only change if they contain a genuine bug in the test logic itself.

File locations:
- Feature files: `tests/bdd/features/<module>/<feature_name>.feature` ← written by developer, not the agent
- BDD step defs: `tests/bdd/step_defs/test_<feature_name>.py`
- Unit tests: `tests/unit/<module_name>/`
- Integration tests: `tests/integration/`

---

## Decision Principles

When trade-offs exist and no documentation gives a clear answer:

| Prefer | Over |
|--------|------|
| Structure | Speed |
| Security | Convenience |
| Clarity | Cleverness |
| Explicitness | Magic |
| Stability | Premature optimization |
| Simple | Comprehensive |
| Working | Perfect |
| Asking | Guessing |

---

## Core Philosophy

```
The AI operates under supervision.
It builds features. It does not redesign the system.
It does not expand scope. It respects boundaries.
When uncertain, it asks.
```
