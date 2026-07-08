# PurrfectReqs Pi Harness

This directory contains the project-local Pi harness for PurrfectReqs.

The harness does not replace `CLAUDE.md`. `CLAUDE.md` remains the project constitution. This README is only a practical command and troubleshooting reference.

## Workflow

The harness drives a spec-first, phase-gated, test-first pipeline. Every feature starts from a `.feature` file and moves through planning, into governed execution. There are two kinds of commands:

- **Prompt commands** (`/preplan`, `/plan`, `/iterate`, `/write-tests`, `/implement`, `/review`) — each loads a role-specific prompt that drives the agent through one workflow step.
- **Control commands** (`/box`, `/phase`) — human-only governance commands you run to set the gates (workflow phase, Feature Box scope, RED/GREEN confirmation). The agent cannot invoke these. Full reference further below.

Substitute `<module>` (e.g. `auth`) and `<feature>` (e.g. `login`) throughout. The feature file is `tests/features/<module>/<feature>.feature`; the plan file is `tests/bdd/plans/<module>_<feature>.plan.md`.

### Stage 1 — Planning (produces a FROZEN plan)

```text
/preplan tests/features/<module>/<feature>.feature
/plan    tests/features/<module>/<feature>.feature
/iterate tests/features/<module>/<feature>.feature adversarial
/iterate tests/features/<module>/<feature>.feature enrich
/iterate tests/features/<module>/<feature>.feature testability
/iterate tests/features/<module>/<feature>.feature freeze
```

Phase gating is optional during planning (phase `IDLE` is permissive). For stricter enforcement you may set the matching phase first — `/phase set PREPLAN` before `/preplan`, `/phase set PLANNING` before `/plan`, `/phase set ITERATING` before the `/iterate` lenses — so only the expected artifact class is writable at each step.

### Stage 2 — Governed execution (requires the FROZEN plan)

```text
/box set <module>
/box plan tests/bdd/plans/<module>_<feature>.plan.md
/box freeze-check
/box allow-files-from-plan
/phase set WRITE_TESTS
/write-tests tests/features/<module>/<feature>.feature
/box run-red pytest tests/bdd/step_defs/test_<feature>.py -v
/phase set IMPLEMENTING
/implement tests/features/<module>/<feature>.feature
/box run-green pytest tests/bdd/step_defs/test_<feature>.py -v
/phase set REVIEWING
/review tests/features/<module>/<feature>.feature
```

### What each step does

| Command | What it does |
|---------|--------------|
| `/preplan <feature>` | Analyzes the existing codebase against the feature and writes `tests/bdd/plans/<module>_<feature>.analysis.md`. Documentarian only — no plans, code, or tests. |
| `/plan <feature>` | Reads the `.feature` and its analysis, then produces the implementation plan through iterative discussion with you. Writes the plan as `Status: DRAFT`. Requires the analysis file (run `/preplan` first) and a `# Type:` comment in the feature. No code or tests. |
| `/iterate <feature> adversarial` | Applies the adversarial lens to the draft plan and proposes targeted changes after your approval. |
| `/iterate <feature> enrich` | Applies the enrich lens — fills gaps and missing detail in the plan. |
| `/iterate <feature> testability` | Applies the testability lens — makes scenarios concretely testable. |
| `/iterate <feature> freeze` | Final lens. Runs the freeze checks and, once satisfied, promotes the plan from `DRAFT` to `FROZEN`. |
| `/write-tests <feature>` | Reads only the files the frozen plan specifies and writes pytest-bdd step definitions and unit tests that fail because the code does not exist yet. No implementation, no `.feature` edits. |
| `/implement <feature>` | Writes the minimum production-quality code to make the failing tests pass, following the frozen plan exactly. Stops and reports if reality does not match the plan. No test edits, no scope expansion. |
| `/review <feature>` | Read-only. Produces a pass/fail/N-A compliance check plus learning notes. Cannot change code. |

### Control commands used between steps

| Command | What it does |
|---------|--------------|
| `/box set <module>` | Restricts app-module source writes to that module (Feature Box scope). |
| `/box plan <plan-file>` | Points governance at the active plan file (used for the FROZEN check and manifest import). |
| `/box freeze-check` | Verifies the plan's freeze prerequisites (the three prior scopes ran, no unresolved escalations). |
| `/box allow-files-from-plan` | Imports the writable test/implementation files from Section 14 of the FROZEN plan into the allowlist. |
| `/phase set <PHASE>` | Moves the workflow phase (`WRITE_TESTS`, `IMPLEMENTING`, `REVIEWING`, …), which controls which file class may be written. |
| `/box run-red <pytest-command>` | Executes pytest and confirms RED only when it shows genuine failing tests. Gate for entering implementation. |
| `/box run-green <pytest-command>` | Executes pytest and confirms GREEN only when it passes cleanly. Gate for entering review. |

The `/write-tests`, `/implement`, and `/review` prompts will refuse to proceed and tell you which control commands to run if the required governance state is not set.

## File layout

```text
.pi/settings.json                 # Project-local Pi settings
.pi/prompts/                      # Native Pi prompt templates
.pi/extensions/governance.ts      # Pi extension entrypoint (adapter)
.pi/governance/config.ts          # PurrfectReqs governance configuration/prose
.pi/governance/engine.ts          # Governance engine
.pi/governance/engine.test.ts     # node:test coverage for the engine's pure functions
.pi/feature-box.json              # Generated workflow state, when active
.pi/sessions/                     # Local Pi sessions, gitignored
.pi/_wip/                         # Harness plans, assessments, backups
```

Only `.pi/extensions/governance.ts` should live in `.pi/extensions/` as a TypeScript entrypoint. Helper modules belong outside `.pi/extensions/`.

## How governance is wired

The extension exposes two distinct surfaces, bound to two distinct Pi mechanisms. Keep them separate when reasoning about behavior:

- **Enforcement gates** — registered on `pi.on("tool_call")`. The agent's `edit`, `write`, and `bash` calls flow through here; the engine returns `{ block: true, reason }` to veto a call, or asks for confirmation. This is the always-on layer that blocks `.feature`/protected-path edits, banned dependencies, naive UTC, browser token storage, cross-module model imports, out-of-box source edits, and file-writing bash commands.
- **Control plane** — `/box` and `/phase` are registered with `pi.registerCommand(...)`. Registered slash commands are **not** part of the LLM tool registry, so only the human can invoke them. Phase transitions, Feature Box scope, `allow-core`, manifest imports, and RED/GREEN confirmation are therefore human-only by construction — the agent cannot promote its own gates. Command output is shown via the UI notification channel.

A consequence worth remembering: until the human drives `/box` and `/phase`, the workflow state stays at its defaults (`phase: IDLE`, empty scope), so the stateful gates (FROZEN-before-write, RED-before-implement, manifest allowlists) are dormant. The stateless gates above still apply in every phase.

## Testing

The engine's pure functions (path classification, pytest-command parsing, RED/GREEN validation, bash write-target extraction, freeze-check, Section 14 manifest parsing) are covered by `node:test`. Run from the project root with no extra dependencies (Node >= 22.18 strips TypeScript types):

```text
node --test .pi/governance/engine.test.ts
```

Stateful feature-box file I/O and the Pi adapter wiring are not unit-tested; verify those in a live Pi session.

## Model and packaging policy

**You choose the coding model PI runs.** Set `defaultProvider`, `defaultModel`, and `enabledModels` in `.pi/settings.json`. The harness is model-agnostic — the prompts and governance gates make no assumption about which model drives them. Pick for the workload: the governed phases (`/write-tests`, `/implement`, `/review`) reward a model that follows strict instructions reliably.

Two things to know before you pick:

- **Anthropic (`claude-*`) through PI bills separately.** Since 2026-06-15, using Claude models via a third-party harness (PI is one) draws on a separate Agent-SDK credit pool, not your Claude subscription. Restrict `enabledModels` to exclude `claude-*` if you want to prevent selecting it by accident. Claude Code (the first-party harness) is where Claude runs on the subscription. (Billing terms change and are account-dependent — verify the current terms; this only records what was true when the policy was written.)
- **Local Ollama models** are fine for low-risk read-only work but must be validated before any governed phase — see `MODEL_POLICY.md`.

PurrfectReqs *application* AI runs offline/local via Ollama; that constrains the app being built, not the coding model you drive PI with.

This project's current pinned choice and full rationale live in `MODEL_POLICY.md`. Packaging, generic app-agnostic extraction, and custom context-router tooling are deferred. Keep this harness project-local until it has been validated on a brand-new feature end to end.

See:

```text
.pi/MODEL_POLICY.md
.pi/PACKAGING_DECISION.md
.pi/APP_AGNOSTIC_EXTRACTION_DECISION.md
.pi/CONTEXT_ROUTER_DECISION.md
```

## Prompt commands

Pi loads these prompt templates:

```text
/preplan <feature-file>
/plan <feature-file>
/iterate <feature-file> <adversarial|enrich|testability|freeze>
/write-tests <feature-file>
/implement <feature-file>
/review <feature-file>
```

Recommended planning order:

```text
/preplan tests/features/<module>/<feature>.feature
/plan tests/features/<module>/<feature>.feature
/iterate tests/features/<module>/<feature>.feature adversarial
/iterate tests/features/<module>/<feature>.feature enrich
/iterate tests/features/<module>/<feature>.feature testability
/iterate tests/features/<module>/<feature>.feature freeze
```

## Normal governed workflow

After the plan is frozen, initialize the Feature Box and phase gates:

```text
/box set <module>
/box plan tests/bdd/plans/<module>_<feature>.plan.md
/box freeze-check
/box allow-files-from-plan
/phase set WRITE_TESTS
/write-tests tests/features/<module>/<feature>.feature
/box run-red pytest tests/bdd/step_defs/test_<feature>.py -v
/phase set IMPLEMENTING
/implement tests/features/<module>/<feature>.feature
/box run-green pytest tests/bdd/step_defs/test_<feature>.py -v
/phase set REVIEWING
/review tests/features/<module>/<feature>.feature
```

## Governance footer status

The governance extension adds a compact persistent status segment to Pi's footer using `ctx.ui.setStatus`. It does not replace Pi's built-in footer, so token usage, context size, cost, working directory, and model details remain visible.

Format:

```text
Gov <PHASE> | Plan: <STATUS> | RED: <yes|no> | GREEN: <yes|no> | Box: <module|->
```

The status refreshes on session start and after `/box` or `/phase` commands. For details, use:

```text
/box status --verbose
/phase status --verbose
```

## `/box` command reference

### Status and scope

```text
/box status
/box status --verbose
/box set <module>
/box clear
```

- `status` prints raw Feature Box state.
- `status --verbose` prints a human-readable gate summary.
- `set` restricts app-module writes to the named module.
- `clear` resets Feature Box state.

### Plan and manifest gates

```text
/box plan <plan-file>
/box freeze-check
/box allow-files-from-plan
/box allow-file <path>
/box clear-allowed-files
```

- `plan` sets the active plan file.
- `freeze-check` verifies freeze prerequisites in the plan.
- `allow-files-from-plan` imports writable test and implementation files from Section 14 of a FROZEN plan.
- `allow-file` manually allows one approved file.
- `clear-allowed-files` clears imported/allowed manifests.

### RED/GREEN validation

```text
/box run-red <pytest-command>
/box run-green <pytest-command>
/box clear-test-state
```

- `run-red` executes pytest and confirms RED only when pytest shows valid failing tests.
- `run-green` executes pytest and confirms GREEN only when pytest passes cleanly.
- `clear-test-state` clears RED/GREEN state.

Disabled commands:

```text
/box mark-red <note>
/box mark-green <note>
```

Manual RED/GREEN attestation is disabled. Use `run-red` and `run-green` so validation is based on actual pytest execution.

### Core exception

```text
/box allow-core <reason>
/box disallow-core
```

Use only after explicit developer confirmation. `app/core/*` is shared infrastructure and normally requires escalation.

### Phase shortcut

```text
/box phase <PHASE>
```

Equivalent to `/phase set <PHASE>`.

## `/phase` command reference

```text
/phase status
/phase status --verbose
/phase set <PHASE>
/phase clear
```

Valid phases:

```text
IDLE
PREPLAN
PLANNING
ITERATING
WRITE_TESTS
IMPLEMENTING
REVIEWING
```

Phase write behavior:

- `IDLE`: legacy/permissive mode.
- `PREPLAN`: only analysis files under `tests/bdd/plans/*.analysis.md`.
- `PLANNING`: only plan files under `tests/bdd/plans/*.plan.md`.
- `ITERATING`: only plan files under `tests/bdd/plans/*.plan.md`.
- `WRITE_TESTS`: only approved test files from Section 14.
- `IMPLEMENTING`: only approved implementation files from Section 14, after RED.
- `REVIEWING`: only review artifact files under `tests/bdd/plans/*.review.md`, after GREEN.

## Section 14 manifest workflow

The frozen plan's Section 14 is the write manifest used by governance.

It should separate:

```text
Files to READ before writing tests
Files to CREATE/MODIFY during test writing
Files to READ before implementing
Files to CREATE/MODIFY during implementation
```

`/box allow-files-from-plan` imports only recognized writable test and implementation files. It intentionally skips `.feature` files, docs, read-only sections, and ambiguous entries.

## Safety rules enforced

The governance extension enforces several project rules before tool execution:

- `.feature` files are hard-blocked from agent modification.
- Protected paths such as `.env`, `.git`, `.venv`, and `node_modules` are hard-blocked.
- Phase write rules restrict which file classes can be edited.
- Feature Box rules block cross-module source edits.
- `app/core/*` requires explicit allowance.
- Dangerous or non-allowlisted bash commands require confirmation.
- Bash commands that write files are routed through the same path rules as direct writes.
- Banned dependencies are blocked.
- Naive UTC time patterns are blocked.
- Token storage in browser storage is blocked.
- Cross-module SQLAlchemy model imports are blocked.

When a confirmation is required and Pi has no UI, governance blocks instead of silently allowing the action.

## Troubleshooting

### Prompts or extension did not load

Run:

```text
/reload
```

Expected output should include:

```text
[Prompts]
  /implement, /iterate, /plan, /preplan, /review, /write-tests

[Extensions]
  governance.ts
```

The governance extension also registers the `/box` and `/phase` commands. Type `/` at the prompt to confirm they appear in the command list; if they do not, the extension failed to load.

If prompts are missing, check:

```text
.pi/settings.json
.pi/prompts/*.md
```

If extra extensions load, check that `.pi/extensions/` contains only intended extension entrypoints.

### IMPLEMENTING is blocked

Check:

```text
/box status --verbose
```

Common causes:

- plan is not FROZEN
- RED not confirmed with `/box run-red ...`
- Section 14 files not imported with `/box allow-files-from-plan`
- target file is not listed in `allowedImplementationFiles`

### WRITE_TESTS is blocked

Check:

```text
/box status --verbose
```

Common causes:

- plan is not FROZEN
- allowed test files were not imported
- test file is not listed in `allowedTestFiles`

### REVIEWING is blocked

Check:

```text
/box status --verbose
```

Common causes:

- GREEN not confirmed with `/box run-green ...`
- attempting to write something other than a review artifact

## Reload checklist

After changing settings, prompts, or extensions:

```text
/reload
```

Confirm startup shows:

```text
[Context]
  CLAUDE.md

[Prompts]
  /implement, /iterate, /plan, /preplan, /review, /write-tests

[Extensions]
  governance.ts
```

The `governance.ts` extension registers the `/box` and `/phase` commands at load. Confirm both are offered in the `/` command list after reload.
