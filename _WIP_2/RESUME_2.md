# RESUME — Harness Toolkit work

> Single orientation entry point after a `/compact` or `/clear`. Read this, then the three files
> below, then continue from "Immediate next step."

## What we're building
A harness-neutral **harness toolkit**: a constitution + supporting docs (usable standalone with
**Claude Code** or **Devin**) + an optional **PI** engine/extension layer + an interactive installer.
Distilled from a six-point big picture (repo · installer modes · interactive install · PI extraction ·
finish Claude/Devin docs · common architecture across harnesses).

## Locations (canonical FLIPPED 2026-06-26)
- **Canonical — work from here now:** `~/projects/harness-toolkit/` — all design docs + Workstream A
  artifacts now live here; **all ongoing edits happen here** (keeps context/token use down). User
  handles git/commits. Layout: `RESUME/STATUS/harness-adr/toolkit-build-plan` + the workstream-a docs at
  root; `constitution/` (CLAUDE.* + Makefile); `workflow/` (playbook + tail-contract + specs);
  `tails/{claude,pi,devin}/`; `docs/`, `install/`.
- **Archive — do NOT edit:** `purrfectreqs/_WIP_2/` (every file suffixed `_2`) — frozen snapshot of the
  pre-flip working folder; reference only.

## Read first (in order) — all under `~/projects/harness-toolkit/`
1. `STATUS.md` — current state, pre-extraction checklist, PI analysis & punch-list.
2. `toolkit-build-plan.md` — master plan: 6 workstreams (A common architecture / B PI extraction /
   C Claude-Devin tails / D repo+installer), 3-layer architecture, sequencing, gates.
3. `harness-adr.md` — decision log (ADR-001…023).
4. **Workstream A outputs:** `workstream-a-crosscheck.md` (PI prompts ↔ §8, the P/M/C split, T1–T11
   obligations) + `workstream-a-tail-streams.md` (tail enforcement surfaces; one tiered contract, not
   two streams); `workflow/tail-contract.md`; `workflow/playbook-spec.md` (+ `workflow/playbook.md`
   once written).

## Settled decisions — do NOT re-litigate
- **Extend, not fork** — toolkit depends on `@earendil-works/pi-coding-agent` (npm); never fork/vendor PI.
- **Neutral root** repo; PI is a peer under `tails/pi/`, not the substrate.
- **Three-layer architecture:** constitution (DONE) → shared workflow playbook → harness tails.
- **One tiered tail-contract, not two streams** (ADR-018) — T1–T11, each at a §0 tier per harness.
- **Claude+PI are siblings; Devin is the outlier** (ADR-019); Claude/PI share prompt bodies via
  mechanics injection (ADR-020); Claude's control plane is a hook+state-file, not a slash command (ADR-021).
- **Shared neutral layer = constitution + docs + playbook + tail-contract** (ADR-022); only Devin's
  skill-*building mechanics* diverge, never the discipline.
- **All GreaseBook validation is POST-toolkit** (ADR-023, supersedes "generalize via GreaseBook first"):
  build complete on PurrfectReqs-provable gates, then adopt on GreaseBook; corrections = defects.
- **Keep both constitution editions:** `CLAUDE.draft.md` (teaching) + `make lean` → `CLAUDE.lean.md` (production).
- **Docs always install; PI is additive** — installer asks "also install the PI engine?".

## Done
- Constitution: frontmatter + §0–§14, both editions; coherence pass clean; `make lean` tooling.
- `AGENT.md` Devin tail (STUB — mechanics TBD).
- PI analysis complete: **extend-not-fork verified** (PI = npm package, our layer is a clean adapter);
  punch-list in STATUS.
- New repo scaffolded at `~/projects/harness-toolkit` (copy-only; not committed by us).

## Immediate next step
Workstream A cross-check is **DONE** (both analysis files above); decisions logged (ADR-018…021).
**In progress: authoring the two Workstream A deliverables** —
1. `workflow/tail-contract.md` — the tiered T1–T11 obligations × `[GATE]/[PROCESS]/[REVIEW]` per harness.
2. `workflow/playbook.md` — one entry per §8 phase (P-column discipline), authored spec-first (ADR-013:
   I draft falsifiable checks → user approves → I write).

After A: B + C in parallel (Claude+PI paired per ADR-019) → D installer → GreaseBook validation.

Also still pending (parallel track): four candidate constitution amendments surfaced by the cross-check
(`workstream-a-crosscheck.md` §5) — plan-approval gate, refinement-completeness gate, diff-scoped review
attribution, "gate necessary-but-not-sufficient." User call: in-constitution (spec-first) vs playbook-only.

## Open decisions still pending
- **OQ-3 repo home — RESOLVED:** `~/projects/harness-toolkit`.
- ~~**OQ-1/2 GreaseBook stack**~~ — no longer blocks toolkit; deferred to post-toolkit adoption (ADR-023).
- **Sessions/runtime-state gitignore** reconciliation vs the "nothing PI gitignored" principle (Workstream B).
- **Installer language** — Python recommended (interactive frontmatter fill) (Workstream D).
- **Four constitution amendments** (`workstream-a-crosscheck.md` §5) — in-constitution vs playbook-only.
- **Three tail-contract tier judgment-calls** (tail-contract.md §2) — PI T3 gate?, Devin T7 dual?, T1 gate-vs-process?
