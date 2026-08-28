---
id: ADR-0040
title: A requirement cannot contain a requirement; the object chain is the structure and labels do the grouping
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [data-model, requirements, ux, scope]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0041, ADR-0042]
affects_modules: [app/projects, app/traceability]
governed_by: [docs/DATA_MODELS.md, docs/GLOSSARY.md, docs/SCOPE.md]
rejected_alternatives: [fixed-three-level-hierarchy, free-tree-with-depth-cap]
---

# ADR-0040: A requirement cannot contain a requirement; the object chain is the structure and labels do the grouping

## Context

`docs/DATA_MODELS.md` fixed a three-level hierarchy — epic contains story, story
contains subtask — enforced by a `type` enum and a self-referencing `parent_id`.
Every organisation arranges work items differently, so any fixed set of levels is
wrong somewhere and any configurable set is a second product. No code depends on
the old rule: only `app/auth` has models, and the only migration creates `users`.

## Decision

A requirement belongs directly to a project and cannot contain another
requirement. `parent_id` and `type` are removed. Structure comes from the object
chain — project, requirement, acceptance criterion, Gherkin scenario — which the
schema fixes at four levels. Grouping is done with namespaced labels
(`group:Registration`) in a `labels` table; a label is a view axis, not a folder.
`parent_of` is removed from `traceability_links.link_type`.

## Rationale

The four levels are not process levels: each is a different kind of object with
different fields and a different reader, so forcing them states what the objects
are rather than how a company works. Epic, story and subtask are an org
convention, and a convention belongs in a label. Labels beat folders for the case
that actually occurs — one requirement legitimately belongs to Auth, to Security,
and to one meeting at the same time — because a label lets the user re-pivot
instead of choosing one true home.

## Consequences

### Positive

- No recursive CTEs, no depth cap, no cycle guard, no subtree rewrite on move.
- One `type`-free requirement removes the invented-label conflict entirely.
- The MVP shrinks: "move requirements within hierarchy" is deleted, not built.

### Negative

- The outline root is every requirement in the project, so group-by is required
  for the screen to work at scale — it is not optional polish.
- Importing from a nested tool is lossy: the source hierarchy collapses to labels.
- Users who want folders will simulate them in label values, so the schema must
  forbid `/`, `\`, and `:` inside a value.

## Alternatives considered

### fixed-three-level-hierarchy

Keeping epic/story/subtask as structural levels was rejected: it matches no real
organisation, and it forces the AI to produce a nested tree from a transcript —
a much less reliable task than producing a list.

### free-tree-with-depth-cap

A self-referencing tree capped at five levels was decided on 2026-08-28 and
reversed the same day. It kept every cost of a tree — a denormalized depth
column, a subtree rewrite on every move, recursive queries — to buy grouping that
labels supply more cheaply and more flexibly.
