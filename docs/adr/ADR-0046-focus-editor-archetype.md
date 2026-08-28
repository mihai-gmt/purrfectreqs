---
id: ADR-0046
title: The archetype catalogue holds six; Focus Editor is a full-width authoring route
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, architecture]

supersedes: []
superseded_by: null
depends_on: [ADR-0036]
related_to: [ADR-0042, ADR-0044]
affects_modules: [app/templates, app/static]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [deep-edit-as-a-mode-of-master-detail, chrome-less-editor, reuse-reading-content]
---

# ADR-0046: The archetype catalogue holds six; Focus Editor is a full-width authoring route

## Context

ADR-0036 closed the page-level layout catalogue at five and made a sixth an
explicit escalation. This ADR is that escalation; ADR-0036's decision — one
archetype per screen, a closed set, additions by escalation — still governs.

ADR-0044 approved the Ace editor "for the deep-edit state", and `docs/SCOPE.md`
and `docs/TECH_STACK.md` both name that state. No archetype described it.
ADR-0042 had already settled the browse half — the master outline needed no
archetype change — but it did not reach the editing surface. Archetypes 2 and 3
keep the master pane, which the editor needs the width of; archetype 4 is for
dense tables; archetype 5 caps at ~720 px for prose. An implementer had a
governed dependency and no governed layout to put it in.

## Decision

Add archetype 6, **Focus Editor**: the app shell is present, the rail and the
master outline yield to a narrow read-only context strip, and the editor fills
the rest. It is its own route, reached by a boosted navigation, so the browser
back button is cancel. The inspector never opens beside it. Short edits stay in
archetype 2's detail pane. The catalogue is closed again at six; a seventh is a
new escalation.

## Rationale

The value of ADR-0036 is that naming an archetype tells the implementer the
layout. A mode inside archetype 2 would have broken that: the spec would then
have to name an archetype and a mode, and the catalogue would stop being a
complete description of page structure.

A different route with a different layout is a different page, not a state of
one. Making it a route also buys cancel for free through the back button, which
is the cheapest possible answer to "I opened the editor by mistake".

## Consequences

### Positive

- The Ace island has a governed home, so ADR-0044 is implementable.
- Cancel costs nothing: it is the back button.
- Naming an archetype still fully determines the layout.

### Negative

- A closed catalogue was reopened. That is a precedent, and the guard against it
  is only that §8 still calls a seventh an escalation.
- One more shell grid variant in `app.css`.

## Alternatives considered

### deep-edit-as-a-mode-of-master-detail

Making it a mode of archetype 2 keeps the catalogue at five. Rejected because a
spec would then have to name an archetype and a mode, which removes the property
that made ADR-0036 worth having.

### chrome-less-editor

Rendering the editor with no shell at all, like the Centred Form. Rejected: the
author needs to see which requirement and which criterion they are formalising,
and a chrome-less page gives no place to say it.

### reuse-reading-content

Archetype 5 was rejected on width. Its ~720 px cap exists for prose line length;
a Gherkin step line is long and must not wrap mid-clause.
