<!--
  TEMPLATE — Devin tail STUB (per ADR-007). Project-neutral. In an instantiated project this is
  AGENT.md at the repo root, read by Devin alongside CLAUDE.md. Claude Code / PI never load it.
  The <… TBD> markers are Devin workflow mechanics, filled in by doing (see "Filling this in").
-->

---
# AGENT.md — declares itself the Devin tail; identity proper lives in CLAUDE.md (ADR-004).
role:         Devin tail — workflow mechanics for the constitution in CLAUDE.md
status:       STUB — Devin-specific mechanics pending; fill by doing
depends_on:   CLAUDE.md          # the constitution; binds in full, ranks above this file
applies_to:   Devin (Devin Local)
not_loaded_by: [Claude Code, PI] # their mechanics live in .claude/ + .pi/
---

# AGENT.md — Devin Tail (STUB)

This is the **Devin tail**. It adds **no rules**. The binding constitution is `CLAUDE.md`; this
file says only *how Devin executes* the constitution's `[PROCESS]` phases and `[GATE]` checks.

**Read `CLAUDE.md` first and in full.** It binds every harness, Devin included. On any conflict,
`CLAUDE.md` wins — it is rank 1 (CLAUDE.md §1). Nothing here may weaken, reinterpret, or expand it.

## Devin load semantics

- Devin loads `AGENTS.md`, `AGENT.md`, and `CLAUDE.md` — all always-on, treated identically.
- Global, cross-project rules live in `~/.config/devin/AGENTS.md`.
- `constitution.md` is **not** a Devin-supported filename — the constitution is `CLAUDE.md`.

## Harness boundary (CLAUDE.md §2)

- This file is **Devin-only**. Claude Code and PI never load it; their mechanics live in
  `.claude/` and `.pi/`.
- Do **not** import another harness's workflow assumptions — its commands, its phase mechanics —
  into Devin, or Devin's into them. The constitution is shared; the mechanics are not.

## Lifecycle mechanics — maps Devin onto CLAUDE.md §8

The canonical phases are fixed by the constitution (§8). Here is how **Devin** runs each. STUB —
each `<… TBD>` is filled as the Devin workflow is learned.

1. **Preplan** — analyse context/codebase before planning. `<Devin mechanic: TBD>`
2. **Plan** — produce the plan from the spec (§4) + preplan analysis. `<TBD>`
3. **Plan-refinement loop** — iterate / enrich / adversarial / testability, on the *plan artifact*
   only (CLAUDE.md §8). `<TBD>`
4. **Freeze** — lock the plan/scope; nothing below begins until frozen. `<TBD>`
5. **Write tests** — author tests, observe **RED**. `<Devin mechanic for capturing the RED record: TBD>`
6. **Implement** — minimum code to **GREEN**. `<TBD>`
7. **Review** — verify against the completion gate (CLAUDE.md §14). `<TBD>`

## Enforcing `[PROCESS]` at phase boundaries (CLAUDE.md §0, §8)

- `[PROCESS]` rules cannot be reconstructed from the final diff, so Devin verifies them at the
  **boundary between phases**, not after the fact. `<How Devin checkpoints a boundary — session
  checkpoint, commit/PR record, …: TBD>`
- **Test-first proof.** The RED observation (CLAUDE.md §7, §14) is captured as evidence, never
  narrated. "Narration is not evidence" (§0). `<Devin mechanic for the execution record: TBD>`

## Enforcing `[GATE]`s (CLAUDE.md §14)

- Project gates — lint, format, static analysis, coverage floor, mutation threshold (per `docs/`)
  — run via `<Devin mechanism: TBD>`. Proof is the tool output.
- **Read-completeness `[GATE]`** for governed docs (ADR-012) is **deferred for Devin** — built
  after the Claude-side hook exists.

## Devin skills / workflows

- If Devin uses a skills folder, it is `.devin/`. `<List Devin skills and how each binds to the
  phases above: TBD>`

## Filling this in

This stub is intentionally minimal (ADR-007). The Devin workflow specifics are learned **by doing**
— building the GreaseBook Android client in Devin (harness-adr.md §3). As each phase mechanic is
decided, replace its `<… TBD>` and log the decision as an ADR in `harness-adr.md`. Until then Devin
still binds to `CLAUDE.md` in full; only the *mechanics* are pending.
