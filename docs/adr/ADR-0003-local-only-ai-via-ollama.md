---
id: ADR-0003
title: Fully local AI via Ollama; no external AI APIs
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [ai, privacy, dependencies]

supersedes: []
superseded_by: null
depends_on: []
related_to: []
affects_modules: [app/nlp]
governed_by: [docs/TECH_STACK.md, docs/SCOPE.md]
rejected_alternatives: [openai-sdk, langchain, semantic-kernel]
---

# ADR-0003: Fully local AI via Ollama; no external AI APIs

## Context

The product's core value is AI-assisted requirements analysis. Requirements
documents are sensitive business data, and the target user runs the system
locally. Sending content to a cloud AI API would create privacy exposure,
recurring cost, and a hard online dependency.

## Decision

All LLM inference runs locally through Ollama. The app calls Ollama's HTTP API
directly via `httpx`. No external AI API calls — ever. No LLM orchestration
frameworks. LLM output is advisory only: never authoritative until validated
by deterministic checks, schemas, tests, or human approval.

## Rationale

"Privacy, offline capability, no API costs, self-hosted"
(`docs/ARCHITECTURE.md`, Decision Log). Direct `httpx` calls keep the
integration transparent and debuggable; an orchestration framework would add
abstraction without MVP value (`docs/TECH_STACK.md`).

## Consequences

### Positive

- Requirements data never leaves the machine; the app works fully offline.
- No per-token costs; no API-key secrets to manage for AI.

### Negative

- Analysis quality is bounded by what a local model can do.
- The deployment story must accommodate a model runtime (see the
  Ollama-native-on-macOS ADR).

## Alternatives considered

### openai-sdk

Requires external API — violates the offline-first requirement
(`docs/TECH_STACK.md`, Rejected table).

### langchain

Heavyweight abstraction over simple Ollama HTTP calls; complexity without MVP
value.

### semantic-kernel

Not needed for MVP; same reasoning as langchain.
