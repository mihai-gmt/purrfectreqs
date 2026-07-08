---
id: ADR-0023
title: Ruff replaces black, flake8, and isort
status: accepted
date: 2026-04-21
backfilled: true
deciders: [mihai]
tags: [tooling, code-quality]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0025]
affects_modules: []
governed_by: [docs/TECH_STACK.md, docs/GUIDE.md]
rejected_alternatives: [add-isort, black-flake8-isort-stack]
---

# ADR-0023: Ruff replaces black, flake8, and isort

## Context

`docs/GUIDE.md` referenced isort for import ordering, but isort was not in
the dependency stack. The choice was: add isort and move on, or migrate the
whole code-quality toolchain to ruff now (journal 2026-04-21).

## Decision

Ruff is the single formatter, linter, and import sorter. Configuration lives
in `pyproject.toml` `[tool.ruff]`: line length 120, rule set
`E, F, I, UP, B, SIM`, with four reasoned ignores (`E501` formatter-owned;
`B008` FastAPI `Depends` idiom; `UP042`/`UP046` behavioural rewrites deferred
to deliberate tasks). black, flake8, and isort must not be reintroduced.

## Rationale

The developer's words: "option A seems like introducing tech debt, and
project is young, so let's go with RUFF now and save me a lot of trouble
later." One Rust-based tool, orders of magnitude faster, one config surface.
The migration also recorded a durable pattern: a suggested starter config was
stress-tested line by line — three of four parts needed correction, one of
which would have silently reverted the deliberate 120-char line length.

## Consequences

### Positive

- One dev dependency and one config for format/lint/imports; fast enough for
  pre-commit.

### Negative

- Modernisation rules (StrEnum, PEP 695 generics) are deliberately ignored —
  each is its own future task, not a tooling side effect.

## Alternatives considered

### add-isort

Minimal fix for the doc/stack mismatch; rejected as "introducing tech debt"
— a third tool for a young project that would need unwinding later.

### black-flake8-isort-stack

The status quo: three tools, three configs, slower runs. Superseded wholesale
by ruff's equivalents.
