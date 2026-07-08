---
id: ADR-0010
title: TLS terminates at a reverse proxy, not in the application
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [security, deployment]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0001]
affects_modules: [app/core]
governed_by: [docs/SECURITY.md]
rejected_alternatives: [app-terminates-tls]
---

# ADR-0010: TLS terminates at a reverse proxy, not in the application

## Context

Local development runs plain HTTP, but any public beta/production deployment
must enforce HTTPS, manage certificates, and hide internal services
(PostgreSQL, Redis, Grafana, Loki) from the network.

## Decision

A reverse proxy (Caddy or Nginx) fronts the Docker stack in production/beta:
it terminates TLS, redirects HTTP to HTTPS, and exposes only port 443. The
FastAPI application never terminates TLS. The app trusts
`X-Forwarded-For`/`X-Forwarded-Proto` only from IPs in `TRUSTED_PROXY_IPS`.
The `Secure` cookie flag is conditional on `APP_ENV` so localhost HTTP still
works in development.

## Rationale

"App stays simple; proxy handles certs, redirects, and header injection"
(`docs/ARCHITECTURE.md`, Decision Log). Certificate automation (Let's Encrypt
via Caddy or certbot) is a solved problem at the proxy layer and an ongoing
liability inside an application process.

## Consequences

### Positive

- No certificate code or renewal logic in the app; internal service ports are
  never host-exposed in production.

### Negative

- Production has a component that development doesn't, so proxy-dependent
  behaviour (forwarded headers, HTTPS-only cookies) needs deliberate testing.

## Alternatives considered

### app-terminates-tls

Uvicorn can serve TLS directly, but that puts certificate management,
renewal, and redirect logic into the application and still leaves internal
services to be firewalled separately.
