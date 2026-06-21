# 12 — Defer Package Extraction

## Purpose

Record that packaging the harness should wait until the local harness is proven.

## Why defer

Packaging too early freezes assumptions and creates maintenance overhead.

## Preconditions before packaging

- `.pi/settings.json` is stable.
- Six Pi prompts are ported and used.
- Governance has been used on at least one real feature.
- `.pi/README.md` exists.
- Remaining high-priority assessment issues are addressed.

## Future package shape

```text
purrfectreqs-pi-harness/
├── package.json
├── prompts/
├── extensions/
├── skills/
└── README.md
```

## Decision point

After real-feature validation, decide:

1. keep harness project-local
2. create PurrfectReqs-specific package
3. start generic phase-gated harness package

## Validation when eventually packaging

- package loads prompts
- package loads extensions
- no duplicate prompts
- project-local overrides still work
- package source is reviewed before trust
