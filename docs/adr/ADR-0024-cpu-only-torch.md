---
id: ADR-0024
title: CPU-only torch via PyTorch index pre-install in Docker and CI
status: accepted
date: 2026-04-21
backfilled: true
deciders: [mihai]
tags: [supply-chain, ai, deployment]

supersedes: []
superseded_by: null
depends_on: [ADR-0006, ADR-0020]
related_to: [ADR-0004]
affects_modules: []
governed_by: [docs/TECH_STACK.md]
rejected_alternatives: [split-requirements-files]
---

# ADR-0024: CPU-only torch via PyTorch index pre-install in Docker and CI

## Context

`torch==2.11.0` is one pin that resolves to different wheels per platform. On
macOS arm64 it gives the MPS/CPU wheel; in a Linux container (and on CI's
ubuntu runners) PyPI's default resolution gives the CUDA wheel, dragging in
~2–5 GB of `nvidia-*` packages onto machines with no GPU. The LLM runs on the
host via Ollama; only sentence-transformers and spaCy run in-process, both
CPU-happy (journals 2026-04-21 and 2026-04-24).

## Decision

The Dockerfile and both CI jobs install torch from the PyTorch CPU index
*before* `requirements.txt`:

```dockerfile
RUN pip install --no-cache-dir torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
```

pip finds torch already satisfied and skips re-resolving it; no nvidia-*
wheels are pulled.

## Rationale

From the journal: "for a project with exactly one package that needs a
platform-specific wheel, two lines in the Dockerfile are the minimum viable
fix." Image size and build time drop dramatically; the container's workload
is small-model embedding inference, not GPU compute.

## Consequences

### Positive

- Container/CI installs shed gigabytes of dead GPU packages.

### Negative

- Local venv and container install different torch wheels from different
  indices — correct (different hardware) but it means a torch version bump
  must also touch the Dockerfile and CI lines. Flagged for the future
  pip-tools pass.

## Alternatives considered

### split-requirements-files

`requirements-base.txt` + `requirements-docker.txt` with `--extra-index-url`:
cleaner in theory, rejected because it creates two files that must stay in
lockstep for the sake of a single platform-specific package. Revisit if a
second such package appears.
