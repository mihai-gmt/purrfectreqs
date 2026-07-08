---
id: ADR-0027
title: Double-submit CSRF tokens on login and register
status: superseded
date: 2026-04-21
backfilled: true
deciders: [mihai]
tags: [security, auth, csrf]

supersedes: []
superseded_by: ADR-0029
depends_on: []
related_to: []
affects_modules: [app/auth]
governed_by: [docs/SECURITY.md]
rejected_alternatives: []
---

# ADR-0027: Double-submit CSRF tokens on login and register

## Context

During the 2026-04-21 TECH_STACK.md review the question arose: does CSRF
apply to `POST /auth/login` and `POST /auth/register` when no session exists
yet? Yes — login CSRF: an attacker forges a login request to log a victim
into an attacker-controlled account, then observes everything the victim does
in that account.

## Decision

(As made on 2026-04-21, since superseded.) The corresponding `GET` endpoint
sets a `csrf_token` cookie and renders the same token as a hidden form field;
the `POST` rejects the request if the two do not match. `SameSite=Lax` was
noted as supplementary, not a replacement.

## Rationale

The double-submit cookie pattern was the textbook answer to login CSRF at the
time of the review. It was written into TECH_STACK.md's CSRF section in
detail.

## Consequences

### Positive

- Recognised the login-CSRF threat on pre-session endpoints — the threat
  model survives into the superseding decision.

### Negative

- Added token generation, embedding, and verification machinery that the next
  day's analysis showed to be unnecessary given `SameSite=Lax` plus the
  no-state-changing-GET rule. Superseded by ADR-0029 on 2026-04-22; the
  detailed TECH_STACK CSRF section was replaced with a pointer to
  `docs/SECURITY.md` §9 ("two sources of truth always drift").

## Alternatives considered

None recorded at decision time; the fuller alternatives analysis happened in
the superseding decision.
