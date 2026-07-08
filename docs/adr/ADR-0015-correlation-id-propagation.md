---
id: ADR-0015
title: Correlation ID propagated through every request, service call, and log
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [observability, conventions]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0014, ADR-0018]
affects_modules: [app/core]
governed_by: [CLAUDE.md, docs/GUIDE.md]
rejected_alternatives: []
---

# ADR-0015: Correlation ID propagated through every request, service call, and log

## Context

Debugging a request that crosses middleware, router, service, database, and
audit log requires stitching those records together. Structured logs ship to
Loki/Grafana; without a shared key, tracing a single request through them is
guesswork.

## Decision

Every API endpoint, service function, audit log entry, and error response
includes and propagates a UUID correlation ID. Middleware reads
`X-Correlation-ID` from the request (clients may supply their own for
end-to-end tracing) or generates a UUID; the `get_correlation_id` dependency
exposes it to endpoints; the same ID is echoed in the `X-Correlation-ID`
response header, in the `ApiResponse` envelope, in every log entry, and in
`audit_logs.correlation_id`.

## Rationale

A single key that survives the whole request path turns "what happened?" into
one Grafana/SQL filter (`docs/GUIDE.md`, Correlation ID flow). Accepting a
client-supplied ID extends the trace across system boundaries. Making
propagation a hard rule for every new function (`CLAUDE.md` invariant) is
what keeps the chain unbroken — one missing link breaks the trace.

## Consequences

### Positive

- One filter correlates logs, audit rows, and API responses per request.

### Negative

- Every service function signature carries a `correlation_id` parameter —
  boilerplate accepted deliberately in exchange for traceability.

## Alternatives considered

None recorded — the pattern was adopted as a baseline convention at project
inception rather than weighed against alternatives (e.g. contextvars-based
implicit propagation), which would be a separate proposal if the parameter
boilerplate ever becomes a real cost.
