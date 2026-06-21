# 07 — Move Remaining Hardcoded Paths into Config

## Purpose

Make path classification more maintainable and move PurrfectReqs-specific paths out of the engine.

## Current hardcoded examples

```text
tests/bdd/plans
tests/bdd/step_defs
tests/unit
docs/
```

## Why this matters

The original migration plan says generic engine code should avoid hardcoded PurrfectReqs paths.

## Suggested config additions

In `.pi/governance/config.ts`, add:

```ts
planDir: "tests/bdd/plans",
analysisSuffix: ".analysis.md",
planSuffix: ".plan.md",
reviewSuffix: ".review.md",
testDirs: ["tests/bdd/step_defs", "tests/unit"],
docsDir: "docs",
featureDirs: ["tests/features"],
```

## Engine changes

Update `classifyPath()` to use config values for:

- analysis files
- plan files
- review files
- test files
- docs
- features where possible

## Validation

- Existing PurrfectReqs paths classify exactly as before.
- Custom `testRoots` / `testDirs` can classify tests.
- Custom `planDir` can classify plans.
- Review mode still only allows review artifacts.

## Stop conditions

Stop if regex simplification causes classification drift for existing paths.
