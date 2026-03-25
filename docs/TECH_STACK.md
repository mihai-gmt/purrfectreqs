# PurrfectReqs — Tech Stack

> **Purpose:** This file lists every approved library and tool, explains why it was chosen, and documents what was explicitly rejected and why. Agents use this to understand what is available and to avoid introducing unapproved dependencies.

---

## Backend Framework

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `fastapi` | latest stable | Modern async Python web framework with automatic OpenAPI docs, dependency injection, and first-class Pydantic integration |
| `uvicorn[standard]` | latest stable | ASGI server for FastAPI; `[standard]` includes `uvloop` and `httptools` for performance |

---

## Database

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `sqlalchemy` | 2.x (async) | Industry-standard Python ORM; v2 async API fits FastAPI's async model |
| `alembic` | latest stable | Database migration tool for SQLAlchemy; generates and applies schema version files |
| `asyncpg` | latest stable | High-performance async PostgreSQL driver; required by SQLAlchemy's async engine |

**Database:** PostgreSQL 16 with extensions:
- `pgvector` — vector storage for embeddings (required for semantic search)
- `uuid-ossp` — UUID generation for correlation IDs

---

## Data Validation & Configuration

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `pydantic` | v2 | Input validation, serialization, and type enforcement; v2 has significantly better performance than v1 |
| `pydantic-settings` | latest stable | Environment variable loading with type coercion and validation; integrates with Pydantic v2 |
| `python-dotenv` | latest stable | Loads `.env` file into environment variables at startup |

---

## Authentication & Security

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `PyJWT` | latest stable | JWT encode/decode; lightweight, no unnecessary abstractions |
| `passlib[argon2]` | latest stable | Password hashing; argon2 is the Password Hashing Competition winner — preferred over bcrypt for resistance to GPU attacks |
| `python-multipart` | latest stable | Required by FastAPI for `multipart/form-data` (file uploads and form parsing) |

---

## Rate Limiting & Caching

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `fastapi-limiter` | latest stable | Rate limiting for FastAPI using Redis as the backend |
| `redis` | latest stable | Redis client; used as rate limiter backend and available for future caching needs |

---

## HTTP Client

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `httpx` | latest stable | Async HTTP client; used for Ollama API calls and as FastAPI's async test client (`httpx.AsyncClient`) |

---

## NLP & AI

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `spacy` | latest stable | Production-grade NLP: tokenization, Named Entity Recognition, dependency parsing; fast, offline, well-maintained |
| `sentence-transformers` | latest stable | Vector embeddings for semantic similarity; `all-MiniLM-L6-v2` model produces 384-dimensional vectors suitable for pgvector |
| `python-docx` | latest stable | Parses Word `.docx` files for document ingestion |
| `gherkin-official` | latest stable | Official Gherkin parser; validates syntax of `.feature` files and acceptance criteria |

**Local LLM (Docker service, not a Python package):**
- Ollama running `mistral:7b-instruct-v0.3-q4_K_M`
- Accessed via HTTP from the `app` container at `http://ollama:11434`
- Runs on AMD ROCm GPU (RX 6650 XT / gfx1032)
- Called via `httpx` — no LLM framework wrapper

**spaCy model:** `en_core_web_sm` (small English model). Downloaded at Docker build time.
**Embedding model:** `all-MiniLM-L6-v2`. Downloaded at Docker build time.

---

## Frontend

| Library | Delivery | Why |
|---------|----------|-----|
| `jinja2` | Python package (built into FastAPI) | Server-side HTML templating; no build step, no Node.js |
| `aiofiles` | Python package | Async static file serving from `app/static/` |
| HTMX | Static file (`app/static/js/htmx.min.js`) | HTML-attribute-driven dynamic interactions; avoids JavaScript for most UI patterns |
| PicoCSS | Static file (`app/static/css/pico.min.css`) | Minimal semantic CSS; works with plain HTML elements, no custom class soup |

Both HTMX and PicoCSS are downloaded at Docker build time. No CDN references in production — the application must run in fully offline environments.

---

## Testing

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `pytest` | latest stable | Standard Python test runner |
| `pytest-asyncio` | latest stable | Enables `async def` test functions; required for testing FastAPI async endpoints |
| `pytest-bdd` | latest stable | Connects Gherkin `.feature` files to Python step definitions; chosen over `behave` for native pytest integration and Python 3.12 support |

---

## Code Quality

| Library | Version constraint | Why |
|---------|-------------------|-----|
| `black` | latest stable | Opinionated formatter; eliminates formatting debates; 88 character line length |
| `flake8` | latest stable | Linter for catching errors and style violations beyond what black handles |

---

## Monitoring & Logging (Docker services)

| Service | Image | Why |
|---------|-------|-----|
| Loki | `grafana/loki:latest` | Lightweight log aggregation; designed for Docker log collection |
| Grafana | `grafana/grafana:latest` | Log visualization and search; connects to Loki as data source |

Application logs are structured JSON, shipped to Loki via Docker log driver, viewable in Grafana.

---

## Explicitly Rejected Libraries

These were considered and rejected. Do not propose them again without a strong new reason.

| Library | Rejected for | Use instead |
|---------|-------------|-------------|
| `openai` (Python SDK) | Requires external API — violates offline-first AI requirement | Ollama via `httpx` |
| `langchain` | Heavyweight abstraction over what are simple Ollama HTTP calls; adds complexity without value at MVP scale | Direct `httpx` calls to Ollama |
| `semantic-kernel` | Not needed for MVP | Direct `httpx` calls to Ollama |
| `nltk` | Older, slower, less accurate than spaCy for the same tasks | `spacy` |
| `textblob` | Built on NLTK; superseded by spaCy for all required NLP tasks | `spacy` |
| `gensim` | Topic modeling library; sentence-transformers covers the semantic similarity need better | `sentence-transformers` |
| `react` / `vite` / `typescript` | Requires a separate build system, Node.js, and deployment pipeline; HTMX + Jinja2 is sufficient for this UI | HTMX + Jinja2 |
| `kawaii-gherkin` | Less mature than `gherkin-official`; dropped during library evaluation | `gherkin-official` |
| `behave` | BDD runner without native pytest integration; would require a separate test run | `pytest-bdd` |
| `cucumber` | JVM/Node ecosystem; incompatible with Python-native test stack | `pytest-bdd` |

---

## Adding a New Dependency

To request a library not on the approved list:

1. State the library name
2. State what specific problem it solves
3. Explain why no approved library can solve the same problem
4. Note any security, license, or maintenance concerns

This is an escalation trigger — do not add unapproved libraries without developer confirmation.
