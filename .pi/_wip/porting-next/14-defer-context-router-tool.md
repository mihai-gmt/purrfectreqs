# 14 — Defer Custom Context-Router Tool or Skill

## Purpose

Record that context routing should begin in prompts, not with a custom tool.

## Why defer

The prompts do not exist yet. Building a context-router tool before seeing prompt behavior would be premature.

## Current recommendation

Use prompt-only context routing first:

- each prompt lists required docs
- each prompt explains what not to read
- implementation prompt follows Section 14

## Revisit trigger

Build a context-router skill/tool only if:

- prompts repeatedly read too much context
- prompts forget required docs
- file routing becomes hard to maintain in six separate prompts
- multiple workflow profiles are introduced

## Possible future tool

```text
get_project_context(task_type, feature_type, module)
```

Return:

- required files
- optional files
- forbidden files
- relevant document roles

## Validation before revisiting

Use one real feature and record context-routing issues first.
