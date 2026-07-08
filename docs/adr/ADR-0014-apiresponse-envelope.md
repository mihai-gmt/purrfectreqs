---
id: ADR-0014
title: ApiResponse[T] envelope for all API success responses
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [api, conventions]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0015]
affects_modules: [app/core]
governed_by: [docs/GUIDE.md, CLAUDE.md]
rejected_alternatives: [bare-payload-responses]
---

# ADR-0014: ApiResponse[T] envelope for all API success responses

## Context

Without a convention, each endpoint invents its own response shape, and
cross-cutting fields (human-readable message, correlation id) end up
duplicated inconsistently across module schemas.

## Decision

Every API success response is wrapped in the generic `ApiResponse[T]` envelope
from `app/core/schemas.py`: `data` (endpoint-specific payload), `message`,
`correlation_id`. Module schemas define only the `data` payload — never
`message` or `correlation_id`. Routers do the wrapping. Error responses keep
their own consistent shape via `app/core/exceptions.py` (`error_code`,
`message`, `correlation_id`, `details`).

## Rationale

One envelope means clients (including the HTMX frontend and future API
consumers) parse every success response the same way, and the correlation id
is guaranteed present for end-to-end tracing (`docs/GUIDE.md`, Success
Response Format). Keeping the envelope out of module schemas prevents the
duplication drift the rule exists to stop.

## Consequences

### Positive

- Uniform client parsing; tracing metadata cannot be forgotten per endpoint.
- Pydantic generics give typed payloads (`ApiResponse[UserData]`) in OpenAPI.

### Negative

- Every payload is one level deeper (`response.data.x`), and endpoints that
  return HTML fragments (HTMX) sit outside the envelope by nature — the
  envelope governs JSON responses only.

## Alternatives considered

### bare-payload-responses

Returning module schemas directly was rejected: message and correlation
fields would either disappear or be re-declared per schema, drifting apart
across modules.
