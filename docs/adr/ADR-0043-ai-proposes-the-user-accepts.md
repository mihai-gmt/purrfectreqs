---
id: ADR-0043
title: The AI proposes and the user accepts; the AI never authors a domain artifact alone
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [ai, governance, scope, ux]

supersedes: []
superseded_by: null
depends_on: [ADR-0041]
related_to: [ADR-0018, ADR-0040]
affects_modules: [app/nlp, app/gherkin, app/projects]
governed_by: [docs/SCOPE.md]
rejected_alternatives: [ai-writes-directly, gherkin-first-authoring]
---

# ADR-0043: The AI proposes and the user accepts; the AI never authors a domain artifact alone

## Context

`docs/SCOPE.md` stated that the user writes acceptance criteria in Gherkin, while
ADR-0041 made the criterion plain language and the Gherkin a separate artifact the
AI can draft. That left the higher-ranked document contradicting the data model on
who authors what. The UX research records that business stakeholders neither read
nor write Gherkin (8 of 8 reports), but it also records that AI output is trusted
only when a person can see it, judge it, and refuse it.

## Decision

The AI never creates a requirement, an acceptance criterion, or a Gherkin
scenario on its own. A Gherkin scenario reaches the database by one of three
user-initiated paths: the user writes it; the user asks the AI to draft it and
accepts each draft; or the user asks the AI to review a scenario the user wrote.
An AI-authored artifact is stored as a proposal until a person accepts it. The AI
may analyse and advise at any time, because advice is not an artifact.

## Rationale

Ownership is the point. A requirements tool whose contents nobody vouched for is
a liability, and the audit trail must be able to say which person accepted each
statement. Separating advice from authorship keeps that line clean without making
every analysis need a click. Keeping the hand-written path first-class matters
too: a user who can already write Gherkin must never be forced through the AI.

## Consequences

### Positive

- Every domain artifact has a person who accepted it, recorded in `created_by`.
- Refused AI output is auditable, because a dismissed proposal is soft-deleted.
- No schema change: `origin`, `state`, and `validation_results` already cover the
  three paths.

### Negative

- AI-driven intake needs its own staging table, because a proposed requirement
  must not sit in `requirements` pretending to be accepted.
- Every AI feature needs an accept surface, which is more UI than a direct write.

## Alternatives considered

### ai-writes-directly

Letting the AI write scenarios straight into the model was rejected: it removes
the person who vouches for the text and makes the audit trail unable to name who
agreed to a requirement.

### gherkin-first-authoring

Requiring the user to author acceptance criteria in Gherkin was the original
scope and was rejected: all eight UX research reports agree business stakeholders
neither read nor write it.
