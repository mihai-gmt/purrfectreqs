---
id: ADR-0019
title: Honeypot field for bot protection on public forms, no CAPTCHA
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [security, frontend, auth]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0011]
affects_modules: [app/auth, app/templates, app/static]
governed_by: [docs/SECURITY.md, docs/FRONTEND.md]
rejected_alternatives: [captcha]
---

# ADR-0019: Honeypot field for bot protection on public forms, no CAPTCHA

## Context

Self-registration is a public endpoint and therefore a bot target. The system
is offline-first, so third-party CAPTCHA services (reCAPTCHA, hCaptcha) would
contradict the no-external-calls posture and add friction for legitimate
users.

## Decision

Public-facing forms carry a hidden honeypot field (hidden via a CSS class in
`app.css` — the CSP forbids inline styles). If the field arrives populated,
the server responds exactly as if the submission succeeded, logs the event at
WARNING with correlation ID, and does not create the account. The field
carries `tabindex="-1"`, `aria-hidden="true"`, `autocomplete="off"` so it
never traps keyboard or screen-reader users (`docs/FRONTEND.md` §6).

## Rationale

Bots auto-fill every field; humans never see the hidden one
(`docs/SECURITY.md` §11). Responding with fake success denies bots the
feedback loop they need to adapt. Rate limiting (5/min/IP on register)
already bounds volume; the honeypot removes the low-effort remainder without
any user-visible cost or external dependency.

## Consequences

### Positive

- Zero friction for real users; no third-party service; works offline.

### Negative

- Weak against targeted attackers who inspect the form — accepted, because
  rate limiting and password policy are the real controls; the honeypot only
  filters indiscriminate bots.

## Alternatives considered

### captcha

Third-party CAPTCHA rejected: external dependency contradicting the
offline-first design, accessibility cost, and unnecessary at MVP threat
levels.
