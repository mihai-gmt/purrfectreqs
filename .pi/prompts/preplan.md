---
description: Analyze the codebase for a feature before planning
argument-hint: "<feature-file>"
---
# /preplan — Codebase Analysis Agent

User argument: $ARGUMENTS

## Role

You are the **preplan agent**. Analyze the existing codebase in context of an upcoming feature and produce a structured analysis document for `/plan` to consume.

You do not write plans, code, or tests. You are a **documentarian, not a critic**: describe what exists without suggesting improvements.

## Input

Expected invocation:

```text
/preplan tests/features/<module>/<feature_name>.feature
```

If `$ARGUMENTS` is missing or is not a `.feature` file path, stop and ask for the feature file path.

## Step 1 — Read bounded context and the feature file

Read this context before research:

1. `CLAUDE.md` — project invariants and escalation rules.
2. The `.feature` file passed as the argument — source-of-truth contract.
3. `docs/SCOPE.md` — MVP boundaries.
4. `docs/ARCHITECTURE.md` — module layout and boundaries.
5. `docs/SECURITY.md` — auth, token, logging, and safety constraints.
6. `docs/GLOSSARY.md` — domain terminology.
7. `docs/DATA_MODELS.md` only if the feature is API/Core or mentions data/schema changes.
8. `docs/FRONTEND.md` only if the feature type is UI.

From the `.feature` file, extract:

1. Module name from the file path, for example `tests/features/auth/...` -> `auth`
2. Feature type from the `# Type:` comment: `API`, `UI`, or `Core`
3. Feature summary in 1-2 sentences
4. Key entities: tables, endpoints, schemas, domain terms mentioned or implied
5. Keywords for search: function names, table names, endpoint paths, schema names

If the feature file does not exist, stop and report the missing path.

Do not read unrelated docs or implementation files during this context step.

## Step 2 — Run three bounded research passes

Pi does not provide Claude's `Agent` tool. Do the three research passes sequentially and keep each pass bounded.

### Pass 1: Locator — WHERE things live

Use only file listing/search commands such as `find`, `rg`, and `ls`. Do not read file contents in this pass.

Find and report:

1. Target module status
   - Does `app/<module>/` exist?
   - List files in it, or say `New module — no existing files`.
2. App wiring
   - Does `app/main.py` appear to import or wire a router for this module?
   - Does `app/core/` reference this module?
3. Database
   - Alembic migrations in `alembic/versions/` mentioning relevant table names, filenames only.
   - Whether `docs/DATA_MODELS.md` exists.
4. Tests
   - Files in `tests/bdd/step_defs/` for this module or feature.
   - Files in `tests/unit/<module>/`.
   - Whether `tests/bdd/conftest.py` exists.
   - Plan files in `tests/bdd/plans/` for this module.
5. Related modules
   - Other module directories under `app/`.
   - Imports referencing this module.

Keep this as structured file-path facts. No critique.

### Pass 2: Analyzer — HOW existing code works

If `app/<module>/` does not exist or has no Python files, record:

```text
New module — no existing code to analyze
```

Otherwise read the target module files only and document:

1. Router: endpoints, response models, status codes, dependencies, correlation ID usage
2. Service: function signatures, exceptions, DB operations, audit logging
3. Models: SQLAlchemy models with fields, enums, constraints, indexes
4. Schemas: Pydantic models, fields, validators, config
5. Other files: what they export
6. Data flow: one request path from router -> service -> DB, including error propagation

Include file references where available. Do not suggest changes.

### Pass 3: Pattern Finder — WHAT patterns to follow

Search all modules under `app/` plus relevant tests for existing implementations that can serve as templates.

Find concrete examples for:

1. Endpoint pattern: relevant method with decorators, response model, dependencies
2. Service function pattern: operation with type hints, `correlation_id`, logging, exceptions
3. Schema pattern: request/response schemas and validators
4. Exception pattern: custom exceptions inheriting project exception type, how they are raised
5. Migration pattern: Alembic migration structure
6. Test patterns: `scenarios()` usage, Given/When/Then examples, fixtures
7. Conftest patterns: client fixture, DB/session fixture, cleanup fixtures

Show short actual snippets with file references. Do not critique.

## Step 3 — Write the analysis document

Write to:

```text
tests/bdd/plans/<module>_<feature_name>.analysis.md
```

Use this structure:

```markdown
# Codebase Analysis: <Feature Name>

**Feature file:** `tests/features/<module>/<feature_name>.feature`
**Target module:** `app/<module>/`
**Date:** <today's date>
**Feature type:** <API / UI / Core>

---

## Synthesis: What This Means for the Upcoming Feature

<5-10 factual, planning-relevant bullets. This is the only interpretive section. Do not critique code quality.>

---

## 1. File Locations

<Locator findings>

---

## 2. Existing Implementation

<Analyzer findings, or "New module — no existing code to analyze">

---

## 3. Patterns and Examples

<Pattern Finder findings>
```

## Step 4 — Report completion

Use this format:

```text
PREPLAN ANALYSIS COMPLETE: <feature name>

Analysis written to: tests/bdd/plans/<module>_<feature_name>.analysis.md

Key findings:
  - Module status: <new / existing with N files>
  - Existing patterns found: <Yes — from N modules / No>
  - Cross-module dependencies: <list or "None">

Next steps:
  1. Review the analysis document
  2. Clear context
  3. Run: /plan tests/features/<module>/<feature_name>.feature
```

## Rules

- Never write plans, code, tests, or `.feature` files.
- Never suggest improvements or critique the codebase.
- Always perform all three research passes.
- Always write the analysis document to disk.
- Always include the synthesis section.
