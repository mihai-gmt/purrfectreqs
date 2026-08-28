---
id: ADR-0042
title: The master outline holds groups and requirements only; criteria and scenarios live in the detail
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, navigation]

supersedes: []
superseded_by: null
depends_on: [ADR-0040, ADR-0041]
related_to: [ADR-0035, ADR-0036]
affects_modules: [app/templates, app/projects]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [four-level-outline, flat-filtered-list]
---

# ADR-0042: The master outline holds groups and requirements only; criteria and scenarios live in the detail

## Context

With requirements non-nesting (ADR-0040), the master pane needs a shape. The UX
research praises a persistent left tree beside a document view for macro-context
during micro-edits, and names tree pagination as a specific frustration
(`_TEMP/ux_research/synthesis/20260713/findings.yaml`, cluster
`loved-explorer-tree`). The shell prototype's detail pane already renders a
requirement's criteria and its scenarios together.

## Decision

The master pane holds a two-level outline: a group heading from the current
group-by axis, then the requirements inside it. The default axis is the source
document; the user switches axis with one control. Criteria and scenarios are not
outline nodes — the detail pane renders the selected requirement as a document
containing its criteria, each with its scenarios. The outline never paginates and
holds titles only; groups expand with `hx-get`. This is `docs/FRONTEND.md`
archetype 2 unchanged, so the closed catalogue keeps five entries.

## Rationale

Putting criteria and scenarios in the outline renders the same objects twice, in
two panes, and forces them to stay in sync on every edit; a requirement with
eight criteria and twenty scenarios would also make the outline unreadable. The
research finding is specifically about a tree for macro-context beside a document
for micro-editing, which is this split. Group-by is load-bearing rather than
decorative: without it the outline root is every requirement in the project.

## Consequences

### Positive

- The layout archetype catalogue and ADR-0036 need no amendment.
- No duplicated rendering and no cross-pane synchronisation.
- Re-pivoting the group-by axis is a view change, so no data moves.

### Negative

- Jumping straight to one scenario from navigation needs an in-document anchor
  or search, not a nav click.
- The group-by control and its default are now required for a usable screen.

## Alternatives considered

### four-level-outline

Putting requirement, criterion and scenario all in the outline was rejected: it
duplicates the detail pane, makes the outline unreadable for a large requirement,
and creates a two-pane synchronisation problem on every edit.

### flat-filtered-list

Rendering requirements as a flat list with filter chips was rejected: it discards
the spatial, persistent navigation the research praises and leaves the user with
no macro-context while editing.
