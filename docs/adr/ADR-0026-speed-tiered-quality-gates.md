---
id: ADR-0026
title: Speed-tiered quality gates — pre-commit, pre-push, and CI
status: accepted
date: 2026-04-24
backfilled: true
deciders: [mihai]
tags: [tooling, ci, code-quality]

supersedes: []
superseded_by: null
depends_on: [ADR-0023, ADR-0025]
related_to: []
affects_modules: []
governed_by: [docs/GUIDE.md]
rejected_alternatives: [everything-in-pre-commit, language-system-hooks]
---

# ADR-0026: Speed-tiered quality gates — pre-commit, pre-push, and CI

## Context

Static analysis only helps if it runs where developers actually feel it, but
a slow pre-commit hook trains people to `--no-verify`. Tools needed placing
by cost (journal 2026-04-24).

## Decision

Three tiers by speed budget: **pre-commit** (<5s) runs ruff, bandit, and the
suppression-discipline greps; **pre-push** (<30s) adds mypy; **CI** runs the
full lint job, pip-audit on dependency changes plus weekly on schedule, and
the test suite against real Postgres and Redis services. Hooks use official
pre-commit mirrors (PyCQA/bandit, mirrors-mypy), not `language: system`.

## Rationale

Measured timings landed at 0.34s / 0.44s — well inside budget. The mirror
choice fixes a real failure: `language: system` hooks resolve executables
from the caller's PATH, and VS Code's git integration does not activate the
venv, so commits from the editor failed with "executable not found." Mirrors
manage isolated environments, making venv activation irrelevant. A second
recorded lesson: mypy's `warn_unused_ignores = true` is load-bearing, and the
fix for CI/local suppression drift is to give CI the full dependency context,
never to drop the warning.

## Consequences

### Positive

- Feedback arrives at the cheapest point that can catch each class of issue;
  the weekly pip-audit catches CVEs between dependency changes.

### Negative

- Three places define quality checks; keeping local hooks and CI equivalent
  is a maintenance duty (the unused-ignore incident is what drift looks
  like).

## Alternatives considered

### everything-in-pre-commit

Running mypy on every commit blew the 5-second budget class of concern —
slow hooks get bypassed, which is worse than fewer hooks.

### language-system-hooks

The first implementation; rejected after VS Code commits failed on PATH
resolution. Official mirrors carry their own environments.
