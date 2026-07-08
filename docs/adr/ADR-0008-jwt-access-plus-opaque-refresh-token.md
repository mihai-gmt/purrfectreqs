---
id: ADR-0008
title: JWT access token plus opaque DB-backed refresh token
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [security, auth]

supersedes: []
superseded_by: null
depends_on: []
related_to: []
affects_modules: [app/auth]
governed_by: [docs/SECURITY.md]
rejected_alternatives: [jwt-refresh-token, in-memory-revocation]
---

# ADR-0008: JWT access token plus opaque DB-backed refresh token

## Context

The system needs stateless request authentication and the ability to revoke
sessions instantly (logout, admin action, lockout). Pure-JWT designs make
revocation awkward: a JWT is valid until expiry unless a server-side denylist
is consulted anyway.

## Decision

Short-lived JWT access tokens (HS256, 15 minutes, `jti` claim) paired with
opaque, cryptographically random refresh tokens (7 days). Refresh tokens are
stored server-side only as SHA-256 hashes, rotated on every refresh (old token
revoked, `replaced_by` linkage), and all of a user's tokens are revoked on
logout or new login — single-session enforcement. Revocation is
database-driven, never in-memory.

## Rationale

"Industry standard; opaque refresh token avoids JWT revocation complexity"
(`docs/ARCHITECTURE.md`, Decision Log). The 15-minute access window bounds the
damage of a leaked JWT without a denylist; the DB-backed refresh token is the
revocation point. Hash-only storage means a database leak does not yield
usable tokens (`docs/SECURITY.md` §1).

## Consequences

### Positive

- Instant, reliable revocation; rotation detects token replay.
- Access-token validation stays stateless and fast.

### Negative

- Refresh flow costs a DB round-trip; refresh_tokens rows need hard-delete
  hygiene after expiry.
- Concurrent sessions are impossible by design in MVP.

## Alternatives considered

### jwt-refresh-token

A JWT refresh token would need a server-side denylist to be revocable —
recreating the database dependency while adding JWT parsing complexity.

### in-memory-revocation

Explicitly prohibited (`CLAUDE.md`): revocation state must survive restarts
and be shared across future instances.
