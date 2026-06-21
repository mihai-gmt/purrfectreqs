# 04 — Add `.pi/README.md` Command and Harness Reference

## Purpose

Document how to use the project-local Pi harness.

## Why this matters

The command surface is now large. A developer needs a single place to see the workflow, commands, and expected order.

## Target file

```text
.pi/README.md
```

## Contents to include

1. Harness overview
2. File layout
3. Normal workflow
4. `/box` command reference
5. `/phase` command reference
6. RED/GREEN workflow
7. Section 14 manifest workflow
8. Safety rules enforced by governance
9. Troubleshooting
10. Reload checklist

## Normal workflow to document

```text
/box set <module>
/box plan <plan-file>
/box freeze-check
/box allow-files-from-plan
/phase set WRITE_TESTS
/box run-red pytest ...
/phase set IMPLEMENTING
/box run-green pytest ...
/phase set REVIEWING
```

## Important warnings

- `.feature` files are hard-blocked.
- `.env`, `.git`, `.venv`, and `node_modules` are hard-blocked.
- Confirmation decisions block when no UI exists.
- Manual RED/GREEN commands are fallback only.

## Validation

- README matches implemented command names.
- README mentions actual current file paths:

```text
.pi/extensions/governance.ts
.pi/governance/config.ts
.pi/governance/engine.ts
```

- README does not duplicate full project law from `CLAUDE.md`.

## Stop conditions

Stop if README starts to become a second constitution. It should reference `CLAUDE.md`, not replace it.
