---
id: ADR-0013
title: PicoCSS as styling baseline, accepting the upstream freeze as MVP risk
status: accepted
date: 2026-04-21
backfilled: true
deciders: [mihai]
tags: [frontend, dependencies, risk]

supersedes: []
superseded_by: null
depends_on: [ADR-0002]
related_to: []
affects_modules: [app/static, app/templates]
governed_by: [docs/TECH_STACK.md, docs/FRONTEND.md]
rejected_alternatives: [tailwindcss, bootstrap, daisyui]
---

# ADR-0013: PicoCSS as styling baseline, accepting the upstream freeze as MVP risk

## Context

The server-rendered UI needs a CSS baseline without build tooling. While
vendoring PicoCSS 2.1.1 (2026-04-21), the developer found that both `main`
and `dev` upstream branches had no commits for over 12 months — not
"feature-complete quiet, actually frozen" (journal 2026-04-21).

## Decision

PicoCSS 2.1.1 remains the styling baseline, vendored locally. Custom CSS is
limited to `app/static/css/app.css` for the sanctioned uses in
`docs/FRONTEND.md` §5. Revisit the choice if (a) a browser change breaks
rendering, (b) a needed feature is missing, or (c) a security advisory hits
the vendored version (`docs/TECH_STACK.md`, PicoCSS Maintenance Note).

## Rationale

From the journal: starting greenfield on a frozen library "is a mild bet
against the future," but CSS is one of the most swappable layers in the
stack, PicoCSS is semantically scoped with no runtime and no transitive
dependencies, any bug can be patched in place, and the whole point of
choosing it over Tailwind/Bootstrap was to minimise frontend decisions so
focus stays on the Python/NLP/LLM work. A clean Snyk report closed the
decision.

## Consequences

### Positive

- Semantic classes on plain HTML; no utility-class sprawl, no build step.

### Negative

- No upstream fixes are coming; the project owns any patch to the vendored
  file (via `app.css` overrides — never editing `pico.min.css`).

## Alternatives considered

### tailwindcss

Adds frontend build/tooling pressure and utility-class sprawl; misfit for a
semantic server-rendered UI.

### bootstrap

More visual/component weight than the MVP needs.

### daisyui

Tailwind-based component abstraction; inherits Tailwind's tooling cost plus
another dependency layer.
