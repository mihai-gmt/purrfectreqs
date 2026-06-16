# Pi Harness Migration Plan for PurrfectReqs

> **Purpose:** This document is the working migration guide for turning the current Claude Code workflow into a first-class, project-specific Pi harness.
>
> **Scope:** This is not an application feature plan. It is a harness/customization migration plan for Pi: settings, prompt templates, extensions, workflow enforcement, and optional packaging.
>
> **Intended use:** Work through this document iteratively with an AI agent. Each phase is intentionally small enough to validate before moving on.

---

## 1. Migration Assumption

Yes: the correct approach is to migrate iteratively through the four customization strategies until Pi becomes a harness tailored to the PurrfectReqs workflow.

The end goal is **not** merely to make Pi load `CLAUDE.md`. Pi already does that. The end goal is to make Pi actively support the way this project is built:

- strict document authority
- finely sliced units of work
- BDD/TDD workflow
- feature-file-first development
- escalation protocol
- no scope drift
- phase-specific slash commands
- protected files and command safety
- reproducible local/offline architecture
- junior-developer learning support

The migration should proceed in layers:

1. **Settings and prompt templates** — make Pi understand the existing workflow commands.
2. **Guardrails** — prevent common workflow violations mechanically.
3. **Workflow state enforcement** — make Pi aware of the current lifecycle phase.
4. **Context routing and packaging** — make the harness reusable, maintainable, and context-efficient.

---

## 2. Source Material to Migrate

The current Claude Code setup contains several categories of useful data. They should not all be copied directly into Pi. Each category has a target location.

| Source | Purpose | Pi target |
|---|---|---|
| `CLAUDE.md` | Project constitution and highest-priority agent rules | Keep at repo root; Pi loads it automatically |
| `docs/*.md` | Scope, security, architecture, data model, frontend, guide, glossary, tech stack | Keep as project docs; read selectively |
| `.claude/commands/*.md` | Claude slash-command workflows | Port to `.pi/prompts/*.md` |
| `.claude/commands/scopes/*.md` | Support files for `/iterate` | Keep as support docs or copy under `.pi/prompts/support/`; do not expose as commands |
| `.claude/settings.local.json` | Claude permission intent | Translate into Pi extension behavior |
| Claude memory / main instructions | Personal or project preferences | Classify before migrating; do not dump wholesale |
| Claude hooks, if any | Automation and safety gates | Translate into Pi extensions |
| MCP config, if any | External tools | Inventory; replace with shell tools, skills, or extensions only if needed |

---

## 3. Target Harness Shape

A mature project-local Pi harness may look like this:

```text
.pi/
├── settings.json
├── _wip/
│   └── pi-harness-migration.md
├── prompts/
│   ├── preplan.md
│   ├── plan.md
│   ├── iterate.md
│   ├── write-tests.md
│   ├── implement.md
│   ├── review.md
│   └── support/
│       └── scopes/
│           ├── adversarial.md
│           ├── enrich.md
│           ├── testability.md
│           └── freeze.md
├── extensions/
│   ├── purrfect-guardrails.ts
│   ├── purrfect-workflow.ts
│   └── purrfect-context-router.ts
└── sessions/                  # optional, usually gitignored
```

Later, once stable, the harness can become a reusable Pi package:

```text
purrfectreqs-pi-harness/
├── package.json
├── prompts/
├── extensions/
├── skills/
└── themes/
```

---

## 4. Operating Rules for This Migration

Follow the same discipline used for application work.

### 4.1 One phase at a time

Do not build the full harness in one pass. Complete and validate one phase before starting the next.

### 4.2 Preserve the Claude Code setup until Pi is proven

Do not destructively edit `.claude/commands/*.md` while porting. Copy them into `.pi/prompts/` and adapt the Pi versions.

### 4.3 Do not duplicate project law

Do not copy the entire contents of `CLAUDE.md` or `/docs` into Pi prompts or system prompts. Keep durable project rules in the project docs. Pi prompts should reference them and instruct the agent when to read them.

### 4.4 Prefer enforcement over repeated reminders

Prompt instructions are useful, but Pi extensions should enforce high-risk rules where practical:

- protected files
- dangerous bash commands
- phase-specific file boundaries
- read-only review mode
- no `.feature` modification

### 4.5 Keep project-specific and personal rules separate

- Project rules belong in this repo: `CLAUDE.md`, `/docs`, `.pi/*`.
- Personal cross-project preferences belong globally: `~/.pi/agent/AGENTS.md`.
- Pi-specific supplemental behavior can go in `.pi/APPEND_SYSTEM.md`, but use it sparingly.

---

# Phase 0 — Inventory and Baseline

## Goal

Establish what exists today and decide what will be migrated, rewritten, or ignored.

## Manual tasks

- [ ] List current Claude commands:

  ```bash
  find .claude/commands -maxdepth 2 -type f -name '*.md' -print
  ```

- [ ] Confirm top-level commands:

  ```text
  .claude/commands/preplan.md
  .claude/commands/plan.md
  .claude/commands/iterate.md
  .claude/commands/write-tests.md
  .claude/commands/implement.md
  .claude/commands/review.md
  ```

- [ ] Confirm support scope files:

  ```text
  .claude/commands/scopes/adversarial.md
  .claude/commands/scopes/enrich.md
  .claude/commands/scopes/testability.md
  .claude/commands/scopes/freeze.md
  ```

- [ ] Review `.claude/settings.local.json` and identify permission intent:
  - allowed test/lint commands
  - allowed git commands
  - allowed network domains
  - dangerous commands that should require confirmation
  - files that should be protected

- [ ] Decide whether project-local Pi sessions should be kept in `.pi/sessions`.

- [ ] Add `.pi/sessions/` to `.gitignore` if project-local sessions are enabled.

## AI-agent tasks

Ask the AI agent to:

```text
Review the current Claude Code setup and produce a migration inventory.
Classify each item as:
1. direct Pi prompt candidate
2. support document
3. extension behavior
4. global personal preference
5. obsolete / do not migrate
Do not modify files.
```

## Validation checklist

- [ ] Migration inventory exists in notes or chat.
- [ ] No source files were modified.
- [ ] Claude Code setup remains intact.
- [ ] You know which files will be copied into `.pi/prompts/`.

---

# Phase 1 — Project Pi Settings

## Goal

Create the minimum `.pi/settings.json` needed for the project-local harness.

## Recommended initial `.pi/settings.json`

```json
{
  "defaultProvider": "anthropic",
  "defaultModel": "claude-sonnet-4-20250514",
  "defaultThinkingLevel": "medium",
  "prompts": [
    "./prompts/*.md"
  ],
  "enableSkillCommands": true,
  "compaction": {
    "enabled": true,
    "reserveTokens": 16384,
    "keepRecentTokens": 20000
  },
  "retry": {
    "enabled": true,
    "maxRetries": 3
  },
  "enabledModels": [
    "claude-*"
  ],
  "sessionDir": ".pi/sessions",
  "extensions": [
    "./extensions"
  ]
}
```

## Explanation of each setting

### `defaultProvider`

Sets the default model provider. For a Claude Code migration, `anthropic` is the closest behavioral match.

### `defaultModel`

Sets the model used by default in this repo. Your commands are long and procedural, so use a strong coding model.

### `defaultThinkingLevel`

Sets the default reasoning effort. `medium` is a practical baseline for this workflow. Use `high` for difficult planning or review work.

### `prompts`

Loads native Pi prompt templates from `.pi/prompts/*.md`. Relative paths in `.pi/settings.json` resolve from `.pi/`, so `./prompts/*.md` means `.pi/prompts/*.md`.

### `enableSkillCommands`

Allows actual skills to be invoked via `/skill:name`. This does not affect prompt templates.

### `compaction`

Keeps long sessions usable by summarizing older context. This matters because the workflow reads `.feature` files, plans, docs, tests, and implementation files.

### `retry`

Retries transient provider failures. Useful for multi-step agent workflows.

### `enabledModels`

Limits Ctrl+P model cycling. This prevents accidentally switching to a weak model during strict workflow phases.

### `sessionDir`

Stores Pi sessions under the project. Optional, but useful for project-specific session history.

### `extensions`

Loads project-local extensions from `.pi/extensions/`. This is where guardrails and workflow enforcement will live.

## Manual tasks

- [ ] Create `.pi/settings.json`.
- [ ] Add the initial settings.
- [ ] Create required directories:

  ```bash
  mkdir -p .pi/prompts .pi/extensions .pi/sessions
  ```

- [ ] Trust the project:

  ```text
  /trust
  ```

  or run once with:

  ```bash
  pi --approve
  ```

## AI-agent tasks

Ask the AI agent to:

```text
Review .pi/settings.json for Pi path correctness and project fit.
Do not modify anything unless I explicitly approve.
```

## Validation checklist

- [ ] Pi starts without settings errors.
- [ ] Startup indicates project settings/resources are loaded.
- [ ] Project is trusted.
- [ ] Session directory behavior is understood.

---

# Phase 2 — Port Claude Slash Commands as Native Pi Prompt Templates

## Goal

Convert Claude slash commands into Pi-native prompt templates that preserve the workflow but remove Claude-specific assumptions.

## Why not direct-load `.claude/commands/*.md` forever?

Direct loading is useful for a quick test, but native Pi prompts are safer because:

- Pi templates need explicit `$ARGUMENTS`, `$1`, etc.
- Claude-specific references such as the `Agent` tool may not exist in Pi.
- Pi prompt templates benefit from frontmatter like `description` and `argument-hint`.
- Support files under `scopes/` should not be exposed as slash commands.

## Target files

Create:

```text
.pi/prompts/preplan.md
.pi/prompts/plan.md
.pi/prompts/iterate.md
.pi/prompts/write-tests.md
.pi/prompts/implement.md
.pi/prompts/review.md
```

Optionally copy support docs to:

```text
.pi/prompts/support/scopes/adversarial.md
.pi/prompts/support/scopes/enrich.md
.pi/prompts/support/scopes/testability.md
.pi/prompts/support/scopes/freeze.md
```

If you keep support docs in `.claude/commands/scopes/`, update the Pi prompt text to reference that location explicitly.

## Required Pi prompt frontmatter

Every prompt should start with frontmatter:

```markdown
---
description: Short description shown in Pi autocomplete
argument-hint: "<expected-argument>"
---
```

Example:

```markdown
---
description: Implement a frozen BDD feature plan
argument-hint: "<feature-file>"
---

# /implement — Implementation Agent

User argument: $ARGUMENTS

Follow the implementation workflow for the feature file passed in `User argument`.
```

## Prompt-specific migration notes

### `/preplan`

Current Claude behavior assumes spawning three research agents. Pi does not include Claude Code subagents by default.

Options:

- **Option A:** Rewrite `/preplan` to perform the three analyses sequentially in one agent turn.
- **Option B:** Use a Pi subagent extension/package later.
- **Option C:** Keep the conceptual three-role structure but instruct Pi to run the three research passes using normal tools.

Recommended initial choice: **Option C**, then revisit after guardrails are stable.

Checklist:

- [ ] Add `$ARGUMENTS`.
- [ ] Replace Claude `Agent` tool references with Pi-compatible instructions.
- [ ] Keep the Locator / Analyzer / Pattern Finder roles conceptually.
- [ ] Ensure it writes `tests/bdd/plans/<module>_<feature_name>.analysis.md`.

### `/plan`

The current command maps well to Pi.

Checklist:

- [ ] Add `$ARGUMENTS`.
- [ ] Ensure it still requires `/preplan` output.
- [ ] Ensure it does not read `app/` directly.
- [ ] Ensure feedback loops remain explicit.

### `/iterate`

This command depends on support scope files.

Checklist:

- [ ] Add `$ARGUMENTS`.
- [ ] Confirm scope parsing still works.
- [ ] Update scope file paths if moved to `.pi/prompts/support/scopes/`.
- [ ] Do not expose individual scope files as slash commands.

### `/write-tests`

This command maps well to Pi, but should remain strict.

Checklist:

- [ ] Add `$ARGUMENTS`.
- [ ] Preserve the rule: do not write implementation code.
- [ ] Preserve RED-state confirmation.
- [ ] Preserve `.feature` file authority.

### `/implement`

This command should later be backed by workflow guardrails.

Checklist:

- [ ] Add `$ARGUMENTS`.
- [ ] Preserve the rule: never modify tests.
- [ ] Preserve phase-by-phase verification.
- [ ] Preserve Feature Box reporting.
- [ ] Preserve plan mismatch escalation.

### `/review`

This should be read-only except for writing the review artifact.

Checklist:

- [ ] Add `$ARGUMENTS`.
- [ ] Preserve the rule: never modify source/test files.
- [ ] Preserve compliance checklist.
- [ ] Preserve junior-developer learning notes.

## Manual tasks

- [ ] Copy each `.claude/commands/*.md` file into `.pi/prompts/`.
- [ ] Add Pi frontmatter to each prompt.
- [ ] Add explicit `User argument: $ARGUMENTS` to each prompt.
- [ ] Rewrite Claude-specific tool assumptions.
- [ ] Decide whether support scope files stay under `.claude/` or move under `.pi/prompts/support/`.

## AI-agent tasks

Ask the AI agent to process one prompt at a time:

```text
Port .claude/commands/implement.md to .pi/prompts/implement.md as a native Pi prompt template.
Requirements:
- preserve behavior
- add Pi frontmatter
- add explicit $ARGUMENTS handling
- remove Claude-specific assumptions
- do not modify the original .claude file
After writing, summarize what changed.
```

## Validation checklist

- [ ] `/preplan` appears in Pi slash autocomplete.
- [ ] `/plan` appears in Pi slash autocomplete.
- [ ] `/iterate` appears in Pi slash autocomplete.
- [ ] `/write-tests` appears in Pi slash autocomplete.
- [ ] `/implement` appears in Pi slash autocomplete.
- [ ] `/review` appears in Pi slash autocomplete.
- [ ] Running a prompt with an argument includes the argument in the expanded prompt.
- [ ] Scope support files are not exposed as user-facing commands.

---

# Phase 3 — Build Guardrail Extension

## Goal

Translate high-risk rules from `CLAUDE.md`, `.claude/settings.local.json`, and project docs into mechanical Pi enforcement.

## Target file

```text
.pi/extensions/purrfect-guardrails.ts
```

## Guardrail categories

### 3.1 Protected paths

Block or confirm edits to sensitive files.

Suggested blocked paths:

```text
.env
.env.age
.git/
node_modules/
.venv/
```

Suggested confirmation paths:

```text
CLAUDE.md
docs/SECURITY.md
docs/DATA_MODELS.md
docs/ARCHITECTURE.md
docs/SCOPE.md
docs/TECH_STACK.md
pyproject.toml
requirements.txt
docker-compose.yml
alembic/versions/
```

Reasoning:

- `.env` contains secrets and should not be edited by the agent casually.
- dependency files are governed by `docs/TECH_STACK.md` and require explicit approval.
- security/data-model/architecture docs have high authority.
- migrations can affect database state and should be intentional.

### 3.2 Dangerous bash commands

Confirm or block commands matching patterns like:

```text
rm -rf
sudo
chmod 777
chown
kill
reboot
git reset --hard
git clean -fd
git push
pip install
npm install
alembic downgrade
```

Reasoning:

The Claude permissions file allowed specific commands. Pi does not use that file, so equivalent behavior must be implemented as an extension.

### 3.3 Feature file protection

Block edits to:

```text
*.feature
```

unless the user explicitly asks to modify a feature file.

Reasoning:

`CLAUDE.md` says `.feature` files are contracts. The agent must not modify them to match implementation.

### 3.4 Dependency governance

Require confirmation for edits to:

```text
pyproject.toml
requirements.txt
package.json
package-lock.json
```

and for commands like:

```text
pip install
npm install
```

Reasoning:

The project only allows approved dependencies. Dependency changes are escalation triggers.

## Manual tasks

- [ ] Create `.pi/extensions/purrfect-guardrails.ts`.
- [ ] Start from Pi examples:
  - `permission-gate.ts`
  - `protected-paths.ts`
- [ ] Implement path blocking.
- [ ] Implement confirmation for sensitive paths.
- [ ] Implement dangerous command confirmation.
- [ ] Implement non-interactive defaults: block high-risk actions when no UI is available.

## AI-agent tasks

Ask the AI agent:

```text
Create a Pi extension at .pi/extensions/purrfect-guardrails.ts.
Use Pi's extension API.
Implement:
- block writes/edits to .env, .env.age, .git, node_modules, .venv
- require confirmation for docs/SECURITY.md, docs/DATA_MODELS.md, docs/ARCHITECTURE.md, docs/SCOPE.md, docs/TECH_STACK.md, CLAUDE.md, dependency files, docker-compose.yml, alembic/versions
- require confirmation for dangerous bash commands
- block high-risk actions in non-interactive mode
Do not modify application source files.
```

## Validation checklist

- [ ] Pi loads the extension without errors.
- [ ] Attempting to edit `.env` is blocked.
- [ ] Attempting to edit `docs/SECURITY.md` prompts for confirmation.
- [ ] Attempting `rm -rf` prompts or blocks.
- [ ] Attempting `pip install` prompts or blocks.
- [ ] Normal reads and safe test commands still work.

---

# Phase 4 — Build Workflow-State Extension

## Goal

Make Pi aware of the current PurrfectReqs workflow phase and enforce phase-specific boundaries.

## Target file

```text
.pi/extensions/purrfect-workflow.ts
```

## Desired workflow states

```text
IDLE
PREPLAN
PLAN_DRAFT
ITERATING_ADVERSARIAL
ITERATING_ENRICH
ITERATING_TESTABILITY
FROZEN
TESTS_RED
IMPLEMENTING
GREEN
REVIEWING
REVIEWED
```

## Desired commands

Possible extension commands:

```text
/workflow
/workflow set <state>
/workflow clear
/workflow status
```

Potential automatic detection:

- When `/write-tests` runs, set phase to `TESTS_RED` after RED confirmation.
- When `/implement` runs, set phase to `IMPLEMENTING`.
- When `/review` runs, set phase to `REVIEWING`.

Initial implementation can be manual. Automation can come later.

## Phase-specific rules

### During planning

Allowed:

- read files
- write analysis/plan files

Restricted:

- modifying `app/`
- modifying tests
- modifying `.feature` files

### During `/write-tests`

Allowed:

- write `tests/bdd/step_defs/test_<feature_name>.py`
- write relevant `tests/unit/<module>/...`

Restricted:

- modifying `app/`
- modifying `.feature` files
- modifying docs unless explicitly required

### During `/implement`

Allowed:

- modify files listed in the frozen plan's file manifest
- run tests/lint/format checks
- update plan checkboxes

Restricted:

- modifying test files
- modifying `.feature` files
- touching files outside the Feature Box

### During `/review`

Allowed:

- read source/test/docs
- run test/lint commands
- write `tests/bdd/plans/<module>_<feature_name>.review.md`

Restricted:

- modifying application code
- modifying test files
- modifying `.feature` files

## Manual tasks

- [ ] Define the minimum viable phase states.
- [ ] Decide whether state is manual-only at first.
- [ ] Add a status-line/footer indicator.
- [ ] Add file-write restrictions by phase.
- [ ] Add helpful notifications when an action is blocked.

## AI-agent tasks

Ask the AI agent:

```text
Design a Pi workflow-state extension for this project.
First produce a design only; do not implement.
It should track phases for preplan, plan, iterate, write-tests, implement, and review.
It should enforce phase-specific file boundaries.
It should show current phase in the Pi UI.
```

Then, after approval:

```text
Implement the approved workflow-state extension in .pi/extensions/purrfect-workflow.ts.
Keep the first version simple and manually controlled with /workflow commands.
```

## Validation checklist

- [ ] `/workflow status` works.
- [ ] Current phase appears in the UI.
- [ ] In `REVIEWING`, source edits are blocked.
- [ ] In `IMPLEMENTING`, test edits are blocked.
- [ ] In `WRITE_TESTS` or `TESTS_RED`, `app/` edits are blocked.
- [ ] Manual phase changes are persisted or at least clearly visible during the session.

---

# Phase 5 — Build Context Router

## Goal

Reduce context bloat and improve correctness by helping the agent read the right docs for each task.

## Target implementation options

### Option A: Skill

Create a Pi skill that explains which docs to read for task types.

Example path:

```text
.pi/skills/purrfect-context/SKILL.md
```

### Option B: Extension tool

Create a custom tool:

```text
get_project_context(task_type, feature_type, module)
```

that returns a recommended read list.

### Option C: Prompt-only

Add a standardized context-routing section to every Pi prompt.

Recommended initial choice: **Option C**, then build Option B later if useful.

## Context routing matrix

| Task type | Docs to read |
|---|---|
| API feature planning | `CLAUDE.md`, `.feature`, preplan analysis, `docs/SCOPE.md`, `docs/DATA_MODELS.md`, `docs/SECURITY.md`, `docs/ARCHITECTURE.md`, `docs/GUIDE.md`, `docs/GLOSSARY.md` |
| API implementation | frozen plan, `.feature`, files listed in plan Section 14, relevant parts of `docs/GUIDE.md`, `docs/SECURITY.md`, `docs/DATA_MODELS.md` if DB work |
| UI feature planning | `CLAUDE.md`, `.feature`, preplan analysis, `docs/SCOPE.md`, `docs/SECURITY.md`, `docs/FRONTEND.md`, `docs/TECH_STACK.md`, `docs/ARCHITECTURE.md`, `docs/GLOSSARY.md` |
| UI implementation | frozen plan, `.feature`, files listed in plan Section 14, `docs/FRONTEND.md`, `docs/SECURITY.md`, `docs/TECH_STACK.md` |
| Dependency change | `CLAUDE.md`, `docs/SCOPE.md`, `docs/TECH_STACK.md`, relevant dependency files |
| Security-sensitive change | `CLAUDE.md`, `docs/SECURITY.md`, `docs/ARCHITECTURE.md`, `docs/GUIDE.md` |
| Review | `docs/SECURITY.md`, `docs/GUIDE.md`, `docs/ARCHITECTURE.md`, `.feature`, frozen plan, changed files |

## Manual tasks

- [ ] Add context-routing language to each Pi prompt.
- [ ] Keep prompts from reading all docs unnecessarily.
- [ ] Decide whether a custom context-router extension is worth building.

## AI-agent tasks

Ask the AI agent:

```text
Review the Pi prompt templates and add context-routing instructions.
Do not duplicate project docs.
Ensure each prompt reads only the docs required for that phase.
```

## Validation checklist

- [ ] `/plan` reads all required planning docs.
- [ ] `/implement` reads only the frozen plan's file manifest plus required pattern docs.
- [ ] UI tasks route to `docs/FRONTEND.md` and `docs/TECH_STACK.md`.
- [ ] Dependency tasks route to `docs/TECH_STACK.md`.
- [ ] Prompts do not blindly read every doc every time.

---

# Phase 6 — Optional Local Model Configuration

## Goal

Decide whether Pi should use local Ollama models for any harness tasks.

PurrfectReqs itself is offline/local-AI oriented, but the coding harness can still use Anthropic unless you choose otherwise. If you want Pi to use Ollama, configure Pi custom models separately.

## Target file

```text
~/.pi/agent/models.json
```

## Example Ollama provider

```json
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "compat": {
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false
      },
      "models": [
        {
          "id": "qwen2.5-coder:7b",
          "name": "Qwen 2.5 Coder 7B Local",
          "reasoning": false,
          "input": ["text"],
          "contextWindow": 128000,
          "maxTokens": 8192,
          "cost": {
            "input": 0,
            "output": 0,
            "cacheRead": 0,
            "cacheWrite": 0
          }
        }
      ]
    }
  }
}
```

## Checklist

- [ ] Decide whether coding-agent traffic must be local-only.
- [ ] If yes, configure Ollama in `~/.pi/agent/models.json`.
- [ ] Test `/model` in Pi.
- [ ] Test one read-only prompt with the local model.
- [ ] Do not assume smaller local models can reliably follow the full strict workflow.

---

# Phase 7 — Package the Harness

## Goal

Once prompts and extensions stabilize, package the harness so it can be reused and versioned.

## Package structure

```text
purrfectreqs-pi-harness/
├── package.json
├── prompts/
├── extensions/
├── skills/
└── README.md
```

## Example `package.json`

```json
{
  "name": "purrfectreqs-pi-harness",
  "version": "0.1.0",
  "private": true,
  "keywords": ["pi-package"],
  "pi": {
    "prompts": ["./prompts"],
    "extensions": ["./extensions"],
    "skills": ["./skills"]
  },
  "peerDependencies": {
    "@earendil-works/pi-coding-agent": "*",
    "typebox": "*"
  }
}
```

## Manual tasks

- [ ] Decide whether package should live inside this repo or a separate repo.
- [ ] Move mature prompts/extensions into the package.
- [ ] Keep project-specific docs in PurrfectReqs, not in the package, unless the package is intentionally PurrfectReqs-only.
- [ ] Install locally with Pi package tooling or reference local paths.

## AI-agent tasks

Ask the AI agent:

```text
Design a local Pi package for the stabilized PurrfectReqs harness.
Do not move files yet.
Explain which files should be packaged and which should remain project-local.
```

## Validation checklist

- [ ] Package loads prompts.
- [ ] Package loads extensions.
- [ ] No duplicate prompts appear.
- [ ] Project-local overrides still work.
- [ ] Package source is reviewed before trusting it.

---

# Phase 8 — Hardening and Maintenance

## Goal

Make the harness reliable enough to use daily.

## Hardening checklist

- [ ] Add a `README.md` under `.pi/` or the package explaining the harness.
- [ ] Document every custom extension.
- [ ] Add comments explaining why each protected path exists.
- [ ] Add comments explaining why each dangerous bash pattern exists.
- [ ] Review prompts after several real features.
- [ ] Remove prompt instructions that extensions now enforce.
- [ ] Keep `CLAUDE.md` as the canonical behavior source.
- [ ] Keep `/docs` as the canonical project source.
- [ ] Avoid prompt drift between `.claude/commands` and `.pi/prompts`.
- [ ] Decide whether Claude Code support remains active or Pi becomes the primary harness.

## Regression checklist after Pi updates

- [ ] `pi --version` works.
- [ ] Pi starts in the repo.
- [ ] Project trust still works.
- [ ] Prompt templates appear.
- [ ] Extensions load.
- [ ] Guardrails still block `.env` edits.
- [ ] Dangerous command confirmation still works.
- [ ] Workflow-state command still works.
- [ ] A read-only `/review` dry run behaves as expected.

---

# Suggested Agent Collaboration Pattern

Use the following pattern for each phase.

## 1. Ask for design first

```text
Design Phase N of the Pi harness migration.
Do not write files yet.
Give me:
- files to create/modify
- risks
- validation steps
- recommended implementation order
```

## 2. Approve a small file set

Keep each implementation task to 1-3 files.

```text
Implement only the approved changes for Phase N.
Do not touch application code.
Do not modify .feature files.
Afterward, show exact files changed and validation steps.
```

## 3. Validate manually

Run Pi, invoke commands, and test guardrails.

## 4. Record lessons

Update this migration doc or a harness README with what changed.

---

# Final End-State Checklist

The Pi harness migration is complete when:

- [ ] Pi loads project settings from `.pi/settings.json`.
- [ ] Pi loads `CLAUDE.md` automatically.
- [ ] Native Pi prompt templates exist for:
  - [ ] `/preplan`
  - [ ] `/plan`
  - [ ] `/iterate`
  - [ ] `/write-tests`
  - [ ] `/implement`
  - [ ] `/review`
- [ ] Every prompt has Pi frontmatter.
- [ ] Every prompt explicitly handles `$ARGUMENTS`.
- [ ] Claude-specific assumptions have been removed or replaced.
- [ ] Scope support files are not exposed as commands.
- [ ] Guardrail extension protects sensitive paths.
- [ ] Guardrail extension confirms dangerous bash commands.
- [ ] Feature files are protected from accidental edits.
- [ ] Dependency changes require confirmation.
- [ ] Workflow-state extension exists or has a documented design.
- [ ] Review mode is read-only except for review artifact output.
- [ ] Implementation mode blocks test modifications.
- [ ] Test-writing mode blocks implementation modifications.
- [ ] Context routing prevents unnecessary doc loading.
- [ ] Optional local model configuration is decided.
- [ ] Optional package plan is decided.
- [ ] The harness has been validated on at least one real feature from preplan through review.

---

## Recommended Next Action

Start with **Phase 1 and Phase 2** only:

1. Create `.pi/settings.json`.
2. Port one prompt, preferably `/implement`, into `.pi/prompts/implement.md`.
3. Validate argument handling in Pi.
4. Port the remaining prompts one at a time.

Do not start extensions until the prompt templates are working.

---

# TO-DO checklist for turning this into an app-agnostic customized PI harness

> **When to use this section:** Complete the PurrfectReqs-specific harness first. Once it works reliably for this project, use this checklist to extract the reusable parts into a generic, application-agnostic Pi harness.
>
> **Core idea:** The reusable asset is not PurrfectReqs itself. The reusable asset is the **human-authored, phase-gated, test-first development protocol**: a human writes the intent/specification, the AI plans and implements inside explicit boundaries, and the harness enforces phase discipline.

## A. Split generic harness concerns from project adapter concerns

- [ ] Identify which parts of the current harness are genuinely generic.

  Generic examples:

  - phase-gated workflow
  - prompt-template migration pattern
  - protected path enforcement
  - dangerous command confirmation
  - workflow status display
  - read-only review mode
  - implementation phase boundaries
  - human approval checkpoints
  - artifact validation before phase transitions

- [ ] Identify which parts are PurrfectReqs-specific.

  PurrfectReqs-specific examples:

  - `CLAUDE.md` authority order
  - `docs/SCOPE.md`, `docs/SECURITY.md`, `docs/DATA_MODELS.md`, etc.
  - FastAPI module layout under `app/`
  - pytest-bdd paths
  - `.feature` file contract rules
  - Alembic migration rules
  - ruff/pytest command assumptions
  - PurrfectReqs module names and approved dependencies

- [ ] Create a conceptual split:

  ```text
  generic-pi-harness/
    prompts/
    extensions/
    README.md

  project-repo/.pi/
    settings.json
    harness.config.json
    project-specific prompts or overrides
  ```

- [ ] Avoid hardcoding PurrfectReqs paths into generic extensions.

---

## B. Rename and reframe the harness away from PurrfectReqs

- [ ] Decide on a generic harness name.

  Candidate names:

  - `phase-gated-pi-harness`
  - `human-authored-dev-harness`
  - `spec-first-pi-harness`
  - `ai-pairing-phase-gate`

- [ ] Rename generic package references.

  Current project-specific name:

  ```text
  purrfectreqs-pi-harness
  ```

  Possible generic name:

  ```text
  phase-gated-pi-harness
  ```

- [ ] Keep a separate project adapter name if needed:

  ```text
  purrfectreqs-pi-adapter
  ```

- [ ] Rewrite the generic README around the workflow pattern, not the application.

  Generic framing:

  ```text
  A Pi harness for human-authored, phase-gated software development.
  The human writes the source-of-truth artifact. The agent plans, tests,
  implements, and reviews under explicit file and phase boundaries.
  ```

---

## C. Replace hardcoded `CLAUDE.md` assumptions with configurable constitution files

- [ ] Do not assume every project uses `CLAUDE.md`.

  Other projects may use:

  ```text
  AGENTS.md
  CLAUDE.md
  CONTRIBUTING.md
  docs/AGENT_GUIDE.md
  .pi/PROJECT_RULES.md
  ```

- [ ] Add config for constitution/context files.

  Example future config:

  ```json
  {
    "constitutionFiles": [
      "CLAUDE.md",
      "AGENTS.md"
    ]
  }
  ```

- [ ] In generic prompts, refer to "project constitution files" rather than `CLAUDE.md` specifically.

- [ ] In the PurrfectReqs adapter, map the constitution file to:

  ```json
  {
    "constitutionFiles": ["CLAUDE.md"]
  }
  ```

---

## D. Replace hardcoded docs with document roles

- [ ] Stop treating these exact files as universal:

  ```text
  docs/SCOPE.md
  docs/GUIDE.md
  docs/DATA_MODELS.md
  docs/SECURITY.md
  docs/ARCHITECTURE.md
  docs/FRONTEND.md
  docs/GLOSSARY.md
  docs/TECH_STACK.md
  ```

- [ ] Define generic document roles instead.

  Example roles:

  ```text
  scope
  security
  architecture
  data-model
  coding-guide
  frontend-guide
  glossary
  tech-stack
  testing-guide
  deployment-guide
  ```

- [ ] Add a project config mapping roles to files.

  Example:

  ```json
  {
    "authorityDocs": {
      "scope": "docs/SCOPE.md",
      "security": "docs/SECURITY.md",
      "architecture": "docs/ARCHITECTURE.md",
      "dataModel": "docs/DATA_MODELS.md",
      "codingGuide": "docs/GUIDE.md",
      "frontendGuide": "docs/FRONTEND.md",
      "glossary": "docs/GLOSSARY.md",
      "techStack": "docs/TECH_STACK.md"
    }
  }
  ```

- [ ] Update the context router to return document roles first, then resolve roles to project files.

- [ ] Allow roles to be missing. Not every project has a dedicated data model, frontend, glossary, or security document.

---

## E. Generalize workflow commands beyond BDD/PurrfectReqs

- [ ] Decide whether the generic harness should keep the current command names or expose more generic names.

  Current PurrfectReqs commands:

  ```text
  /preplan
  /plan
  /iterate
  /write-tests
  /implement
  /review
  ```

  Possible generic phase names:

  ```text
  /discover
  /design
  /refine
  /test
  /build
  /review
  ```

- [ ] Consider supporting workflow profiles.

  Example:

  ```json
  {
    "workflowProfile": "bdd-feature"
  }
  ```

  Other possible profiles:

  ```text
  bugfix
  refactor
  docs-change
  migration
  ui-change
  dependency-update
  ```

- [ ] Keep PurrfectReqs as a `bdd-feature` profile rather than the default universal workflow.

- [ ] Make command prompts refer to generic artifacts where possible:

  ```text
  source-of-truth artifact
  implementation plan
  test artifact
  review artifact
  ```

  instead of always:

  ```text
  .feature file
  pytest-bdd step definitions
  tests/bdd/plans
  ```

---

## F. Generalize human-authored source-of-truth artifacts

- [ ] Do not assume all projects use `.feature` files.

  Other valid human-authored artifacts may include:

  ```text
  .feature files
  issue specs
  RFCs
  ADRs
  design briefs
  bug reports
  migration requests
  API contract files
  security review requests
  docs change requests
  ```

- [ ] Add config for source artifact patterns.

  Example:

  ```json
  {
    "sourceArtifacts": [
      {
        "type": "gherkin-feature",
        "pattern": "tests/features/**/*.feature"
      },
      {
        "type": "rfc",
        "pattern": "docs/rfcs/*.md"
      }
    ]
  }
  ```

- [ ] Keep `.feature` protection as one artifact-protection rule, not the universal rule.

- [ ] Generalize the principle:

  ```text
  The source-of-truth artifact must not be modified by implementation phases.
  ```

---

## G. Generalize project structure assumptions

- [ ] Remove hardcoded assumptions that the source root is always:

  ```text
  app/
  ```

- [ ] Support configurable source roots:

  ```json
  {
    "sourceRoots": ["app"]
  }
  ```

  Other projects may use:

  ```text
  src/
  packages/*/src
  backend/
  frontend/
  crates/
  cmd/
  internal/
  ```

- [ ] Remove hardcoded assumptions that tests are always:

  ```text
  tests/bdd/step_defs
  tests/unit
  ```

- [ ] Support configurable test roots:

  ```json
  {
    "testRoots": [
      "tests/bdd/step_defs",
      "tests/unit"
    ]
  }
  ```

- [ ] Make implementation-phase restrictions use configured roots, not PurrfectReqs-specific paths.

---

## H. Generalize language/toolchain assumptions

- [ ] Do not assume every project uses Python, FastAPI, pytest, ruff, or Alembic.

- [ ] Move tool commands into config.

  PurrfectReqs example:

  ```json
  {
    "commands": {
      "test": ["pytest"],
      "lint": ["ruff check ."],
      "formatCheck": ["ruff format --check ."],
      "migrationUpgrade": ["alembic upgrade head"]
    }
  }
  ```

- [ ] Allow other stacks to define their own commands:

  ```json
  {
    "commands": {
      "test": ["npm test"],
      "lint": ["npm run lint"],
      "formatCheck": ["npm run format:check"]
    }
  }
  ```

- [ ] Make dangerous command detection generic, but allow project-specific additions.

---

## I. Generalize protected path rules

- [ ] Split path protection into generic defaults and project-specific additions.

  Generic blocked defaults:

  ```text
  .env
  .git/
  node_modules/
  .venv/
  ```

- [ ] Make confirmation paths configurable.

  PurrfectReqs-specific confirmation paths:

  ```text
  docs/SECURITY.md
  docs/DATA_MODELS.md
  docs/ARCHITECTURE.md
  docs/SCOPE.md
  docs/TECH_STACK.md
  pyproject.toml
  requirements.txt
  docker-compose.yml
  alembic/versions/
  ```

- [ ] Support categories rather than only literal paths.

  Example categories:

  ```text
  dependencyFiles
  securityDocs
  architectureDocs
  migrationDirs
  deploymentFiles
  environmentFiles
  sourceOfTruthArtifacts
  ```

- [ ] Resolve categories through project config.

---

## J. Generalize workflow states

- [ ] Separate generic workflow states from PurrfectReqs aliases.

  Generic states:

  ```text
  IDLE
  DISCOVERY
  DESIGN
  REFINEMENT
  TEST_AUTHORING
  IMPLEMENTATION
  VERIFICATION
  REVIEW
  DONE
  ```

- [ ] Map PurrfectReqs states onto generic states.

  Example:

  ```text
  PREPLAN -> DISCOVERY
  PLAN_DRAFT -> DESIGN
  ITERATING_ADVERSARIAL -> REFINEMENT
  ITERATING_ENRICH -> REFINEMENT
  ITERATING_TESTABILITY -> REFINEMENT
  FROZEN -> DESIGN/READY
  TESTS_RED -> TEST_AUTHORING
  IMPLEMENTING -> IMPLEMENTATION
  REVIEWING -> REVIEW
  REVIEWED -> DONE
  ```

- [ ] Let projects define custom sub-states.

  Example:

  ```json
  {
    "workflowStates": {
      "base": ["DISCOVERY", "DESIGN", "REFINEMENT", "TEST_AUTHORING", "IMPLEMENTATION", "REVIEW"],
      "custom": ["ITERATING_ADVERSARIAL", "ITERATING_ENRICH", "ITERATING_TESTABILITY", "FROZEN"]
    }
  }
  ```

---

## K. Generalize review lenses

- [ ] Treat current `/iterate` scopes as configurable review lenses.

  Current PurrfectReqs lenses:

  ```text
  adversarial
  enrich
  testability
  freeze
  ```

- [ ] Support other future lenses:

  ```text
  security
  accessibility
  performance
  migration-risk
  api-contract
  dependency-risk
  operations
  documentation
  privacy
  data-integrity
  ```

- [ ] Add config for lenses.

  Example:

  ```json
  {
    "reviewLenses": [
      {
        "name": "adversarial",
        "file": ".pi/prompts/support/scopes/adversarial.md",
        "requiredBeforeFreeze": true
      },
      {
        "name": "testability",
        "file": ".pi/prompts/support/scopes/testability.md",
        "requiredBeforeFreeze": true
      }
    ]
  }
  ```

- [ ] Make `freeze` validate required lenses from config instead of assuming exactly three prerequisite scopes.

---

## L. Generalize context routing

- [ ] Replace hardcoded context routing like:

  ```text
  API feature planning -> docs/SCOPE.md, docs/DATA_MODELS.md, docs/SECURITY.md
  ```

  with role-based routing:

  ```text
  API feature planning -> scope, data-model, security, architecture, coding-guide
  ```

- [ ] Resolve document roles through project config.

- [ ] Allow projects to define their own task types.

  Example:

  ```json
  {
    "contextRoutes": {
      "api-feature-planning": ["scope", "dataModel", "security", "architecture", "codingGuide"],
      "ui-feature-planning": ["scope", "frontendGuide", "security", "techStack"],
      "dependency-change": ["techStack", "security"]
    }
  }
  ```

- [ ] Make missing roles non-fatal unless the route marks them required.

---

## M. Define a generic harness config contract

- [ ] Create a draft config schema for:

  ```text
  .pi/harness.config.json
  ```

- [ ] Include at least these sections:

  ```json
  {
    "projectName": "",
    "constitutionFiles": [],
    "authorityDocs": {},
    "sourceArtifacts": [],
    "sourceRoots": [],
    "testRoots": [],
    "planDir": "",
    "reviewDir": "",
    "workflowProfile": "",
    "workflowStates": {},
    "reviewLenses": [],
    "protectedPaths": [],
    "confirmationPaths": [],
    "dangerousCommands": [],
    "commands": {},
    "contextRoutes": {}
  }
  ```

- [ ] Keep this config declarative.

  The generic harness should read config. It should not need source changes for each new application.

- [ ] Add validation for missing or invalid config.

- [ ] Make the first version permissive: warn when config is incomplete rather than failing everywhere.

---

## N. Package generic harness separately from project adapter

- [ ] Create a generic package only after the PurrfectReqs-specific harness has proven itself.

- [ ] Possible package split:

  ```text
  phase-gated-pi-harness/
    prompts/
    extensions/
    README.md

  purrfectreqs/.pi/
    settings.json
    harness.config.json
    prompts/project-overrides/
  ```

- [ ] Keep reusable extensions in the generic package.

- [ ] Keep PurrfectReqs-specific docs and paths in `.pi/harness.config.json`.

- [ ] Decide whether PurrfectReqs-specific prompt wording should remain local or become a profile in the package.

---

## O. Defer MCP and knowledge graph work

- [ ] Do not add MCP servers just to read local files, docs, tests, or code.

  Pi already has local tools for that.

- [ ] Do not add a knowledge graph while the knowledge base is still manageable as Markdown files.

- [ ] Revisit knowledge graph or structured index only if the project grows enough that Markdown docs become too large or hard to navigate.

- [ ] If future structure is needed, prefer a simple local artifact index before a full graph.

  Example:

  ```text
  .pi/state/artifact-index.json
  ```

  Possible contents:

  ```json
  {
    "features": [],
    "plans": [],
    "reviews": [],
    "sourceArtifacts": [],
    "phaseTransitions": []
  }
  ```

- [ ] Treat MCP as an external-integration mechanism only, not core harness infrastructure.

---

## P. Validate app-agnostic extraction on a second project

- [ ] Do not declare the harness app-agnostic until it has been tested outside PurrfectReqs.

- [ ] Choose a small second project with a different stack or structure.

- [ ] Configure only `.pi/harness.config.json` and minimal project prompts.

- [ ] Confirm the generic extensions work without code changes.

- [ ] Record every PurrfectReqs assumption that leaks during the second-project test.

- [ ] Move leaked assumptions behind config or into the PurrfectReqs adapter.

---

## App-agnostic extraction end-state checklist

The harness is application-agnostic when:

- [ ] Generic package name no longer references PurrfectReqs.
- [ ] Generic extension code does not hardcode PurrfectReqs paths.
- [ ] Constitution files are configurable.
- [ ] Authority docs are role-based and configurable.
- [ ] Source artifacts are configurable.
- [ ] Source/test roots are configurable.
- [ ] Tool commands are configurable.
- [ ] Workflow states have generic base states plus project-specific aliases.
- [ ] Review lenses are configurable.
- [ ] Context routing is role-based.
- [ ] Protected paths are configurable.
- [ ] Dangerous command patterns are configurable or extendable.
- [ ] PurrfectReqs-specific behavior lives in `.pi/harness.config.json` or local prompt overrides.
- [ ] The harness has been validated on at least one non-PurrfectReqs project.
