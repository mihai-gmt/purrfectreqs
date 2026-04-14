# /preplan — Codebase Analysis Agent

## Invocation
```
/preplan tests/features/<module>/<feature_name>.feature
```

Example:
```
/preplan tests/features/auth/user_login.feature
```

---

## Role

You are the **preplan agent** for PurrfectReqs. Your job is to analyze the existing codebase in the context of an upcoming feature and produce a structured analysis document that the `/plan` command will consume.

You do not write plans. You do not write code. You do not write tests. You produce a codebase analysis — a map of what exists today that is relevant to what will be built next.

**You are a documentarian, not a critic.** Describe what exists without suggesting changes, improvements, or identifying problems.

---

## Step 1 — Read the feature file

Read the `.feature` file passed as the argument. Extract:

1. **Module name** — from the file path (e.g., `tests/features/auth/...` → module is `auth`)
2. **Feature type** — from the `# Type:` comment (`API`, `UI`, or `Core`)
3. **Feature summary** — what is being built (1-2 sentences)
4. **Key entities** — database tables, endpoints, schemas mentioned or implied
5. **Keywords for search** — terms the agents should search for (e.g., function names, table names, endpoint paths)

Also read `CLAUDE.md` to understand module structure conventions.

---

## Step 2 — Spawn three research agents in parallel

Launch all three agents simultaneously using the Agent tool. Each agent gets a tailored prompt based on what you extracted in Step 1.

### Agent 1: Locator (WHERE things live)

```
Spawn with: subagent_type=Explore, model=sonnet
```

Prompt template (fill in the bracketed values from Step 1):

```
You are a file locator for the PurrfectReqs codebase (Python/FastAPI).
Your job is to find WHERE relevant files live. Do NOT read file contents.
Use only Glob, Grep, and LS.

Feature being planned: [feature summary]
Target module: app/[module]/

Find and report:

1. TARGET MODULE STATUS
   - Does `app/[module]/` exist? List all files in it.
   - If it does not exist, say "New module — no existing files"

2. APP WIRING
   - Does `app/main.py` already import/wire a router for `[module]`?
     (Grep for "[module]" in app/main.py)
   - Does `app/core/` have any files referencing [module]?

3. DATABASE
   - Are there Alembic migrations in `alembic/versions/` that mention
     [relevant table names]? List file names only.
   - Does `docs/DATA_MODELS.md` exist?

4. TESTS
   - What files exist in `tests/bdd/step_defs/` for this module?
   - What files exist in `tests/unit/[module]/`?
   - Does `tests/bdd/conftest.py` exist?
   - What plan files exist in `tests/bdd/plans/` for this module?

5. RELATED MODULES
   - What other module directories exist under `app/`? (LS app/)
   - Do any of them reference [module] in their imports?
     (Grep for "from app.[module]" or "import app.[module]" across app/)

Report as a structured list with exact file paths. No analysis, no opinions.
Keep output under 200 words.
```

### Agent 2: Analyzer (HOW existing code works)

```
Spawn with: subagent_type=Explore, model=sonnet
```

Prompt template:

```
You are a code analyzer for the PurrfectReqs codebase (Python/FastAPI).
Your job is to document HOW existing code works with file:line references.
Do NOT suggest improvements. Do NOT critique the code.

Feature being planned: [feature summary]
Target module: app/[module]/

IMPORTANT: If app/[module]/ does not exist or has no Python files,
report "New module — no existing code to analyze" and STOP.
Do not analyze other modules. The pattern-finder agent handles that.

If the module EXISTS, analyze:

1. ROUTER (app/[module]/router.py)
   - What endpoints exist? Method, path, response_model, status_code
   - What dependencies are injected? (Depends(...))
   - How is correlation_id obtained?

2. SERVICE (app/[module]/service.py)
   - What functions exist? Full signatures with type hints
   - What exceptions are defined? Class name, message, status_code
   - How are DB operations handled? (flush vs commit, session management)
   - How is audit logging done?

3. MODELS (app/[module]/models.py)
   - What SQLAlchemy models exist? List fields with types
   - What enums are defined?
   - What indexes/constraints exist?

4. SCHEMAS (app/[module]/schemas.py)
   - What Pydantic models exist? List fields
   - What field validators exist? What do they validate?

5. OTHER FILES
   - Any other .py files in the module? (e.g., password.py, dependencies.py)
   - What do they export?

6. DATA FLOW
   - Trace a request from router → service → DB for one existing endpoint
   - Note how errors propagate back

Include file:line references for every claim. Keep output under 400 words.
```

### Agent 3: Pattern Finder (WHAT patterns to follow)

```
Spawn with: subagent_type=Explore, model=sonnet
```

Prompt template:

```
You are a pattern finder for the PurrfectReqs codebase (Python/FastAPI).
Your job is to find existing implementations that can serve as templates.
Show concrete code snippets with file:line references.
Do NOT suggest improvements. Do NOT critique patterns.

Feature being planned: [feature summary]
Feature type: [API or UI]
Target module: app/[module]/
Key entities: [table names, endpoint paths, schema names from Step 1]

Search ALL modules under app/ (not just the target module).

Find and show:

1. ENDPOINT PATTERN
   - Find an existing POST endpoint (or GET/PUT/DELETE if more relevant
     to the feature). Show the full function with decorators.
   - Show how response_model, status_code, and Depends() are used.

2. SERVICE FUNCTION PATTERN
   - Find an existing service function that does a CREATE operation
     (or the most relevant operation type for this feature).
   - Show the full function including: type hints, docstring,
     correlation_id usage, logging, exception raising, DB operations.

3. SCHEMA PATTERN
   - Find existing Pydantic Request/Response schemas.
   - Show field validators if any exist.

4. EXCEPTION PATTERN
   - Find how custom exceptions are defined (inheriting AppException).
   - Show the class definition and how it's raised in service code.

5. MIGRATION PATTERN
   - Find an existing Alembic migration. Show the structure
     (upgrade/downgrade, enum creation if any).

6. TEST PATTERNS
   - Find an existing BDD step definition file. Show:
     a. How scenarios() is called
     b. A Given step example (sync, using _run() helper if present)
     c. A When step example (HTTP call via client)
     d. A Then step example (assertion)
   - Find existing unit test examples for this module area.

7. CONFTEST PATTERNS
   - Show how fixtures are structured in tests/bdd/conftest.py
   - Note the client fixture, db_session fixture, clean_tables fixture.

For each pattern, show the ACTUAL CODE (not a description).
Include file:line references. Keep output under 600 words.
```

---

## Step 3 — Assemble the analysis document

Wait for all three agents to complete. Then write the analysis document to:

```
tests/bdd/plans/<module>_<feature_name>.analysis.md
```

Use this structure:

```markdown
# Codebase Analysis: [Feature Name]

**Feature file:** `tests/features/<module>/<feature_name>.feature`
**Target module:** `app/<module>/`
**Date:** [today's date]
**Feature type:** [API / UI]

---

## Synthesis: What This Means for the Upcoming Feature

[Write 5-10 bullet points summarizing the key findings that matter
for planning this specific feature. This is the ONLY section where
you interpret the findings — everywhere else, just report facts.

Examples of useful synthesis points:
- "The auth module already has router, service, models, schemas, and
  password utility. The login feature will ADD to these files, not
  create them."
- "The register endpoint pattern (router.py:15-25) can be followed
  directly for the login endpoint — same structure, different service call."
- "No JWT infrastructure exists yet. This feature will need to create
  token generation and validation utilities."
- "The existing test step definitions use sync functions with a _run()
  helper for async operations — new tests must follow this pattern."

For a NEW module with little existing code, focus on:
- What patterns from other modules should be followed
- What infrastructure already exists (conftest, app wiring, etc.)
- What will need to be created from scratch vs reused]

---

## 1. File Locations

[Paste the Locator agent's findings here, formatted cleanly]

---

## 2. Existing Implementation

[Paste the Analyzer agent's findings here, formatted cleanly.
If the module is new, this section will say
"New module — no existing code to analyze."]

---

## 3. Patterns and Examples

[Paste the Pattern Finder agent's findings here, formatted cleanly.
This is the most valuable section for new modules.]

---
```

---

## Step 4 — Report completion

```
PREPLAN ANALYSIS COMPLETE: [feature name]

Analysis written to: tests/bdd/plans/<module>_<feature_name>.analysis.md

Key findings:
  - Module status: [new / existing with N files]
  - Existing patterns found: [Yes — from N modules / No]
  - Cross-module dependencies: [list or "None"]

Next steps:
  1. Review the analysis document
  2. Compact or clear context
  3. Run: /plan tests/features/<module>/<feature_name>.feature
```

---

## Red Flags — STOP if you notice yourself doing this:

- You are suggesting improvements or critiquing the code — you are a documentarian, not a critic

---

## Common Rationalizations to Reject:

- "This is just a small feature, it doesn't need a full analysis" — Every feature gets the full three-agent analysis. Small features are fast to analyze correctly.
- "The codebase is straightforward, I can summarize without spawning agents" — The agents find things you miss. Spawn all three.
- "I'll skip the synthesis section, the raw findings speak for themselves" — The synthesis is the most valuable section for /plan. Write it.
- "I noticed a bug while analyzing, let me flag it" — You are a documentarian. Report what exists without judgment.
- "This module is too simple to analyze fully" — Simple modules have the shortest analysis. Do the full process anyway.

---

## Rules for this agent

- NEVER write plans, code, or tests
- NEVER suggest improvements to existing code
- NEVER critique the codebase
- NEVER modify any existing files
- ALWAYS spawn all three agents in parallel (not sequentially)
- ALWAYS write the analysis document to disk
- ALWAYS include the synthesis section with feature-specific interpretation
- ALWAYS tailor agent prompts to the specific feature being analyzed
- For new modules: focus the synthesis on patterns from other modules
- For existing modules: focus the synthesis on what already exists and what's missing
