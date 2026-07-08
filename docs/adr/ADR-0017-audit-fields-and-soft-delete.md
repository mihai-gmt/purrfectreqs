---
id: ADR-0017
title: Mandatory audit fields on every table; soft delete for user content
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [database, conventions]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0016, ADR-0018]
affects_modules: [app]
governed_by: [docs/DATA_MODELS.md, CLAUDE.md]
rejected_alternatives: [hard-delete-everywhere]
---

# ADR-0017: Mandatory audit fields on every table; soft delete for user content

## Context

A requirements management system is a system of record: who changed what, and
when, is product functionality, not an afterthought. Destroyed user content
(requirements, projects, documents) is unrecoverable and breaks traceability
links that reference it.

## Decision

Every table carries `created_at`, `updated_at`, `created_by`, `updated_by`.
Tables storing user-created content additionally carry `is_deleted`,
`deleted_at`, `deleted_by` and are soft-deleted. Hard deletes are permitted
only for refresh tokens, expired session data, and temporary processing
records.

## Rationale

Uniform audit fields make "who/when" queryable on any row without joins to
the audit log, and soft delete preserves referential integrity for
traceability links and history (`docs/DATA_MODELS.md`, Global Rules). The
hard-delete exceptions are precisely the rows with no audit value and real
hygiene cost (token table growth).

## Consequences

### Positive

- Recoverable deletions; intact link graphs; per-row provenance.

### Negative

- Every read query must filter `is_deleted` (a forgotten filter shows deleted
  data — a recurring class of bug to test for).
- Unique constraints interact awkwardly with soft-deleted rows (a "deleted"
  name still occupies the constraint).

## Alternatives considered

### hard-delete-everywhere

Simpler queries, but destroys history and dangles traceability references;
unacceptable for a system whose purpose is tracking requirement provenance.
