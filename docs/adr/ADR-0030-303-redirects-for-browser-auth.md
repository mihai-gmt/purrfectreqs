---
id: ADR-0030
title: 303 redirects for browser login/logout, not HTMX HX-Redirect
status: accepted
date: 2026-04-22
backfilled: true
deciders: [mihai]
tags: [security, auth, frontend]

supersedes: []
superseded_by: null
depends_on: [ADR-0028]
related_to: [ADR-0002]
affects_modules: [app/auth, app/templates]
governed_by: [docs/SECURITY.md, docs/FRONTEND.md]
rejected_alternatives: [hx-redirect-header]
---

# ADR-0030: 303 redirects for browser login/logout, not HTMX HX-Redirect

## Context

Browser login and logout need a post-action navigation. The HTMX-native
option is returning an `HX-Redirect` response header for the client library
to act on; the plain-HTTP option is a real 303 redirect.

## Decision

Browser-path auth endpoints return HTTP 303 See Other: login redirects to
`POST_LOGIN_REDIRECT_URL` (env var, default `/` — the security doc shouldn't
know the app's landing page), logout clears both cookies and redirects to
`/auth/login`, register redirects to `/auth/login`. Auth forms work as plain
HTML form posts; HTMX riding the same flow follows the redirect as a full
navigation.

## Rationale

From the journal: "Login is the one page where progressive enhancement
actually matters; silent success if HTMX fails is the worst failure mode for
a login page." A 303 works with JavaScript disabled, broken, or blocked;
`HX-Redirect` only works when the HTMX script executed. The exception is
`/auth/refresh`, which is called from inside the authenticated app and
returns 200 with new cookies — no redirect.

## Consequences

### Positive

- Auth flows are dependable plain-HTTP; no JS execution is load-bearing for
  getting in or out of the app.

### Negative

- No fragment-swap finesse on login/logout — full navigations by design
  (`docs/FRONTEND.md` §6: a post-login 303 lands as full navigation, never a
  partial swap).

## Alternatives considered

### hx-redirect-header

Rejected for auth: it inverts the progressive-enhancement dependency by
making a script the precondition for the security-critical flow completing
visibly.
