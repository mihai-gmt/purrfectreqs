---
id: ADR-0048
title: The requirements table is a read-only lens on its own route, never the authoring surface
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, scope]

supersedes: []
superseded_by: null
depends_on: [ADR-0040, ADR-0042]
related_to: [ADR-0049]
affects_modules: [app/projects, app/templates]
governed_by: [docs/FRONTEND.md, docs/SCOPE.md]
rejected_alternatives: [editable-grid-with-bulk-actions, no-table-in-mvp, table-as-a-mode-of-archetype-2]
---

# ADR-0048: The requirements table is a read-only lens on its own route, never the authoring surface

## Context

The shell prototype carried no table view at all, and `docs/FRONTEND.md` states
an anti-grid position. The UX research does not fully support that position.
Contradiction C3 in `_TEMP/ux_research/synthesis/20260713/contradictions.md`
records both sides: all eight reports carry the "Excel Online" grid-overload
complaint, and four of eight warn against an absolute anti-grid rule, because
teams do bulk scanning and trace work in tables. The research conclusion is
"the grid is not the default authoring surface", not "there is no grid".

ADR-0042 made the outline the spine, and it holds two levels only. A question
such as "which requirements in this project have no scenarios" is therefore
answered by opening rows one at a time. That is the gap.

## Decision

Add one table over requirement data, called the **table lens**.

- It is **read-only**. Every cell displays; no cell edits.
- It is **its own route**, `/projects/{id}/requirements/table`, archetype 4. It
  is not a mode inside archetype 2.
- It shows the title, the status, the labels, the assignee, and the coverage
  mark of ADR-0049. It sorts and filters on the server.
- It has no bulk action and no multi-select in the MVP.
- The outline stays the default view of the Requirements module.
- Build order: after the outline works. The lens reads the same query.

## Rationale

Read-only is the whole decision. It answers the research on both sides at once:
the table exists for scanning and comparison, and it cannot become the place
where people author requirements, because it cannot author anything.

Read-only also removes the implementation problem. An editable grid needs cell
focus management, dirty state, and per-cell save — real client-side JavaScript,
which `docs/TECH_STACK.md` permits only for Alpine components and the Ace
island. A read-only table is a Jinja partial and an `hx-get`.

## Consequences

### Positive

- The C3 contradiction is closed with a written rule, not a preference.
- Bulk scanning, sorting, and comparison exist without new dependencies.
- The lens and the outline read the same data through the same query.

### Negative

- Requirement data renders in two places, so a new displayed field is two
  template changes and two tests.
- Bulk editing, which the research names as a real BA need, is not in the MVP.
  A user who must change twenty statuses opens twenty requirements.

## Alternatives considered

### editable-grid-with-bulk-actions

Inline cell edit plus multi-select actions. Rejected for the MVP: it needs
custom JavaScript beyond the sanctioned uses, and a grid that edits becomes the
authoring surface, which is the exact failure the research names.

### no-table-in-mvp

Ship the outline alone. Rejected: it leaves C3 unanswered, and a table added
after the product has shipped arrives as a competitor to the outline rather
than as a lens on it.

### table-as-a-mode-of-archetype-2

A toggle that swaps the master and detail panes for a table. Rejected for the
reason ADR-0046 gives: a spec that names an archetype must fully determine the
layout. A mode breaks that property.
