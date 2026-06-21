# 09 — Clean Stale Comments

## Purpose

Update comments and docs that still refer to old helper module names.

## Current issue

`.pi/extensions/governance.ts` comment references:

```text
governance-config.ts
governance-engine.ts
```

Actual files are:

```text
.pi/governance/config.ts
.pi/governance/engine.ts
```

## Tasks

1. Update adapter file header.
2. Ensure comments mention Pi loads only `.pi/extensions/*.ts` as extension entrypoints.
3. Ensure helper modules are documented as internal modules under `.pi/governance/`.

## Validation

- Comments match actual layout.
- No behavior changes.
- `/reload` remains clean.

## Stop conditions

None. This is low-risk cleanup.
