# 03 — Harden Manual RED/GREEN Commands

## Purpose

Prevent manual RED/GREEN commands from becoming an agent-callable bypass.

Current manual commands:

```text
/box mark-red <note>
/box mark-green <note>
```

Safer automatic commands already exist:

```text
/box run-red <pytest-command>
/box run-green <pytest-command>
```

## Why this matters

The original governance plan says RED/GREEN are human gates. If the agent can set these flags itself, the gate can become theater.

## Preferred behavior

- `/box run-red` and `/box run-green` remain the normal workflow.
- `/box mark-red` and `/box mark-green` remain emergency/manual fallback.
- Manual commands require UI confirmation.
- In no-UI mode, manual commands block.

## Implementation options

### Option A — Require UI confirmation

Best short-term option.

- Modify command handling so manual mark commands return a confirm decision or call confirmation path.
- If `ctx.hasUI === false`, block.

### Option B — Disable manual commands

Strictest option.

- Remove or reject `/box mark-red` and `/box mark-green`.
- Require `/box run-red` and `/box run-green` only.

### Option C — Actor/source metadata

Best long-term option only if Pi exposes reliable actor metadata.

## Recommended implementation

Use Option A now.

## Validation

- `/box mark-red note` prompts in UI.
- `/box mark-green note` prompts in UI.
- In no-UI mode, both block.
- `/box run-red pytest ...` still works.
- `/box run-green pytest ...` still works.

## Stop conditions

Stop if Pi slash command events cannot be confirmed cleanly from the current engine structure without making slash commands awkward.
