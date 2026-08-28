# PurrfectReqs — Glossary

> **Purpose:** Canonical definitions for all domain terms used in PurrfectReqs. When writing code, documentation, or Gherkin scenarios, use these terms exactly as defined. Consistency in naming prevents confusion between humans and AI agents.

---

## Requirements

**Requirement**
One thing the system must do. It belongs to exactly one project. A requirement cannot contain another requirement. It is a row in the `requirements` table.

**Object chain**
The fixed four-level structure of the product: project → requirement → acceptance criterion → gherkin scenario. Each level is a different kind of object with different fields and a different reader. The chain is set by the schema. A user cannot add a level or remove one.

**Label**
A named tag on a requirement, used for grouping and filtering. Written `namespace:value`, for example `group:Registration`. A label is a view axis. It never changes the object chain, and it is not a folder.

**Namespace**
The axis a label belongs to. The set is closed and controlled by the schema. A user creates label values; a user never creates a namespace.

**Group by**
The chosen axis for the master pane outline. The user switches it at any time. It lives in the URL as a query parameter, so a link carries it and the back button restores it. The same requirement can appear under a different heading in each axis, because a label is not a home.

**Source**
The raw input a requirement was derived from, held in `requirements.raw_input_id`. A raw input is a pasted note or a parsed document, so one field covers both. It is provenance, not structure. It is distinct from an attached document, which is a `requirement_documents` row.

**Intake**
The capability that captures unstructured source material for a project and holds AI-proposed requirements until a person accepts them. Module 8. It is a separate rail entry, not a view inside Requirements.

**Raw input**
One unit of unstructured source material: a pasted note, or a parsed document. A row in the `raw_inputs` table. It is never edited after creation.

**Candidate requirement**
A proposed requirement that no person has accepted yet. A row in the `candidate_requirements` table. It is NOT a requirement and it never appears in the requirements outline. Accepting one creates the `requirements` row.

---

## Acceptance Criteria

**Acceptance Criteria (AC)**
A condition that a requirement must satisfy to be complete. Written in plain language by a business reader. It holds NO Gherkin. Stored in the `acceptance_criteria` table, linked to a `requirement`.

**Gherkin Scenario**
The formal, executable statement of one acceptance criterion, written in Gherkin. Stored in the `gherkin_scenarios` table, linked to a criterion. One criterion can have many scenarios. The AI can propose one; a person accepts it or dismisses it.

**Origin**
The producer of a scenario's first version: `human` or `ai`. It never changes after creation.

**Authoring state**
How far a scenario has moved through agreement: `proposed`, `draft`, or `accepted`. It is not test coverage.

**Stale**
A scenario is stale when the criterion it came from changed after the scenario was accepted. It is computed on read from a stored hash. It is never stored.

**Gherkin**
A structured, plain-English syntax for writing acceptance criteria and test scenarios. Uses keywords: `Feature`, `Scenario`, `Given`, `When`, `Then`, `And`, `But`. Parsed by `gherkin-official`.

**Feature File (`.feature`)**
A file containing one or more Gherkin scenarios. Stored under `tests/bdd/features/<module>/`. In PurrfectReqs' own development workflow, these are the primary specification artifacts — written by the developer before any code is written. They are the executable contract that implementation must satisfy.

**Scenario**
A single test case within a feature file. Describes one specific behaviour with a sequence of Given/When/Then steps.

**Step**
A single line in a Gherkin scenario, beginning with `Given`, `When`, `Then`, `And`, or `But`.

---

## Coverage States

These four states belong to a **Gherkin scenario**, not to an acceptance criterion. A plain criterion has no test, so it has no coverage state of its own.

| State | Meaning |
|-------|---------|
| `not_covered` | The scenario exists but no test references it yet |
| `covered` | A test references this scenario, but it has not run or passed |
| `test_passed` | The test for this scenario passes — the scenario is done |
| `test_failed` | A test exists but currently fails |

A criterion is **covered** when it has at least one scenario and every scenario is `test_passed`. A requirement is **done** when every one of its criteria is covered. Both facts are derived on read. Neither is stored.

---

## Project & Access Terms

**Project**
A container for requirements. Represents a software project or product being managed. Users are assigned to projects with a role.

**Project Role**
The role a user has within a specific project: `owner`, `editor`, or `viewer`. Separate from the system-wide role.

**System Role**
The role a user has across the whole application: `admin`, `super_user`, or `user`. Controls access to system-level features.

**Owner (project)**
A user with full control over a specific project. Can manage members, requirements, and settings within the project.

**Editor**
A user who can create and modify requirements within a project but cannot manage project members or settings.

**Viewer**
A user who can read requirements in a project but cannot make changes.

---

## System Roles

**Admin**
Full system access. Can manage all users, all projects, view all audit logs, and access all system settings. Creates all user accounts.

**Super-user**
Elevated access. Can manage users in a limited capacity. For other functions, equivalent to `user`. Stored as `super_user` in the database.

**User**
Standard access. Can manage their own projects and requirements within their assigned project roles.

---

## AI & Analysis Terms

**NLP (Natural Language Processing)**
Automated analysis of text to extract meaning. In PurrfectReqs, NLP is used to analyze requirement descriptions for quality, ambiguity, entity recognition, and semantic similarity.

**NER (Named Entity Recognition)**
A specific NLP task that identifies and classifies named entities in text (e.g., system names, user roles, technical components). Performed by spaCy.

**Embedding / Vector Embedding**
A numerical representation of text as a high-dimensional vector. Semantically similar texts produce similar vectors. Used for semantic search and similarity analysis. Generated by sentence-transformers (`all-MiniLM-L6-v2`), stored in PostgreSQL via pgvector.

**Semantic Similarity**
A measure of how similar two pieces of text are in meaning, regardless of the exact words used. Computed by comparing vector embeddings.

**LLM (Large Language Model)**
The AI model used for requirement analysis. In PurrfectReqs, this is Qwen 3 32B Q4 (general-purpose, non-Coder variant) running locally via Ollama. Never refers to an external cloud AI service.

**Ollama**
The local LLM runtime that serves the Qwen 3 model via HTTP. Runs natively on macOS (Metal GPU acceleration on Apple Silicon), not inside Docker. Accessed by the application container at `http://host.docker.internal:11434`.

**Analysis Result**
The output of an NLP or LLM analysis run on a requirement or document. Stored in the `analysis_results` table with a typed `result_data` JSON field.

---

## Technical Infrastructure Terms

**Correlation ID**
A UUID assigned to every API request. Propagated through all service calls, log entries, and error responses within that request. Enables tracing a complete request across logs.

**Audit Log**
An append-only record of every data change in the system. Stored in the `audit_logs` table. Never modified or deleted.

**Soft Delete**
Marking a record as deleted (`is_deleted = True`) without removing it from the database. Preserves history and allows recovery. Hard deletes are only used for session tokens and temporary data.

**Feature Box**
The set of files and modules that a single task is permitted to touch. Defined by the agent before starting work. Cross-module changes outside the Feature Box require escalation.

**Alembic Migration**
A versioned script that modifies the database schema. Every schema change must have one. Run automatically on container startup.

**Seed Data**
A set of initial records loaded into the database in development environments only. Currently: 3 test users (admin, super-user, user). Controlled by `APP_ENV=development`.

---

## BDD/TDD Workflow Terms

**TDD (Test-Driven Development)**
A development practice where tests are written before implementation code. The cycle: RED (tests fail) → GREEN (tests pass) → REFACTOR.

**BDD (Behaviour-Driven Development)**
An extension of TDD using human-readable Gherkin scenarios as the specification. Tests are derived from acceptance criteria, not invented after the fact.

**RED state**
The state where tests have been written but the implementation does not yet exist — tests fail. This is the expected state after the test-writing phase.

**GREEN state**
The state where all tests pass because the implementation satisfies the acceptance criteria.

**Step Definition**
A Python function that maps a Gherkin step to executable test code. Written using `pytest-bdd` decorators (`@given`, `@when`, `@then`).

**Feature Phase**
One complete development cycle for a single `.feature` file: Plan → Write Tests (RED) → Implement (GREEN) → Commit.

---

## UI & Frontend Terms

**App Shell**
The persistent frame (module rail · master · detail, plus an on-demand inspector) that wraps every authenticated screen and is not replaced between modules. Defined in `docs/FRONTEND.md` §2.

**Layout Archetype**
One of the six closed, named page-level layouts every screen is assigned: Centred Form, Master-Detail, Master-Detail + Inspector, Full-width Data, Reading/Content, Focus Editor. A spec names the archetype; the implementer applies it. Catalogue in `docs/FRONTEND.md` §2.

**Chrome-less**
A screen rendered without the app shell (no rail, no nav) so the user has a single focus. Used for pre-authentication pages. The Centred Form archetype is chrome-less.

**Focus Editor**
Archetype 6. A full-width authoring route where the rail and the master outline yield to a narrow read-only context strip. Used by the Gherkin scenario editor. The inspector never opens beside it.

**Inspector**
The on-demand right-hand pane of archetype 3. One pane with several jobs: AI analysis, validation results, traceability links, and AI proposals awaiting an accept. The "AI drawer" of the shell prototype is this pane.

**Module Rail (Rail)**
The left navigation zone of the app shell. It has two sections: a global section (Projects, Admin) that is always present, and a project section (Requirements, Intake, Documents, Gherkin, Traceability) that appears only when a project is active. The rail stands at ≥768 px.

**Master / Detail**
The two core shell zones. **Master** is the outline of items — for requirements, a group heading and the requirements inside it; **detail** is the selected item and where editing happens. Criteria and scenarios are never outline nodes.

**Table lens**
The read-only table over the requirements of a project. Archetype 4, its own route. It sorts and filters; it never edits. The outline stays the default view.

**Coverage mark**
The one derived signal on an outline row. It says whether the requirement has at least one accepted scenario. It is computed on read, never stored.

**Inspector**
An on-demand pane that slides in beside the detail to show supporting information (AI analysis, Gherkin validation, traceability links). Not permanently present; built only when there is data for it.

**Progressive Disclosure**
Revealing UI only when there is content or a need for it — e.g. the inspector pane is not built before analysis data exists.

**Design Token**
A named CSS custom property for a semantic colour, type step, or spacing step (e.g. `--color-surface`, `--space-2`). Templates reference tokens, never raw hex or pixel values. Defined in `docs/FRONTEND.md` §5.

**Macro / Partial**
The two reusable template units. A **macro** (`{% macro %}`) is a parameterised atom/molecule rendered inside a page (form field, button, badge). A **partial** (`{% include %}`) is a self-contained fragment, often an HTMX swap target. Their contracts are registered in `docs/UI_CATALOGUE.md`.

---

## File Naming Conventions

| Thing | Convention | Example | Location |
|-------|-----------|---------|----------|
| Feature files | `snake_case.feature` | `user_login.feature` | `tests/bdd/features/<module>/` |
| BDD step definition files | `test_<feature_name>.py` | `test_user_login.py` | `tests/bdd/step_defs/` |
| Unit test files | `test_<module>_<thing>.py` | `test_auth_service.py` | `tests/unit/<module>/` |
| Jinja2 templates | `snake_case.html` | `requirement_detail.html` | `app/templates/<module>/` |
| Jinja2 partials | `_snake_case.html` | `_criteria_list.html` | `app/templates/<module>/` |
| Plan files | `<module>_<feature>.plan.md` | `auth_login.plan.md` | `tests/bdd/plans/` |
