---
id: ADR-0028
title: Dual auth delivery — HttpOnly cookies for the browser, Bearer header for API clients
status: accepted
date: 2026-04-22
backfilled: true
deciders: [mihai]
tags: [security, auth, frontend]

supersedes: []
superseded_by: null
depends_on: [ADR-0008, ADR-0002]
related_to: [ADR-0029]
affects_modules: [app/auth]
governed_by: [docs/SECURITY.md]
rejected_alternatives: [localstorage-tokens, single-delivery-path]
---

# ADR-0028: Dual auth delivery — HttpOnly cookies for the browser, Bearer header for API clients

## Context

The same FastAPI app serves a server-rendered HTMX UI and a JSON API. Browser
auth must not depend on JavaScript-readable tokens (XSS exposure), while API
clients (curl, scripts, integrations) work naturally with bearer headers, not
cookie jars. This was one of three blockers resolved at the start of the UI
security session (journal 2026-04-22).

## Decision

Content negotiation on `Accept` selects the path. Browser (`text/html`):
tokens in HTTP-only cookies — `access_token` (`HttpOnly; Secure;
SameSite=Lax; Path=/`) and `refresh_token` (same, `Path=/auth/refresh`);
`Secure` is env-conditional for localhost dev. API (`application/json`):
tokens in the response body, attached by the client as `Authorization:
Bearer`. `get_current_user` resolves **header first, cookie second**. Tokens
never touch localStorage, sessionStorage, or JavaScript variables.

## Rationale

HttpOnly cookies remove the token from XSS reach entirely for the browser,
while the body/header path "matches how API clients actually work; cookie
jars are unusual for them" (journal). Header-first resolution exists for a
specific failure mode: a stray browser cookie on the same host must never
affect an API client's request. The refresh cookie's narrow
`Path=/auth/refresh` keeps it off every other request.

## Consequences

### Positive

- Browser tokens are invisible to scripts; both client types get their
  idiomatic flow from one endpoint set.

### Negative

- Every auth endpoint implements two response shapes (cookies+303 vs JSON),
  doubling test surface (`docs/SECURITY.md` §14 is the reference table).

## Alternatives considered

### localstorage-tokens

Prohibited outright: any XSS reads localStorage; HttpOnly cookies are
specifically immune to that.

### single-delivery-path

Cookies-only would force cookie jars on scripts; header-only would put tokens
in browser JavaScript. Neither client type should pay the other's cost.
