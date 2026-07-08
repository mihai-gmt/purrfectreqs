---
id: ADR-0006
title: spaCy + sentence-transformers for deterministic NLP
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [ai, nlp, dependencies]

supersedes: []
superseded_by: null
depends_on: [ADR-0003]
related_to: []
affects_modules: [app/nlp]
governed_by: [docs/TECH_STACK.md]
rejected_alternatives: [nltk, textblob, gensim]
---

# ADR-0006: spaCy + sentence-transformers for deterministic NLP

## Context

Alongside the advisory LLM, the system needs deterministic NLP: tokenisation,
Named Entity Recognition, dependency parsing, and semantic similarity via
embeddings. These must run offline, in-process, on CPU.

## Decision

spaCy (`en_core_web_sm`) handles linguistic extraction — NER, parsing,
tokenisation. sentence-transformers (`all-MiniLM-L6-v2`) produces
384-dimensional embeddings for semantic similarity. If the embedding model
ever changes, all existing embeddings must be regenerated.

## Rationale

Both are production-grade, offline, and well-maintained
(`docs/TECH_STACK.md`, NLP & AI). MiniLM's 384-dimension output is small
enough for pgvector at MVP scale while remaining adequate for
requirement-similarity tasks.

## Consequences

### Positive

- Deterministic NLP results the LLM's advisory output can be checked against.
- Fully offline; no model API dependencies.

### Negative

- sentence-transformers pulls PyTorch as a transitive dependency (see the
  CPU-only-torch ADR for the supply-chain consequences).
- In-process CPU inference becomes a bottleneck at scale; a background task
  queue is the noted future mitigation.

## Alternatives considered

### nltk

Older and less suitable than spaCy for the required NLP tasks.

### textblob

Built on NLTK; superseded by spaCy for these tasks.

### gensim

Topic-modelling library; sentence-transformers covers semantic similarity
better for this project.
