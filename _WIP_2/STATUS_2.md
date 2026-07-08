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
| `harness-adr.md` | Decision log (ADR-001…017) | current |
| `CLAUDE.skeleton.md` | Locked section structure | done |
| `CLAUDE.section-specs.md` | Per-section acceptance checks (the "tests") | §0–§14 done |
| `CLAUDE.draft.md` | Constitution prose (lean + expanded) | §0–§14 + frontmatter done |
| `AGENT.md` | Devin tail (workflow mechanics) | STUB — mechanics TBD |
| `Makefile` | Template tooling (`make lean`) | done |
| `toolkit-build-plan.md` | Master plan: repo + installer + PI extraction + tails (6-point big picture) | DRAFT |
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
- ~~Stub `AGENT.md` (Devin tail)~~ — DONE. Minimal stub written; maps Devin onto §8, marks every
  Devin mechanic `<… TBD>` to fill by doing (GreaseBook Android work).
1. **Decide the template's permanent home** (OQ-3) — own repo vs folder; then delete from
   `purrfectreqs/_WIP/`.
2. **Instantiate against GreaseBook** to find the bad seams.
3. **Fill `AGENT.md` mechanics by doing** — as each Devin phase mechanic is decided, replace its
   `<… TBD>` and log an ADR. (Ongoing, not blocking the above.)

## Pre-extraction checklist (before OQ-3 — the template must be self-consistent)

The constitution and `AGENT.md` reference artifacts that do not exist yet. They're implied but
unwritten; fine inside `_WIP/`, but extraction is the moment to create them so the shipped template
is self-consistent (ADR-007: template ships rules + skeletal workflow + docs placeholders).

- [ ] **`docs/` placeholder files** referenced by the constitution's `docs:` map (§1) and body —
  `SECURITY.md`, `SCOPE.md`, `ARCHITECTURE.md`, `DATA_MODELS.md`, `<LANG>_GUIDE.md`, `GLOSSARY.md`,
  plus the `tests/features/` specs location (§4). Each a stub stating its role + a fill marker.
  (Note: stack authority is distributed across SCOPE/guide/ARCHITECTURE per ADR-016 — no separate
  `TECH_STACK.md` precedence doc required; add a descriptive one only if wanted.)
- [ ] **`.claude/` + `.pi/` skeletal workflow** (ADR-007) — the Claude/PI tail: slash commands /
  prompts / phase scaffolding mapping onto the §8 lifecycle. Currently nonexistent as template
  artifacts.
- [ ] **`.devin/` skills** placeholder, if Devin uses a folder (referenced by `AGENT.md`).
- [ ] **Read-completeness `[GATE]` hook** (ADR-012) — `settings.json` hook for the Claude tail;
  deferred, build when doing the Claude-side tail.
- [ ] **`CLAUDE.md` itself** = the generated lean edition (`make lean`); decide commit-vs-gitignore
  for the build artifact at the new home.
- [ ] **README / instantiation guide** — how an adopter fills the frontmatter form + docs and wires
  their harness tails. (OQ-5 ties in: ship a filled GreaseBook reference instance too?)

## PI harness extraction — analysis & punch-list

From a full read of `purrfectreqs/.pi/` (2026-06-26). The PurrfectReqs `.pi/` tree is left **as-is**;
everything below is addressed *at extraction*, not by patching that tree.

**Headline verdict — it's EXTEND, not fork.** PI is the published npm package
`@earendil-works/pi-coding-agent`. The whole governance layer is a clean adapter
(`.pi/extensions/governance.ts`) on PI's *public* `ExtensionAPI` (`pi.on`, `pi.registerCommand`,
`ctx.ui`) plus native prompt/settings mechanisms — **zero PI source modified**. Consequence: the
toolkit **depends on the package, never forks or vendors it.** No license entanglement, no merge
tax. This single decision drives the repo/installer design.

**Architecture (sound, reuse-ready).** Four layers: adapter (`extensions/governance.ts`, ~75 ln) /
engine (`governance/engine.ts`, ~849 ln, ~40 pure fns + `createGovernanceEngine(config)` — config is
dependency-injected) / config seam (`governance/config.ts`, all PurrfectReqs specifics; already reads
`.pi/harness.config.json` overrides via `loadHarnessConfig`) / audit (`governance/audit.ts`, new,
append-only JSONL). 35 `node:test` cases on the pure core.

**Convergence with the constitution.** The PI engine *is* the `[GATE]` enforcement of the
constitution: `preplan→…→review` = §8 lifecycle; `pi.on("tool_call")` blocking = the `[GATE]` layer;
human-only `/box`/`/phase` (not in the LLM tool registry) = the `[PROCESS]` boundary made unfakeable;
`run-red`/`run-green` (manual attestation disabled) = "narration is not evidence" in code. Two
workstreams, one thing: constitution states the discipline, PI enforces it for one harness.

**Generalization gate (do it *via* GreaseBook).** Still PurrfectReqs-coupled: `CONFIG` defaults,
`PATTERNS` (Python/FastAPI UTC + cross-model-import regexes), `PROSE_RULES`. The seam exists; finish
it by **instantiating against GreaseBook**, which satisfies the `APP_AGNOSTIC_EXTRACTION_DECISION`
"validate on a second non-PurrfectReqs project" gate. Do not generalize in the abstract.

**Punch-list (deferred to extraction):**
- [ ] **Depend, don't fork** — declare `@earendil-works/pi-coding-agent` as an npm dependency; toolkit
  ships only the extension layer (prompts + engine + settings).
- [ ] **Complete the config seam** — make `CONFIG`/`PATTERNS`/`PROSE_RULES` fully driven by
  `harness.config.json`; prove it on GreaseBook.
- [ ] **`MODEL_POLICY.md` is a per-project artifact**, not a shipped mandate. README model section
  already reframed to "user chooses" (done in `.pi/README.md`). Keep `enabledModels` restriction +
  the **Agent-SDK billing caveat** (Claude via 3rd-party harness bills a separate pool) as a
  documented default for adopters.
- [ ] **Runtime-state hygiene** — `feature-box.json` embeds absolute local paths + stale
  `red/greenConfirmed:true`; consider engine change to write **relative** paths and not ship
  pre-satisfied gates. (User principle: *nothing PI-related gitignored* — so the transient-state and
  `sessions/*.jsonl` **transcript-secrets risk** are reconciled at extraction, esp. if the repo goes
  public; currently `.pi/sessions/` is the only ignored PI path.)

**Repo/installer shape (recommended, OQ-3 open):** one repo, **neutral root** (not PI-based — PI is a
peer package under `tails/pi/`), PI as an npm dependency. **Selective** installer
(`--harness claude,devin,pi`) with `init` vs `update` modes (never clobber a filled `CLAUDE.md`).
Python if it interactively fills the frontmatter form; bash if it's dumb-copy. Three-way model split
to document: app AI → local Ollama; PI harness → hosted (e.g. gpt-5.5); Claude Code → Claude on
subscription.

## The process (per ADR-013) — repeat for each remaining unit
1. I draft a **spec** of falsifiable acceptance checks → `CLAUDE.section-specs.md`.
2. **User approves the spec** (spec authority — prevents self-certification).
3. I write the **prose** (lean + expanded, ADR-015) → `CLAUDE.draft.md`.
4. I **verify** per-check, report pass/fail. Failures fix the prose, never the spec.

## Open questions
- **OQ-1/2** GreaseBook stack — web frontend undecided; backend "probably Python".
- ~~**OQ-3** Template's permanent home.~~ **RESOLVED:** `~/projects/harness-toolkit` (scaffolded
  copy-only 2026-06-26; user handles git/commits; originals stay in `_WIP/` until extraction done).
- **OQ-4** PI extraction timeline (affects how much Claude-side workflow to formalize). See the
  *PI harness extraction — analysis & punch-list* section above (extend-not-fork; depend on the npm package).
- **OQ-5** Ship a filled-in GreaseBook reference instance alongside the blank template?
