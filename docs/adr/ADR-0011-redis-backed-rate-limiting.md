---
id: ADR-0011
title: Redis-backed rate limiting via fastapi-limiter
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [security, dependencies, infrastructure]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0008]
affects_modules: [app/auth, app/core]
governed_by: [docs/SECURITY.md, docs/TECH_STACK.md]
rejected_alternatives: [in-process-rate-limiting]
---

# ADR-0011: Redis-backed rate limiting via fastapi-limiter

## Context

Public auth endpoints (login, register) are brute-force and enumeration
targets, and AI/NLP endpoints are expensive to invoke. Both need request-rate
enforcement that survives process restarts.

## Decision

Rate limiting uses `fastapi-limiter` with Redis as the backend. Limits are
per-endpoint (`docs/SECURITY.md` §7): 5/min/IP on login and register,
10/min/user on refresh and logout, 3/hour/IP on admin password reset,
100/min/user generally. Stricter limits apply to auth and expensive AI/NLP
endpoints. Redis is not to be used as an implicit application state store;
new caching behaviour is an architectural decision requiring approval.

## Rationale

Counter state must live outside the app process to survive restarts and any
future multi-instance deployment; Redis is the conventional store and
`fastapi-limiter` integrates it with FastAPI dependencies directly
(`docs/TECH_STACK.md`, Rate Limiting & Caching).

## Consequences

### Positive

- Durable, shared rate-limit state; per-endpoint tuning via dependencies.

### Negative

- Redis becomes a hard runtime dependency and one more service to secure
  (password required outside development, `docs/SECURITY.md` §15).

## Alternatives considered

### in-process-rate-limiting

An in-memory limiter was rejected: counters reset on every restart —
defeating lockout-adjacent protections — and cannot be shared if the app ever
scales past one process.
