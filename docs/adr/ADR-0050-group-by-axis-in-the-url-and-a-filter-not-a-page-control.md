---
id: ADR-0050
title: The group-by axis lives in the URL; the outline filters and never paginates
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, navigation]

supersedes: []
superseded_by: null
depends_on: [ADR-0042]
related_to: [ADR-0037]
affects_modules: [app/projects, app/templates]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [saved-per-project-preference, capped-group-with-show-more, client-side-filter]
---

# ADR-0050: The group-by axis lives in the URL; the outline filters and never paginates

## Context

Two questions were left open by ADR-0042. First, where the group-by axis is
held: a control that the user sets each visit, or a stored preference. Second,
what the outline does when one group holds 400 requirements. ADR-0042 forbids a
page control inside the outline, because the UX research names it as a
frustration, but it gives no alternative.

## Decision

- **The axis is a URL query parameter**, for example `?group=label:team`. It is
  not stored. There is no user preference and no project preference.
- **The outline header carries one filter field.** It filters on the server and
  returns the same partial.
- **Each group heading shows its count**, so the user sees the size of a group
  before expanding it.
- **No page control, at any size.** A large group is a signal to filter or to
  change the axis.

## Rationale

A URL parameter is state the browser already manages. It makes the axis
shareable and bookmarkable, and it makes the back button restore the previous
axis at no cost — the same argument ADR-0037 makes for boosted navigation. A
stored preference needs a column, a write path, and a scope rule, and it buys
one saved click.

The filter is the honest answer to scale. Pagination breaks a tree because the
user cannot tell whether an item is absent or on another page. A filter never
creates that doubt: what is not shown does not match.

## Consequences

### Positive

- Any outline view can be pasted into a message and it opens the same way.
- No schema change and no preference mechanism.
- Scale has an answer that does not contradict ADR-0042.

### Negative

- The axis resets to the default on every fresh visit, which annoys a user who
  always works in one axis.
- A group of 400 that the user does not filter still renders 400 rows. The
  filter is a tool, not a guarantee.

## Alternatives considered

### saved-per-project-preference

Store the last axis per user and project. Rejected: a new column, a new write
path, and a scope question, for a small gain. It can be added later without
changing the URL contract.

### capped-group-with-show-more

Render the first N rows and offer a control for the rest. Rejected: it is a page
control under another name, and it creates the same doubt about what is missing.

### client-side-filter

Filter the loaded rows in the browser. Rejected: it needs custom JavaScript, and
it can only filter what is already loaded, so it lies on a partially expanded
outline.
