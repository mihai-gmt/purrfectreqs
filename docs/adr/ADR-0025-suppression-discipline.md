---
id: ADR-0025
title: Every lint/type/security suppression must carry a reason
status: accepted
date: 2026-04-24
backfilled: true
deciders: [mihai]
tags: [tooling, code-quality, process]

supersedes: []
superseded_by: null
depends_on: [ADR-0023]
related_to: [ADR-0026]
affects_modules: []
governed_by: [docs/GUIDE.md]
rejected_alternatives: [bare-suppressions]
---

# ADR-0025: Every lint/type/security suppression must carry a reason

## Context

The PR-review tooling plan (2026-04-24) was about to enable bandit and mypy.
Enabling more tools first invites triage fatigue and mass bare suppressions
that make CI look green while hiding real issues — so the discipline rule had
to land before the tools did.

## Decision

Bare suppressions are blocked by tooling: ruff rule `PGH003` rejects
`# type: ignore` without a specific error code, and a pre-commit `pygrep`
hook rejects `# noqa` and `# nosec` not followed by `: <reason>`. The reason
follows on the same line, e.g.
`# nosec: B105 — user-facing error message, not a credential`.

## Rationale

From `docs/GUIDE.md`: "mass-suppression without reasons defeats the purpose
of running the tools — future readers (including you) can't distinguish
'considered and safe' from 'silenced to make CI green.'" Sequencing mattered:
the rule preceded bandit/mypy adoption precisely so the initial triage of
their findings produced reasoned suppressions (the codebase started with zero
bare suppressions).

## Consequences

### Positive

- Every suppression is an auditable mini-decision; false-positive patterns
  (e.g. bandit B105 on variables named `*password*`) get documented at the
  site.

### Negative

- Slightly more ceremony per suppression — the intended friction.

## Alternatives considered

### bare-suppressions

The default behaviour of the tools. Rejected: a suppression without a reason
is indistinguishable from silencing noise, and the distinction is the entire
value of running static analysis.
