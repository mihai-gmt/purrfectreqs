---
id: ADR-0037
title: hx-boost as the default navigation model; targeted swaps only where they earn it
status: accepted
date: 2026-06-14
backfilled: true
deciders: [mihai]
tags: [frontend, htmx, ux]

supersedes: []
superseded_by: null
depends_on: [ADR-0002]
related_to: [ADR-0029, ADR-0030]
affects_modules: [app/templates]
governed_by: [docs/FRONTEND.md, docs/SECURITY.md]
rejected_alternatives: [per-element-htmx-wiring, plain-mpa-navigation]
---

# ADR-0037: hx-boost as the default navigation model; targeted swaps only where they earn it

## Context

An HTMX app can wire every interaction explicitly (`hx-get`/`hx-target` on
each element) or boost ordinary links and forms wholesale. The choice sets
the default cost of every future screen.

## Decision

`hx-boost` on the shell is the default: normal `<a>`/`<form>` navigation is
intercepted and the body swapped via AJAX. Explicit `hx-get`/`hx-post` +
`hx-target` partial swaps are reserved for where a small swap genuinely beats
a boosted page load: the requirement tree, inline validation, the inspector
pane, search-as-you-type — always targeting the smallest element that
changes. Bound to the read/write rule: reads are boosted GETs; every mutation
is `hx-post`/`hx-put`/`hx-patch`/`hx-delete` or a real POST form, and
state-changing actions never degrade to a GET link.

## Rationale

Boosting delivers the app-like feel (no white flash, preserved scroll) with
"almost none of the per-element HTMX wiring," and degrades to ordinary
full-page navigation without JavaScript — progressive enhancement for free
(`docs/FRONTEND.md` §3). The read/write rule is not style: it is the
precondition that keeps SameSite=Lax a sufficient CSRF defense (ADR-0029).

## Consequences

### Positive

- New screens get dynamic navigation by default with plain HTML; partial-swap
  complexity is opt-in and localised.

### Negative

- Boosted navigation swaps whole bodies — focus/scroll preservation and
  loading indicators still need per-case attention (`docs/FRONTEND.md` §7.4).

## Alternatives considered

### per-element-htmx-wiring

Explicit attributes everywhere: maximal control, but every link/form becomes
hand-wired surface area, and a missed element silently falls back
inconsistently.

### plain-mpa-navigation

No HTMX at all would work (progressive enhancement guarantees it) but gives
up the responsiveness that justified HTMX in the stack.
