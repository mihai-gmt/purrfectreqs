# PurrfectReqs — Tech Stack

> **Purpose:** This file lists every approved library and tool, explains why it was chosen, and documents what was explicitly rejected and why. Agents use this to understand what is available and to avoid introducing unapproved dependencies.
>
> **Authority:** This document explains approved dependencies and runtime tooling. It does not override `CLAUDE.md`, `docs/SECURITY.md`, `.feature` files, `docs/SCOPE.md`, `docs/ARCHITECTURE.md`, `docs/DATA_MODELS.md`, or `docs/GUIDE.md`.
>
> **Agent rule:** Do not add, replace, upgrade, downgrade, or remove dependencies unless the current task explicitly requests a dependency change and the developer approves it.

---

## Version and Reproducibility Policy

`TECH_STACK.md` defines approved dependency families and architectural choices. Exact versions are pinned in the project dependency files.

### Dependency files

The project uses two files with distinct roles:

- **`pyproject.toml`** — declares top-level Python dependencies (what the project directly depends on), with pinned versions.
- **`requirements.txt`** — full lock file: exact pinned versions for top-level **and** transitive dependencies. This is the authoritative file used for Docker builds and reproducible environments.

Both files must contain pinned versions. Unpinned or range-based specifiers (e.g. `fastapi`, `fastapi>=0.100`) are not allowed in committed versions of either file.

### Rules

- Top-level dependencies in `pyproject.toml` must be pinned to exact versions (`==`).
- `requirements.txt` must pin every dependency, including transitive ones, to exact versions.
- Do not use unpinned Docker image tags such as `latest` in committed deployment files.
- Do not use unpinned static asset downloads.
- Do not use CDN references in production.
- Do not update dependency versions unless the task explicitly requests it.
- Static frontend assets and ML/NLP models must be pinned by version and checksum where practical, or vendored locally.
- Agents must not modify dependency files, Docker image versions, static asset versions, or ML model versions unless the task explicitly says dependency update.

### Rationale

Pinning both top-level and transitive dependencies defends against supply-chain attacks, where a malicious release of an upstream package could otherwise be pulled in silently during a rebuild. A pinned `requirements.txt` means every environment installs the same bytes until the developer deliberately updates.

### Future hardening (not required for MVP)

- `pip-tools` (`pip-compile pyproject.toml -o requirements.txt`) to regenerate `requirements.txt` deterministically from `pyproject.toml` rather than by hand.
- Hash-pinned installs (`pip install --require-hashes -r requirements.txt`) to verify package contents against known SHA256 digests at install time.

These are not required today. Introducing them is an escalation trigger.

---

## Backend Framework

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `fastapi` | pinned in dependency lock file | Modern async Python web framework with automatic OpenAPI docs, dependency injection, Starlette middleware support, and first-class Pydantic integration |
| `uvicorn[standard]` | pinned in dependency lock file | ASGI server for FastAPI; `[standard]` includes production-oriented performance extras such as `uvloop` and `httptools` |

---

## Database

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `sqlalchemy` | 2.x async, pinned in dependency lock file | Industry-standard Python ORM; v2 async API fits FastAPI's async model |
| `alembic` | pinned in dependency lock file | Database migration tool for SQLAlchemy; generates and applies schema version files |
| `asyncpg` | pinned in dependency lock file | High-performance async PostgreSQL driver; required by SQLAlchemy's async engine |

**Database:** PostgreSQL 16 with extensions:

- `pgvector` — vector storage for embeddings, required for semantic search.
- `uuid-ossp` — UUID generation support where needed.

Rules:

- All schema changes require Alembic migrations.
- SQLAlchemy models must match `docs/DATA_MODELS.md`.
- Do not modify database schema directly.
- Prefer SQLAlchemy expression APIs over raw SQL.
- Any raw SQL must be parameterized.

---

## Data Validation & Configuration

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `pydantic` | v2, pinned in dependency lock file | Input validation, serialization, and type enforcement; v2 has better performance and stricter modelling than v1 |
| `pydantic-settings` | pinned in dependency lock file | Environment variable loading with type coercion and validation; integrates with Pydantic v2 |
| `python-dotenv` | pinned in dependency lock file | Loads local `.env` files during development |

Rules:

- Application configuration is read through `app/core/config.py` using `pydantic-settings`.
- `python-dotenv` is for local development loading only.
- Application code must not call `os.getenv()` directly outside the settings/configuration layer unless explicitly approved.
- Secrets, passwords, service URLs, and environment-specific values must not be hardcoded.

---

## Authentication & Security

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `PyJWT` | pinned in dependency lock file | JWT encode/decode; lightweight, no unnecessary abstractions |
| `passlib[argon2]` | pinned in dependency lock file | Password hashing; Argon2 is preferred over bcrypt for resistance to GPU attacks |
| `python-multipart` | pinned in dependency lock file | Required by FastAPI for `multipart/form-data`, including file uploads and form parsing |

### Browser UI Authentication Model

The browser UI is server-rendered with Jinja2 and enhanced with HTMX. Browser authentication must not depend on JavaScript-readable tokens.

Rules:

- Auth tokens must not be stored in `localStorage` or `sessionStorage`.
- Auth tokens must not be exposed to JavaScript variables.
- Browser authentication uses HTTP-only cookies set by the server.
- HTMX requests rely on browser-sent cookies, not browser-readable bearer tokens.
- CSRF defense for cookie-authed unsafe methods is handled by `SameSite=Lax` plus the no-state-changing-GET rule. See `docs/SECURITY.md` §9.
- API clients (scripts, integrations, future non-browser clients) use the `Authorization: Bearer` header. This is a first-class supported pattern, not an escalation.

### Public Endpoint Rule

Public endpoints are allowed only when explicitly specified by `docs/SECURITY.md` or a feature file.

Public means no existing authenticated user session is required. Public does not mean unprotected.

Expected public endpoints:

- `GET /auth/login`
- `POST /auth/login`
- `GET /auth/register`
- `POST /auth/register`
- static assets
- health check, if configured

Public auth endpoints must still enforce:

- strict input validation
- rate limiting
- correlation ID propagation
- security logging
- generic error messages where user enumeration is possible
- honeypot validation on registration, if configured by `docs/SECURITY.md`

### CSRF Policy

See `docs/SECURITY.md` §9 for the CSRF strategy. TECH_STACK.md does not restate policy to avoid drift between the two documents.

### Security Components Without Extra Libraries

The following security components are implemented using approved dependencies, FastAPI/Starlette, or the Python standard library:

- CORS: `starlette.middleware.cors.CORSMiddleware`, available through FastAPI/Starlette.
- Security headers: FastAPI/Starlette middleware.
- Correlation ID middleware: FastAPI/Starlette middleware.
- Token generation: Python `secrets`.
- Refresh token hashing: `hashlib.sha256`.
- UTC timestamps: `datetime.now(UTC)`.

Do not introduce packages such as `fastapi-csrf-protect`, `itsdangerous`, or additional auth/session frameworks unless the developer explicitly approves them.

---

## Rate Limiting & Caching

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `fastapi-limiter` | pinned in dependency lock file | Rate limiting for FastAPI using Redis as the backend |
| `redis` | pinned in dependency lock file | Redis client; used as the rate limiter backend and available for approved future caching needs |

Rules:

- Apply stricter limits to authentication endpoints and expensive AI/NLP endpoints.
- Do not use Redis as an implicit application state store unless the feature explicitly requires it.
- Adding new caching behavior is an architectural decision and must be approved.

---

## HTTP Client

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `httpx` | pinned in dependency lock file | Async HTTP client; used for Ollama API calls and as FastAPI's async test client (`httpx.AsyncClient`) |

Rules:

- Outbound HTTP calls are allowed only to approved local services unless explicitly approved.
- Runtime LLM calls go through Ollama using `httpx`.
- Do not add LLM orchestration frameworks.
- Do not add calls to external AI APIs.

---

## NLP & AI

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `spacy` | pinned in dependency lock file | Production-grade NLP: tokenization, Named Entity Recognition, dependency parsing; fast, offline, and well-maintained |
| `sentence-transformers` | pinned in dependency lock file | Vector embeddings for semantic similarity; `all-MiniLM-L6-v2` produces 384-dimensional vectors suitable for pgvector |
| `python-docx` | pinned in dependency lock file | Parses Word `.docx` files for document ingestion |
| `gherkin-official` | pinned in dependency lock file | Official Gherkin parser; validates syntax of `.feature` files and acceptance criteria |

### Local LLM Runtime

Ollama runs natively on macOS, not as a Docker service, to use Apple Silicon Metal acceleration.

Runtime model:

- Qwen 3 32B Q4, non-Coder variant.
- Used for requirement analysis, ambiguity detection, completeness review, and quality feedback.

Connection:

- The FastAPI app container calls Ollama via `http://host.docker.internal:11434`.
- Calls are made directly through `httpx`.
- No LangChain, Semantic Kernel, OpenAI SDK, or external AI API is approved.

Development note:

- Coder models may be used as development tools outside the application runtime, but they are not part of the app dependency stack.

### NLP and Embedding Models

- spaCy model: `en_core_web_sm`, pinned by version or vendored in the Docker build context.
- Embedding model: `all-MiniLM-L6-v2`, pinned by model revision where practical.
- If the embedding model changes, existing embeddings must be regenerated because vector dimensions and semantic space may change.

Rules:

- Use `gherkin-official` for Gherkin syntax validation.
- Use spaCy for linguistic extraction.
- Use sentence-transformers for semantic similarity.
- Use the LLM for advisory analysis only.
- LLM output is not authoritative until validated by deterministic checks, schemas, tests, or human approval.
- Do not execute, persist, or trust LLM-generated output without validation.

---

## Frontend

| Library | Delivery | Why |
|---------|----------|-----|
| `jinja2` | Python package | Server-side HTML templating; no build step, no Node.js |
| `aiofiles` | Python package | Async static file serving from `app/static/` |
| HTMX | Static file: `app/static/vendor/htmx/2.0.9/htmx.min.js` | HTML-attribute-driven dynamic interactions; avoids custom JavaScript for most UI patterns |
| PicoCSS | Static file: `app/static/vendor/pico/2.1.1/pico.min.css` | Minimal semantic CSS; works with plain HTML elements and avoids utility-class sprawl |

### Static Asset Policy

HTMX and PicoCSS are **vendored into the repository** under `app/static/vendor/<library>/<version>/` and committed to git. No CDN references, no build-time downloads, no npm — the Docker build simply `COPY`s the repo.

Current pinned versions and SHA256 checksums (verify after any version bump):

| Asset | Version | Path | SHA256 |
|---|---|---|---|
| HTMX | 2.0.9 | `app/static/vendor/htmx/2.0.9/htmx.min.js` | `57d9191515339922bd1356d7b2d80b1ee3b29f1b3a2c65a078bb8b2e8fd9ae5f` |
| PicoCSS | 2.1.1 | `app/static/vendor/pico/2.1.1/pico.min.css` | `fbc9a63fc9fc9f72d12fd7fc9806e11fa9f77ae4f9cad146b27003a1119ba3db` |

Bumping a vendored asset is an escalation trigger: replace the file, update the version folder name, update this table's version and SHA256, and update the `<link>` / `<script>` references in templates.

### PicoCSS Maintenance Note

PicoCSS 2.1.1 is the latest release and the upstream repository has had no commits on `main` or `dev` for over 12 months as of 2026-04. Accepted risk for the MVP: the library is semantically scoped, vendored locally, has no transitive dependencies, and any bug we hit can be patched in place. Revisit this choice if (a) a browser change breaks rendering in practice, (b) we need a feature PicoCSS does not provide, or (c) a security advisory is filed against the vendored version.

Rules:

- No npm.
- No frontend package manager.
- No frontend build pipeline.
- No client-side routing.
- No React, Vue, Svelte, Vite, TypeScript, Tailwind, Bootstrap, DaisyUI, or Alpine.js.
- No inline JavaScript unless explicitly approved.
- No custom JavaScript unless HTMX cannot handle the interaction and the developer approves the exception.
- PicoCSS is the styling baseline.
- Custom CSS must be small, project-specific, and placed in `app/static/css/app.css` only when PicoCSS cannot achieve the required element.

### Browser UI Security Model

Rules:

- Jinja2 autoescaping must remain enabled.
- Do not use `|safe` on user-controlled content.
- Do not render user-provided HTML unless a deliberate sanitization policy exists.
- Do not generate CSS classes, `hx-*` attributes, URLs, or HTML attributes directly from user input.
- HTMX partial endpoints must enforce the same authentication, authorization, validation, and audit rules as full-page routes.
- HTMX `hx-headers` must use static JSON only. Do not use `js:` or `javascript:` in `hx-headers`.
- Templates must not contain business logic. Business decisions belong in `service.py`.
- UI validation is a usability hint only. Server-side validation is authoritative.

---

## Testing

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `pytest` | pinned in dependency lock file | Standard Python test runner |
| `pytest-asyncio` | pinned in dependency lock file | Enables `async def` test functions; required for testing FastAPI async endpoints |
| `pytest-bdd` | pinned in dependency lock file | Connects Gherkin `.feature` files to Python step definitions; chosen over `behave` for native pytest integration and Python 3.12 support |

Rules:

- Tests are written before implementation.
- `.feature` files are the detailed executable specification for feature behavior.
- Agents must not modify `.feature` files to make tests pass.
- Security behavior needs BDD and/or integration tests, especially auth, authorization, rate limiting, and unsafe redirects.

---

## Code Quality

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `ruff` | pinned in dependency lock file | Single Rust-based tool that replaces `black` (formatting), `flake8` (linting), and `isort` (import ordering). Orders of magnitude faster, one config surface, one dev dependency to maintain |

Rules:

- Run `ruff format .` before considering implementation complete.
- Run `ruff check .` before considering implementation complete.
- Ruff is configured in `pyproject.toml` under `[tool.ruff]`, including line length (120), target Python version, selected rule set, and import-order handling.
- Ruff's import sorter (rule set `I`) replaces `isort`. Import order follows: stdlib → third-party → local `app.*`.
- `black`, `flake8`, and `isort` are superseded by ruff and must not be reintroduced.

---

## Monitoring & Logging (Docker Services)

| Service | Image | Why |
|---------|-------|-----|
| Loki | explicit pinned `grafana/loki` image tag | Lightweight log aggregation; designed for Docker log collection |
| Grafana | explicit pinned `grafana/grafana` image tag | Log visualization and search; connects to Loki as data source |

Application logs are structured JSON, shipped to Loki via Docker logging configuration, and viewable in Grafana.

Rules:

- Do not use `latest` image tags in committed deployment files.
- Do not log passwords, raw tokens, refresh tokens, or secrets.
- Do not log PII beyond user ID unless explicitly required and approved.
- All security events must include correlation ID.

---

## File Upload and Document Processing Surface

The approved stack supports document ingestion, but uploaded files are untrusted input.

Rules:

- Enforce maximum upload size from configuration.
- Validate allowed file types.
- Do not trust filename, extension, MIME type, or document metadata by themselves.
- Store uploaded files outside executable code paths.
- Never use user-provided filenames as filesystem paths.
- Limit extracted text size before NLP/LLM processing.
- Treat document text as untrusted content, including possible prompt injection.
- Do not let document content override system prompts, security rules, architecture rules, or feature specifications.

---

## Explicitly Rejected Libraries

These were considered and rejected. Do not propose them again without a strong new reason.

| Library | Rejected for | Use instead |
|---------|-------------|-------------|
| `openai` Python SDK | Requires external API — violates offline-first AI requirement | Ollama via `httpx` |
| `langchain` | Heavyweight abstraction over simple Ollama HTTP calls; adds complexity without MVP value | Direct `httpx` calls to Ollama |
| `semantic-kernel` | Not needed for MVP | Direct `httpx` calls to Ollama |
| `nltk` | Older and less suitable than spaCy for the required NLP tasks | `spacy` |
| `textblob` | Built on NLTK; superseded by spaCy for required NLP tasks | `spacy` |
| `gensim` | Topic modelling library; sentence-transformers covers semantic similarity better for this project | `sentence-transformers` |
| `react` / `vite` / `typescript` | Requires a separate build system, Node.js, and deployment pipeline; HTMX + Jinja2 is sufficient for this UI | HTMX + Jinja2 |
| `tailwindcss` | Adds frontend build/tooling pressure and utility-class sprawl; PicoCSS fits semantic server-rendered UI better | PicoCSS |
| `bootstrap` | More visual/component weight than needed for MVP | PicoCSS |
| `daisyui` | Adds Tailwind-based component abstraction and frontend dependency complexity | PicoCSS + Jinja2 macros |
| `alpine.js` | Not needed for current MVP slices; local browser state can be reconsidered later | HTMX + server-rendered fragments |
| `kawaii-gherkin` | Less mature than `gherkin-official`; dropped during library evaluation | `gherkin-official` |
| `behave` | BDD runner without native pytest integration; would require a separate test run | `pytest-bdd` |
| `cucumber` | JVM/Node ecosystem; incompatible with Python-native test stack | `pytest-bdd` |
| `black` | Superseded by `ruff format` — one tool, one config, same formatting semantics | `ruff` |
| `flake8` | Superseded by `ruff check` — same error classes plus many flake8 plugins built in | `ruff` |
| `isort` | Superseded by `ruff check` rule set `I` — same import-ordering behavior | `ruff` |

---

## Adding a New Dependency

To request a library not on the approved list:

1. State the library name.
2. State what specific problem it solves.
3. Explain why no approved library can solve the same problem.
4. State the expected runtime/development impact.
5. State the license.
6. State maintenance status and project maturity.
7. State known security/advisory concerns.
8. State transitive dependency impact.
9. State whether it affects Docker, deployment, static assets, or environment variables.

This is an escalation trigger. Do not add unapproved libraries without developer confirmation.

---

## Agent Enforcement Rules

Agents must stop and escalate before:

- adding a new dependency
- replacing an approved dependency
- changing dependency versions
- changing Docker image versions
- adding frontend build tooling
- adding npm or a frontend package manager
- changing auth token delivery
- changing CSRF behavior
- changing CORS behavior
- adding outbound HTTP calls to non-local services
- changing LLM model/runtime configuration
- changing static asset delivery
- modifying security headers

Escalation must identify the requested change, why the current approved stack is insufficient, and the recommended option.
