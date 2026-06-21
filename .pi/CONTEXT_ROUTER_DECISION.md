# Context Router Decision

## Decision

Do not build a custom context-router tool or skill yet.

Use prompt-only context routing for now.

## Why a custom router is deferred

The six Pi prompt templates now include bounded context instructions. The workflow should be validated with those prompts before adding another abstraction layer.

A custom router would add complexity before we know whether the prompt-level routing is insufficient.

## Current context-routing strategy

Each prompt is responsible for routing its own context:

- `/preplan` reads project authority docs, the feature file, and only relevant supporting docs.
- `/plan` reads the feature file, analysis artifact, and planning docs, but not implementation files directly.
- `/iterate` uses embedded scope-specific read lists.
- `/write-tests` reads the frozen plan, `.feature` file, testing guidance, and Section 14 test-writing files.
- `/implement` reads the frozen plan, failing tests, relevant docs, and Section 14 implementation files.
- `/review` reads only compliance docs, the feature, the plan, and changed files, then writes only the review artifact.

## Revisit triggers

Consider a context-router skill or tool only if real feature validation shows repeated problems, such as:

- prompts read too much context
- prompts forget required docs
- Section 14 routing becomes hard to maintain in prompts
- multiple workflow profiles are needed
- prompt-level context rules drift from governance rules

## Possible future tool

A future router could expose:

```text
get_project_context(task_type, feature_type, module)
```

Possible return fields:

```text
required files
optional files
forbidden files
authority document roles
phase-specific notes
```

## Validation required before revisiting

Before building a router, validate the current prompt-only approach on a brand-new feature and record:

- whether required docs were missed
- whether irrelevant docs were read
- whether Section 14 was sufficient
- whether review context was too broad or too narrow
- whether any governance false positive/negative came from context routing

Until that evidence exists, keep context routing in prompts.
