---
id: ADR-0049
title: The outline row carries one derived coverage mark and no counts
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, ux, data-model]

supersedes: []
superseded_by: null
depends_on: [ADR-0042]
related_to: [ADR-0041, ADR-0048]
affects_modules: [app/projects, app/templates]
governed_by: [docs/FRONTEND.md, docs/DATA_MODELS.md]
rejected_alternatives: [titles-only, full-rollup-counts, stored-coverage-flag]
---

# ADR-0049: The outline row carries one derived coverage mark and no counts

## Context

ADR-0042 put groups and requirements in the outline and pushed criteria and
scenarios into the detail pane. It did not say what a row displays beside the
title. The choice has a cost: a title-only row is one query per group, and any
per-row rollup over criteria and scenarios is a two-level aggregate. The
decision is cheap now and expensive after the outline is built.

## Decision

An outline row holds the title and **one derived coverage mark**.

- The mark says one thing: the requirement has at least one accepted scenario,
  or it has none.
- A requirement is covered when at least one of its acceptance criteria has a
  `gherkin_scenarios` row with `state = 'accepted'` and `is_deleted = false`.
- It is computed on read, in the same query that loads a group. No column, no
  stored flag, no cache.
- It is rendered as text plus an icon, never colour alone (`docs/FRONTEND.md`
  §7.2).
- No counts appear in the outline. Criteria counts, scenario counts, and stale
  counts belong to the detail pane and the table lens.

## Rationale

One boolean is one `EXISTS` in the group query. Counts are a `GROUP BY` over two
joins per row, and they must be recomputed on every scenario edit.

The stronger reason is what a row is for. The outline is the spine: it exists to
get the user to the right requirement. A row that reports numbers becomes a
dashboard, and a dashboard invites the user to work in the outline instead of in
the requirement. ADR-0048 gives numbers a place to live.

## Consequences

### Positive

- "Which requirements have no scenarios" is answerable by eye, in the spine.
- The group query stays a single statement.
- No invalidation problem: nothing is stored, so nothing goes stale.

### Negative

- The mark is coarse. One accepted scenario on one criterion marks the whole
  requirement covered, which overstates coverage on a requirement with six
  criteria.
- Every group expansion pays for the `EXISTS`, even when nobody looks at it.

## Alternatives considered

### titles-only

No derived state at all. Rejected: the coverage question is the most frequent
one in the product, and answering it would need the table lens every time.

### full-rollup-counts

Criteria, scenario, and stale counts per row. Rejected: a two-level aggregate
per row, and it turns the spine into a dashboard that duplicates ADR-0048.

### stored-coverage-flag

A boolean column on `requirements`, written when a scenario changes. Rejected
for the reason the stale rule was rejected in the v2 amendment: a stored
derivation is wrong the moment any writer forgets to update it.
