---
id: ADR-0039
title: UI acceptance criteria are archetype-anchored and sorted into three test buckets
status: accepted
date: 2026-06-21
backfilled: true
deciders: [mihai]
tags: [testing, frontend, bdd]

supersedes: []
superseded_by: null
depends_on: [ADR-0036, ADR-0012, ADR-0032]
related_to: []
affects_modules: [tests/features, tests/bdd]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [pixel-assertions, eyeball-verification]
---

# ADR-0039: UI acceptance criteria are archetype-anchored and sorted into three test buckets

## Context

UI ACs risk being either brittle ("form has max-width 440px" breaks when a
designer touches a token) or unfalsifiable ("looks professional" verified by
eye and reported as a passing test). Both fail the project's RED→GREEN
discipline.

## Decision

A `.feature` file names the layout archetype and observable behaviour, never
pixel values — the size/visual contract belongs to the archetype and its
design tokens. Every UI AC is sorted at spec review into one of three
buckets (`docs/FRONTEND.md` §9): **structural/contract** (verified
in-process via TestClient), **rendered behaviour/size/interaction** (real
browser via Playwright, `@pytest.mark.ui`, `make test-ui`), and
**irreducibly aesthetic** (explicit manual `[REVIEW]` — never a faked
automated pass). Browser tests run on the macOS host against a uvicorn
live-server fixture bound to the test database, preserving the app/test
session isolation of ADR-0032.

## Rationale

Anchoring to the archetype keeps specs stakeholder-readable and decouples
them from tokens: "a designer changing a token must not break a feature
file." The bucket sort keeps the AC lifecycle honest — buckets 1–2 follow
`not_covered → covered → test_passed`; bucket 3 is recorded as manual
verification, because "a criterion checked only by eye is an unfalsifiable
gate." A `.feature` leaning entirely on bucket 3 for observable behaviour is
a testability smell to escalate at spec review.

## Consequences

### Positive

- UI work stays inside RED→GREEN; the BDD chain
  (AC ← scenario ← step def ← implementation) holds for UI exactly as for
  services.

### Negative

- A browser tier enters the stack (pytest-playwright + vendored browser
  binaries) with its own speed/flakiness budget, kept out of the default
  `make test` run.

## Alternatives considered

### pixel-assertions

Literal sizes in `.feature`/tests: brittle, implementation-detail-level, not
stakeholder-readable.

### eyeball-verification

Manual checking reported as test passes — the "faked automated pass" the
three-bucket rule exists to prevent.
