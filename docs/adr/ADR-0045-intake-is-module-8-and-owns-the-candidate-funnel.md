---
id: ADR-0045
title: Intake is Module 8 and owns the candidate funnel; provenance is a raw input, not a document
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [scope, data-model, ai, ux]

supersedes: []
superseded_by: null
depends_on: [ADR-0043]
related_to: [ADR-0040, ADR-0041]
affects_modules: [app/intake, app/documents, app/projects, app/nlp]
governed_by: [docs/SCOPE.md, docs/DATA_MODELS.md, docs/ARCHITECTURE.md]
rejected_alternatives: [intake-inside-module-2, two-staging-tables, state-column-on-requirements, source-document-id-provenance]
---

# ADR-0045: Intake is Module 8 and owns the candidate funnel; provenance is a raw input, not a document

## Context

ADR-0043 requires that every AI-authored domain artifact starts as a proposal a
person accepts. A requirement has no authoring state, so an AI-derived
requirement had nowhere to wait. `docs/SCOPE.md` Module 3 already claimed
"extract candidate requirements from documents" and "store extracted
requirements as drafts", with no table to hold either. The UI shell prototype
showed an "Intake / RawInput" rail entry that the scope did not contain, and the
UX research records free-text-first intake as the recommended pattern in four of
eight reports.

## Decision

Intake is Module 8, package `app/intake/`, with its own rail entry scoped to the
active project. It owns two tables. `raw_inputs` holds one unit of unstructured
source material, either pasted text or a parsed document. `candidate_requirements`
holds a proposal until a person accepts it, at which point the service creates
the `requirements` row and links the two.

Intake owns the funnel for every source. Module 3 parses a file and hands the
result to Intake; it no longer stores drafts of its own.

`requirements.source_document_id` is replaced by `requirements.raw_input_id`. A
document raw input stores no text; the text is read from the file at
decomposition time.

## Rationale

One funnel means one staging table, one accept surface, and one place where "the
AI proposed and a person accepted" is recorded. Two funnels would have duplicated
the accept UI and forced a cross-module model import, which the architecture
forbids.

One provenance field covers both sources because a raw input generalises over a
paste and a document. Keeping `source_document_id` beside a paste-shaped source
would have left half the requirements with no provenance at all.

Reusing the `origin` and `state` vocabulary from `gherkin_scenarios`, and
recording a dismissal as a soft delete rather than an enum value, keeps one word
meaning one thing across both proposal tables.

## Consequences

### Positive

- Every requirement that an AI produced has a named person who accepted it.
- A dismissed candidate stays in the audit trail, soft-deleted.
- Document content still never lives in the database.
- A requirement typed by hand simply has a NULL `raw_input_id`; no special case.

### Negative

- A decomposition is not reproducible from the database alone. If a file leaves
  the volume, the candidates remain but their source text is gone.
- The module count moves from seven to eight, which touches the app shell, the
  rail, and the glossary.
- A raw input is immutable, so correcting a paste means deleting it and starting
  again.

## Alternatives considered

### intake-inside-module-2

Making intake a capture view inside Projects & Requirements was rejected: it
hides a distinct capability behind the repository it feeds, and it puts proposals
in the module that owns accepted requirements.

### two-staging-tables

Letting Module 3 keep its own draft store beside Intake's was rejected: two
staging tables mean two accept surfaces for one user action, and the two modules
would have to reach into each other's models.

### state-column-on-requirements

Adding a `proposed` state to `requirements` was rejected: an unaccepted proposal
would then sit in the requirements table, visible to every query that forgot to
filter it, which is exactly what ADR-0043 forbids.

### source-document-id-provenance

Keeping `requirements.source_document_id` was rejected once intake accepted
pasted text: a requirement derived from a paste has no document, so the field
would be NULL for a whole class of real provenance.
