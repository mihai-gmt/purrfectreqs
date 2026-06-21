# Pi Harness Packaging Decision

## Decision

Do not package the PurrfectReqs Pi harness yet.

Keep the harness project-local under:

```text
.pi/
```

## Why packaging is deferred

Packaging too early would freeze assumptions before the workflow has been validated on a new feature end to end.

The current harness is useful, but it is still being proven as a PurrfectReqs-local workflow. A package would add maintenance overhead before the prompts, governance rules, and developer ergonomics are stable.

## Preconditions before revisiting packaging

Revisit package extraction only after all of the following are true:

- `.pi/settings.json` is stable.
- The six prompt templates are used successfully in real work:
  - `/preplan`
  - `/plan`
  - `/iterate`
  - `/write-tests`
  - `/implement`
  - `/review`
- Governance has been validated on at least one brand-new feature end to end.
- `.pi/README.md` remains accurate after real use.
- High-priority governance assessment issues are resolved or explicitly accepted.
- `/reload` consistently loads prompts and exactly one extension entrypoint.

## Future package shape, if needed

A future PurrfectReqs-specific package could look like:

```text
purrfectreqs-pi-harness/
├── package.json
├── prompts/
├── extensions/
├── skills/
└── README.md
```

## Decision point after validation

After real-feature validation, choose one of:

1. Keep the harness project-local.
2. Create a PurrfectReqs-specific Pi package.
3. Start a generic phase-gated harness package.

## Validation required before any package is trusted

If packaging is later attempted, verify:

- package loads all prompts
- package loads the governance extension
- no duplicate prompts appear
- project-local overrides still work
- package source is reviewed before trust
- no helper modules are accidentally loaded as extension entrypoints

## Current status

Deferred until the next brand-new feature validates the full workflow.
