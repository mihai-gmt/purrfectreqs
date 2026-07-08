---
id: ADR-0022
title: spaCy model installed as a pinned wheel URL in requirements.txt
status: accepted
date: 2026-04-21
backfilled: true
deciders: [mihai]
tags: [supply-chain, ai, dependencies]

supersedes: []
superseded_by: null
depends_on: [ADR-0020, ADR-0006]
related_to: []
affects_modules: [app/nlp]
governed_by: [docs/TECH_STACK.md]
rejected_alternatives: [dockerfile-spacy-download]
---

# ADR-0022: spaCy model installed as a pinned wheel URL in requirements.txt

## Context

`en_core_web_sm` was installed via `RUN python -m spacy download` in the
Dockerfile — whatever version spaCy decided was compatible on any given
build. An ML model is a runtime artifact and deserves the same pinning as any
dependency (journal 2026-04-21).

## Decision

The spaCy model is declared in `requirements.txt` as a direct wheel URL
(`en_core_web_sm @ https://github.com/explosion/spacy-models/releases/download/...-3.8.0-...whl`).
The Dockerfile's `spacy download` line was removed.

## Rationale

From the journal: the wheel-URL option "keeps the lock file as the single
source of truth for all runtime artifacts and sets the project up cleanly for
the future `--require-hashes` hardening step." One file answers "what exactly
is installed?" — code and model alike.

## Consequences

### Positive

- Model version is reviewable, diffable, and locked with everything else.

### Negative

- pip-audit skips the GitHub-URL package (not on PyPI) — model advisories
  must be tracked manually.
- Model bumps edit requirements.txt rather than riding spaCy compatibility
  resolution (intended).

## Alternatives considered

### dockerfile-spacy-download

Pinning inside the Dockerfile via `spacy download <pkg>-<version> --direct`
would work but splits runtime-artifact truth across two files; rejected in
favour of the lock file as single source of truth.
