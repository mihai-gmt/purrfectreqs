# Harness Template — Status & Next Steps

> Quick orientation. For decisions see `harness-adr.md`; for the section "tests" see
> `CLAUDE.section-specs.md`; for the prose see `CLAUDE.draft.md`. Temporary home in
> `purrfectreqs/_WIP/`.

## What this is
A reusable, teachable **harness-support template**: a tech-agnostic constitution (`CLAUDE.md`)
+ harness tails (`AGENT.md` for Devin; `.claude/.pi` for Claude/PI) + project docs. First
instance to validate it: **GreaseBook**.

## Artifacts (all in `_WIP/`)
| File | Role | State |
|---|---|---|
| `harness-adr.md` | Decision log (ADR-001…015) | current |
| `CLAUDE.skeleton.md` | Locked section structure | done |
| `CLAUDE.section-specs.md` | Per-section acceptance checks (the "tests") | §0–§14 done |
| `CLAUDE.draft.md` | Constitution prose (lean + expanded) | §0–§14 + frontmatter done |
| `STATUS.md` | This file | — |

## Where we are
- **Constitution body §0–§14: COMPLETE.** Every section written via the spec-first loop and
  individually GREEN against its approved spec.
- **Frontmatter (instantiation form): COMPLETE.** Written + GREEN (17/17 checks). Fields:
  `project`, `summary`, structured `stack:` map, `architecture_pattern`, `learning_context`,
  `harnesses`, `docs:` map (§1 classes 2–8). Resolved two forks with the body: no `TECH_STACK.md`
  precedence class (stack authority stays distributed in scope/guide/architecture); no
  preferred-discipline toggle (TDD+BDD is structural, frontmatter can't toggle a binding rule).
  The §8→§14 completion-gate cross-reference was also corrected (prose + spec).
- **Coherence pass (ADR-014): COMPLETE & clean.** 47 `§N` cross-references all resolve (incl. the
  §8→§14 fix); redundancy is all intentional bookending (§0↔§12, §0↔§14, §10 lens, §14
  consolidation, §13 disposition) — no accidental dup; no section over the 60-line flag (§7 largest
  at 48 lean lines). No trims required.
- **ADR-015 strip/keep resolved (ADR-017): keep both.** `CLAUDE.draft.md` (701 lines) is the
  teaching source of truth; `make lean` → `CLAUDE.lean.md` is the production edition (**474 lines,
  within the ~450–550 north-star**, 15 sections, zero EXPANDED markers). Tooling in `_WIP/Makefile`.
- **The constitution (frontmatter + §0–§14) is COMPLETE.**
- 17 ADRs logged; all open design forks for the constitution itself are closed.

## What's next (in order)
1. **Stub `AGENT.md`** (Devin tail) — deliberately minimal until Claude-side work is done; the
   user fills the Devin workflow specifics by doing (ADR, harness #1 decision).
2. **Decide the template's permanent home** (OQ-3) — own repo vs folder; then delete from
   `purrfectreqs/_WIP/`.
3. **Instantiate against GreaseBook** to find the bad seams.

## The process (per ADR-013) — repeat for each remaining unit
1. I draft a **spec** of falsifiable acceptance checks → `CLAUDE.section-specs.md`.
2. **User approves the spec** (spec authority — prevents self-certification).
3. I write the **prose** (lean + expanded, ADR-015) → `CLAUDE.draft.md`.
4. I **verify** per-check, report pass/fail. Failures fix the prose, never the spec.

## Open questions
- **OQ-1/2** GreaseBook stack — web frontend undecided; backend "probably Python".
- **OQ-3** Template's permanent home.
- **OQ-4** PI extraction timeline (affects how much Claude-side workflow to formalize).
- **OQ-5** Ship a filled-in GreaseBook reference instance alongside the blank template?
