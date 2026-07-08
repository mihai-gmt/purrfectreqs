---
id: ADR-0035
title: App shell Option D (rail → master-detail → inspector), built incrementally
status: accepted
date: 2026-06-14
backfilled: true
deciders: [mihai]
tags: [frontend, ux, architecture]

supersedes: []
superseded_by: null
depends_on: [ADR-0002]
related_to: [ADR-0036]
affects_modules: [app/templates, app/static]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [top-nav-mpa, sidebar-explorer-only, three-pane-upfront]
---

# ADR-0035: App shell Option D (rail → master-detail → inspector), built incrementally

## Context

Before writing the auth UI Gherkins, the post-login information architecture
needed a direction. Four shell archetypes were surveyed: top-nav MPA,
left-sidebar explorer, permanent three-pane master/detail/inspector, and a
hybrid icon-rail + master-detail + on-demand inspector (journal 2026-06-14).

## Decision

Option D is the north star: module rail (the seven MVP modules), master
list/tree, detail pane, and an inspector that slides in on demand for AI
analysis. It is reached incrementally: auth ships chrome-less centred forms
(no shell at all); the rail + master-detail arrives with the first post-login
screen; the inspector is built only when Module 4 produces analysis to show.

## Rationale

The domain is hierarchical (Epic→Story→Subtask) and the AI analysis wants to
sit *beside* the requirement being edited, not on a separate page — D scales
across all seven modules without replacement, where a top-nav MPA "would hit
pain by Module 2." The key reframe: auth never needed the shell resolved —
login/register look identical under any shell — so the decision stopped
blocking auth work. "Don't architect the shell before you have a screen for
it."

## Consequences

### Positive

- One IA that survives all seven modules; no premature three-pane layout
  before there is data for the third pane.

### Negative

- The shell arrives in stages, so early screens will be restructured into it
  (accepted: the stages are designed, not accidental).

## Alternatives considered

### top-nav-mpa

Traditional page-per-module navigation; loses the always-visible requirement
tree and forces context switches by Module 2.

### sidebar-explorer-only

Option B is the *first increment* of D, not the destination — stopping there
leaves analysis on separate pages.

### three-pane-upfront

Building the inspector before Module 4 produces analysis violates progressive
disclosure and builds UI for data that does not exist.
