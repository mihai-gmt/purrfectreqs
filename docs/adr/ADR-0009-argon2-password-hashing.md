---
id: ADR-0009
title: Argon2 via passlib for password hashing
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [security, auth, dependencies]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0008]
affects_modules: [app/auth]
governed_by: [docs/SECURITY.md]
rejected_alternatives: [bcrypt-primary]
---

# ADR-0009: Argon2 via passlib for password hashing

## Context

Password storage needs a modern memory-hard hash. The library choice also
matters: hand-rolling hashing invites parameter mistakes.

## Decision

Passwords are hashed with Argon2 through `passlib[argon2]`. bcrypt remains
available as passlib's automatic verification fallback. Raw passwords are
never stored or logged in any form.

## Rationale

Argon2 "is preferred over bcrypt for resistance to GPU attacks"
(`docs/TECH_STACK.md`, Authentication & Security); it won the Password Hashing
Competition and its memory-hardness resists parallel cracking hardware in a
way bcrypt does not. passlib provides vetted defaults and transparent
algorithm migration on verify.

## Consequences

### Positive

- State-of-the-art at-rest password protection with vetted parameters.
- Old bcrypt hashes (if any ever exist) still verify, enabling gradual
  migration.

### Negative

- Argon2's memory cost is a deliberate CPU/RAM tax on every login — a
  non-issue at MVP scale but a sizing consideration later.

## Alternatives considered

### bcrypt-primary

bcrypt as the primary algorithm was rejected: GPU/ASIC-resistant it is not,
and there was no legacy-hash compatibility requirement pushing toward it.
