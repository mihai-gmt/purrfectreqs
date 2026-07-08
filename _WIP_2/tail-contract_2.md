# Tail Contract (tiered) — what every harness tail must realise

> **Role in the toolkit.** The middle of the three layers (constitution → **this contract + the
> playbook** → tails). The *playbook* says what discipline each §8 phase requires (harness-neutral).
> This *contract* says what a tail must provide so that discipline is actually enforced in a runtime.
> One contract, shared by all tails; each obligation is met at the strongest §0 tier the harness can
> **honestly** reach (ADR-018). Destination on extraction: `workflow/tail-contract.md`.
>
> Status: **DRAFT for review.** Derived from `workstream-a-crosscheck.md` §3 (T1–T11) and
> `workstream-a-tail-streams.md` (enforcement surfaces). Not authored from scratch — factored from the
> six proven PI prompts.

---

## 1. How this contract works

- **Obligations are fixed; tiers are per-harness.** The 11 obligations (T1–T11) are the same for every
  tail. What differs is the §0 tier at which each harness satisfies an obligation:
  - **`[GATE]`** — enforced by tooling *outside the model*; the agent cannot fake or skip it.
  - **`[PROCESS]`** — enforced by phase/commit order, checked at the boundary; not reconstructable from
    the final diff.
  - **`[REVIEW]`** — discipline only; the agent complies, a human verifies. The weakest tier.
- **Honest degradation, never silent (§0).** A tail MUST declare the tier it achieves for each
  obligation. Claiming `[GATE]` without an out-of-model mechanism is the self-certification §0 forbids.
  A genuine `[REVIEW]` clearly labelled is acceptable; a `[REVIEW]` dressed as a `[GATE]` is not.
- **Tiering, not splitting (ADR-018).** Divergence between harnesses is absorbed by the tier column, so
  the contract stays single and no harness drags the others to a lowest common denominator.
- **This contract owns mechanics only.** Discipline lives in the playbook (P); project specifics live
  in `harness.config.json` (C). If an item here states *what discipline*, it has leaked from the
  playbook; if it names a concrete path/tool, it has leaked from config.

---

## 2. The obligations at a glance

Target tiers reflect ADR-019 (Claude+PI siblings; Devin outlier) and OQ-8 (Devin enforcement unknown).

| # | Obligation | §8 phase(s) | PI | Claude | Devin |
|---|---|---|---|---|---|
| T1 | Invoke each phase as a discrete, named unit | all | `[GATE]`¹ | `[GATE]`¹ | `[PROCESS]` |
| T2 | Pass the spec (feature) path into the phase | all | `[PROCESS]` | `[PROCESS]` | `[PROCESS]` |
| T3 | Enforce the bounded read-set | all | `[REVIEW]`² | `[GATE]` (hook) | `[REVIEW]` |
| T4 | Write the phase output artifact to the agreed path | all | `[PROCESS]` | `[PROCESS]` | `[PROCESS]` |
| T5 | Phase-state tracking; refuse out-of-order | all | `[GATE]` | `[GATE]` | `[REVIEW]` (OQ-8) |
| T6 | Feature-box enforcement (file-granular allowlist) | 5,6 | `[GATE]` | `[GATE]` | `[REVIEW]` (OQ-8) |
| T7 | Gate attestation that isn't narration (RED/GREEN) | 5,6 | `[GATE]` | `[GATE]` | `[REVIEW]`/`[PROCESS]` (OQ-8) |
| T8 | Freeze lock (one-way DRAFT→FROZEN, human reopen) | 4 | `[PROCESS]` | `[PROCESS]` | `[PROCESS]` |
| T9 | Escalation surface (stop, emit §12 format, wait) | all | `[REVIEW]` | `[REVIEW]` | `[REVIEW]` |
| T10 | Context isolation between phases | all | `[PROCESS]` | `[PROCESS]` | `[PROCESS]` |
| T11 | Typed handoff (report block naming next phase) | all | `[REVIEW]` | `[REVIEW]` | `[REVIEW]` |

¹ Discrete invocation is `[GATE]`-strength only insofar as the runtime makes a phase a distinct,
addressable command/skill; the *human-only* property that matters for gating lives in T5/T6/T7, not T1.
² PI enforces the read-set by prompt discipline today; it could be raised to `[GATE]` with a
`pi.on("tool_call")` read-veto. Recorded as a Workstream B option, not required by this contract.

**The load-bearing three are T5/T6/T7.** They are what make `[PROCESS]`/`[GATE]` real rather than
narrated, and they are where Claude must be engineered to match PI (ADR-021) and where Devin honestly
degrades (OQ-8). The rest are either structural (`[PROCESS]`) or discipline the tail can only host, not
enforce (`[REVIEW]`).

---

## 3. Obligation detail

Each obligation: **What** it requires · **Why** (which playbook discipline it makes real) ·
**Realisation** per harness · **Acceptance check** (how to verify a tail satisfies it).

### T1 — Discrete, named phase invocation
- **What:** each §8 phase is a separately addressable unit a human can start; phases are not one
  monolithic run.
- **Why:** phase boundaries are the checkpoints (§8); there is nothing to check at a boundary that
  doesn't exist.
- **Realisation:** PI `prompts/*.md` (6 commands); Claude `tails/claude/commands/*.md`; Devin a
  session/skill per phase.
- **Acceptance:** each of the 7 phases (preplan, plan, refine, freeze, write-tests, implement, review)
  is invocable on its own; freeze may be a sub-mode of the refine command (PI packaging — allowed).

### T2 — Spec path passed into the phase
- **What:** the phase receives the `.feature`/spec identifier as input and halts if it is missing or the
  wrong kind.
- **Why:** input-contract discipline (playbook pattern 1) — a phase with no spec has no contract.
- **Realisation:** PI/Claude `$ARGUMENTS`; Devin session input.
- **Acceptance:** invoking a phase without a valid spec path stops with an ask, never guesses.

### T3 — Bounded read-set enforced
- **What:** the phase reads only the spec + prior artifact + the governing docs its lens needs, and is
  prevented (or at least instructed) from reading outside that set.
- **Why:** bounded-context discipline (playbook pattern 2); each refinement lens has a disjoint read-set.
- **Realisation:** Claude `[GATE]` via the Read-completeness / read-scope `PreToolUse` hook (ADR-012);
  PI `[REVIEW]` by prompt today (raisable to `[GATE]`, footnote ²); Devin `[REVIEW]`.
- **Acceptance:** a read outside the declared set is rejected (Claude) or is a documented `[REVIEW]`
  expectation the prompt states (PI/Devin).

### T4 — Output artifact written to the agreed path
- **What:** every phase produces one durable artifact at a derived, conventional path.
- **Why:** named-output discipline (playbook pattern 4); the next phase consumes it.
- **Realisation:** all three write to the config-defined path scheme.
- **Acceptance:** after a phase completes, the artifact exists at the path the config dictates; a phase
  that produced none has not completed.

### T5 — Phase-state tracking (refuse out-of-order) — **load-bearing**
- **What:** the current phase is recorded outside the model, and a phase refuses to run if the prior
  phase's state isn't satisfied (e.g. implement won't run before RED).
- **Why:** §8's temporal `[PROCESS]` guarantee is only real if "what phase are we in" can't be asserted
  by the agent.
- **Realisation:** PI `/phase set …` (`registerCommand`, outside the LLM tool registry). Claude **state
  file mutated by a human-run script, read by a `PreToolUse` hook** — **not** a slash command, because
  the model can invoke its own slash commands (ADR-021). Devin `[REVIEW]` until OQ-8.
- **Acceptance:** the agent cannot advance the phase itself; only a human action changes phase state;
  out-of-order phase invocation is blocked (Claude/PI) or flagged (Devin).

### T6 — Feature-box enforcement (file-granular allowlist) — **load-bearing**
- **What:** during write-tests/implement, edits are restricted to the files the frozen plan authorises.
- **Why:** §9 Feature Box discipline made enforceable. Honest limit: the allowlist grants the *file*,
  not arbitrary edits within it — an out-of-scope change inside a permitted file still requires human
  escalation (this is a `[GATE]` that is necessary but not sufficient; see playbook Finding 7).
- **Realisation:** PI `/box set/plan/allow-files-from-plan`; Claude `PreToolUse` hook reading the
  allowlist from the state file; Devin `[REVIEW]`.
- **Acceptance:** an edit to a file outside the allowlist is blocked (Claude/PI); the
  necessary-but-not-sufficient caveat is stated to the agent so in-file scope-creep still escalates.

### T7 — Gate attestation that isn't narration (RED/GREEN) — **load-bearing**
- **What:** RED (tests fail pre-impl) and GREEN (tests pass post-impl) are recorded by tooling running
  the tests, not by the agent asserting it.
- **Why:** the canonical "narration is not evidence" (§0). This is the cleanest P/M split: discipline in
  the playbook, mechanism in the tail.
- **Realisation:** PI `/box run-red` / `/box run-green` (manual attestation disabled). Claude a
  hook-wrapped or human-run test invocation that writes the RED/GREEN state the phase gate reads. Devin
  `[REVIEW]`, or `[PROCESS]` if commit order can evidence test-before-code.
- **Acceptance:** a phase cannot treat RED/GREEN as satisfied on the agent's word; the satisfied state
  exists only after a real test run recorded outside the model.

### T8 — Freeze lock (one-way DRAFT→FROZEN)
- **What:** freezing the plan is a one-way transition; further refinement requires a human to reopen it
  to DRAFT.
- **Why:** §8 freeze is the commit point that makes write-tests/implement meaningful; it must not be
  silently reversible.
- **Realisation:** all three via the plan artifact's Status field + the freeze checks (refinement-ran +
  completeness + escalation-scan + consistency).
- **Acceptance:** a FROZEN plan blocks further iterate scopes except a human reopening it; freeze is
  refused unless the refinement lenses are evidenced (changelog).

### T9 — Escalation surface
- **What:** when a §12 trigger fires, the phase stops, emits the constitution's escalation format, and
  waits.
- **Why:** escalation-not-optional (§0/§12).
- **Realisation:** `[REVIEW]` in all three — the tail can host the stop+format, but compliance is the
  agent's; a human resolves.
- **Acceptance:** each phase's prompt/skill instructs the escalation stop+format and names §12 as the
  trigger source.

### T10 — Context isolation between phases
- **What:** each phase starts from a clean context rather than inheriting the previous phase's working
  memory.
- **Why:** keeps a phase bound to its artifacts (T4) and read-set (T3), preventing leakage of unscoped
  context.
- **Realisation:** PI "clear context" instruction; Claude `/clear` or a sub-agent boundary; Devin a new
  session. `[PROCESS]` — verifiable by the handoff convention, not the diff.
- **Acceptance:** the handoff step (T11) directs a context clear before the next phase.

### T11 — Typed handoff
- **What:** each phase ends with a structured report naming what was produced and the next phase to run.
- **Why:** typed-handoff discipline (playbook pattern 7); makes the lifecycle navigable.
- **Realisation:** `[REVIEW]` in all three — fixed report blocks; the next-command names are config (C).
- **Acceptance:** every phase ends with a report block that names the next phase/command.

---

## 4. Devin status (OQ-8) and the degradation rule

Devin's T5/T6/T7 are `[REVIEW]` (T7 possibly `[PROCESS]` via commit order) **until its enforcement
model is known** — whether Devin offers any out-of-model tool-call veto or human-only control plane we
can author. The Devin tail **ships at these tiers** (ADR-023 — Devin validation is post-toolkit); the
enforcement story is learned by adoption, and any tier upgrade is a **defect-driven correction**, not a
completion blocker. This is the toolkit's principal cross-harness quality exposure and is **labelled,
not hidden** (ADR-018). Two consequences:
- Devin tails MUST NOT claim `[GATE]` for T5/T6/T7 before OQ-8 is resolved.
- When the post-toolkit GreaseBook-Android adoption exercises this, each mechanic learned fills the
  `AGENT.md` `<… TBD>` and is logged as an ADR (per ADR-007 / the constitution-track plan). A cheap
  Devin smoke test (does it load `CLAUDE.md`/`AGENT.md` + support skill-linking?) is recommended to
  de-risk the structural assumption before the full adoption validation.

---

## 5. Out of scope for this contract

- **Discipline** (the *what*/*why* of each phase) — owned by `workflow/playbook.md`.
- **Project specifics** (concrete doc names, paths, test commands, the `# Type:` taxonomy, language
  idioms) — owned by `harness.config.json` (Workstream B config seam).
- **Constitution rules** (§0 tags, §8 phases, §9 Feature Box, §12 escalation) — referenced, never
  redefined here.

---

## 6. Open items feeding back

- **OQ-8** — Devin enforcement model (gates Devin `[GATE]`).
- **Footnote ²** — raise PI T3 to `[GATE]` via a read-veto? (Workstream B option, not required.)
- The four candidate constitution amendments (`workstream-a-crosscheck.md` §5) interact with T6/T7/T8
  and review attribution; resolve in the constitution-vs-playbook decision.
</content>
