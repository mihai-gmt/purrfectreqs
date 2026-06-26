# Pi Harness Model Policy

## Decision

Use a strong hosted coding model for the Pi coding harness by default. As of 2026-06-21 that model is `gpt-5.5` via the `openai-codex` provider. Anthropic (Claude) models are deliberately removed from this harness — see Rationale.

Current project settings:

```json
{
  "defaultProvider": "openai-codex",
  "defaultModel": "gpt-5.5",
  "defaultThinkingLevel": "medium",
  "enabledModels": ["gpt-*"]
}
```

## Rationale

PurrfectReqs application AI is designed to run offline/local via Ollama. That requirement applies to the application being built, not automatically to the coding harness used to develop it.

For the harness, strict instruction following is more important than architectural symmetry. The Pi workflow depends on the model reliably following:

- `.feature` file authority
- Feature Box boundaries
- phase-specific write rules
- RED/GREEN discipline
- Section 14 file manifests
- security and escalation rules from `CLAUDE.md`

A strong hosted coding model is the default because it is currently more reliable for those constraints.

### Why not Anthropic models in this harness

Anthropic (`claude-*`) models are removed from `enabledModels`, not merely left off the default. From 2026-06-15, using Anthropic models through a third-party harness (Pi is one) bills against a separate Agent-SDK credit pool rather than the Claude subscription. Keeping `claude-*` selectable here invites accidental spend from that separate pool. Restricting `enabledModels` to `gpt-*` makes it impossible to invoke a Claude model from this harness by mistake. Claude Code (the first-party harness) remains the place to use Anthropic models on the subscription.

## Approved default

Use:

```text
provider: openai-codex
model: gpt-5.5
thinking: medium
```

This is configured in:

```text
.pi/settings.json
```

## Local model policy

Local Ollama models are allowed only as an optional personal/user-level experiment for low-risk work, such as:

- read-only summaries
- exploratory analysis
- non-authoritative draft notes

Do not use local models for strict governed phases unless they have been manually validated to follow the workflow reliably:

```text
/preplan
/plan
/iterate ... freeze
/write-tests
/implement
/review
```

## Where to configure local models

Do not commit project-local model credentials or personal model lists.

If local models are desired, configure them at user level:

```text
~/.pi/agent/models.json
```

Pi's Ollama-compatible shape is:

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": {
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false
      },
      "models": [
        { "id": "qwen2.5-coder:7b" }
      ]
    }
  }
}
```

`apiKey` is required by Pi's provider schema but ignored by Ollama.

## Validation before using a local model for governed work

Before using a local model for anything beyond read-only work, verify:

1. `/model` shows the local model.
2. The model can run a read-only prompt without ignoring instructions.
3. The model respects `.feature` immutability.
4. The model does not write outside the Feature Box.
5. The model follows plan approval loops.
6. The model does not bypass RED/GREEN gates.
7. The model stops and escalates when required.

If any check fails, do not use that model for governed implementation work.
