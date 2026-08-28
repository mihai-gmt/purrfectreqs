---
id: ADR-0051
title: The MVP shell adds no new interaction mechanism - native keyboard, no splitters, no palette
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, accessibility, scope]

supersedes: []
superseded_by: null
depends_on: [ADR-0038]
related_to: [ADR-0046, ADR-0047]
affects_modules: [app/templates, app/static]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [roving-tabindex-outline, command-palette, draggable-splitters]
---

# ADR-0051: The MVP shell adds no new interaction mechanism - native keyboard, no splitters, no palette

## Context

The shell prototype carried an acceptance criterion that arrow keys walk items
and columns without the mouse. It also stated that splitter handles "can exist
on top" and would need a `docs/FRONTEND.md` §8 escalation. The UX research names
speed and click count as pain 1 and pain 5, which argues for a command palette.

None of the three exists in a governed document, and no module beyond auth has
code. Each of the three needs client-side JavaScript, which ADR-0038 and
`docs/TECH_STACK.md` restrict to Alpine CSP components and the Ace island.

## Decision

The MVP shell adds no interaction mechanism beyond the browser's own.

- **Keyboard support is native.** Semantic elements, correct focus order, a
  visible focus ring, a skip link, and every control reachable by `Tab`.
- **No roving `tabindex`** and no arrow-key traversal of the outline.
- **No command palette.**
- **No splitters.** Pane widths come from the design tokens.

Each of the three refused items may return as a §8 escalation after the native
baseline ships and a real screen shows the need.

## Rationale

The native baseline is required anyway by the §7 checklist, and it must be
correct before any enhancement sits on top of it. A roving `tabindex` built over
a broken focus order hides the defect rather than fixing it.

Splitters lost their justification. They existed in the prototype to widen an
authoring pane; ADR-0046 gives authoring its own full-width route. A splitter
now buys preference, at the cost of drag state, a stored width, and a touch
target that fails at 320 px.

## Consequences

### Positive

- No new JavaScript, so the strict CSP surface does not grow.
- The accessibility baseline is a decision, not a later pass.
- Three recurring "wouldn't it be nice" requests have a written answer.

### Negative

- Keyboard-heavy users get `Tab` and nothing better. This is a real cost for the
  power user the research describes.
- The prototype's arrow-key acceptance criterion is not met, so it must not be
  copied into a `.feature` file.

## Alternatives considered

### roving-tabindex-outline

Arrow keys move a single tab stop through groups and requirements, through an
Alpine CSP component. Rejected for the MVP only: it is the first candidate to
return once the outline ships and the native baseline is verified.

### command-palette

A keyboard jump to any project, requirement, or module. Rejected: it needs a
search endpoint and a JavaScript island, and it is worth building only when
there is enough data to search.

### draggable-splitters

User-dragged pane widths. Rejected: ADR-0046 removed the need, and drag state
plus a stored width plus a 320 px touch target is a cost with no remaining
benefit.
