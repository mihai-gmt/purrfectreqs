---
id: ADR-0018
title: Append-only immutable audit log
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [database, security, admin]

supersedes: []
superseded_by: null
depends_on: [ADR-0015]
related_to: [ADR-0017]
affects_modules: [app/admin]
governed_by: [docs/DATA_MODELS.md, docs/SCOPE.md]
rejected_alternatives: []
---

# ADR-0018: Append-only immutable audit log

## Context

Module 7 (Admin & Audit) promises an audit trail for all data changes. An
audit trail that can itself be edited or pruned is evidence of nothing.

## Decision

`audit_logs` is append-only: rows are never updated or deleted, there is no
soft delete, and the table deliberately omits `updated_at`/`updated_by`. Each
row records table, record id, action type (CREATE/UPDATE/DELETE), old and new
values as JSON, the acting user, the correlation ID, and a timestamp. Every
service-layer create/update/delete writes an entry.

## Rationale

Immutability is what distinguishes an audit log from a change log — the
schema itself (no update columns) encodes the rule rather than trusting code
review to enforce it (`docs/DATA_MODELS.md`, audit_logs notes). Old/new value
JSON makes each row self-contained even after later changes to the source
row; the correlation ID ties the audit entry to the request logs that caused
it.

## Consequences

### Positive

- Trustworthy history; per-request traceability into Loki/Grafana logs via
  correlation ID.

### Negative

- The table grows without bound — retention/archival policy is a future
  operational decision, and exports (an MVP admin feature) are the interim
  answer.
- JSON snapshots duplicate data; storage is traded for self-containment.

## Alternatives considered

None recorded — immutability follows directly from the product requirement
of an audit trail; no competing design was seriously entertained.
