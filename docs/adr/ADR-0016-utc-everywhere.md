---
id: ADR-0016
title: UTC everywhere with timezone-aware datetimes
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [conventions, database]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0017]
affects_modules: [app]
governed_by: [CLAUDE.md, docs/GUIDE.md]
rejected_alternatives: [naive-datetimes]
---

# ADR-0016: UTC everywhere with timezone-aware datetimes

## Context

Timestamps drive security behaviour (token expiry, account lockout windows,
session timeout). Python offers three lookalike ways to get "now" —
`datetime.now()`, `datetime.utcnow()`, `datetime.now(UTC)` — and only one of
them is safe: the first is local-time, the second is deprecated *and* returns
a naive datetime, and comparing naive with aware datetimes raises
`TypeError` at runtime.

## Decision

All timestamps are UTC and timezone-aware, no exceptions. Python code uses
`datetime.now(UTC)`; `datetime.utcnow()` and bare `datetime.now()` are
forbidden. All SQLAlchemy timestamp columns are `DateTime(timezone=True)`.
API responses serialise as ISO 8601 with offset.

## Rationale

Time-delta security logic (lockout expiry, token expiry) silently breaks or
raises when naive and aware datetimes mix (`docs/GUIDE.md`, UTC Time
Standard). Fixing one convention at the column type and call-site level is
cheaper than auditing every comparison. The `utcnow()` trap is specifically
called out because it *looks* correct and is the one a .NET developer
(`DateTime.UtcNow`) reaches for by instinct.

## Consequences

### Positive

- No timezone arithmetic bugs class-wide; DB comparisons are always valid.

### Negative

- Display-local-time becomes purely a presentation concern (acceptable — the
  UI can format at render time).

## Alternatives considered

### naive-datetimes

Storing naive UTC (the `utcnow()` pattern) was rejected: it relies on every
reader remembering an out-of-band "it's UTC, trust me" convention, and it is
deprecated in Python 3.12.
