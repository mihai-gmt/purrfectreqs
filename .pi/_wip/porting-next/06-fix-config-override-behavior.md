# 06 — Fix Config Override Behavior

## Purpose

Make `createGovernanceEngine(config)` meaningful and avoid overwriting custom configs with global defaults.

## Current issue

The engine accepts a config:

```ts
createGovernanceEngine(config = CONFIG)
```

but each tool call runs:

```ts
governanceConfig = loadHarnessConfig(cwd)
```

If no `.pi/harness.config.json` exists, loader returns global `CONFIG`, not the config passed to the engine.

## Why this matters

This blocks true reuse and conflicts with app-agnostic extraction goals.

## Desired behavior

- Engine has a base config in closure.
- `.pi/harness.config.json`, if present, merges over that base config.
- If JSON is missing, use the engine base config.

## Suggested implementation

1. Change config loader signature:

```ts
loadHarnessConfig(cwd: string, baseConfig: GovernanceConfig = CONFIG): GovernanceConfig
```

2. Merge JSON over `baseConfig`, not always `CONFIG`.
3. In `createGovernanceEngine`, store:

```ts
const baseConfig = config;
```

4. On tool call:

```ts
governanceConfig = loadHarnessConfig(cwd, baseConfig);
```

## Validation

- No JSON config: behavior unchanged for PurrfectReqs.
- Custom config passed to engine is preserved.
- JSON config overrides custom config where provided.
- Invalid JSON falls back to base config, not always global config.

## Stop conditions

Stop if TypeScript type inference around `GovernanceConfig` makes partial config merging unsafe.
