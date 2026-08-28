# PurrfectReqs — Project Status

> **Purpose:** The single honest answer to "what is actually built?" Humans read it to orient; agents read it for context before planning work.
>
> **Authority:** None. This file *describes* reality — it never governs it. If it disagrees with the code, the code is right and this file is stale: fix the file. It is outranked by every document in `CLAUDE.md` → Document Authority.

---

## Snapshot

| | |
|---|---|
| **Phase** | Module 1 (Auth) in progress — registration and login shipped, session lifecycle and admin not started |
| **Last updated** | 2026-08-28 |
| **Last code commit** | 2026-07-08 (`8cd493f`) |
| **Last verified by** | Full `make test` run — all tests passing (2026-08-28) |

**Where the project stands in one paragraph.** The platform layer is complete: the app boots, the Docker stack runs, `app/core/*` is fully built, and CI enforces lint, types, security, and dependency scanning. One module of eight has code — **auth** — and within it, registration (API + UI) and login (with account lockout) are done and green. Everything else in auth, and all seven other modules, are empty packages. The bulk of effort since April 2026 has gone into governance, tooling, ADRs, and UX research rather than product features.

---

## How to update this file

`CLAUDE.md` → Mandatory Pre-Task Steps requires updating this file whenever a feature completes. When you do:

1. Change the **artifact cells** for the feature (Contract / Tests / Code), never a vague summary.
2. Update **Last updated**, and **Last verified by** if you re-ran the suite.
3. If a feature is done but carries an open defect, keep the cells ✅ and name the `BUG-NNN` in Notes. Done and defective are different facts; do not collapse them.
4. Do not record intent here. Planned work belongs in `Backlog.md`.

---

## Legend

Each feature is tracked by the three artifacts its lifecycle produces, so partial progress is visible instead of hidden behind one symbol.

| Column | Meaning |
|---|---|
| **Contract** | A `.feature` file exists and is the agreed spec |
| **Tests** | Step definitions / unit tests exist and execute the contract |
| **Code** | Implementation exists and the tests pass against it |

| Cell | Meaning |
|---|---|
| ✅ | Exists, complete, committed |
| 🔄 | Started, incomplete |
| ⬜ | Does not exist |

**State** is derived from the cells, not asserted independently:

| State | Cells |
|---|---|
| **Done** | ✅ ✅ ✅ |
| **Red** | ✅ ✅ ⬜ — tests written and failing, awaiting implementation |
| **Contract only** | ✅ ⬜ ⬜ — spec agreed, no tests yet |
| **Not started** | ⬜ ⬜ ⬜ |

**Surface** records where the behaviour lives: `API` (JSON), `UI` (server-rendered HTML), or `—` (no external surface).

---

## Platform & Infrastructure

### Runtime & stack

| Item | Status | Notes |
|---|---|---|
| Docker Compose stack | ✅ | Postgres + Redis; Ollama runs natively on the host, not in the stack |
| Dockerfile | ✅ | CPU-only torch pinned ahead of `requirements.txt` (ADR-0024) |
| `scripts/start.sh` | ✅ | |
| Makefile | ✅ | `dev`, `test`, `test-ui`, `lint`, `typecheck`, `security`, `format`, `migrate`, `reset-db`, `ollama-*` |
| `.env.example` | ✅ | |
| `pyproject.toml` | ✅ | ruff config, line length 120 (ADR-0023) |

### Core application scaffolding (`app/core/`)

| Item | Status | Notes |
|---|---|---|
| `config.py` | ✅ | All configuration via env vars; no secrets in source |
| `database.py` | ✅ | |
| `logging.py` | ✅ | |
| `exceptions.py` | ✅ | |
| `dependencies.py` | ✅ | Shared correlation-ID dependency |
| `schemas.py` | ✅ | `ApiResponse[T]` envelope (ADR-0014) |
| `app/main.py` wiring | ✅ | Correlation-ID middleware (ADR-0015), security-header + CSP middleware, `/health`, static mount, auth router |
| Alembic setup | ✅ | 1 migration: `20260407153113_create_users_table` |

### Frontend foundation

| Item | Status | Notes |
|---|---|---|
| `app/templates/base.html` | ✅ | |
| `app/static/css/app.css` | ✅ | Token layer (both schemes, contrast-verified), density tuning, and the `.auth-layout` / `.app-shell` / `.app-shell--focus` primitives, written 2026-08-28. No screen uses them yet — BUG-001 is the first consumer. |
| Vendored assets | ✅ | PicoCSS 2.1.1, HTMX 2.0.9, Alpine CSP build 3.15.11 (ADR-0021, ADR-0038) |
| App shell / navigation | 🔄 | `base.html` only; the full shell of FRONTEND.md §2 is not built |

### Quality gates

| Item | Status | Notes |
|---|---|---|
| Pre-commit hooks | ✅ | |
| GitHub Actions CI | ✅ | ruff, bandit, mypy, pip-audit |
| Local `make lint` parity with CI | ✅ | Closed by BUG-003 / BUG-004 |
| Playwright UI test harness | ✅ | `make test-ui`, `make playwright-install` (ADR-0039) |

---

## Module overview

| # | Module | Package | Features done | State |
|---|---|---|---|---|
| 1 | Auth | Implemented | 4 of 12 | In progress |
| 2 | Projects & Requirements | Stub (`__init__.py` only) | 0 of 9 | Not started |
| 3 | Document Ingestion | Stub (`__init__.py` only) | 0 of 4 | Not started |
| 4 | NLP & AI Analysis | Stub (`__init__.py` only) | 0 of 6 | Not started |
| 5 | Gherkin Validation | Stub (`__init__.py` only) | 0 of 3 | Not started |
| 6 | Traceability | Stub (`__init__.py` only) | 0 of 2 | Not started |
| 7 | Admin & Audit | Stub (`__init__.py` only) | 0 of 3 | Not started |
| 8 | Intake & AI Structuring | Package does not exist | 0 of 8 | Not started |

"Stub" means the package directory contains only `__init__.py` — no models, no service, no router. Nothing has been started behind the scenes.

---

## Module 1: Auth

Files: `models.py`, `schemas.py`, `service.py`, `router.py`, `jwt_handler.py`, `password.py`.
Endpoints live: `GET /auth/register`, `POST /auth/register`, `GET /auth/login`, `POST /auth/login`.

| Feature | Surface | Contract | Tests | Code | State | Notes |
|---|---|---|---|---|---|---|
| Register user | API | ✅ | ✅ | ✅ | Done | `20260407_basic_register_user_api.feature` — 11 scenarios |
| Register user | UI | ✅ | ✅ | ✅ | Done | `20260621_basic_register_user_ui.feature` — 3 scenarios. **BUG-001 open** (full-bleed layout on desktop) |
| User login | API | ✅ | ✅ | ✅ | Done | `20260408_basic_login_user_api.feature` — 5 scenarios. Dual JSON/HTML delivery (ADR-0028) |
| Account lockout | — | ✅ | ✅ | ✅ | Done | No standalone contract — covered by 3 scenarios inside the login feature. `failed_login_attempts` + `locked_until` on `User` |
| Search users | API | ✅ | ⬜ | ⬜ | Contract only | `20260407_basic_search_users_api.feature` — 7 scenarios written, **no step-def file and no service function**. The oldest unpaid contract in the repo |
| User login | UI | ⬜ | ⬜ | 🔄 | Not started | `login.html` and `GET /auth/login` exist; no UI contract or UI tests cover them |
| User logout | — | ⬜ | ⬜ | ⬜ | Not started | |
| Token refresh | API | ⬜ | ⬜ | ⬜ | Not started | ADR-0008 decided the design; nothing built |
| RBAC dependencies | — | ⬜ | ⬜ | ⬜ | Not started | `UserRole` enum exists on the model; no `require_role()` dependency |
| Admin: create user | API | ⬜ | ⬜ | ⬜ | Not started | |
| Admin: list users | API | ⬜ | ⬜ | ⬜ | Not started | |
| Admin: edit user | API | ⬜ | ⬜ | ⬜ | Not started | |
| Admin: password reset | API | ⬜ | ⬜ | ⬜ | Not started | |

---

## Module 2: Projects & Requirements

Package is a stub. No contracts written.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Create project | API | ⬜ | ⬜ | ⬜ | Not started |
| List / search projects | API | ⬜ | ⬜ | ⬜ | Not started |
| Edit / delete project | API | ⬜ | ⬜ | ⬜ | Not started |
| Manage project members | API | ⬜ | ⬜ | ⬜ | Not started |
| Create requirement | API | ⬜ | ⬜ | ⬜ | Not started |
| Edit / delete requirement | API | ⬜ | ⬜ | ⬜ | Not started |
| Group / filter requirements by label | API | ⬜ | ⬜ | ⬜ | Not started |
| Add / edit acceptance criteria (plain text) | API | ⬜ | ⬜ | ⬜ | Not started |
| Add / edit Gherkin scenarios | API | ⬜ | ⬜ | ⬜ | Not started |
| Update scenario coverage status | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 3: Document Ingestion

Package is a stub. No contracts written.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Upload document | API | ⬜ | ⬜ | ⬜ | Not started |
| Parse document | — | ⬜ | ⬜ | ⬜ | Not started |
| Extract candidate requirements | — | ⬜ | ⬜ | ⬜ | Not started |
| List / delete documents | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 4: NLP & AI Analysis

Package is a stub. No contracts written. Ollama runs natively on the host (ADR-0004); nothing in the app talks to it yet.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Ollama client (`llm_client.py`) | — | ⬜ | ⬜ | ⬜ | Not started |
| spaCy processor | — | ⬜ | ⬜ | ⬜ | Not started |
| Embeddings service | — | ⬜ | ⬜ | ⬜ | Not started |
| Requirement quality analysis | API | ⬜ | ⬜ | ⬜ | Not started |
| NER analysis | API | ⬜ | ⬜ | ⬜ | Not started |
| Semantic similarity | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 5: Gherkin Validation

Package is a stub. No contracts written.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Syntax validation | API | ⬜ | ⬜ | ⬜ | Not started |
| Testability analysis | API | ⬜ | ⬜ | ⬜ | Not started |
| Complexity flag + split suggestions | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 6: Traceability

Package is a stub. No contracts written.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Create / edit / delete links | API | ⬜ | ⬜ | ⬜ | Not started |
| View linked requirements | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 7: Admin & Audit

Package is a stub. No contracts written. ADR-0018 decided the append-only audit-log design; no table and no code exist.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Audit log (append on all changes) | — | ⬜ | ⬜ | ⬜ | Not started |
| Admin: view / search audit logs | API | ⬜ | ⬜ | ⬜ | Not started |
| Admin: export audit logs | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 8: Intake & AI Structuring

The package `app/intake/` **does not exist yet** — this module was created on paper on
2026-08-28 (ADR-0045). No contracts, no tables, no code. `docs/DATA_MODELS.md` defines
`raw_inputs` and `candidate_requirements`; neither has a migration.

| Feature | Surface | Contract | Tests | Code | State |
|---|---|---|---|---|---|
| Paste raw text into a project | API + UI | ⬜ | ⬜ | ⬜ | Not started |
| Create a raw input from a parsed document | API | ⬜ | ⬜ | ⬜ | Not started |
| Ask the AI to decompose a raw input | API | ⬜ | ⬜ | ⬜ | Not started |
| List candidates for a raw input | API + UI | ⬜ | ⬜ | ⬜ | Not started |
| Edit a candidate before accepting it | API | ⬜ | ⬜ | ⬜ | Not started |
| Accept a candidate (creates the requirement) | API | ⬜ | ⬜ | ⬜ | Not started |
| Dismiss a candidate (soft delete) | API | ⬜ | ⬜ | ⬜ | Not started |
| List / view / delete raw inputs | API | ⬜ | ⬜ | ⬜ | Not started |

---

## Cross-cutting

### Test inventory

| Kind | Count | Location |
|---|---|---|
| `.feature` contracts | 4 (26 scenarios) | `tests/features/auth/` |
| BDD step-def modules | 3 | `tests/bdd/step_defs/` |
| Unit test modules | 1 (password validation) | `tests/unit/auth/` |
| Doc tests | 1 (ADR validation) | `tests/docs/` |

All coverage is auth-only. One contract (`search_users`) has no step definitions.

### Open defects

Tracked in `bugs.md` — not duplicated here.

| ID | Title | Severity | Status |
|---|---|---|---|
| BUG-001 | Registration screen renders full-bleed on desktop | Medium | **Open** |

BUG-002 through BUG-005 are Verified (mypy reassignment; `make lint` missing typecheck; `make lint` missing bandit; bandit comment-parsing noise).

### Decision record

51 ADRs in `docs/adr/` (ADR-0001 … ADR-0051). ADR-0040 to ADR-0051 were all decided on 2026-08-28: the requirement model (no nesting, labels group, criteria plain, scenarios separate) and the whole UI shell. Many decide designs for modules that do not exist yet — an ADR is a decision, not an implementation, and must not be read as progress.

### Research

UX research synthesis complete: `_TEMP/ux_research/synthesis/20260713/` (8 Deep Research reports → `synthesis.md`, `findings.yaml`, `contradictions.md`, `dropped.md`). Its central finding — that business stakeholders do not read or write Gherkin — was acted on during 2026-08-28: acceptance criteria are plain text with Gherkin in a separate table (ADR-0041), the AI proposes and a person accepts (ADR-0043), and Intake became Module 8 (ADR-0045). Contradiction C3 produced the read-only table lens (ADR-0048). The UI decision trail is `_TEMP/20260828_ui_prototype_conflicts.md`; the reference prototype is `docs/prototypes/20260828_shell_redraw.html`.

---

## Next up

Not a commitment — the candidates a planning session should choose between.

1. **BUG-001** — the only open defect, and it blocks the first real UI screen from matching its own archetype.
2. **Search users** — a 7-scenario contract that has sat unimplemented since April.
3. **Session lifecycle** — logout, token refresh, RBAC dependencies. Auth cannot be called done without them, and every other module depends on `require_role()`.
4. **The intake funnel (Module 8)** — the module the research says decides whether the business persona works. It is fully specified and completely unbuilt.
5. **Telemetry** — Part 2 of `_TEMP/20260424_pr_review_and_telemetry_plan.md`, 7 tasks, none started. The coverage delta gate (Task 1.5) is the last open Part 1 item.
