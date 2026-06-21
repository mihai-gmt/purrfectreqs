# governance.ts Improvement Plan

> **Purpose:** Turn `.pi/extensions/governance.ts` from a first-draft structural guardrail into the deterministic governance layer for the PurrfectReqs Pi harness.
>
> **Source spec:** `WORKFLOW.md`, `CLAUDE.md`, and the existing Claude command workflow under `.claude/commands/`.
>
> **Non-goal for first iteration:** Do not implement the entire workflow engine at once. Build one enforceable gate at a time and validate each in Pi.

---

## Current Assessment

The current `governance.ts` is a strong foundation. It already contains the right design direction:

- a PurrfectReqs-specific `CONFIG` seam at the top
- a generic-ish decision model: `allow`, `block`, `confirm`
- `tool_call` interception
- Feature Box module checks
- `app/core` protection
- dependency governance
- banned dependency blocking
- UTC-time enforcement
- cross-module SQLAlchemy model import detection
- security-sensitive confirmation prompts

However, compared with `WORKFLOW.md`, it currently enforces only part of the workflow.

Current behavior is closest to:

```text
Feature Box + protected path + code-invariant guardrail
```

Target behavior is:

```text
spec-driven, phase-gated, artifact-state workflow governance
```

The most important conceptual change is:

```text
Feature Box must become workflow state, not just module scope.
```

Eventually it should know:

```text
feature file
plan file
current phase
plan status
allowed modules
allowed read files
allowed write files
RED/GREEN confirmation
escalation approvals
```

---

## Guiding Principles

- [ ] Keep project-specific values in one config seam.
- [ ] Keep rule logic as app-agnostic as practical.
- [ ] Prefer deterministic blocking for hard invariants.
- [ ] Use confirmation for escalation-worthy actions.
- [ ] Do not silently bypass blocked actions.
- [ ] Build incrementally and validate each gate manually.
- [ ] Do not try to parse every workflow artifact in version 1.
- [ ] Treat `WORKFLOW.md` as the porting spec for behavior.

---

## Scope of Enforcement (what governance does NOT do)

Be honest about coverage so omissions don't look like oversights. Some `WORKFLOW.md`
mechanics cannot be deterministically enforced from a `tool_call` hook and remain
**prose-enforced** (via `PROSE_RULES`) or **session-discipline**:

| Mechanism | Why not code-enforced | Where it lives |
|---|---|---|
| "Read ONLY the files the plan lists" | Blocking reads is noisy and low-value vs blocking writes | prose |
| Analysis-required-before-plan | Requires interpreting workflow stage, not a tool signal | prose |
| Plan approval loops (Loop 1 / Loop 2) | Human-judgment dialogue, not a detectable action | prose |
| Per-phase manual verification | Human action between phases | prose |
| Context clearing between stages | Handled by sessions/handoff, not governance | session discipline |

Everything else in this plan IS code-enforceable and is the target of the phases below.

---

# Phase 0 — Make the Extension API-Correct

## Goal

Ensure the extension actually loads, prompts, and injects instructions using Pi's documented extension API.

## Required updates

- [ ] Replace assumed `ctx.ui.confirm` object-call style with documented Pi signature.

Current draft:

```ts
ctx?.ui?.confirm?.({ message: "...", defaultValue: false })
```

Target style:

```ts
await ctx.ui.confirm("Governance confirmation", message)
```

- [ ] Replace mutation-based `before_agent_start` handling with documented return shape.

Current draft:

```ts
event.systemPromptOptions.appendedText = ...
```

Target style:

```ts
return {
  systemPrompt: event.systemPrompt + "\n\n" + PROSE_RULES,
};
```

- [ ] Prefer typed extension entrypoint.

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ...
}
```

- [ ] Keep defensive event normalization, but verify actual field names in a live Pi session.

Expected documented shape:

```ts
event.toolName
event.input
```

## Acceptance criteria

- [ ] Pi starts with the extension loaded.
- [ ] `/reload` reloads the extension without errors.
- [ ] A deliberately confirmed command shows a confirmation prompt.
- [ ] The prose rules are actually included in the system prompt for a turn.

---

# Phase 1 — Safety-Critical Hardening

## Goal

Close gaps that could allow the agent to violate non-negotiable project rules before phase-gating exists.

## 1. Block `.feature` edits

`WORKFLOW.md` and `CLAUDE.md` both define `.feature` files as contracts.

Add a hard block:

```ts
if (p.endsWith(".feature")) {
  return block("Feature files are source-of-truth contracts and must not be modified by the agent.");
}
```

Acceptance:

- [ ] Attempting to write/edit `tests/features/**/*.feature` is blocked.

## 2. Block obvious protected paths

Add hard blocks for:

```text
.env
.env.*
.git/
.venv/
node_modules/
```

Acceptance:

- [ ] Editing `.env` is blocked.
- [ ] Editing `.git/config` is blocked.
- [ ] Editing files under `.venv/` or `node_modules/` is blocked.

## 3. Harden bash governance

Current allowlist is too broad because it silently allows all `git` and all `alembic` commands.

Dangerous checks must run before allowlist checks.

Confirm or block patterns like:

```text
rm -rf
sudo
chmod 777
chown
git reset --hard
git clean -fd
git push
pip install
uv add
poetry add
npm install
alembic downgrade
```

Replace broad allowlist entries:

```text
git
alembic
```

with narrower safe commands:

```text
git status
git diff
git log
git show
git branch --show-current
alembic current
alembic heads
alembic history
alembic upgrade head
```

Acceptance:

- [ ] `pytest ...` runs silently.
- [ ] `ruff check .` runs silently.
- [ ] `git status` runs silently.
- [ ] `git reset --hard` prompts or blocks.
- [ ] `git push` prompts or blocks.
- [ ] `alembic downgrade ...` prompts or blocks.
- [ ] `pip install ...` prompts or blocks.

## 4. Close the bash file-write bypass (CRITICAL)

This is the single most important gap. Every Feature Box, phase, and `.feature`
protection is built on the `edit`/`write` tools — but **bash can write files too**,
bypassing all of it. The current draft even admits this in its own confirm message.

Without this rule, governance gives a false sense of safety: the agent can do
`echo ... > app/other/service.py` and skip every edit-time gate.

Detect write-capable bash and route it through the SAME path rules as edits
(or block/confirm it). Patterns to catch:

```text
>   >>            (redirection to a file)
| tee  / tee      (write via tee)
sed -i, perl -i   (in-place edit)
cat > PATH, heredoc (cat <<EOF > PATH)
python -c / python - with open(..., 'w'|'a')
cp, mv, dd, install  targeting app/ or tests/
```

Implementation approach:

- [ ] Add `evaluateBashWrite(command)` that extracts target paths from redirects/
      in-place flags and runs them through `evaluateEdit`'s path rules (Feature Box,
      phase class, `.feature`, protected paths).
- [ ] If a write target cannot be safely parsed, default to **confirm** (or block in
      non-interactive mode).
- [ ] Keep this check BEFORE the allowlist so `tee`/`sed -i` cannot slip through.

Acceptance:

- [ ] `echo x > app/other/service.py` is blocked/confirmed per Feature Box rules.
- [ ] `sed -i '...' app/auth/service.py` outside the box is blocked.
- [ ] `cat > tests/features/x.feature` is blocked (`.feature` is a contract).
- [ ] `python -c "open('app/x.py','w')..."` is confirmed/blocked.
- [ ] `pytest`, `ruff`, `git status` (no redirection) still run silently.

## 5. Protect authority documents

`CLAUDE.md`'s document-authority hierarchy and `WORKFLOW.md` treat these as
high-authority. The draft only protects `.env`/`.git`. Add a **confirm** gate
(not a hard block — the developer may legitimately edit them) for:

```text
CLAUDE.md
WORKFLOW.md
docs/SECURITY.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
docs/SCOPE.md
docs/TECH_STACK.md
```

Rationale: an implementer agent should never silently rewrite the rules it is
governed by. A confirmation makes such edits deliberate.

Acceptance:

- [ ] Editing `docs/SECURITY.md` prompts for confirmation.
- [ ] Editing `CLAUDE.md` prompts for confirmation.
- [ ] Editing an ordinary `docs/<module>.md` note does not (unless a later phase
      rule blocks docs entirely).

## 6. Define evaluation order explicitly

Once phases exist, rule precedence matters. Example hazard: in `WRITE_TESTS`,
`tests/**` is writable, but `tests/features/**/*.feature` lives under `tests/` —
so the `.feature` hard block MUST win over the phase allow-list.

Pin this fixed order in code and in the plan:

```text
1. HARD blocks      (.feature, .env, .git/, .venv/, node_modules/)
2. content invariants (UTC, cross-module model imports, banned deps)
3. phase write-class rules (per current phase)
4. Feature Box module rules (in-scope modules, app/core)
5. soft confirms    (deps, config/env, auth dirs, authority docs, secrets)
```

Acceptance:

- [ ] `.feature` edit is blocked even in `WRITE_TESTS` where `tests/` is allowed.
- [ ] A banned dependency is blocked regardless of phase.

## 7. Specify non-interactive behavior

Mirror the `permission-gate.ts` example: when there is no UI to confirm with,
fail safe.

```text
If ctx.hasUI is false, every "confirm" decision becomes "block".
```

Do this explicitly rather than relying on optional-chaining returning `undefined`
(which the current draft does by accident).

Acceptance:

- [ ] In a non-interactive run, a "confirm" action is blocked, not silently allowed.

---

# Phase 2 — Make Feature Box Usable

## Goal

Move Feature Box from a manually edited JSON file to a first-class Pi command interface.

## Current state

The draft reads:

```text
.pi/feature-box.json
```

but does not provide commands to manage it.

## Target state file

Initial version:

```json
{
  "featureFile": "tests/features/auth/basic_login.feature",
  "planFile": "tests/bdd/plans/auth_basic_login.plan.md",
  "phase": "IDLE",
  "inScope": ["auth"],
  "allowCore": false,
  "allowCoreReason": null,
  "allowedFiles": [],
  "redConfirmed": false,
  "greenConfirmed": false,
  "escalationApprovals": []
}
```

Keep it simple at first. Only `inScope` and `allowCore` need to be enforced immediately.

## Commands to add

- [ ] `/box status`
- [ ] `/box set <module>`
- [ ] `/box clear`
- [ ] `/box allow-core <reason>`
- [ ] `/box disallow-core`

Optional later:

- [ ] `/box feature <feature-file>`
- [ ] `/box plan <plan-file>`
- [ ] `/box allow-file <path>`
- [ ] `/box phase <phase>`

## Acceptance criteria

- [ ] `/box status` shows current Feature Box state.
- [ ] `/box set auth` writes `.pi/feature-box.json`.
- [ ] With `inScope: ["auth"]`, edits under `app/auth/` are allowed.
- [ ] With `inScope: ["auth"]`, edits under another `app/<module>/` are blocked.
- [ ] Edits under `app/core/` are blocked unless `allowCore` is enabled.
- [ ] `/box clear` removes or resets the Feature Box.

---

# Phase 3 — Add Phase State

## Goal

Represent the workflow phases from `WORKFLOW.md` so governance can enforce role-specific write boundaries.

## Initial phases

Use a small phase set first:

```text
IDLE
PREPLAN
PLANNING
ITERATING
WRITE_TESTS
IMPLEMENTING
REVIEWING
```

Later phases can include:

```text
FROZEN
TESTS_RED
GREEN
REVIEWED
```

## Commands

- [ ] `/phase status`
- [ ] `/phase set <phase>`
- [ ] `/phase clear`

Or combine with `/box`:

```text
/box phase IMPLEMENTING
```

## Path classification helper

Add:

```ts
type PathClass =
  | "feature"
  | "analysis"
  | "plan"
  | "review"
  | "test"
  | "source"
  | "migration"
  | "doc"
  | "config"
  | "unknown";
```

Classify paths such as:

```text
tests/features/**/*.feature          -> feature
tests/bdd/plans/*.analysis.md        -> analysis
tests/bdd/plans/*.plan.md            -> plan
tests/bdd/plans/*.review.md          -> review
tests/bdd/step_defs/**/*.py          -> test
tests/unit/**/*.py                   -> test
app/core/**                          -> core      (classify BEFORE generic source)
app/**/*.py                          -> source
alembic/versions/**/*                -> migration
docs/**/*.md                         -> doc
```

Note: `app/core/**` must be classified as its own `core` class, not lumped into
`source`, because it has dedicated escalation rules.

## Phase write rules

### `PREPLAN`

Allowed writes:

```text
tests/bdd/plans/*.analysis.md
```

Blocked:

```text
app/
tests/bdd/step_defs/
tests/unit/
*.feature
```

### `PLANNING`

Allowed writes:

```text
tests/bdd/plans/*.plan.md
```

Blocked:

```text
app/
tests/
*.feature
```

### `ITERATING`

Allowed writes:

```text
tests/bdd/plans/*.plan.md
```

Blocked:

```text
app/
tests/bdd/step_defs/
tests/unit/
*.feature
```

### `WRITE_TESTS`

Allowed writes:

```text
tests/bdd/step_defs/**/*.py
tests/unit/**/*.py
```

Blocked:

```text
app/
*.feature
```

### `IMPLEMENTING`

Allowed writes:

```text
app/<in-scope-module>/**
alembic/versions/** if schema work is expected
plan file checkbox updates
```

Blocked:

```text
tests/bdd/step_defs/**/*.py
tests/unit/**/*.py
*.feature
```

### `REVIEWING`

Allowed writes:

```text
tests/bdd/plans/*.review.md
```

Blocked:

```text
app/
tests/bdd/step_defs/
tests/unit/
*.feature
```

## Acceptance criteria

- [ ] In `WRITE_TESTS`, edits under `app/` are blocked.
- [ ] In `IMPLEMENTING`, edits under `tests/` are blocked.
- [ ] In `REVIEWING`, source and test edits are blocked.
- [ ] In `PLANNING`, source and test edits are blocked.
- [ ] Review file writing is allowed during `REVIEWING`.

---

# Phase 4 — Add Plan Status Gates

## Goal

Enforce the artifact gates from `WORKFLOW.md`:

```text
DRAFT -> FROZEN
FROZEN required before write-tests and implement
```

## Plan parser

Add a helper that reads the current plan file from Feature Box state and extracts status.

Supported patterns should tolerate Markdown variation:

```text
Status: DRAFT
Status: FROZEN
**Status:** DRAFT
**Status:** FROZEN
```

Return:

```ts
type PlanStatus = "DRAFT" | "FROZEN" | "UNKNOWN" | "MISSING";
```

## Enforcement

- [ ] Entering or operating in `WRITE_TESTS` requires plan status `FROZEN`.
- [ ] Entering or operating in `IMPLEMENTING` requires plan status `FROZEN`.
- [ ] If plan is `DRAFT`, block and instruct to run freeze.

Message:

```text
PLAN IS NOT FROZEN
The plan must be frozen before writing tests or implementing.
Run: /iterate <feature-file> freeze
```

## Acceptance criteria

- [ ] With `Status: DRAFT`, `WRITE_TESTS` writes are blocked.
- [ ] With `Status: DRAFT`, `IMPLEMENTING` writes are blocked.
- [ ] With `Status: FROZEN`, phase writes proceed subject to phase/file rules.

---

# Phase 5 — Add RED/GREEN Confirmation Gates

## Goal

Model test-state gates without making the extension run expensive commands automatically.

`WORKFLOW.md` requires:

```text
RED before IMPLEMENTING
GREEN before REVIEWING
```

## State fields

Add:

```json
{
  "redConfirmed": false,
  "greenConfirmed": false,
  "redCommand": null,
  "greenCommand": null
}
```

## Commands

- [ ] `/box mark-red <command-or-note>`
- [ ] `/box mark-green <command-or-note>`
- [ ] `/box clear-test-state`

## Enforcement

- [ ] `IMPLEMENTING` requires `redConfirmed: true`.
- [ ] `REVIEWING` requires `greenConfirmed: true`.
- [ ] Gating is evaluated at **tool_call time** against persisted `feature-box.json`
      state. `/box` and `/phase` commands only mutate state; they do not enforce.

## Trust boundary (important)

`mark-red` / `mark-green` are **human attestations**, not agent self-certification.
If the agent can flip these flags, the gate is theater — it could mark itself RED
and proceed. `WORKFLOW.md` treats RED/GREEN as hard gates.

- [ ] Document that `/box mark-red` and `/box mark-green` are developer-run only.
- [ ] Preferred hardening (later): have governance run pytest itself and parse the
      result instead of trusting a manual flag.

## Acceptance criteria

- [ ] Attempting to enter or write in `IMPLEMENTING` without RED confirmation blocks.
- [ ] After `/box mark-red`, implementation writes are allowed subject to Feature Box rules.
- [ ] Attempting to enter or write in `REVIEWING` without GREEN confirmation blocks.
- [ ] After `/box mark-green`, review file writes are allowed.

---

# Phase 6 — Section 14 File Manifest Enforcement

## Goal

Move from module-level enforcement to exact file-manifest enforcement.

`WORKFLOW.md` says Section 14 is the hand-off protocol. Downstream agents should read/write only what the plan lists.

## Initial approach

Start with manual allowed files in Feature Box state:

```json
{
  "allowedReadFiles": [],
  "allowedWriteFiles": []
}
```

Commands:

```text
/box allow-file <path>
/box allow-files-from-plan
```

## Later approach

Parse Section 14 from plan file.

Expected sections may include:

```text
Files to READ before writing tests
Files to CREATE/MODIFY while writing tests
Files to READ before implementing
Files to CREATE/MODIFY while implementing
```

## Enforcement

- [ ] During `WRITE_TESTS`, allow only test files listed for creation/modification.
- [ ] During `IMPLEMENTING`, allow only implementation files listed for creation/modification.
- [ ] Allow plan checkbox updates during `IMPLEMENTING`.

## Acceptance criteria

- [ ] An in-module but unlisted source file is blocked during `IMPLEMENTING`.
- [ ] A listed source file is allowed.
- [ ] A listed test file is allowed during `WRITE_TESTS`.
- [ ] An unlisted test file is blocked during `WRITE_TESTS` unless explicitly allowed.

---

# Phase 7 — Freeze Prerequisite Scan

## Goal

Enforce the `/iterate freeze` gate from `WORKFLOW.md`.

Freeze should only pass if the plan changelog shows:

```text
adversarial ran
enrich ran
testability ran
no unacknowledged escalation triggers remain
```

## Suggested implementation

This does not need to be implemented first. It can be exposed as a command:

```text
/freeze-check <plan-file>
```

or:

```text
/box freeze-check
```

The command should inspect Section 15 changelog and report pass/fail.

## Acceptance criteria

- [ ] Missing adversarial changelog entry fails.
- [ ] Missing enrich changelog entry fails.
- [ ] Missing testability changelog entry fails.
- [ ] Unacknowledged escalation text fails.
- [ ] Complete changelog passes.

---

# Phase 8 — Review-Only Enforcement

## Goal

Make `/review` read-only except for the review artifact.

This is partially covered by phase rules, but should be explicitly tested because review drift is high risk.

## Rules

During `REVIEWING`:

Allowed write:

```text
tests/bdd/plans/<module>_<feature>.review.md
```

Blocked writes:

```text
app/**
tests/bdd/step_defs/**
tests/unit/**
tests/features/**
docs/** unless explicitly approved
```

## Acceptance criteria

- [ ] Attempted source edit during review is blocked.
- [ ] Attempted test edit during review is blocked.
- [ ] Review file write is allowed.

---

# Phase 9 — App-Agnostic Extraction Prep

## Goal

Keep the extension extraction-ready while still serving PurrfectReqs now.

## Updates

- [ ] Separate the **rule engine** from the **config** into different files
      (config already lives in a `CONFIG` object — the real work is splitting the
      engine out so the same engine can load different configs).
- [ ] Keep hardcoded PurrfectReqs values only in `CONFIG`.
- [ ] Consider future `.pi/harness.config.json`.
- [ ] Keep path classifiers configurable.

Potential future config:

```json
{
  "projectName": "PurrfectReqs",
  "sourceRoots": ["app"],
  "testRoots": ["tests/bdd/step_defs", "tests/unit"],
  "featurePatterns": ["tests/features/**/*.feature"],
  "planDir": "tests/bdd/plans",
  "coreDirs": ["app/core"],
  "migrationDirs": ["alembic/versions"],
  "dependencyFiles": ["pyproject.toml", "requirements*.txt"],
  "phases": {}
}
```

## Acceptance criteria

- [ ] Adding another project later should not require rewriting the rule engine.
- [ ] PurrfectReqs-specific paths are easy to identify.

---

# Recommended Implementation Order

Do not implement all phases at once.

## Iteration 1 — Reliable guardrail baseline

Implement only:

- [ ] Phase 0 API fixes
- [ ] Phase 1 safety hardening
- [ ] Basic validation in Pi

This gives immediate safety.

## Iteration 2 — Usable Feature Box

Implement only:

- [ ] `/box status`
- [ ] `/box set <module>`
- [ ] `/box clear`
- [ ] `/box allow-core <reason>`

This makes governance usable.

## Iteration 3 — Phase write restrictions

Implement:

- [ ] phase field in state
- [ ] `/phase` or `/box phase`
- [ ] path classification
- [ ] write restrictions for `WRITE_TESTS`, `IMPLEMENTING`, `REVIEWING`

This starts matching `WORKFLOW.md` role isolation.

## Iteration 4 — Artifact gates

Implement:

- [ ] plan status parser
- [ ] FROZEN gate
- [ ] RED confirmation
- [ ] GREEN confirmation

This starts matching the pipeline gates.

## Iteration 5 — Manifest enforcement

Implement:

- [ ] Section 14 manual allow-files first
- [ ] parser later

This turns Feature Box from module-level to exact-file-level governance.

---

# Validation Matrix

| Test | Expected result |
|---|---|
| Edit `.feature` file | Blocked |
| Edit `.env` | Blocked |
| Run `pytest ...` | Allowed |
| Run `git status` | Allowed |
| Run `git reset --hard` | Confirm/block |
| Run `pip install foo` | Confirm/block |
| `echo x > app/other/service.py` (bash write) | Blocked per box rules |
| `sed -i ... app/auth/service.py` out of box | Blocked |
| `cat > tests/features/x.feature` | Blocked (`.feature`) |
| Edit `docs/SECURITY.md` | Confirm |
| Edit `CLAUDE.md` | Confirm |
| Confirm decision with `ctx.hasUI = false` | Blocked (fail-safe) |
| Agent runs `/box mark-green` itself | Disallowed (human-only) |
| `/box set auth`, edit `app/auth/service.py` | Allowed |
| `/box set auth`, edit `app/projects/service.py` | Blocked |
| `/box set auth`, edit `app/core/config.py` | Blocked unless core allowed |
| Phase `WRITE_TESTS`, edit `app/auth/service.py` | Blocked |
| Phase `IMPLEMENTING`, edit `tests/unit/auth/test_service.py` | Blocked |
| Phase `REVIEWING`, edit `app/auth/service.py` | Blocked |
| Phase `REVIEWING`, write review artifact | Allowed |
| Plan `Status: DRAFT`, phase `WRITE_TESTS` | Blocked |
| Plan `Status: FROZEN`, phase `WRITE_TESTS` | Allowed subject to path rules |
| Implement without RED confirmation | Blocked |
| Review without GREEN confirmation | Blocked |

---

# Definition of Done for governance.ts v1

The first trustworthy version of `governance.ts` is done when:

- [ ] Pi loads it without errors.
- [ ] It uses documented Pi API shapes.
- [ ] It blocks `.feature` edits.
- [ ] It blocks protected paths.
- [ ] It confirms or blocks dangerous bash commands before allowlist logic.
- [ ] It provides `/box status`, `/box set`, and `/box clear`.
- [ ] It closes the bash file-write bypass (redirection, `tee`, `sed -i`, heredoc, `python -c`).
- [ ] It confirm-gates authority docs (`CLAUDE.md`, `WORKFLOW.md`, `docs/SECURITY.md`, etc.).
- [ ] It applies a fixed evaluation order (hard blocks before phase/box rules).
- [ ] It blocks (not silently allows) confirm decisions when `ctx.hasUI` is false.
- [ ] It enforces module-level Feature Box boundaries.
- [ ] It blocks `app/core` unless explicitly allowed.
- [ ] It injects prose-only governance reminders correctly.
- [ ] All behavior above has been manually tested in Pi.

After that, phase-gating can be layered in safely.
