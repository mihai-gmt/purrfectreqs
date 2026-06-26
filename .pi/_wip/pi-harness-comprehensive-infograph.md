# PurrfectReqs Pi Harness — Comprehensive Infograph

## Purpose

The PurrfectReqs Pi harness turns Pi from a general coding assistant into a governed, phase-gated development workflow for this project.

The core philosophy is:

```text
Human writes the contract.
AI performs bounded work.
Harness enforces phase, file, test, and safety gates.
```

---

## 1. High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         PI CODING AGENT                              │
│                                                                     │
│  Loads project-local settings from .pi/settings.json                 │
│  Loads CLAUDE.md automatically as project constitution               │
│  Loads prompt templates from .pi/prompts/*.md                        │
│  Loads extension entrypoint from .pi/extensions/governance.ts        │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      .pi/settings.json                               │
├─────────────────────────────────────────────────────────────────────┤
│ Provider: openai-codex                                               │
│ Model: gpt-5.5                                                       │
│ Thinking: medium                                                     │
│ Enabled models: gpt-*                                                │
│ Prompts: ./prompts/*.md                                              │
│ Extensions: ./extensions                                             │
│ Sessions: .pi/sessions                                               │
│ Compaction enabled                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Two Surfaces: Prompt Commands and Control Commands

```text
                           ┌──────────────────────┐
                           │        HUMAN          │
                           └──────────┬───────────┘
                                      │
                 slash commands       │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PROMPT COMMANDS                              │
├─────────────────────────────────────────────────────────────────────┤
│ /preplan     → analyze codebase, write .analysis.md                  │
│ /plan        → create DRAFT implementation plan                      │
│ /iterate     → adversarial/enrich/testability/freeze plan review     │
│ /write-tests → write BDD/unit tests, confirm RED                     │
│ /implement   → implement frozen plan after RED                       │
│ /review      → read-only compliance review after GREEN               │
└─────────────────────────────────────────────────────────────────────┘

                           ┌──────────────────────┐
                           │        HUMAN          │
                           └──────────┬───────────┘
                                      │
                 control commands     │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CONTROL PLANE                                  │
├─────────────────────────────────────────────────────────────────────┤
│ /box     → Feature Box, plan, allowlists, RED/GREEN, history         │
│ /phase   → workflow phase state                                      │
│                                                                     │
│ These are registered slash commands, not LLM tools.                  │
│ The agent cannot promote itself through gates.                       │
└─────────────────────────────────────────────────────────────────────┘

                           ┌──────────────────────┐
                           │        AGENT          │
                           └──────────┬───────────┘
                                      │
                edit/write/bash tools │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ENFORCEMENT GATES                              │
├─────────────────────────────────────────────────────────────────────┤
│ pi.on("tool_call") intercepts edit/write/bash                        │
│ Blocks, confirms, or allows before tool execution                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. File Layout

```text
.pi/
├── settings.json
├── README.md
├── MODEL_POLICY.md
├── PACKAGING_DECISION.md
├── APP_AGNOSTIC_EXTRACTION_DECISION.md
├── CONTEXT_ROUTER_DECISION.md
│
├── prompts/
│   ├── preplan.md
│   ├── plan.md
│   ├── iterate.md
│   ├── write-tests.md
│   ├── implement.md
│   └── review.md
│
├── extensions/
│   └── governance.ts          # Pi adapter only
│
├── governance/
│   ├── config.ts              # PurrfectReqs config + prose rules
│   ├── engine.ts              # deterministic governance engine
│   ├── audit.ts               # per-feature JSONL audit log
│   ├── engine.test.ts
│   └── audit.test.ts
│
├── feature-box.json           # current workflow state
├── audit/
│   └── <module>_<feature>.audit.jsonl
│
├── sessions/
└── _wip/
    └── design notes, observations, future improvements
```

---

## 4. End-to-End Workflow

```text
┌────────────┐
│ .feature   │  human-authored contract
└─────┬──────┘
      ▼
┌────────────┐
│ /preplan   │  reads bounded context, writes .analysis.md
└─────┬──────┘
      ▼
┌────────────┐
│ /plan      │  creates DRAFT plan after approval loops
└─────┬──────┘
      ▼
┌────────────┐
│ /iterate   │  adversarial → enrich → testability → freeze
└─────┬──────┘
      ▼
┌────────────┐
│ FROZEN     │  plan becomes executable contract for agents
└─────┬──────┘
      ▼
┌────────────┐
│ /box setup │  set module, plan, freeze-check, import Section 14 files
└─────┬──────┘
      ▼
┌────────────┐
│ WRITE_TESTS│  /write-tests can only write approved test files
└─────┬──────┘
      ▼
┌────────────┐
│ RED        │  /box run-red executes pytest and confirms real failures
└─────┬──────┘
      ▼
┌────────────┐
│ IMPLEMENT  │  /implement can only write approved implementation files
└─────┬──────┘
      ▼
┌────────────┐
│ GREEN      │  /box run-green executes pytest and confirms pass
└─────┬──────┘
      ▼
┌────────────┐
│ REVIEWING  │  /review can only write the review artifact
└────────────┘
```

---

## 5. Governance State

Workflow state is stored in:

```text
.pi/feature-box.json
```

It records:

- current phase
- in-scope module
- active plan file
- allowed test files
- allowed implementation files
- RED/GREEN confirmation state
- test command summaries
- core-edit allowance, if any

Example state shape:

```json
{
  "phase": "REVIEWING",
  "inScope": ["auth"],
  "planFile": "tests/bdd/plans/auth_20260621_basic_register_user_ui.plan.md",
  "redConfirmed": true,
  "greenConfirmed": true,
  "allowedTestFiles": [
    "tests/bdd/step_defs/test_20260621_basic_register_user_ui.py"
  ],
  "allowedImplementationFiles": [
    "app/auth/router.py",
    "app/auth/service.py",
    "app/auth/schemas.py",
    "app/templates/base.html"
  ]
}
```

---

## 6. Path Classification Model

The engine classifies paths before deciding whether an agent write is legal.

```text
tests/features/**/*.feature        → feature      hard-blocked
tests/bdd/plans/*.analysis.md      → analysis     PREPLAN only
tests/bdd/plans/*.plan.md          → plan         PLANNING / ITERATING
tests/bdd/plans/*.review.md        → review       REVIEWING only
tests/bdd/step_defs/**/*.py        → test         WRITE_TESTS allowlist
tests/unit/**/*.py                 → test         WRITE_TESTS allowlist
app/core/**                        → core         requires /box allow-core
app/**/*.py                        → source       IMPLEMENTING allowlist
app/templates/**                   → frontend     IMPLEMENTING allowlist
app/static/**                      → frontend     IMPLEMENTING allowlist
alembic/versions/**                → migration    IMPLEMENTING allowlist
docs/PROJECT_STATUS.md             → status       IMPLEMENTING / REVIEWING
docs/**/*.md                       → doc          usually blocked by phase
Backlog.md                         → backlog      PREPLAN / PLANNING / ITERATING
.env, .git, .venv, node_modules    → protected    hard-blocked
```

---

## 7. Enforcement Decision Order

```text
Agent tool call
     │
     ▼
┌────────────────────────────────────┐
│ 1. Hard path blocks                 │
│    .feature, .env, .git, .venv      │
└────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ 2. Content invariants               │
│    banned deps, naive UTC,          │
│    browser token storage,           │
│    cross-module model imports       │
└────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ 3. Phase rules                      │
│    PREPLAN / PLANNING /             │
│    WRITE_TESTS / IMPLEMENTING /     │
│    REVIEWING                        │
└────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ 4. Feature Box rules                │
│    module scope, app/core gate       │
└────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────┐
│ 5. Soft confirmations               │
│    authority docs, deps, config,     │
│    auth-sensitive files, secrets     │
└────────────────────────────────────┘
     │
     ▼
 allow / confirm / block
```

If confirmation is required but Pi has no UI, the harness blocks instead of allowing.

---

## 8. Phase Write Rules

| Phase | Writable by agent | Key gate |
|---|---|---|
| `IDLE` | permissive legacy mode | stateless hard gates still apply |
| `PREPLAN` | `*.analysis.md`, `Backlog.md` | no source/test writes |
| `PLANNING` | `*.plan.md`, `Backlog.md` | no source/test writes |
| `ITERATING` | `*.plan.md`, `Backlog.md` | no source/test writes |
| `WRITE_TESTS` | approved Python test files only | plan must be FROZEN |
| `IMPLEMENTING` | approved source/frontend/migration/plan files, plus `docs/PROJECT_STATUS.md` | FROZEN + RED |
| `REVIEWING` | `*.review.md`, plus `docs/PROJECT_STATUS.md` | GREEN |

Important nuance: `/phase set IMPLEMENTING` itself does not block if RED is missing. The write gate blocks when the agent tries to write. Phase commands mutate state; tool calls enforce state.

---

## 9. Section 14 Manifest Enforcement

```text
Frozen plan Section 14
        │
        ▼
/box allow-files-from-plan
        │
        ▼
parseAllowedFilesFromPlan()
        │
        ├── test files           → allowedTestFiles
        └── implementation files → allowedImplementationFiles
```

The parser understands the canonical plan tables:

```text
Files to CREATE
Files to MODIFY
```

It routes rows by file class:

```text
test       → allowedTestFiles
source     → allowedImplementationFiles
frontend   → allowedImplementationFiles
migration  → allowedImplementationFiles
core       → allowedImplementationFiles, but still needs allow-core
doc        → skipped
feature    → skipped / hard-blocked
status     → not manifest-importable; phase-gated separately
backlog    → not manifest-importable; phase-gated separately
```

---

## 10. RED/GREEN Gates

```text
/box run-red pytest tests/bdd/step_defs/test_x.py -v
        │
        ▼
engine parses command
        │
        ├── only allows pytest or python -m pytest
        ├── rejects pipes, redirects, command chaining
        └── resolves pytest/python to .venv/bin/... if present
        │
        ▼
executes pytest
        │
        ├── RED valid if:
        │     - non-zero exit
        │     - output shows real test failure
        │     - not import/setup/collection failure
        │
        └── stores redConfirmed=true
```

```text
/box run-green pytest tests/bdd/step_defs/test_x.py -v
        │
        ▼
executes pytest through venv-aware resolver
        │
        ├── GREEN valid if:
        │     - exit code 0
        │     - output contains passed
        │     - not "no tests ran"
        │
        └── stores greenConfirmed=true
```

Manual attestation commands are disabled:

```text
/box mark-red   → DISABLED
/box mark-green → DISABLED
```

---

## 11. Bash Governance

The harness guards `bash` in addition to `edit` and `write`.

```text
bash command
   │
   ├── dangerous pattern?
   │      rm -rf, sudo, git reset --hard, pip install, npm install, etc.
   │      → confirm/block
   │
   ├── write intent?
   │      >, >>, tee, sed -i, perl -i, cp, mv, install, dd of=,
   │      python open(..., "w"/"a"/"x")
   │      → extract target path
   │      → run same path rules as edit/write
   │
   ├── safe allowlist?
   │      pytest, python -m pytest, ruff, make test,
   │      git status/diff/log/show, alembic current/heads/history/upgrade head
   │      → allow
   │
   └── unknown command
          → confirm/block
```

---

## 12. Prompt Roles

| Prompt | Role | Writes |
|---|---|---|
| `/preplan` | documentarian codebase analysis | `.analysis.md` |
| `/plan` | planning agent with approval loops | `.plan.md` as `DRAFT` |
| `/iterate adversarial` | risk/security/architecture lens | approved plan edits |
| `/iterate enrich` | fills missing implementation/test detail | approved plan edits or Backlog recommendations |
| `/iterate testability` | fixture/test-signal lens | approved plan edits |
| `/iterate freeze` | final consistency gate | flips `DRAFT` → `FROZEN` |
| `/write-tests` | test writer only | approved test files |
| `/implement` | implementer only | approved implementation files |
| `/review` | read-only reviewer | `.review.md` only |

---

## 13. Control-Plane Audit Log

Every state-changing `/box` or `/phase` command is logged per feature:

```text
.pi/audit/<module>_<feature>.audit.jsonl
```

Record types:

```text
header
event
artifact_registered
```

Human-readable commands:

```text
/box history
/box history --failed
/box history --artifacts
```

The audit log records:

- phase transitions
- failed and successful RED/GREEN runs
- manifest imports
- command attempts
- artifact registrations
- outcome status

---

## 14. Footer / Status Line

The extension sets a compact governance status in Pi’s UI:

```text
Gov REVIEWING | Plan: FROZEN | RED: yes | GREEN: yes | Box: auth
```

It also detects stale governance engine source:

```text
⚠ ENGINE STALE — restart Pi
```

This matters because `/new` clears conversation context but does not reload extension code. After editing `.pi/governance/*.ts`, restart Pi for the engine change to take effect.

---

## 15. Model Policy

Current model policy:

```text
Provider: openai-codex
Model: gpt-5.5
Enabled models: gpt-*
```

Rationale:

- Application AI remains local/offline via Ollama.
- Coding harness AI is allowed to be hosted because strict instruction following matters more for workflow reliability.
- Anthropic models are intentionally removed to avoid accidental Agent-SDK credit usage through Pi.

Local Ollama models are allowed only for low-risk/read-only experiments until validated against the strict workflow.

---

## 16. What Worked in Real Testing

From the real feature dry run, the most important validated wins were:

```text
GOOD:
- .feature hard gate blocked model attempt to edit contract
- Feature Box and phase gates prevented drift
- Section 14 manifest became central source for allowed writes
- Review surfaced real defects and produced useful learning notes
- Audit log captured the control-plane timeline
- Venv-aware test execution fixed interpreter guessing
```

The big design lesson:

```text
Prompt prose is not enough.
High-risk constraints need structural enforcement.
```

---

## 17. Known Open / Judgment-Boundary Areas

| Area | Status |
|---|---|
| `/plan` validation gate can still be too prose-dependent | open from observations |
| UI/security controls not always structurally enforceable | partly prompt-enforced |
| Phase entry itself is permissive; writes are gated | deliberate/current behavior |
| File allowlist is file-granular, not region-granular | known judgment boundary |
| `allowedReadFiles` / `allowedWriteFiles` exist but are mostly reserved | low-risk ambiguity |
| Prompt-only context routing may need future tool if it drifts | deferred |
| Package extraction | deferred |
| App-agnostic extraction | deferred |

---

## 18. Mental Model

```text
Your Pi harness is not just “Pi with prompts.”

It is a three-layer governed development system:

1. PROMPTS
   Tell the model what role it is playing and what artifact to produce.

2. CONTROL PLANE
   Lets the human move the workflow through phases and approve boundaries.

3. ENFORCEMENT ENGINE
   Mechanically blocks tool calls that violate contracts, phases, manifests,
   source-of-truth files, protected paths, or core architectural rules.
```

The compact summary:

```text
Human writes the contract.
Agent plans inside bounded context.
Human freezes the plan.
Agent writes tests.
Human/engine confirms RED.
Agent implements only allowed files.
Human/engine confirms GREEN.
Agent reviews without modifying code.
Engine blocks structural violations throughout.
```
