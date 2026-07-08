---
id: ADR-0002
title: Server-rendered frontend with HTMX + Jinja2, no SPA
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [frontend, architecture]

supersedes: []
superseded_by: null
depends_on: [ADR-0001]
related_to: []
affects_modules: [app/templates, app/static]
governed_by: [docs/FRONTEND.md, docs/TECH_STACK.md]
rejected_alternatives: [react-spa]
---

# ADR-0002: Server-rendered frontend with HTMX + Jinja2, no SPA

## Context

The UI is a dense professional tool for POs/PMs, served by the same FastAPI
process as the API. A separate frontend application would add a build system,
Node.js, a deployment pipeline, and a second source of truth for state — all
for an MVP maintained by one developer.

## Decision

The frontend is server-rendered HTML: Jinja2 templates enhanced with HTMX for
dynamic interactions. No React, no SPA, no client-side routing, no frontend
build step, no npm. Application state lives on the server; HTMX swaps
server-rendered fragments.

## Rationale

"Simpler deployment, no build step, sufficient for requirements management UI"
(`docs/ARCHITECTURE.md`, Decision Log). The server-authoritative model also
eliminates the API/UI state-duplication class of bugs, and the whole stack
stays Python — important for a developer learning the language.

## Consequences

### Positive

- Zero frontend toolchain; templates deploy with the app via `COPY . .`.
- Progressive enhancement: pages degrade to plain HTML forms/links.

### Negative

- Complex client-side interactions need care (HTMX for server round-trips,
  Alpine.js CSP build for ephemeral state — see the Alpine/CSP ADR).
- Rendering load stays on the server.

## Alternatives considered

### react-spa

React/Vite/TypeScript rejected (`docs/TECH_STACK.md`, Explicitly Rejected
Libraries): requires a separate build system, Node.js, and deployment
pipeline; HTMX + Jinja2 is sufficient for this UI.
