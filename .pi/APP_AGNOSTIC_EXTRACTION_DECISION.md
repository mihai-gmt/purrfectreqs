# App-Agnostic Extraction Decision

## Decision

Do not extract a generic app-agnostic harness yet.

Keep the current harness PurrfectReqs-local while continuing small configuration-seam improvements that make the local harness easier to maintain.

## Why extraction is deferred

The governance engine has been split from the Pi adapter and now has a configuration seam, but the workflow is still intentionally shaped around PurrfectReqs.

A generic harness should not be extracted until the PurrfectReqs workflow has been validated on a brand-new feature end to end. Extracting earlier would risk generalizing unproven assumptions.

## Current PurrfectReqs assumptions

The harness still assumes parts of this stack and workflow:

- Python/FastAPI-style source layout
- `app/` as the application root
- `app/core` as shared infrastructure
- `tests/bdd/plans` as the plan/artifact directory
- `tests/bdd/step_defs` and `tests/unit` as test roots
- Alembic migrations
- pytest-based RED/GREEN checks
- ruff/format quality checks
- `.feature` files as immutable executable specs
- PurrfectReqs authority docs such as `CLAUDE.md`, `docs/SECURITY.md`, and `docs/SCOPE.md`

Some of these are now configurable, but the overall workflow is not yet generic.

## Near-term rule

Allowed now:

- small config-seam improvements
- clearer docs
- reduced hardcoding when it directly helps PurrfectReqs maintainability
- bug fixes in the local harness

Not allowed yet:

- generic npm package extraction
- second-project abstraction work
- project-agnostic command grammar
- configurable workflow-state engine beyond what PurrfectReqs needs now

## Future extraction checklist

Before revisiting generic extraction, verify that these can be configured cleanly:

- constitution/context files
- authority document roles
- source roots
- test roots
- feature-file locations
- plan/artifact directories
- protected paths
- dependency files
- migration directories
- allowed shell commands
- workflow states and aliases
- review lenses
- context routes
- RED/GREEN command strategy

## Required validation before extraction

Generic extraction should require both:

1. successful end-to-end validation on a brand-new PurrfectReqs feature
2. successful trial on a second non-PurrfectReqs project

Until then, keep the harness local and PurrfectReqs-specific.
