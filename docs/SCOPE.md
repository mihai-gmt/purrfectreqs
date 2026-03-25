# PurrfectReqs — Scope

> **Purpose:** This file defines WHAT we are building, for whom, and at what scale. It is the authoritative reference for MVP boundaries.
>
> **Rule for agents:** If a requested feature is not listed as MVP here, do not build it. Mark it as out of scope and escalate.

---

## What PurrfectReqs Is

PurrfectReqs is an AI-powered requirements management system designed for Product Owners and Product Managers. It helps users write, analyze, validate, and track software requirements using locally-run AI — no external API dependencies, no cloud AI services.

The system enforces BDD/TDD practices by treating Gherkin acceptance criteria as first-class artifacts: requirements are not "done" until their acceptance criteria have associated passing tests.

---

## Target Users

| Scale | Description |
|-------|-------------|
| **Solo / Small** | A single person running the application locally (own machine, rented VM, home server). Primary MVP target. |
| **Medium** | A small business managing requirements for a few applications with a small team. |
| **Large** | Outsourcing companies or large organizations. Post-MVP. |

The MVP focuses on solo and small-team usage. Early architecture decisions prioritize ease of local deployment, simplicity for single users, and straightforward project/team management for small groups.

---

## Deployment Model

- Distributed as Docker images with a `docker-compose.yml`
- Users need only Docker installed — single command to start the full stack
- Uploaded documents stored on host filesystem via Docker volume (not in the database)
- Database stores only file metadata and relative paths
- Backups must include both the database and the uploads volume
- Monitoring: Loki (log aggregation) + Grafana (log visualization) included as Docker services

---

## MVP Modules

### Module 1: User & Access Management ✅ MVP

**What it does:** Handles authentication, authorization, and user administration.

| Feature | MVP |
|---------|-----|
| User login (email + password) | ✅ |
| User logout (token invalidation) | ✅ |
| Role-based access control (admin, super-user, user) | ✅ |
| User self-registration via registration form | ✅ |
| Admin creates/edits/removes users | ✅ |
| View user list with roles and statuses | ✅ |
| JWT token generation, validation, revocation | ✅ |
| Password policy enforcement | ✅ |
| Failed login tracking + account lockout | ✅ |
| Admin-initiated password reset | ✅ |
| User-to-project assignment | ✅ |
| Per-project access rights | ✅ |

**Key constraint:** New users can self-register via a registration form. Admins can also create, edit, and remove accounts directly. Default role on self-registration is `user`; accounts start in `pending` status until approved by an admin.

---

### Module 2: Project & Requirements Repository ✅ MVP

**What it does:** The central data store. All other modules read from and write to this one.

| Feature | MVP |
|---------|-----|
| Create / edit / delete projects | ✅ |
| List / search / filter projects | ✅ |
| Create / edit / delete requirements | ✅ |
| Hierarchical requirement organization (epic → story → subtask) | ✅ |
| Move requirements within hierarchy | ✅ |
| Attach documents to requirements | ✅ |
| Assign requirements to users | ✅ |
| Set and update requirement status | ✅ |
| Add / edit acceptance criteria (Gherkin) | ✅ |
| Track acceptance criteria state (not covered / covered / test passed / test failed) | ✅ |
| Search / filter / sort requirements | ✅ |
| Manually link requirements to other requirements | ✅ |
| View and manage traceability links | ✅ |

---

### Module 3: Document Ingestion & Parsing ✅ MVP

**What it does:** Accepts uploaded files, extracts content, and feeds it to the NLP module.

| Feature | MVP |
|---------|-----|
| Upload text, Word (.docx), and Markdown files | ✅ |
| File type and size validation | ✅ |
| Store file on filesystem (Docker volume); store metadata in DB | ✅ |
| Parse document content | ✅ |
| Extract candidate requirements from documents | ✅ |
| Store extracted requirements as drafts | ✅ |
| Link extracted requirements to their source document | ✅ |
| List / download / delete uploaded documents | ✅ |
| View document metadata and associations | ✅ |

**File types supported (MVP):** `.txt`, `.md`, `.docx`, `.doc`
**Max upload size:** 10 MB (configurable via env var)

---

### Module 4: NLP & AI Analysis ✅ MVP

**What it does:** Analyzes requirement text and documents for quality, clarity, and semantic properties using local AI only.

| Feature | MVP |
|---------|-----|
| Analyze requirement descriptions and acceptance criteria | ✅ |
| Analyze uploaded document content | ✅ |
| Named Entity Recognition (NER) for system components | ✅ |
| Text classification for requirement categorization | ✅ |
| Semantic similarity analysis | ✅ |
| Identify inconsistencies, gaps, and ambiguities | ✅ |
| Generate quality metrics and tags | ✅ |
| Expose analysis results to the user via UI | ✅ |
| Vector embeddings for semantic search (pgvector) | ✅ |

**AI stack:**
- Local LLM: Ollama running Mistral 7B Q4 (AMD ROCm GPU via Docker)
- NLP: spaCy (NER, parsing, tokenization)
- Embeddings: sentence-transformers (`all-MiniLM-L6-v2`, 384 dimensions)
- No external AI API calls — ever

---

### Module 5: Gherkin Validation & Coverage ✅ MVP

**What it does:** Validates acceptance criteria written in Gherkin and tracks their test coverage status.

| Feature | MVP |
|---------|-----|
| Validate Gherkin syntax and structure | ✅ |
| Highlight and explain syntax errors | ✅ |
| Analyze testability of acceptance criteria | ✅ |
| Flag acceptance criteria that are too complex for a single test | ✅ |
| Suggest how to split complex criteria into smaller ones | ✅ |
| Track and update coverage status per acceptance criterion | ✅ |
| Store validation results | ✅ |
| Expose validation results in the UI | ✅ |

---

### Module 6: Traceability & Impact Analysis ✅ MVP (manual)

**What it does:** Maintains links between requirements. Manual only in MVP — no automated detection.

| Feature | MVP |
|---------|-----|
| Manually create / edit / remove traceability links | ✅ |
| Display linked items in requirement detail view | ✅ |
| Show linked requirements as a list | ✅ |
| Highlight impacted requirements when a linked requirement changes | ✅ |
| Log changes to traceability links (audit) | ✅ |

---

### Module 7: Admin & Audit ✅ MVP

**What it does:** System administration and immutable audit trail.

| Feature | MVP |
|---------|-----|
| Append-only audit log for all data changes | ✅ |
| Admin can view, filter, and search audit logs | ✅ |
| Export audit logs | ✅ |
| Manage environment settings | ✅ |
| Admin views all users, roles, and statuses | ✅ |

---

## BDD/TDD Integration

Requirements are tracked through a test lifecycle:

1. User writes a requirement with description and acceptance criteria in Gherkin
2. The system validates the acceptance criteria syntax and testability
3. Acceptance criteria start in state: `not_covered`
4. When a test is written against the criteria: state becomes `covered`
5. When the test passes: state becomes `test_passed`
6. When the test fails: state becomes `test_failed`
7. A requirement is only considered "done" when all its acceptance criteria are in `test_passed` state
8. Traceability between requirements and tests is managed manually by the user

---

## Project File Structure

```
purrfectreqs/
├── app/
│   ├── core/                  # Shared infrastructure
│   │   ├── config.py          # Settings via pydantic-settings
│   │   ├── database.py        # Async SQLAlchemy engine + session
│   │   ├── logging.py         # Centralized logging configuration
│   │   └── exceptions.py      # Shared exception classes
│   ├── auth/                  # Module 1: User & Access Management
│   ├── projects/              # Module 2: Projects & Requirements
│   ├── documents/             # Module 3: Document Ingestion & Parsing
│   ├── nlp/                   # Module 4: NLP & AI Analysis
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── llm_client.py      # Ollama HTTP client
│   │   ├── prompts.py         # LLM prompt templates
│   │   ├── embeddings.py      # sentence-transformers wrapper
│   │   └── spacy_processor.py # spaCy pipeline wrapper
│   ├── gherkin/               # Module 5: Gherkin Validation
│   ├── traceability/          # Module 6: Traceability
│   ├── admin/                 # Module 7: Admin & Audit
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html          # Shared layout (nav, footer, HTMX script)
│   │   ├── auth/
│   │   ├── projects/
│   │   ├── documents/
│   │   ├── nlp/
│   │   ├── gherkin/
│   │   ├── traceability/
│   │   └── admin/
│   └── static/
│       ├── css/
│       │   └── pico.min.css
│       └── js/
│           └── htmx.min.js
├── alembic/
│   └── versions/
├── tests/
│   ├── bdd/
│   │   ├── features/              # Gherkin .feature files (written by developer)
│   │   │   ├── auth/
│   │   │   ├── projects/
│   │   │   └── ...
│   │   └── step_defs/             # pytest-bdd step definitions
│   ├── unit/                      # Unit tests per module
│   └── integration/               # Integration tests
├── scripts/
│   └── start.sh               # Container startup: migrate → serve
├── docs/                      # All project documentation
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── .env.example
├── pyproject.toml
└── CLAUDE.md                  # Claude Code global constitution (root)
```

---

## Module Interaction Summary

```
User & Access Management ──────────────────── auth for all modules
        │
        ▼
Project & Requirements Repo ◄──────────────── central data hub
        │           │
        ▼           ▼
Document          NLP & AI Analysis
Ingestion    ────►  (spaCy + sentence-transformers + Ollama)
                    │
                    ▼
              Gherkin Validation ──► updates AC status in Repo
                    │
                    ▼
              Traceability ──────── links requirements manually
                    │
                    ▼
              Admin & Audit ──────── append-only log of all changes
```

All module communication is synchronous (direct function calls) for MVP. No message queues.

---

## Post-MVP Roadmap

These features are explicitly excluded from MVP. Agents MUST NOT implement them.

### Baseline & Versioning
- Snapshots of requirement sets at a point in time
- Diff between versions
- Rollback to a previous baseline

### Collaboration & Stakeholders
- Comments and discussion threads on requirements
- Notifications (email or in-app)
- Stakeholder approval workflows
- Invitation-based user registration

### Conflict Detection & Impact Analysis (automated)
- Automated detection of conflicting requirements
- Semantic conflict analysis using embeddings
- Regression risk scoring

### Context-Aware Requirement Analysis (RAG)
- Full RAG pipeline: build knowledge base from all existing requirements
- Cross-requirement semantic search
- Proactive gap detection based on existing context

### Agentic AI Capabilities
- Autonomous traceability and status management
- Dynamic workflow optimization
- Automated documentation and reporting

### External Integrations
- Integration with Jira, GitHub, GitLab
- Automated test execution via Cucumber
- Version control linking (Git commit → requirement status)
- External AI APIs (OpenAI, Anthropic) as optional backends

### Scalability
- Horizontal scaling (multiple app instances)
- Message queues for async processing
- Multi-tenant architecture
