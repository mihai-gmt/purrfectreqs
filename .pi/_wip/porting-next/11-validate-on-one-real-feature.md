# 11 — Validate Harness on One Real Feature End-to-End

## Purpose

Prove the harness works in real workflow, not just mocked validation.

## Why this matters

Governance and prompts may pass unit-like checks but still be awkward during real feature work.

## Candidate workflow

```text
/preplan <feature-file>
/plan <feature-file>
/iterate <feature-file> adversarial
/iterate <feature-file> enrich
/iterate <feature-file> testability
/iterate <feature-file> freeze
/box set <module>
/box plan <plan-file>
/box freeze-check
/box allow-files-from-plan
/phase set WRITE_TESTS
/write-tests <feature-file>
/box run-red pytest ...
/phase set IMPLEMENTING
/implement <feature-file>
/box run-green pytest ...
/phase set REVIEWING
/review <feature-file>
```

## What to observe

- Do prompts ask for correct context?
- Does Section 14 list the right files?
- Does governance block the right things?
- Are RED/GREEN commands usable?
- Does review-only mode prevent drift?
- Are error messages clear?

## Output

Create a short lessons-learned file:

```text
.pi/_wip/harness-real-feature-validation.md
```

Include:

- feature used
- what worked
- what was confusing
- governance false positives
- governance false negatives
- prompt improvements needed

## Stop conditions

Stop if the feature requires changing application architecture or conflicts with MVP scope.
