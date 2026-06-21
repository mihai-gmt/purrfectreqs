# 01 — Port the Six Pi Prompt Templates

## Purpose

Create native Pi prompt templates for the workflow commands that currently exist as Claude Code slash commands.

Target prompts:

```text
.pi/prompts/preplan.md
.pi/prompts/plan.md
.pi/prompts/iterate.md
.pi/prompts/write-tests.md
.pi/prompts/implement.md
.pi/prompts/review.md
```

## Why this is highest priority

The governance extension now enforces phase and file boundaries, but prompts are what guide the agent through the actual workflow. Without native Pi prompts, the harness is enforcement-heavy but workflow-light.

## Source material

Read and port from:

```text
.claude/commands/preplan.md
.claude/commands/plan.md
.claude/commands/iterate.md
.claude/commands/write-tests.md
.claude/commands/implement.md
.claude/commands/review.md
```

Support files:

```text
.claude/commands/scopes/adversarial.md
.claude/commands/scopes/enrich.md
.claude/commands/scopes/testability.md
.claude/commands/scopes/freeze.md
```

## Required Pi prompt format

Each prompt must start with frontmatter:

```markdown
---
description: Short description shown in Pi autocomplete
argument-hint: "<expected-argument>"
---
```

Each prompt must explicitly include:

```markdown
User argument: $ARGUMENTS
```

## Command-specific guidance

### `/preplan`

- Preserve Locator / Analyzer / Pattern Finder concepts.
- Replace Claude `Agent` tool assumptions with sequential Pi-compatible instructions.
- Output should be an analysis file under:

```text
tests/bdd/plans/<module>_<feature_name>.analysis.md
```

### `/plan`

- Require the `.feature` file and preplan analysis.
- Preserve approval loops.
- Preserve rule that planning does not read or modify `app/` unless allowed by workflow.
- Produce a plan file under:

```text
tests/bdd/plans/<module>_<feature_name>.plan.md
```

### `/iterate`

- Preserve scopes:
  - adversarial
  - enrich
  - testability
  - freeze
- Reference support scope files explicitly.
- Do not expose scope files as direct slash commands.

### `/write-tests`

- Require frozen plan.
- Use Section 14 write manifest.
- Write only approved test files.
- Must not write implementation code.
- Should instruct developer to use `/box run-red pytest ...`.

### `/implement`

- Require frozen plan and RED state.
- Modify only approved implementation files.
- Must not modify tests or `.feature` files.
- Should instruct developer to use `/box run-green pytest ...` after implementation.

### `/review`

- Require GREEN state.
- Read-only except review artifact.
- Write only:

```text
tests/bdd/plans/<module>_<feature_name>.review.md
```

## Implementation steps

1. Read one Claude command file.
2. Draft the Pi prompt equivalent.
3. Remove Claude-specific assumptions.
4. Add frontmatter.
5. Add `$ARGUMENTS` handling.
6. Add context-routing instructions.
7. Save under `.pi/prompts/`.
8. Reload Pi and verify slash autocomplete.
9. Repeat one prompt at a time.

## Validation

- `/preplan` appears in Pi autocomplete.
- `/plan` appears in Pi autocomplete.
- `/iterate` appears in Pi autocomplete.
- `/write-tests` appears in Pi autocomplete.
- `/implement` appears in Pi autocomplete.
- `/review` appears in Pi autocomplete.
- Running each prompt with an argument includes the argument in expanded prompt.
- Support scope files are not exposed as direct user-facing commands.

## Stop conditions

Stop if a Claude command depends on a tool Pi does not provide and no safe equivalent is obvious.
