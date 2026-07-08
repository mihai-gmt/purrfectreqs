---
id: ADR-NNNN
title: <sentence-case decision title>
status: proposed            # proposed | accepted | deprecated | superseded
date: 2026-01-01            # best-known decision date (ISO)
backfilled: false           # true when the record was written after the fact
deciders: [mihai]
tags: []                    # lowercase-kebab topic tags

supersedes: []              # ADR ids this decision replaces
superseded_by: null         # ADR id that replaced this one (status must be `superseded`)
depends_on: []              # ADR ids this decision assumes
related_to: []              # ADR ids
affects_modules: []         # repo paths, e.g. app/auth, app/static
governed_by: []             # doc paths that constrain this decision, e.g. docs/SECURITY.md
rejected_alternatives: []   # kebab slugs; each gets an H3 under "Alternatives considered"
---

# ADR-NNNN: <title>

## Context

What forces are at play — the problem, the constraints, and why a decision was
needed. Keep it to the facts that made the decision necessary.

## Decision

One declarative paragraph: "We will …" / "We use …".

## Rationale

Why this option won. Cite the source (doc section, journal entry) the reasoning
comes from; quote the developer's own reasoning where it was recorded.

## Consequences

### Positive

### Negative

## Alternatives considered

### <slug>

What it was and why it was rejected. One H3 per `rejected_alternatives` entry;
the heading must match the slug exactly.

<!--
Authoring rules (enforced by tests/docs/test_adr_validation.py):
- Filename: ADR-NNNN-<kebab-slug>.md; frontmatter id must match the prefix.
- Relations/metadata live in frontmatter only; reasoning lives in the body only.
- Every relation target must exist; supersedes/superseded_by must be set on both sides.
- Add the ADR to the README.md index table (id, title, status, date) in the same change.
- Keep the body under ~60 lines. Records, not essays.
-->
