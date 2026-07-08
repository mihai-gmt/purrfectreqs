---
id: ADR-0032
title: BDD tests give the app its own DB session, separate from the test's session
status: accepted
date: 2026-04-22
backfilled: true
deciders: [mihai]
tags: [testing, database]

supersedes: []
superseded_by: null
depends_on: [ADR-0012]
related_to: [ADR-0031]
affects_modules: [tests/bdd]
governed_by: [CLAUDE.md, docs/GUIDE.md]
rejected_alternatives: [shared-session-with-mirrored-semantics]
---

# ADR-0032: BDD tests give the app its own DB session, separate from the test's session

## Context

The failed-login-counter bug (see ADR-0031) had a passing BDD test — because
the test conftest handed the app *the same session* the test asserted
through. The app's flushed-but-rolled-back write was visible to the test's
re-query, since both read the same uncommitted transaction. The test "had
always passed. It would have continued to pass forever, for a feature that
never worked in production" (journal 2026-04-22).

## Decision

The BDD `client` fixture builds a dedicated `async_sessionmaker` for the app:
the `get_db` override manufactures a fresh session per request with full
production try/commit/except/rollback semantics. The test's own `db_session`
is only for `@given` setup writes (which must `.commit()` to become visible
to the app) and `@then` assertions (which must `expire_all()` to see what the
app committed). The only coupling between app and test is committed state.

## Rationale

"The app sees the DB the way production sees it; the test sees the DB the way
any external observer sees it" (journal). Test-infrastructure mistakes that
make bugs invisible are worse than the bugs — the suite is the instrument
that reports whether anything is broken, and an instrument that lies is worse
than none.

## Consequences

### Positive

- Transaction-boundary bugs (flush-vs-commit, rollback behaviour) are
  observable by tests instead of masked by shared state.

### Negative

- Fixtures are more elaborate, and `@given`/`@then` steps must remember
  commit/expire calls (documented in the conftest docstrings).

## Alternatives considered

### shared-session-with-mirrored-semantics

Wrapping the shared-session override in try/commit/rollback "would have
caught this specific bug and nothing else" — the deeper flaw, one session
serving two observers, would remain.
