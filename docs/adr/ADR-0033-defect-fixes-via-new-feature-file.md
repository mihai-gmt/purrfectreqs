---
id: ADR-0033
title: Defects are fixed through a new dedicated .feature file, never by editing the original
status: accepted
date: 2026-06-21
backfilled: true
deciders: [mihai]
tags: [testing, process, bdd]

supersedes: []
superseded_by: null
depends_on: [ADR-0012]
related_to: []
affects_modules: [tests/features]
governed_by: [CLAUDE.md, docs/GUIDE.md]
rejected_alternatives: [amend-original-feature]
---

# ADR-0033: Defects are fixed through a new dedicated .feature file, never by editing the original

## Context

`CLAUDE.md` (.feature File Authority) already forbids modifying a `.feature`
file to match code. A defect creates temptation from the other direction:
"the spec missed this case, so extend the original file." Either way, the
original contract stops being a stable record of what was specified and
verified at the time.

## Decision

A defect is addressed by writing a **new** `.feature` file dedicated to the
bug, citing the BUG identifier, specifying the corrected behaviour as its own
scenarios. The original feature's `.feature` file is never modified as part
of a defect fix. The new file then follows the normal RED→GREEN cycle.

## Rationale

The original `.feature` is the contract the implementation was accepted
against; rewriting it during a fix destroys the evidence of what changed and
why. A dedicated bug-file makes the defect, its scenarios, and its fix a
traceable unit — the same append-only instinct as the audit log (ADR-0018),
applied to specifications.

## Consequences

### Positive

- Specification history is append-only and auditable; each bug carries its
  own executable regression scenarios permanently.

### Negative

- Behaviour for one feature can span multiple `.feature` files over time;
  readers must treat the set, not a single file, as current truth.

## Alternatives considered

### amend-original-feature

Editing the original spec to cover the defect case was rejected: it
back-dates the contract, hides that a gap existed, and conflicts with the
spirit of the `.feature`-authority rule even when the letter (matching code)
is not violated.

<!-- NOTE (backfill): established as developer feedback in a working session
(~2026-06-21); written into docs/GUIDE.md Rule 6 on 2026-07-08. -->
