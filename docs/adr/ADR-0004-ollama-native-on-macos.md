---
id: ADR-0004
title: Ollama runs natively on macOS, not in Docker
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [ai, deployment, performance]

supersedes: []
superseded_by: null
depends_on: [ADR-0003]
related_to: []
affects_modules: [app/nlp]
governed_by: [docs/ARCHITECTURE.md, docs/TECH_STACK.md]
rejected_alternatives: [ollama-in-docker]
---

# ADR-0004: Ollama runs natively on macOS, not in Docker

## Context

The rest of the stack runs as Docker Compose services (OrbStack on macOS). A
32B-parameter model needs GPU acceleration to be usable interactively; the dev
machine is an Apple Silicon M4 Max with Metal.

## Decision

Ollama runs natively on the macOS host, outside Docker. The `app` container
reaches it at `http://host.docker.internal:11434` via the `extra_hosts`
directive in `docker-compose.yml`; the URL comes from the `OLLAMA_BASE_URL`
environment variable.

## Rationale

"Metal GPU passthrough not supported in Docker VMs on Apple Silicon; native
gives full Metal acceleration" (`docs/ARCHITECTURE.md`, Decision Log). Running
the model CPU-only inside the container would make a 32B model impractical.

## Consequences

### Positive

- Full Metal acceleration for LLM inference.
- The model runtime upgrades independently of the app stack.

### Negative

- The stack is not fully self-contained in Compose: Ollama is a host
  prerequisite, and `host.docker.internal` is a Docker-on-desktop convention.
- Production/VM deployment does not ship Ollama (`docs/SECURITY.md` §15
  service table) — AI features are dev-machine-bound for now.

## Alternatives considered

### ollama-in-docker

Rejected because Docker VMs on Apple Silicon cannot pass through the Metal
GPU; containerised Ollama would fall back to CPU inference.
