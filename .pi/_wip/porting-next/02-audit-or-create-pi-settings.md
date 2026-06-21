# 02 — Audit or Create `.pi/settings.json`

## Purpose

Ensure the project-local Pi harness loads prompts, extensions, sessions, compaction, and models consistently.

## Why this matters

The governance extension currently loads, but the full harness needs project-local settings so Pi reliably finds prompts and extension entrypoints.

## Target file

```text
.pi/settings.json
```

## Recommended initial settings

Adapted from the migration plan:

```json
{
  "defaultProvider": "anthropic",
  "defaultModel": "claude-sonnet-4-20250514",
  "defaultThinkingLevel": "medium",
  "prompts": [
    "./prompts/*.md"
  ],
  "enableSkillCommands": true,
  "compaction": {
    "enabled": true,
    "reserveTokens": 16384,
    "keepRecentTokens": 20000
  },
  "retry": {
    "enabled": true,
    "maxRetries": 3
  },
  "enabledModels": [
    "claude-*"
  ],
  "sessionDir": ".pi/sessions",
  "extensions": [
    "./extensions"
  ]
}
```

## Tasks

1. Check whether `.pi/settings.json` already exists.
2. If it exists, compare it against the recommended settings.
3. If it does not exist, create it.
4. Ensure these directories exist:

```text
.pi/prompts
.pi/extensions
.pi/sessions
```

5. Decide whether `.pi/sessions/` should be gitignored.
6. Confirm `.pi/extensions` contains only extension entrypoints, not helper modules.

## Validation

- Pi starts without settings errors.
- `/reload` works.
- Startup shows project resources loaded.
- `governance.ts` is loaded as the only extension entrypoint.
- After prompt porting, native prompts appear in autocomplete.

## Stop conditions

Stop if settings conflict with current user-level Pi configuration or model availability.
