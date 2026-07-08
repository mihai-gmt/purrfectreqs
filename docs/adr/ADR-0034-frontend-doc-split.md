---
id: ADR-0034
title: Frontend guidance split into docs/FRONTEND.md for context economy
status: accepted
date: 2026-06-14
backfilled: true
deciders: [mihai]
tags: [process, documentation, frontend]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0002]
affects_modules: []
governed_by: [CLAUDE.md]
rejected_alternatives: [grow-guide-md]
---

# ADR-0034: Frontend guidance split into docs/FRONTEND.md for context economy

## Context

`docs/GUIDE.md` had become a mixed document: backend patterns plus a ~90-line
UI checklist. Only `CLAUDE.md` is auto-loaded; everything in `docs/` is read
on demand — so a backend task loaded typography/HTMX rules it never used, and
a UI task loaded correlation-ID/SQLAlchemy patterns it never used. The cost
cut both directions (journal 2026-06-14).

## Decision

All frontend guidance lives in `docs/FRONTEND.md` (design principles, app
shell, navigation model, template/component architecture, design tokens, UI
checklist), registered at authority rank 8 in `CLAUDE.md`. `GUIDE.md` keeps
stub pointers. Peer docs cross-reference reciprocally, and frontend
escalation triggers appear in both FRONTEND.md §8 and the central CLAUDE.md
escalation table.

## Rationale

The docs already separate invariants (`ARCHITECTURE.md`) from patterns
(`GUIDE.md`) and defer rather than duplicate (TECH_STACK punts CSRF to
SECURITY §9); frontend obeys the same split instead of becoming a fourth
mixed pattern. The 2026-06-14 cross-check session also proved the split's
value: comparing the new doc against SECURITY.md surfaced two real
contradictions and the CSP-consequences gap before any code was written.

## Consequences

### Positive

- UI work loads UI context only, and vice versa; a single home for frontend
  rules makes drift detectable.

### Negative

- One more authority-ranked document to keep reciprocally cross-referenced —
  embedding it took a deliberate audit (4 missing inbound references found).

## Alternatives considered

### grow-guide-md

Keeping one how-to-code doc was rejected: a mixed doc taxes every task with
the other half's content, and the tax grows with each addition.
