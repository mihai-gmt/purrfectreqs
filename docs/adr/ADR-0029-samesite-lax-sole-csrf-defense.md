---
id: ADR-0029
title: SameSite=Lax as sole CSRF defense, with a hard no-state-changing-GET rule
status: accepted
date: 2026-04-22
backfilled: true
deciders: [mihai]
tags: [security, csrf, frontend]

supersedes: [ADR-0027]
superseded_by: null
depends_on: [ADR-0028]
related_to: []
affects_modules: [app/auth]
governed_by: [docs/SECURITY.md]
rejected_alternatives: [csrf-library, double-submit-cookie]
---

# ADR-0029: SameSite=Lax as sole CSRF defense, with a hard no-state-changing-GET rule

## Context

The day after adopting double-submit tokens (ADR-0027), the CSRF design was
re-derived from first principles. Two wrong premises in the initial "we're
already covered" reasoning had to be corrected on the way (journal
2026-04-22): **HttpOnly is not a CSRF defense** (CSRF never reads the cookie
— the browser attaches it), and **CORS is not a CSRF defense** for HTMX forms
(CORS governs response *reading*; HTMX posts `x-www-form-urlencoded`, no
preflight, so the request still lands).

## Decision

`SameSite=Lax` on all auth cookies is the sole CSRF defense — no CSRF tokens,
no CSRF library. Its load-bearing companion is a hard rule: state-changing
actions are POST/PUT/PATCH/DELETE only; a GET must never mutate anything.
Four preconditions are recorded in `docs/SECURITY.md` §9 (no mutating GETs,
single origin, HTTPS outside dev, modern browsers) — if any stops holding,
the decision must be revisited.

## Rationale

`SameSite=Lax` makes the browser omit auth cookies on cross-site unsafe
methods, blocking classic CSRF before it reaches the server. The named reason
for the GET rule: inbound email/IM links land as *top-level GET navigations*,
on which Lax deliberately does send cookies — so any mutating GET is a CSRF
hole waiting for a crafted link. Since the defense is Lax *alone*, there is
no backstop: the design trades token machinery for one strictly enforced
invariant.

## Consequences

### Positive

- No token generation/embedding/verification anywhere; HTMX forms need no
  hidden-field threading.

### Negative

- One misconfigured cookie or one mutating GET endpoint is an instant hole —
  the invariant needs tests and review vigilance, and no-JS fallbacks for
  logout/delete must be POST forms, never links (`docs/FRONTEND.md` §3).

## Alternatives considered

### csrf-library

`fastapi-csrf-protect` rejected without a maintenance evaluation — "we don't
need it" once the Lax analysis held.

### double-submit-cookie

The ADR-0027 design. Correct but redundant under the preconditions;
TECH_STACK's detailed section was replaced with a pointer to SECURITY §9
because two sources of truth always drift.
