# PurrfectReqs Development Workflow

> The extracted conceptual model of how features are built in this project — the process, its
> artifacts, its roles, and its gates. Written **harness-agnostic** (it describes the workflow, not
> Claude Code), so it serves both as documentation and as the porting spec for the Pi harness.
>
> Source of truth for the rules themselves stays in `CLAUDE.md` + `docs/`. This file describes the
> *machine* that applies them.

---

## 1. Core philosophy

The workflow is a **spec-driven, phase-gated, test-first pipeline operated by single-purpose agents.**
Five principles hold it together:

1. **The `.feature` file is the contract.** It is the executable specification, written before any code.
   Nothing is invented beyond it — not tests, not behaviour, not scenarios.
2. **Test-first (RED → GREEN).** Tests are written from the spec and must fail before implementation
   exists. Implementation writes the minimum code to make them pass. Tests are the specification; they
   are never modified to pass.
3. **Feature Box discipline.** Every unit of work has an explicit boundary (which module, which files).
   Work outside the box stops and escalates rather than drifting.
4. **Restricted authority, full quality.** Each agent is a skilled implementer with a narrow remit. It
   may not expand scope, refactor opportunistically, or do another agent's job — but everything it
   does is production-grade.
5. **Stop, don't guess.** Ambiguity, conflicts, and boundary-crossings trigger a fixed **escalation**
   format and a hard stop, never a silent assumption.

---

## 2. The pipeline at a glance

```
  .feature (the contract, authored by developer)
      │
      ▼
  /preplan ──────────►  <module>_<feature>.analysis.md     (WHERE/HOW/WHAT code exists)
      │
      ▼
  /plan ─────────────►  <module>_<feature>.plan.md   [Status: DRAFT]   (+ 2 approval loops)
      │
      ▼
  /iterate × 4 (hardening loop, order matters):
      adversarial  →  "what breaks / where is it naive?"
      enrich       →  "detailed enough to execute without guessing?"
      testability  →  "can each phase be driven by a test?"
      freeze       →  gate: all 3 above ran + no unacknowledged triggers  →  [Status: FROZEN]
      │
      ▼
  /write-tests ──────►  test_<feature>.py + unit tests   →  run pytest  →  RED confirmed
      │
      ▼
  /implement ────────►  production code, phase by phase, inside the Feature Box  →  GREEN
      │
      ▼
  /review ───────────►  <module>_<feature>.review.md   (compliance pass/fail + learning notes)
      │
      ▼
  developer commits
```

**Context is cleared between every stage.** Each command starts fresh and reads only what the plan's
file manifest tells it to. This is deliberate: it forces the plan to be the single source of truth and
prevents context bleed from one stage contaminating the next.

---

## 3. Artifacts & where state lives

| Artifact | Path | Produced by | Role |
|---|---|---|---|
| Feature spec | `tests/features/<module>/<name>.feature` | Developer | The contract. Has a `# Type: API\|UI\|Core` header. |
| Codebase analysis | `tests/bdd/plans/<module>_<feature>.analysis.md` | `/preplan` | Facts about existing code, for the planner. |
| Plan | `tests/bdd/plans/<module>_<feature>.plan.md` | `/plan`, hardened by `/iterate` | The executable plan. Carries **Status**, **Section 14 file manifest**, **Section 15 changelog**. |
| Plan template | `tests/bdd/plans/PLAN_TEMPLATE.md` | (static) | Defines the 15 plan sections. |
| Tests | `tests/bdd/step_defs/test_<feature>.py`, `tests/unit/<module>/` | `/write-tests` | The failing spec-as-tests. |
| Review | `tests/bdd/plans/<module>_<feature>.review.md` | `/review` | Compliance verdict + learning notes. |
| Scope lenses | `.claude/commands/scopes/<scope>.md` | (static) | Definitions of the 4 hardening lenses. |

**Two artifacts carry the workflow's state machine:**
- The plan's **`Status` field** (`DRAFT` → `FROZEN`) gates everything downstream.
- The plan's **`Changelog`** records which hardening scopes ran and which escalations were acknowledged —
  `freeze` reads it to decide whether the plan may be locked.

The **Section 14 File Manifest** is the hand-off protocol: it lists exactly which files each downstream
agent should READ and which to CREATE/MODIFY. Agents do not explore beyond it.

---

## 4. The roles (one purpose each, strict separation)

| Agent | Reads | Writes | Must NOT |
|---|---|---|---|
| **preplan** (documentarian) | `.feature`, the codebase (via 3 parallel search sub-agents) | `analysis.md` | critique code, suggest changes, write plans/code/tests |
| **plan** (architect) | `.feature`, `analysis.md`, `docs/*` (not `app/` code) | `plan.md` [DRAFT] | write code/tests, modify `.feature`, skip the approval loops |
| **iterate** (single-lens reviewer) | the plan + one bounded doc set per scope | updates `plan.md` | blend scopes, modify `.feature`, write code, change the plan without approval |
| **write-tests** (test writer) | `plan.md` (Section 14), `.feature`, `conftest.py` (not `app/`) | test files | write implementation, modify `.feature`, invent scenarios |
| **implement** (implementer) | `plan.md` (Section 14), failing tests, target module | production code | modify tests, expand scope, cross the Feature Box, adapt the plan silently |
| **review** (auditor, read-only) | `docs/*`, `.feature`, `plan.md`, the changed files | `review.md` only | change any source/test file, suggest inline fixes |

The separation is the point: the planner can't quietly start coding, the implementer can't "fix" a test,
the reviewer can't patch what it flags. Each boundary blocks a specific class of scope drift.

---

## 5. Stage detail

### /preplan — codebase analysis
Reads the `.feature` file, extracts module/type/entities, then **spawns three parallel search agents** —
Locator (WHERE files live), Analyzer (HOW existing code works), Pattern-Finder (WHAT patterns to copy) —
and assembles their findings into `analysis.md`. Pure documentation; never critiques or changes code.

### /plan — planning with human checkpoints
Reads the `.feature`, the analysis doc, and the `docs/` source-of-truth set (deliberately **not** `app/`
code — it trusts the analysis). Validates the `.feature` for scope/data-model/security/testability gaps
and **stops if any are found**. Then runs **two approval loops**:
- **Loop 1:** present 2–3 implementation approaches with trade-offs + a recommendation; wait for choice.
- **Loop 2:** present the detailed structure + file-manifest preview; wait for explicit `APPROVE`.

Only then writes the plan from the template, with `Status: DRAFT`. The plan is not implementable yet.

### /iterate × 4 — the hardening loop
The DRAFT plan is reviewed through four **orthogonal lenses**, each reading a *different bounded doc set*
so the lenses don't blur. Order matters (structural problems first, detail last):

1. **adversarial** — "What breaks, where is it naive?" Reads plan, `.feature`, `SECURITY.md`,
   `ARCHITECTURE.md`, `CLAUDE.md`. Hunts architecture violations, security gaps, coupling, migration
   risk, sequencing, scope creep, constraint violations.
2. **enrich** — "Detailed enough to execute without guessing?" Reads plan, `.feature`, `DATA_MODELS.md`,
   `GUIDE.md`. Fills vague sections with concrete column types, error codes, function signatures, file
   lists. (Completeness, not correctness.)
3. **testability** — "Can each phase be driven by a test?" Reads plan, `.feature`, `analysis.md`,
   `conftest.py`. Checks every phase has a test signal, scenario coverage, fixtures, and is small enough
   for a red-green cycle. A phase too large because it crosses modules is an escalation.
4. **freeze** — the gate (see §6).

Each scope **proposes changes, waits for approval**, applies them in place, and appends a changelog entry.
Any scope that hits an escalation trigger stops and uses the escalation format instead.

### /write-tests — RED
Requires `Status: FROZEN` (else stops). Reads only the plan's Section 14 read-list + `.feature` +
`conftest.py`. Writes pytest-bdd step definitions and unit tests for **every** `.feature` scenario, then
**runs pytest to confirm they FAIL**. A test that passes without implementation is wrong and gets fixed.
Never reads `app/` code — tests are driven by the spec, not existing implementation.

### /implement — GREEN
Requires `Status: FROZEN`. Confirms tests exist and are RED. **Declares the Feature Box** (modules,
files to create/modify, files not touched, escalation triggers) — and stops if more than one module is
needed. Implements **phase by phase** in the plan's dependency order, running pytest + ruff + alembic
after each phase and ticking the plan's checkboxes. Pauses for manual verification between phases.
When the plan doesn't match reality, it reports a **plan mismatch** and stops rather than improvising.
May adapt trivia (variable names, formatting); must escalate structural changes.

### /review — audit
Requires tests green. **Read-only.** Runs an 8-category compliance checklist (test integrity, module
structure, function quality, security, database, observability, code quality, UI) marking each
PASS/FAIL/N-A with file:line for failures, writes the verdict + 3–6 learning notes to `review.md`. It
**identifies** problems; it never fixes them.

---

## 6. The gates (what blocks progression)

The workflow is enforced by hard gates, not etiquette:

| Gate | Rule |
|---|---|
| **Analysis required** | `/plan` refuses to run without the `analysis.md` from `/preplan`. |
| **Plan approval** | `/plan` will not write the plan until the developer approves the approach (Loop 1) and structure (Loop 2). |
| **Freeze prerequisites** | `freeze` blocks unless the changelog shows `adversarial`, `enrich`, AND `testability` all ran. |
| **Escalation scan at freeze** | `freeze` blocks if any phase/file hits an escalation trigger that wasn't acknowledged in the changelog. |
| **FROZEN required** | `/write-tests` and `/implement` refuse to run on a `DRAFT` plan. |
| **RED required** | `/implement` stops if the tests already pass (nothing to implement / tests are wrong). |
| **Per-phase verification** | `/implement` runs pytest + ruff after each phase and won't continue past failures. |
| **Green required** | `/review` stops if any test fails. |
| **Feature Box** | `/implement` stops and escalates if work needs more than one module. |
| **Context clearing** | Each stage starts fresh and reads only the plan's manifest — the plan is the only carried state. |

---

## 7. Escalation protocol

Any agent that encounters one of these **structural triggers** stops and emits a fixed
`Trigger / Context / Issue / Options / Recommendation` block, then waits:

- Task touches more than one module
- A new dependency is required
- Authentication/authorization flow would change
- A schema outside the Feature Box must change
- A new environment variable is required
- `app/core/*` must be modified
- The task conflicts with MVP scope
- A core architectural invariant would be affected
- The agent is unsure how to proceed

Escalations raised during `/iterate` are recorded in the plan changelog as *acknowledged* once the
developer resolves them — which is what lets `freeze` later pass its escalation scan.

---

## 8. Document authority hierarchy

When rules conflict, higher wins (and the conflict is flagged):

```
CLAUDE.md  >  docs/SECURITY.md  >  the .feature file  >  docs/SCOPE.md  >  docs/ARCHITECTURE.md
   >  docs/DATA_MODELS.md  >  docs/GUIDE.md  >  docs/FRONTEND.md  >  docs/GLOSSARY.md  >  inline comments
```

A `.feature` file may only be overridden by `CLAUDE.md` and `docs/SECURITY.md`; against anything else it
wins, and a conflict is reported rather than resolved unilaterally.

---

## 9. Invariants enforced throughout

These are checked by `/review` and must hold in all produced code (full detail in `CLAUDE.md` / `docs/`):
module boundaries (no cross-module model imports; logic in `service.py`), `ApiResponse[T]` envelope,
correlation-ID propagation, JWT on every endpoint except `POST /auth/login` + RBAC, no secrets/URLs in
source, UTC time only, mandatory audit fields (+ soft-delete on user content), Alembic migration for every
schema change, approved-dependencies-only, and the security rules (no token/PII logging, no stack traces
in responses, no tokens in browser storage).

---

## 10. Why it's built this way (what the Pi port must preserve)

The mechanics above exist to enforce a few non-negotiable properties. A port that keeps the commands but
loses these has missed the point:

- **The spec is upstream of everything.** Every stage traces back to the `.feature` file; nothing is
  invented. → Preserve the artifact chain, not just the commands.
- **State lives in artifacts on disk, not in a conversation.** Plan status, file manifest, changelog —
  the workflow can resume from files because context is intentionally disposable. → Preserve the plan as
  the carried state and the manifest as the hand-off.
- **Progression is gated, not advisory.** FROZEN-before-tests, RED-before-implement, all-scopes-before-
  freeze are *blocks*. → These are the prime candidates to move from prose into harness-enforced gates.
- **Roles are isolated to prevent drift.** The value is as much in what each agent *can't* do as what it
  can. → Preserve the forbidden-actions per role.
- **Boundary-crossing stops the line.** Escalation is control flow, not a suggestion. → Preserve the
  triggers as deterministic stops where detectable.
