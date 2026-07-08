---
id: ADR-0038
title: Strict CSP with no unsafe-inline/unsafe-eval; Alpine.js only as the CSP build
status: accepted
date: 2026-06-14
backfilled: true
deciders: [mihai]
tags: [security, frontend, csp]

supersedes: []
superseded_by: null
depends_on: [ADR-0002, ADR-0021]
related_to: [ADR-0013]
affects_modules: [app/static, app/templates]
governed_by: [docs/SECURITY.md, docs/TECH_STACK.md, docs/FRONTEND.md]
rejected_alternatives: [alpinejs-default-build, relaxed-csp]
---

# ADR-0038: Strict CSP with no unsafe-inline/unsafe-eval; Alpine.js only as the CSP build

## Context

The security headers mandate `script-src 'self'; style-src 'self'` with no
`'unsafe-inline'` and no `'unsafe-eval'` (`docs/SECURITY.md` §8). Alpine.js
was wanted for ephemeral client state, but its default build evaluates
directive expressions via `Function()` — which requires `'unsafe-eval'` and
meaningfully weakens XSS defense. The 2026-06-14 docs cross-check surfaced
what the strict policy really costs this stack.

## Decision

The CSP stays strict; the stack adapts to it. Alpine.js is permitted only as
the `@alpinejs/csp` build, vendored locally. Components are registered via
`Alpine.data(...)` in `app/static/js/` (no inline scripts); `x-*` attribute
values are static in templates (never interpolating user input — the value is
code, not text); `x-html` is forbidden on user-derived content. No inline
styles anywhere; HTMX's auto-injected `.htmx-indicator` `<style>` block is
disabled via the `htmx-config` meta tag and the rule ships in `app.css`. No
`hx-on`, no `js:` prefixes, no HTMX expression filters. If `'unsafe-eval'` or
`'unsafe-inline'` ever appears in `script-src`, something has crept in — a
blocking review issue.

## Rationale

A strict CSP is cheap to write and expensive to honour; the value is honoring
it. The cross-check found the non-obvious consequence before code did: HTMX's
injected indicator styles are CSP-blocked, so "every mandated loading
indicator renders unstyled" without the meta-tag fix — found by checking docs
against each other, not by debugging a broken form (journal 2026-06-14). The
CSP build replaces `Function()` evaluation with a restricted expression
parser, keeping eval out of the whitelist.

## Consequences

### Positive

- Inline-injection XSS and eval-based gadgets are blocked by policy; the
  CSP-build constraint is enforceable in review (grep for the forbidden
  patterns).

### Negative

- Real ergonomic costs: no inline `x-data` logic (silent failure by design),
  component registration ceremony, and CSP-consequence rules that every
  template author must know (`docs/FRONTEND.md` §6).

## Alternatives considered

### alpinejs-default-build

Requires `'unsafe-eval'` in `script-src` — trading a global XSS-defense layer
for local convenience. Forbidden; must not be vendored or referenced.

### relaxed-csp

Adding `'unsafe-inline'`/`'unsafe-eval'` to accommodate tooling defaults
inverts the priority: the CSP exists to constrain the stack, not the other
way around.
