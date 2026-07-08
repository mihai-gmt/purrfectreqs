# Harness Toolkit — Build Plan (DRAFT)

> **DRAFT for review (2026-06-26).** Supersedes `pi-extraction-plan.md` (now folded in as Workstream B).
> The product is one toolkit, not a PI extraction with extras. Companion to `STATUS.md` and the
> constitution work in this folder. Not frozen.

## Vision

One GitHub repo: a **harness-support toolkit** = a harness-neutral constitution + supporting
documentation (usable on its own with Claude Code or Devin) **plus** the PI engine/extension layer as
an optional add-on, with an **installer** that scaffolds either *(docs only)* or *(docs + PI)* into a
target project and interactively fills the frontmatter. Distilled from the six-point big picture
(2026-06-26): repo (1) · installer modes (2) · interactive install workflow (3) · PI layer extraction
(4) · finish Claude/Devin docs (5) · common architecture across harnesses (6).

## Settled decisions

- **Extend, not fork.** Toolkit declares `@earendil-works/pi-coding-agent` as an npm dependency; PI
  source is never forked or vendored.
- **Neutral root.** Repo root is the harness-neutral toolkit; PI is a peer under `tails/pi/`, not the
  substrate.
- **Three-layer architecture** (the spine — see below).
- ~~**Generalize via GreaseBook, not in the abstract**~~ — **SUPERSEDED by ADR-023.** All GreaseBook
  validation moves to *after* toolkit completion; the config seam is generalized **by design** from
  known references (PurrfectReqs + the PI cross-check) and validated by real-use adoption later, with
  corrections handled as defects. "Toolkit complete" requires only PurrfectReqs-provable gates.
- **Shared neutral layer = constitution + docs + playbook + tail-contract (ADR-022).** Identical across
  Claude/PI/Devin. Only **skill-building mechanics** diverge per harness (Devin's skill model differs
  100% from Claude's); the discipline does not.
- **Docs always install; PI is additive.** The install choice is "also install the PI engine?", not an
  exclusive Claude/Devin-vs-PI fork (Claude Code + PI can run on one project).
- **One tiered tail-contract, not two streams (ADR-018).** A single shared contract of 11 obligations
  (T1–T11), each met at the strongest §0 tier a harness can honestly reach (`[GATE]`→`[PROCESS]`→
  `[REVIEW]`). Tiering — not splitting by harness — prevents lowest-common-denominator quality loss.
  Implementations stay three separate folders; only the contract is shared.
- **Harness affinity: Claude+PI are siblings, Devin is the outlier (ADR-019).** They share enforcement
  capability (out-of-model veto: PI `pi.on("tool_call")`, Claude `PreToolUse` hook) *and* prompt
  lineage (PI prompts are ported Claude commands). PI is "separate" only on build/packaging (npm dep +
  TS engine). Pair Claude+PI for authoring; give Devin its own track with honest `[REVIEW]` degradation.
- **Claude/PI share prompt bodies via mechanics injection (ADR-020).** One canonical per-phase body in
  the playbook; each tail wraps it and injects its mechanics. No per-tail duplication.
- **Claude's human-only control plane is a hook + state file, not a slash command (ADR-021).** Claude's
  `SlashCommand` tool means the model can invoke its own commands, so the human-only guarantee must be
  engineered (state file mutated by a human-run script, read by a `PreToolUse` hook).

## Three-layer architecture (the spine — point 6)

Just §2/§8 of the constitution applied one level down to the supporting docs/skills:

| Layer | Content | Shared? |
|---|---|---|
| **Constitution** | `CLAUDE.md` — §8 names the phases abstractly | shared (DONE) |
| **Workflow playbook** | per phase: what to read, what artifact to produce, which gates apply, escalation hooks — the *discipline* | **shared**, referenced by every tail |
| **Tail-contract** | the 11 obligations (T1–T11) every tail must realise, each at a §0 tier | **shared** (single, tiered — ADR-018) |
| **Tails** `tails/{claude,pi,devin}/` | only the *mechanics*: how a harness invokes/enforces a phase | harness-specific |

The PI prompts today blend three things — neutral discipline + Pi mechanics + PurrfectReqs specifics.
The cross-check (Workstream A) pulls them apart: discipline → playbook, mechanics → `tails/pi`, project
specifics → config. The mechanics split is governed by a single **tiered tail-contract** (ADR-018): a
shared list of obligations each harness meets at the strongest tier it honestly can (Claude+PI at
`[GATE]` for the load-bearing T5/T6/T7; Devin degrading to `[REVIEW]` until its enforcement model is
known — OQ-8). Claude and PI are the close pair (ADR-019) and share prompt bodies via mechanics
injection (ADR-020).

## Repo shape

```
harness-toolkit/
  constitution/   CLAUDE.template.md (+ make lean), docs/ stubs
  workflow/       shared per-phase playbook + the tail-contract spec
  tails/
    claude/       slash commands / skills + Read-completeness hook
    devin/        AGENT.md (+ .devin/)
    pi/           engine + extensions + prompts + settings + sample harness.config.json
  install/        install.py
  README.md       instantiation guide
  <design docs>   ADR log, this plan
```

## Workstreams

### A — Common workflow architecture (the spine; point 6)
**Goal:** define the shared workflow layer by factoring the proven PI prompts against §8.
- Cross-check each PI prompt (`preplan/plan/iterate/write-tests/implement/review`) against the §8
  phases and the constitution's `[GATE]/[PROCESS]/[REVIEW]` tags.
- Per phase, classify content → (i) neutral discipline → **playbook**; (ii) harness mechanics → tail;
  (iii) PurrfectReqs specifics → config.
- Produce the **shared playbook** (one entry per phase) and the **tiered tail-contract spec** (the
  11 obligations T1–T11, each at a §0 tier per harness — ADR-018).
- **Depends on:** PI prompts (exist) + constitution §8 (done). **Feeds:** B and C.
- **Status:** cross-check DONE (`workstream-a-crosscheck.md`); the generalize-vs-LCD line resolved —
  it is not an LCD (see §4 there). Two-stream question resolved (ADR-018: one tiered contract).
  Remaining: author `workflow/playbook.md` (spec-first) + `workflow/tail-contract.md`.
- ~~**Open:** how much genuinely generalizes vs forces a lowest-common-denominator~~ — RESOLVED: the
  P/M/C split is clean; tiering (not splitting) handles the divergence (ADR-018).

### B — PI layer extraction (point 4; ex `pi-extraction-plan.md`)
**Goal:** move our PI layer into `tails/pi/`, depend on the package, split reusable from project-specific.
- `tails/pi/`: `prompts/`, `governance/{engine,config,audit}` + tests, `extensions/governance.ts`,
  `settings.json`, `MODEL_POLICY` (as a per-project template).
- `package.json` declaring the `@earendil-works/pi-coding-agent` dependency.
- **Split:** engine ships as-is (config-injected); PurrfectReqs `CONFIG`/`PATTERNS`/`PROSE_RULES` →
  sample `harness.config.json` + generic defaults. Complete the config seam (the
  `APP_AGNOSTIC_EXTRACTION_DECISION` checklist).
- **Hygiene punch-list:** relative paths in `feature-box.json`; ship no pre-satisfied `red/greenConfirmed`;
  reconcile runtime-state/`sessions` against the "nothing PI gitignored" principle + transcript-secrets
  risk; `MODEL_POLICY` per-project + Agent-SDK billing caveat (README model section already reframed).
- Carry `node:test`; confirm `node --test` passes in the new home.
- **Depends on:** A (discipline/mechanics split) + repo skeleton. **Generalization validated by:** GreaseBook.

### C — Claude/Devin tails + supporting docs (point 5; derived from A)
**Goal:** finish the neutral supporting docs and build the Claude + Devin tails *from the shared playbook*.
Per ADR-019, Claude is PI's sibling, so **author the Claude tail alongside B (the PI tail)**; Devin is
the outlier and gets its own track.
- `docs/` stubs (the constitution's `docs:` map) + instantiation guide.
- `tails/claude/`: per-phase command files that **wrap the shared playbook body and inject Claude
  mechanics** (ADR-020) — do NOT author from scratch, do NOT duplicate the PI prompt bodies.
- **Claude governance hook surface (ADR-021):** a `PreToolUse` hook + a human-mutated state file
  realising the T5/T6/T7 `[GATE]` tier (phase-state, feature-box, RED/GREEN), plus the Read-completeness
  `[GATE]` hook (ADR-012). The control plane is the hook+state-file, never a slash command.
- `AGENT.md` mechanics (currently a stub) — fill from the tail contract; Devin's T5/T6/T7 stay
  `[REVIEW]` until OQ-8 (Devin enforcement model) is resolved.
- **Depends on:** A (tiered tail contract + playbook), B (PI prompts as the shared-body source).

### D — Repo + installer (points 1–3)
**Goal:** the GitHub repo + interactive selective installer.
- Repo per the shape above; `make lean` produces the production `CLAUDE.md`.
- **Installer (Python — interactive):** asks (a) **also install the PI engine layer?** (docs install
  regardless), (b) **target project path**, (c) **frontmatter answers** (project, scope, stack, learning
  context, doc names). Modes: `init` (scaffold + wire PI) and `update` (refresh engine/prompts, **never
  clobber** a filled `CLAUDE.md`/`docs/`). PI wiring = npm-install the package + drop `tails/pi/` + sample
  `harness.config.json`.
- Document the three-way model split: app AI → local Ollama; PI harness → hosted; Claude Code → Claude on
  subscription.
- **Depends on:** A/B/C produce the payload the installer ships.

## Shared phases & recommended sequencing

1. **Decisions** — OQ-3 (repo home/shape), OQ-1/2 (GreaseBook stack), sessions reconciliation, installer language.
2. **Repo skeleton** — converges the constitution track + PI track into one root.
3. **A** (cross-check / spine) — the playbook + tail contract.
4. **B + C in parallel** against A's output (Claude+PI paired per ADR-019; Devin track separate).
5. **D** — installer.
6. **Toolkit complete** at the in-toolkit gates (ADR-023). GreaseBook instantiation (config-seam
   generalization proof + Devin tail) happens **post-toolkit, by adoption**; corrections are defects.

## Validation gates

**In-toolkit (must pass before "complete" — all PurrfectReqs-provable, per ADR-023):**
1. PI validated on a **brand-new PurrfectReqs feature** end-to-end *(partly met — auth-register ran RED→GREEN under PI; confirm it counts)*.
2. `/reload` loads prompts + exactly one extension entrypoint; six prompts used in real work.
3. Claude tail dogfoodable on PurrfectReqs (its gates fire on a real change).

**Post-toolkit (validation by adoption — corrections handled as defects, ADR-023):**
4. PI + config seam on a **second non-PurrfectReqs project = GreaseBook** (the
   `APP_AGNOSTIC_EXTRACTION_DECISION` "second project" check — now satisfied *after* ship).
5. Devin tail on the **GreaseBook Android client** — resolves OQ-8 (Devin enforcement model) and
   upgrades Devin tiers where possible.

## Risks / watch-items
- **Config seam generalized without a second-project check at ship (ADR-023)** — highest-rework-risk
  unvalidated piece; mitigated only by keeping the seam driven from `harness.config.json` and the two
  known references, and by treating post-adoption gaps as defects. Accepted knowingly.
- **Lowest-common-denominator playbook** — A must find the real shared/tail line, not force-share. *(Resolved: the line is clean — ADR-018 tiering, `workstream-a-crosscheck.md` §4.)*
- **Two tracks, one repo** — constitution track + PI track share the repo skeleton; sequence together.
- **Sessions secrets vs no-gitignore principle** — unresolved; conscious call in Decisions/B.
- **Devin tail ships unvalidated (OQ-8)** — structurally provided, validation pending post-toolkit;
  a cheap Devin smoke test (does it load `CLAUDE.md`/`AGENT.md` + support skill-linking?) de-risks the
  structural assumption before the full GreaseBook-Android validation.

## Open decisions
- ~~OQ-3 repo home / shape~~ — RESOLVED: `~/projects/harness-toolkit`.
- ~~OQ-1/2 GreaseBook stack~~ — no longer blocks toolkit; deferred to post-toolkit adoption (ADR-023).
- Sessions/runtime-state gitignore reconciliation (Workstream B).
- Installer language — Python recommended (interactive frontmatter fill) (Workstream D).
- Four candidate constitution amendments (`workstream-a-crosscheck.md` §5) — in-constitution vs playbook-only.
