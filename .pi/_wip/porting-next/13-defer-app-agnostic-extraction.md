# 13 — Defer Generic App-Agnostic Extraction

## Purpose

Avoid premature generalization.

## Current state

The governance engine is split from config, but still contains PurrfectReqs assumptions.

Known assumptions:

- Python/FastAPI-ish source layout
- `app/`
- `app/core`
- `tests/bdd/plans`
- `tests/unit`
- `tests/bdd/step_defs`
- Alembic migrations
- pytest/ruff commands

## Why defer

A generic harness should be extracted only after the PurrfectReqs version works reliably.

## Future extraction checklist

- constitution files configurable
- authority docs role-based
- source artifacts configurable
- source/test roots configurable
- commands configurable
- review lenses configurable
- context routes configurable
- workflow states generic with project aliases
- protected paths configurable
- validated on second non-PurrfectReqs project

## Near-term action

Only perform small config-seam improvements that help PurrfectReqs maintainability.

Do not create a generic package yet.
