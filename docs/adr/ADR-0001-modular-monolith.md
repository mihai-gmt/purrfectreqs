---
id: ADR-0001
title: Modular monolith over microservices
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [architecture, deployment]

supersedes: []
superseded_by: null
depends_on: []
related_to: []
affects_modules: [app]
governed_by: [docs/ARCHITECTURE.md, docs/SCOPE.md]
rejected_alternatives: [microservices, message-queues]
---

# ADR-0001: Modular monolith over microservices

## Context

PurrfectReqs is an MVP targeting solo/small-team local deployment (Docker
Compose, single command to start). Seven domain modules must coexist without
becoming a tangled ball, but the team is one developer learning the Python
stack, and the deployment story must stay trivial.

## Decision

All code runs in a single FastAPI process. Domains are separated by package
boundaries under `app/` (one package per module), not by network. Modules
communicate via direct Python function calls through service interfaces; all
module communication is synchronous.

## Rationale

Simpler to develop, simpler to deploy, simpler to debug — the three costs that
dominate an MVP built by one person (`docs/ARCHITECTURE.md`, Architectural
Style). Discipline is preserved through hard package rules instead of network
boundaries: modules must not import each other's SQLAlchemy models, and
inter-module calls go through services and Pydantic schemas only.

## Consequences

### Positive

- One container, one process, one debugger; no service mesh, no RPC failure modes.
- Module boundaries can still be enforced (and tested) at the import level.

### Negative

- Horizontal scaling and async processing are deferred (explicitly post-MVP in
  `docs/SCOPE.md`).
- Boundary discipline relies on convention plus review rather than compilation
  units — the cross-module import rule must be actively policed.

## Alternatives considered

### microservices

Prohibited by `docs/ARCHITECTURE.md`: network overhead, deployment complexity,
and debugging cost buy nothing at MVP scale.

### message-queues

Async inter-module messaging rejected for MVP — all communication is
synchronous direct calls (`docs/SCOPE.md`, Module Interaction Summary). Queues
reappear on the post-MVP roadmap only if scaling demands them.
