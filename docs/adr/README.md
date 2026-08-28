# Architecture Decision Records

One file per decision, Markdown with YAML frontmatter. The frontmatter carries
machine-readable metadata and graph relations (supersedes, depends_on,
affects_modules, …); the body carries the human reasoning. The format contract
is `TEMPLATE.md` and is enforced by `tests/docs/test_adr_validation.py`.

Read an ADR when a task touches the decision it records — this folder is not
part of the always-loaded context.

Statuses: `proposed` → `accepted`; end states `deprecated` (no replacement) or
`superseded` (points to its replacement via `superseded_by`).

**An ADR body is immutable.** It records what was decided and why, on a date.
Once an ADR is `accepted`, its body is never rewritten to match later decisions,
even when a statement in it has been overtaken. Correct the record by writing a
new ADR and, where the decision itself is replaced, by setting `superseded_by`.
The current truth lives in the governed documents under `docs/`, not in the ADR
history. Frontmatter status and relation fields may change, because they are the
graph, not the reasoning.

Typos, broken links, and formatting may be fixed at any time. Changing what an
ADR says may not.

## Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| ADR-0001 | Modular monolith over microservices | accepted | 2026-03-25 |
| ADR-0002 | Server-rendered frontend with HTMX + Jinja2, no SPA | accepted | 2026-03-25 |
| ADR-0003 | Fully local AI via Ollama; no external AI APIs | accepted | 2026-03-25 |
| ADR-0004 | Ollama runs natively on macOS, not in Docker | accepted | 2026-03-25 |
| ADR-0005 | Qwen 3 32B (non-Coder) for app runtime; Coder models for dev tooling only | accepted | 2026-03-25 |
| ADR-0006 | spaCy + sentence-transformers for deterministic NLP | accepted | 2026-03-25 |
| ADR-0007 | pgvector in PostgreSQL over a dedicated vector database | accepted | 2026-03-25 |
| ADR-0008 | JWT access token plus opaque DB-backed refresh token | accepted | 2026-03-25 |
| ADR-0009 | Argon2 via passlib for password hashing | accepted | 2026-03-25 |
| ADR-0010 | TLS terminates at a reverse proxy, not in the application | accepted | 2026-03-25 |
| ADR-0011 | Redis-backed rate limiting via fastapi-limiter | accepted | 2026-03-25 |
| ADR-0012 | pytest-bdd with .feature files as the executable specification | accepted | 2026-03-25 |
| ADR-0013 | PicoCSS as styling baseline, accepting the upstream freeze as MVP risk | accepted | 2026-04-21 |
| ADR-0014 | ApiResponse[T] envelope for all API success responses | accepted | 2026-03-25 |
| ADR-0015 | Correlation ID propagated through every request, service call, and log | accepted | 2026-03-25 |
| ADR-0016 | UTC everywhere with timezone-aware datetimes | accepted | 2026-03-25 |
| ADR-0017 | Mandatory audit fields on every table; soft delete for user content | accepted | 2026-03-25 |
| ADR-0018 | Append-only immutable audit log | accepted | 2026-03-25 |
| ADR-0019 | Honeypot field for bot protection on public forms, no CAPTCHA | accepted | 2026-03-25 |
| ADR-0020 | Full version pinning — top-level, transitive, models, and images | accepted | 2026-04-21 |
| ADR-0021 | Vendor frontend assets into git with version paths and SHA256 checksums | accepted | 2026-04-21 |
| ADR-0022 | spaCy model installed as a pinned wheel URL in requirements.txt | accepted | 2026-04-21 |
| ADR-0023 | Ruff replaces black, flake8, and isort | accepted | 2026-04-21 |
| ADR-0024 | CPU-only torch via PyTorch index pre-install in Docker and CI | accepted | 2026-04-21 |
| ADR-0025 | Every lint/type/security suppression must carry a reason | accepted | 2026-04-24 |
| ADR-0026 | Speed-tiered quality gates — pre-commit, pre-push, and CI | accepted | 2026-04-24 |
| ADR-0027 | Double-submit CSRF tokens on login and register | superseded | 2026-04-21 |
| ADR-0028 | Dual auth delivery — HttpOnly cookies for the browser, Bearer header for API clients | accepted | 2026-04-22 |
| ADR-0029 | SameSite=Lax as sole CSRF defense, with a hard no-state-changing-GET rule | accepted | 2026-04-22 |
| ADR-0030 | 303 redirects for browser login/logout, not HTMX HX-Redirect | accepted | 2026-04-22 |
| ADR-0031 | Side effects that must survive exceptions commit explicitly at the service boundary | accepted | 2026-04-22 |
| ADR-0032 | BDD tests give the app its own DB session, separate from the test's session | accepted | 2026-04-22 |
| ADR-0033 | Defects are fixed through a new dedicated .feature file, never by editing the original | accepted | 2026-06-21 |
| ADR-0034 | Frontend guidance split into docs/FRONTEND.md for context economy | accepted | 2026-06-14 |
| ADR-0035 | App shell Option D (rail → master-detail → inspector), built incrementally | accepted | 2026-06-14 |
| ADR-0036 | Closed catalogue of five layout archetypes; every screen is assigned one | accepted | 2026-06-14 |
| ADR-0037 | hx-boost as the default navigation model; targeted swaps only where they earn it | accepted | 2026-06-14 |
| ADR-0038 | Strict CSP with no unsafe-inline/unsafe-eval; Alpine.js only as the CSP build | accepted | 2026-06-14 |
| ADR-0039 | UI acceptance criteria are archetype-anchored and sorted into three test buckets | accepted | 2026-06-21 |
| ADR-0040 | A requirement cannot contain a requirement; the object chain is the structure and labels do the grouping | accepted | 2026-08-28 |
| ADR-0041 | Acceptance criteria are plain text; Gherkin scenarios are a separate table | accepted | 2026-08-28 |
| ADR-0042 | The master outline holds groups and requirements only; criteria and scenarios live in the detail | accepted | 2026-08-28 |
| ADR-0043 | The AI proposes and the user accepts; the AI never authors a domain artifact alone | accepted | 2026-08-28 |
| ADR-0044 | Ace is the Gherkin editing surface; CodeMirror 6 and ProseMirror are refused | accepted | 2026-08-28 |
| ADR-0045 | Intake is Module 8 and owns the candidate funnel; provenance is a raw input, not a document | accepted | 2026-08-28 |
| ADR-0046 | The archetype catalogue holds six; Focus Editor is a full-width authoring route | accepted | 2026-08-28 |
| ADR-0047 | The module rail has a global section and a project section; it stands by default | accepted | 2026-08-28 |
| ADR-0048 | The requirements table is a read-only lens on its own route, never the authoring surface | accepted | 2026-08-28 |
| ADR-0049 | The outline row carries one derived coverage mark and no counts | accepted | 2026-08-28 |
| ADR-0050 | The group-by axis lives in the URL; the outline filters and never paginates | accepted | 2026-08-28 |
| ADR-0051 | The MVP shell adds no new interaction mechanism - native keyboard, no splitters, no palette | accepted | 2026-08-28 |
