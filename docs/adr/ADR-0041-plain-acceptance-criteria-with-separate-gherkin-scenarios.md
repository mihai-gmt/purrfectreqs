---
id: ADR-0041
title: Acceptance criteria are plain text; Gherkin scenarios are a separate table
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [data-model, requirements, gherkin, ai, ux]

supersedes: []
superseded_by: null
depends_on: []
related_to: [ADR-0018, ADR-0040]
affects_modules: [app/projects, app/gherkin, app/nlp]
governed_by: [docs/DATA_MODELS.md, docs/GLOSSARY.md]
rejected_alternatives: [one-row-two-columns, ai-system-user-row, updated-at-staleness]
---

# ADR-0041: Acceptance criteria are plain text; Gherkin scenarios are a separate table

## Context

`docs/DATA_MODELS.md` held one `acceptance_criteria` row with a NOT NULL
`gherkin_text` column, so a criterion could not exist without Gherkin. All eight
UX research reports agree that business stakeholders neither read nor write
Gherkin (`_TEMP/ux_research/synthesis/20260713/synthesis.md`, Pillar 2,
CHALLENGED). The UI shell prototype shows two separate lists and links a proposed
scenario back to a named criterion, which one row cannot express.

## Decision

`acceptance_criteria` holds `title` and plain `text` and no Gherkin. A new
`gherkin_scenarios` table holds the Gherkin with a foreign key to the criterion,
so one criterion can have many scenarios. A scenario carries three independent
facts: `origin` (`human` or `ai`), authoring `state` (`proposed`, `draft`,
`accepted`), and coverage `status` (the four existing test states). Staleness is
derived by comparing a `source_text_hash`, written at acceptance, with the
criterion's current text. `validation_results` moves its foreign key to the
scenario.

## Rationale

The business reader owns a sentence; the system owns its formalization. One row
cannot hold two objects with a one-to-many link between them, and it caps a
criterion at one scenario, which the prototype already exceeds. The three enums
stay separate because they answer three different questions — who wrote it, who
agreed to it, and does its test pass — and merging any two loses a fact. Hashing
the source text is exact, cheap, and silent when only a title changes.

## Consequences

### Positive

- A criterion can be written and reviewed with no Gherkin anywhere in sight.
- AI output is attributable and refusable, and the refusal is auditable.
- Gherkin syntax validation attaches to the object that actually has syntax.

### Negative

- "Is this requirement done?" becomes a two-level rollup, not one column read.
- Module 5 and Module 6 must be specified against the new shape before they are built.
- `docs/SCOPE.md` still describes Gherkin-first authoring and now contradicts this
  record at a higher document rank. That is a separate open decision.

## Alternatives considered

### one-row-two-columns

Adding a `plain_text` column beside a nullable `gherkin_text` was rejected: it
caps a criterion at one scenario and cannot express "this proposal came from that
criterion".

### ai-system-user-row

Creating a user row for the AI so `created_by` could point at it was rejected:
ADR-0018 treats the audit trail as append-only fact, and a non-person in the
`users` table makes every audit query lie about who acted.

### updated-at-staleness

Comparing `acceptance_criteria.updated_at` with the scenario timestamp was
rejected: it fires on a title-only edit and on an edit that was reversed, and a
flag that cries wolf gets ignored.
