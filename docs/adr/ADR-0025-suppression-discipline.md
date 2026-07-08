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
follows on the same line:

- `# noqa: E402 — late import required by alembic env.py`
- `# nosec: B105  # user-facing error message, not a credential`

For `# nosec` the reason MUST sit behind a **second `#`**. Bandit's parser
(`NOSEC_COMMENT = #\s*nosec:?\s*(?P<tests>[^#]+)?#?`) captures everything from
`nosec:` up to the next `#` and treats it as a list of test IDs, so an
un-shielded prose reason (`# nosec: B105 — user-facing …`) makes bandit emit a
`Test in comment: <word> is not a test name or id` warning for every word of
the reason. Placing the reason after a second `#` leaves only `B105` in the
capture — the suppression still applies and the run is clean. Ruff's `# noqa`
parser has no such quirk; prose directly after the codes is fine.

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

<!-- AMENDMENT 2026-07-08 (BUG-005): the original `# nosec` example placed the
reason directly after the colon (`# nosec: B105 — user-facing …`), which the
decision above now corrects to the shielded `# nosec: B105  # <reason>` form.
Bandit parses an un-shielded reason as bogus test IDs and warns per word. This
is a factual correction to a format that never worked with bandit — not a
change of the underlying decision. Sole affected suppression fixed at
app/auth/schemas.py:44; hook-comment examples in .pre-commit-config.yaml updated
to match. -->

