# Playbook spec — falsifiable acceptance checks for `workflow/playbook.md`

> **ADR-013 spec-first (RED step).** This file defines what the playbook prose must satisfy *before* it
> is written. **User holds spec authority** — approve/adjust these checks first; then I write the prose
> and verify it per-check (failures fix the prose, never the spec). Mirrors `CLAUDE.section-specs.md`.
>
> **What the playbook is.** The middle layer's *discipline* half: one entry per §8 phase capturing the
> **P-column** (neutral discipline) from `workstream-a-crosscheck.md` §2. It is harness-neutral
> (mechanics → tails) and project-neutral (specifics → `harness.config.json`). Shared by all harnesses
> including Devin (ADR-022). Its companion is `tail-contract.md` (the obligations); the playbook says
> *what each phase must do*, the contract says *what a tail must provide to enforce it*.

---

## A. Structural checks (the document as a whole)

- **A1.** The playbook has exactly **seven phase entries**, in §8 order: Preplan, Plan, Refinement loop,
  Freeze, Write-tests, Implement, Review. No extra phases; none merged.
- **A2.** A **shared preamble** precedes the entries, stating the eight cross-cutting patterns every
  entry inherits (see B). Each entry assumes the preamble and does not restate it.
- **A3.** Every phase entry uses the **same nine-field template** (C). No entry omits a field; "n/a"
  must be explicit, not silent.
- **A4.** Every gate reference in an entry names a **tail-contract obligation (T1–T11)** *and* a **§0
  tag** (`[GATE]`/`[PROCESS]`/`[REVIEW]`). No gate is asserted without both.
- **A5.** Every cross-reference resolves: `§N` → constitution section; `Tn` → tail-contract obligation;
  phase names → an A1 entry.

## B. Shared-preamble checks (the eight patterns — crosscheck §1)

The preamble must state each as a neutral rule the entries inherit:
- **B1.** Input contract; halt if unmet.
- **B2.** Bounded read-set; forbid reading outside it.
- **B3.** One phase = one role with explicit prohibitions.
- **B4.** Each phase writes one named output artifact.
- **B5.** A boundary gate precedes advancing (tagged per §0).
- **B6.** Escalation hook: any §12 trigger → stop, emit the §12 format, wait.
- **B7.** Typed handoff: end with a report naming the next phase; isolate context between phases.
- **B8.** No scope-creep / no self-certification: don't invent scenarios, don't expand, narration is
  not evidence (defer to the gate).

## C. Per-entry template (each of the seven entries must contain)

1. **Phase name + §8 number.**
2. **Role** — the single job and its hard prohibitions.
3. **Input contract** — what must exist / be true to begin; the halt condition.
4. **Read discipline** — the *abstract* read-set (the spec + the prior phase's artifact + only the
   governing docs the phase's question needs) and the prohibition on reading outside it. **No concrete
   file names, paths, or tools** (those are config).
5. **Work** — the discipline of the activity itself.
6. **Output artifact** — what durable artifact the phase produces (abstractly).
7. **Gates** — the tail-contract obligations + §0 tags that bind at this phase's boundary.
8. **Escalation** — phase-specific triggers, deferring to §12.
9. **Handoff** — the next phase + the typed-report + context-isolation expectation.

## D. Per-phase content checks (the specific discipline each entry must carry)

Sourced from `workstream-a-crosscheck.md` §2 (P-bullets) and the four findings.

**D-Preplan.** documentarian-not-critic (describe, never suggest improvements); three research intents —
**locate** (where things live), **analyse** (how current code works), **pattern-find** (what to
imitate); exactly one interpretive "synthesis"; produces an analysis artifact only; writes no plan/code/
tests.

**D-Plan.** skeptical, thorough; **validates the spec before planning** (scope / data-model alignment /
security completeness / terminology / testability / completeness — **flag gaps, never invent
scenarios**); **plan-approval gate** — a human approves the approach and structure *before* the plan
artifact is written (Finding 3); the plan carries a **complete file manifest** so downstream phases
need no exploration; writes no code/tests; never modifies the spec.

**D-Refinement.** **one lens = one question**, no blending; **propose targeted changes, never rewrite**;
**no plan change without explicit approval**; record every applied change in the plan's changelog; each
lens has a **disjoint read-set**; **discovered-scenario rule** — a scenario the spec lacks is
recommended + parked in a backlog, never written into the spec or invented in the plan (§4); the three
lens intents — **adversarial** (what breaks / where naive), **enrich** (detailed enough to execute
without guessing), **testability** (can each phase be test-driven and do we know what the tests prove).

**D-Freeze.** **refinement-completeness gate** — freeze is blocked unless the three lenses are evidenced
(Finding 5); completeness check (required plan content present + specific); **escalation-trigger scan**;
consistency checks (every spec scenario planned; every planned file in the manifest; feasible order);
**freeze is a one-way lock** — reopening to refine requires a human.

**D-Write-tests.** author tests that **fail because the implementation is absent**; **observe RED via
tooling, not assertion** (T7 `[GATE]`); driven by the spec + frozen plan, **not** by reading the
implementation; reuse existing fixtures/steps before adding; a test passing with no implementation is a
bad test — fix it before recording RED; requires the plan FROZEN; writes no implementation, never
modifies the spec, never adds scenarios.

**D-Implement.** minimum production-quality code to **GREEN**; **follow the frozen plan precisely**;
**plan-mismatch → stop and report** (never silently adapt structure); **define the Feature Box before
coding** (§9); implement **phase-by-phase in dependency order, verifying after each**;
**allowlist-is-necessary-but-not-sufficient** — a permitted file does not license out-of-scope edits
within it; those still escalate (Finding 7); never modify tests; never expand beyond failing tests +
frozen plan; **observe GREEN via tooling** (T7 `[GATE]`).

**D-Review.** runs **after GREEN, before commit**; reviewer **cannot change code** — read, assess,
explain; **run tests first, block if not green**; deliverable = a tagged compliance check (PASS/FAIL/
N/A) + learning notes; **diff-scoped attribution** — introduced (blocks) vs pre-existing (logged, not
fixed here); use the **diff**, not just file contents, to attribute (Finding 8); writes only the review
artifact.

## E. Must-NOT-include checks (the layer boundaries)

- **E1.** **No harness mechanics** — no slash-command/skill names, `$ARGUMENTS`, `/box`/`/phase`,
  hooks, `run-red/green`, "clear context" verbs, report-block *formats*. (Those are tails.)
- **E2.** **No project specifics** — no concrete doc names, paths, test/lint commands, the `# Type:`
  taxonomy, language/framework idioms, the A–H compliance checklist content. (Those are config.)
- **E3.** **No new rules** — every rule traces to §8, §0, §4/§9/§12, or a cross-check finding. The
  playbook elaborates the lifecycle per phase; it does not legislate beyond it.
- **E4.** **No tier assignments** — the playbook names *which* obligation/tag applies; the *per-harness
  tier* lives in the tail-contract, not here.

## F. Voice & length checks

- **F1.** Imperative, dense, neutral — the constitution's register (ADR-014 "density, not length").
- **F2.** A phase entry that exceeds ~40 lines is flagged for trim (it is one phase, not a section).
- **F3.** No hedging, no rationale essays inside the binding text; a short "why" per phase is allowed
  only as delimited commentary (ADR-015 style) and introduces no rule.

---

## G. Notes for the approver

- **The four findings (3/5/7/8) are included as playbook discipline by default.** Findings 1/2/4 are
  *also* candidates for the constitution (your open call, `workstream-a-crosscheck.md` §5); putting them
  in the playbook does not pre-empt that — the playbook is the per-phase working home regardless, and
  can reference a constitution section if you later elevate one.
- **Tier judgment-calls (tail-contract §2) do not affect this spec** — the playbook is tier-free (E4).
- On approval, I write `workflow/playbook.md` to satisfy A–F and verify per-check.
</content>
