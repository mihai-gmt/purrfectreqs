---
id: ADR-0047
title: The module rail has a global section and a project section; it stands by default
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, navigation, accessibility]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0045, ADR-0046]
affects_modules: [app/templates]
governed_by: [docs/FRONTEND.md, docs/GLOSSARY.md]
rejected_alternatives: [disabled-entries, two-level-navigation, hidden-pinnable-rail]
---

# ADR-0047: The module rail has a global section and a project section; it stands by default

## Context

ADR-0045 made Intake the eighth module. Five of the eight modules — Requirements,
Intake, Documents, Gherkin, Traceability — are meaningless without an active
project; only Projects and Admin are global. `docs/FRONTEND.md` described the
rail as one flat list with no scoping concept, so what a project-scoped entry
does with no project selected was undefined. Separately, the shell prototype hid
the rail at every width and made it pinnable, while the standard hid it only
below ~768 px.

## Decision

The rail has two sections. The global section holds Projects and Admin and is
always present. The project section holds the five project-scoped modules, is
rendered only when a project is active, and is headed by the project's name.
With no active project the section is absent, not disabled, and a project-scoped
URL without a project sends the user to Projects. NLP/Analysis is not a rail
entry; it is the inspector of archetype 3. The rail stands at ≥768 px and is
hidden only by the responsive collapse.

## Rationale

Absence is honest and a disabled control is not: a greyed-out entry invites a
click that does nothing and teaches the user to distrust the nav. Naming the
project as the section heading also answers "which project am I in?" without
spending a breadcrumb on it.

The rail was hidden in the prototype to buy width for a sliding column window
that ADR-0042 removed and for an editor that ADR-0046 moved to its own route.
The pressure that justified hiding it is gone, and a hidden main navigation
carries a real accessibility obligation under `docs/FRONTEND.md` §7.9. Keeping it
visible is both simpler and safer.

## Consequences

### Positive

- The rail states where the user is, without a separate project indicator.
- No dead controls, and no undefined click.
- No pin state to store, restore, or test.

### Negative

- The rail's contents change as the user moves between projects, so it is not a
  static partial. It re-renders on project change.
- A user who wants maximum width at a wide viewport cannot reclaim the rail's
  space. Archetype 6 exists for the one case where that matters.

## Alternatives considered

### disabled-entries

Showing all eight entries and disabling the project-scoped ones was rejected: a
disabled control is a promise the UI does not keep.

### two-level-navigation

A global rail plus a second navigation inside a project was rejected: it adds a
navigation level to save a section heading.

### hidden-pinnable-rail

The prototype's hidden-by-default, pinnable rail was rejected: the width pressure
that motivated it no longer exists, and hiding the main navigation at every width
takes on an accessibility obligation for no remaining gain.
