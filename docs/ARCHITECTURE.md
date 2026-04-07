# PurrfectReqs — Architecture

> **Purpose:** This file defines structural invariants — rules about how the system is organized and how modules communicate. These are not preferences; they are constraints.
>
> **Authority:** This document is the reference for module boundaries and architectural decisions. `CLAUDE.md` takes precedence in case of conflict.

---

## Architectural Style

**Modular monolith.** All code runs in a single process (one FastAPI application). Modules are separated by package boundaries, not by network — they communicate via direct Python function calls, not HTTP.

This is a deliberate MVP choice: simpler to develop, simpler to deploy, simpler to debug. Do not introduce microservices, service meshes, or inter-module HTTP calls.

---

## Module Boundaries

Each domain has exactly one package under `app/`. The packages are:

| Package | Domain |
|---------|--------|
| `app/auth/` | Authentication, authorization, user management |
| `app/projects/` | Projects and requirements |
| `app/documents/` | Document ingestion and parsing |
| `app/nlp/` | NLP analysis, LLM calls, embeddings |
| `app/gherkin/` | Gherkin validation and coverage |
| `app/traceability/` | Requirement links and traceability |
| `app/admin/` | Audit logs and admin functions |
| `app/core/` | Shared infrastructure (not a domain) |

### The cross-module import rule

Modules MUST NOT import each other's SQLAlchemy models directly. This is the single most important structural rule.

**Wrong:**
```python
# In app/projects/service.py
from app.auth.models import User  # ← VIOLATION
```

**Correct:**
```python
# In app/projects/service.py
from app.auth.schemas import UserResponse  # ← Pydantic schema only
# Or: receive user_id: int as a parameter and look up via service call
```

The only exception is `app/auth/models.py` — other modules may use the `User` model via the `get_current_user` dependency injected by FastAPI, which is a dependency, not an import.

---

## Module Internal Structure

Every module follows this exact layout. No deviation without approval.

```
app/<module_name>/
├── router.py       # FastAPI endpoints — delegates immediately to service
├── service.py      # All business logic — the only place decisions are made
├── models.py       # SQLAlchemy ORM models for this module's tables
├── schemas.py      # Pydantic models for request/response validation
└── dependencies.py # FastAPI dependencies specific to this module (optional)
```

Exception — `app/nlp/` has additional files:
```
app/nlp/
├── router.py
├── service.py
├── models.py
├── schemas.py
├── llm_client.py      # Ollama HTTP client (httpx)
├── prompts.py         # Prompt templates for the LLM
├── embeddings.py      # sentence-transformers wrapper
└── spacy_processor.py # spaCy pipeline wrapper
```

### Layer responsibilities

**`router.py`**
- Defines FastAPI routes (`@router.get`, `@router.post`, etc.)
- Applies FastAPI dependencies (`Depends(get_current_user)`, `Depends(require_role(...))`)
- Extracts path/query/body parameters
- Calls service functions — nothing else
- Returns service results as responses
- Does NOT contain `if/else` business logic
- Does NOT access the database directly

**`service.py`**
- Contains all business logic
- Receives `db: AsyncSession`, `current_user`, `correlation_id` as parameters
- Calls `models.py` for DB access (SQLAlchemy queries)
- Raises domain exceptions (not HTTP exceptions — those belong in the router or exception handlers)
- Calls other modules' services via their public interface (not their models)
- Writes audit log entries for all create/update/delete operations

**`models.py`**
- SQLAlchemy ORM model classes only
- Matches `docs/DATA_MODELS.md` exactly
- No business logic, no validation, no computed properties that run queries

**`schemas.py`**
- Pydantic models for API input/output
- Separate classes for: Create, Update, Response, List (where needed)
- Performs input validation (field constraints, validators)
- Never imports from `models.py` — schemas are independent

**`dependencies.py`**
- FastAPI `Depends()` callables specific to this module
- Examples: pagination parameters, module-specific permission checks

---

## Shared Infrastructure (`app/core/`)

`app/core/` is not a module — it is shared infrastructure. It has no router, no service, no domain models.

```
app/core/
├── config.py       # pydantic-settings Settings class — all env vars
├── database.py     # Async SQLAlchemy engine, session factory, Base class
├── logging.py      # Logging configuration — used everywhere, configured once
└── exceptions.py   # Shared exception base classes and HTTP exception handlers
```

**Rule:** Business logic MUST NOT go in `app/core/`. If you find yourself putting domain logic here, it belongs in a module's `service.py`.

**Rule:** Changes to `app/core/` are always escalation triggers — confirm with the developer before modifying shared infrastructure.

---

## Request Lifecycle

Every request flows through this pipeline in order:

```
HTTP Request
  → Correlation ID middleware
      (extract from X-Correlation-ID header, or generate UUID if absent)
  → OAuth2 token extraction
      (Authorization: Bearer <token> header)
  → get_current_user dependency
      (decode JWT, validate, load User from DB)
  → require_role(*roles) dependency
      (check RBAC — return 403 if insufficient)
  → get_db dependency
      (open async database session)
  → Router function
      (extract parameters, call service)
  → Service function
      (business logic, DB access, audit log)
  → Response
      (Pydantic schema serialization)
```

---

## Frontend Architecture

The frontend is server-rendered. There is no separate frontend application, no build step, no npm.

- **Templating:** Jinja2 — templates in `app/templates/<module>/`
- **Interactivity:** HTMX — dynamic updates via HTML attributes, no custom JavaScript unless HTMX cannot handle the interaction
- **CSS:** PicoCSS — semantic CSS classes, no custom CSS unless PicoCSS cannot achieve the required element
- **Base template:** All templates extend `app/templates/base.html`
- **Partials:** HTML fragments for HTMX targets use underscore prefix (`_form.html`, `_list.html`)
- **Static files:** Served from `app/static/` — no CDN references in production

**Rule:** Templates contain no business logic. Logic belongs in `service.py`.
**Rule:** Auth tokens live in HTTP-only cookies. Never in localStorage or JavaScript variables.

---

## Database Architecture

- PostgreSQL 16 with `pgvector` extension (for embeddings) and `uuid-ossp` (for UUID generation)
- All ORM access via SQLAlchemy async sessions
- All schema changes via Alembic migrations — never modify the schema directly
- Migrations run automatically on container startup (`scripts/start.sh`)

### Migration order (dependency-safe creation sequence)

When creating the schema from scratch, tables must be created in this order:

1. `users`
2. `refresh_tokens`
3. `projects`
4. `project_members`
5. `requirements`
6. `acceptance_criteria`
7. `documents`
8. `requirement_documents`
9. `analysis_results`
10. `embeddings`
11. `validation_results`
12. `traceability_links`
13. `audit_logs`

See `docs/DATA_MODELS.md` for complete schema definitions.

---

## Docker Services

The full stack runs as Docker Compose services (OrbStack on macOS):

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `app` | custom Dockerfile | 8000 | FastAPI application |
| `db` | `pgvector/pgvector:pg16` | 5432 | PostgreSQL database with pgvector |
| `redis` | `redis:7-alpine` | 6379 | Rate limiting backend |
| `loki` | `grafana/loki` | 3100 | Log aggregation |
| `grafana` | `grafana/grafana` | 3000 | Log visualization |

**Ollama runs natively on macOS** (not in Docker) to use Metal GPU acceleration on Apple Silicon. The `app` container reaches Ollama at `http://host.docker.internal:11434` via the `extra_hosts` directive in `docker-compose.yml`.

**Production/beta deployment** adds a reverse proxy (Caddy or Nginx) 
in front of the stack. See `docker-compose.prod.yml` (created when 
preparing for public deployment). Internal service ports (5432, 6379, 
3100, 3000) are NOT exposed on host in production.

**Rule:** Do not add new Docker services without escalating to the developer. Adding infrastructure is an architectural decision.

---

## Startup Sequence

`scripts/start.sh` runs on container start:
1. `alembic upgrade head` — apply all pending migrations
2. `uvicorn app.main:app` — start the FastAPI application

Dev seed data (3 test users) is an Alembic data migration guarded by `APP_ENV=development`. It runs only in development environments.

---

## Architecture Decision Log

Brief record of key decisions and why they were made. Agents should not reverse these without explicit instruction.

| Decision | Choice | Reason |
|----------|--------|--------|
| Frontend framework | HTMX + Jinja2 (no SPA) | Simpler deployment, no build step, sufficient for requirements management UI |
| AI backend | Local Ollama only (Qwen 3 32B Q4) | Privacy, offline capability, no API costs, self-hosted |
| Ollama deployment | Native macOS (not Docker) | Metal GPU passthrough not supported in Docker VMs on Apple Silicon; native gives full Metal acceleration |
| LLM model separation | Qwen 3 32B (non-Coder) for app runtime; Qwen Coder for development tooling | Requirement analysis needs general reasoning, not code generation bias |
| NLP libraries | spaCy + sentence-transformers | Production-grade, offline, sufficient for MVP NLP needs |
| Auth tokens | JWT (access) + opaque refresh token | Industry standard; opaque refresh token avoids JWT revocation complexity |
| Module communication | Direct Python calls | Monolith MVP — no network overhead, simpler debugging |
| Vector store | pgvector in PostgreSQL | Avoids a separate vector database service for MVP scale |
| CSS framework | PicoCSS | Minimal, semantic, no custom build tooling |
| TLS termination | Reverse proxy (not app) | App stays simple; 
  proxy handles certs, redirects, and header injection |
