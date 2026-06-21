# 10 — Decide Local Model Policy

## Purpose

Decide whether the Pi coding harness should use Anthropic/hosted models or local Ollama models.

## Context

PurrfectReqs application AI is offline/local via Ollama. That does not automatically mean the coding harness must be local.

## Options

### Option A — Keep hosted coding models

Pros:

- better instruction following
- better for strict workflow and code changes
- less local setup friction

Cons:

- coding-agent traffic is external

### Option B — Use local Ollama for some tasks

Pros:

- fully local
- aligns with project offline ethos

Cons:

- smaller models may struggle with strict workflow
- may be slower or less reliable

### Option C — Hybrid

- hosted model for implementation/review
- local model for read-only summaries or low-risk tasks

## Suggested decision

Use hosted strong models for now unless there is a hard privacy requirement for harness traffic.

## If local is desired

Configure user-level:

```text
~/.pi/agent/models.json
```

Do not commit personal model config to repo.

## Validation

- `/model` shows intended model choices.
- One read-only prompt works with local model if configured.
- Strict prompts still behave reliably.

## Stop conditions

Stop if local model cannot reliably follow `.feature` authority or phase boundaries.
