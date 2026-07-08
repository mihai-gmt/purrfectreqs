---
id: ADR-0005
title: Qwen 3 32B (non-Coder) for app runtime; Coder models for dev tooling only
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [ai, models]

supersedes: []
superseded_by: null
depends_on: [ADR-0003]
related_to: [ADR-0004]
affects_modules: [app/nlp]
governed_by: [docs/TECH_STACK.md]
rejected_alternatives: [coder-model-for-runtime]
---

# ADR-0005: Qwen 3 32B (non-Coder) for app runtime; Coder models for dev tooling only

## Context

Two distinct LLM jobs exist around this project: the application analyses
requirements text at runtime, and the developer uses coding assistants during
development. One model choice does not serve both.

## Decision

The application runtime uses Qwen 3 32B Q4, the non-Coder variant, for
requirement analysis, ambiguity detection, completeness review, and quality
feedback. Coder models may be used as development tools outside the
application runtime but are not part of the app dependency stack.

## Rationale

"Requirement analysis needs general reasoning, not code generation bias"
(`docs/ARCHITECTURE.md`, Decision Log). A Coder-tuned model biases toward
producing code, which distorts analysis of natural-language requirements.

## Consequences

### Positive

- The runtime model is matched to its actual task (NL reasoning).
- Development tooling can evolve independently of the app.

### Negative

- The model choice is pinned in configuration (`OLLAMA_MODEL=qwen3:32b`);
  changing it is an escalation (`docs/TECH_STACK.md`, Agent Enforcement
  Rules).

## Alternatives considered

### coder-model-for-runtime

Using the Qwen Coder variant for the app runtime was rejected: code-generation
bias is a liability, not an asset, when analysing requirements prose.
