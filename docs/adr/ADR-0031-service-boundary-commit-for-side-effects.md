---
id: ADR-0031
title: Side effects that must survive exceptions commit explicitly at the service boundary
status: accepted
date: 2026-04-22
backfilled: true
deciders: [mihai]
tags: [database, patterns, testing]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0032]
affects_modules: [app/auth, app/core]
governed_by: [docs/GUIDE.md]
rejected_alternatives: [router-level-catch, get-db-business-exceptions]
---

# ADR-0031: Side effects that must survive exceptions commit explicitly at the service boundary

## Context

The failed-login counter stayed at zero through eight wrong-password attempts
(journal 2026-04-22). The service incremented the counter, called
`db.flush()`, then raised `InvalidCredentialsError` — and the `get_db`
dependency's rollback undid the flushed increment. In SQLAlchemy, flush
synchronises session state into the *current transaction*; it is not commit
(EF Core analogue: `SaveChanges()` inside an uncommitted transaction —
reversible).

## Decision

A side effect whose purpose is to survive a raised exception — the
failed-login counter, the lockout marker — is committed explicitly
(`await db.commit()`) in the service before the exception is raised. The
default `get_db` commit-on-success/rollback-on-exception behaviour is
unchanged for everything else.

## Rationale

The counter "has no business being inside the transaction that the exception
rolls back" — its entire purpose is to accumulate across failures (journal).
Placing the commit in the service keeps transaction boundaries a service-layer
concern, where the business meaning of "this must persist" is known.

## Consequences

### Positive

- Security counters persist through auth failures; the transaction-boundary
  decision sits next to the logic that requires it.

### Negative

- An explicit early commit splits the request's work into two transactions —
  callers must not assume request-level atomicity around such code paths.

## Alternatives considered

### router-level-catch

Catching the exception in the router to let `get_db` commit "bends control
flow to work around a transaction-boundary decision that belongs in the
service."

### get-db-business-exceptions

Teaching `get_db` to commit before re-raising "business" exceptions "leaks
business semantics into shared infrastructure."
