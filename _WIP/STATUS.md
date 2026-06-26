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
| `CLAUDE.draft.md` | Constitution prose (lean + expanded) | §0–§14 done |
| `STATUS.md` | This file | — |

## Where we are
- **Constitution body §0–§14: COMPLETE.** Every section written via the spec-first loop and
  individually GREEN against its approved spec.
- 15 ADRs logged; all open design forks for the constitution itself are closed.

## What's next (in order)
1. **Frontmatter (§ head).** The identity/pointer block = the per-project *instantiation form*
   (ADR-004). Still a placeholder at the top of `CLAUDE.draft.md`. Same spec-first loop:
   draft spec → user approves → write → verify. Ships with placeholders; optionally fill a
   GreaseBook instance to demonstrate.
2. **Whole-draft coherence + trim pass (ADR-014).** Now that all sections exist:
   - verify every `§N` cross-reference resolves to the right section;
   - judge cross-section redundancy (confirm §10 & §14 read as intentional bookending);
   - check total vs the ~450–550 line north-star; trim only here, never section-by-section.
3. **Stub `AGENT.md`** (Devin tail) — deliberately minimal until Claude-side work is done; the
   user fills the Devin workflow specifics by doing (ADR, harness #1 decision).
4. **Decide the template's permanent home** (OQ-3) — own repo vs folder; then delete from
   `purrfectreqs/_WIP/`.
5. **Instantiate against GreaseBook** to find the bad seams.

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
