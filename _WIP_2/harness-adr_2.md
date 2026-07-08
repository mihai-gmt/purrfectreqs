# Harness Support — Architecture Decision Record (ADR)

> **Living knowledge doc.** Survives `/compact` and `/clear`. If context is lost, re-read
> this file to reconstruct where we are. Append decisions as ADR entries; never silently
> rewrite a past decision — supersede it with a new entry and mark the old one `Superseded`.
>
> Location is temporary: lives in `purrfectreqs/_WIP/` and will be deleted from this repo
> once the template is extracted to its own home.

---

## 1. Purpose

Design a **reusable, teachable template** for "harness support" — the rule + workflow
scaffolding that makes AI coding agents operate under a shared engineering constitution.

Two outputs:
1. **The template** — a project-neutral starter (constitution + harness tails + docs +
   skeletal workflow) that gets instantiated per project.
2. **A teaching artifact** — used to explain to a few colleagues how to build "harness
   support" as a general pattern, not a one-off.

The template will be **validated by instantiating it against GreaseBook** (see §3). Filling
it in is how we find the bad seams.

---

## 2. Harnesses in scope

| Harness | Reads | Role | Notes |
|---|---|---|---|
| **Claude Code** | `CLAUDE.md` only (auto) + `docs/` on demand | Primary dev harness | Workflow lives in `.claude/` + `.pi/` |
| **PI** | same `.pi/.claude` artifacts as Claude Code | Future standalone engine | **Not a separate tail** — mirrors the Claude side. Design Claude-side artifacts so PI consumes them once extracted. |
| **Devin (Devin Local)** | `AGENTS.md`, `AGENT.md`, **and** `CLAUDE.md` — all always-on, treated identically | Used to learn the tool (work tool of choice); will vibe-code GreaseBook Android client | Global rules: `~/.config/devin/AGENTS.md`. `constitution.md` is NOT a supported filename. |

Horizon decision: design the **seams** for exactly these (Claude/PI + Devin) — no
speculative third-harness abstraction — but keep the layering clean enough that a future
harness drops in as a new tail file. (ADR-010)

---

## 3. First instance: GreaseBook

- **What:** personal car-expense tracker — regular maintenance, other work done, fuel
  costs, misc (road taxes, etc.).
- **Clients:** two frontends expected — a **web UI** and an **Android app**. The Android
  app will be **vibe-coded in Devin** specifically to test how well Devin runs phased,
  gated workflows.
- **Backend:** probably **Python** (not finalized).
- **Frontend/web stack:** undecided (the Android client complicates the choice).
- **Why it's a good test:** small enough to not drown in ceremony; the "don't over-engineer
  the architecture" proportionality clause gets stressed; two clients exercise the
  client/boundary separation; Devin-built Android client tests cross-harness discipline.

---

## 4. Target architecture (three layers)

```
PROJECT_ROOT/
  CLAUDE.md      ← THE CONSTITUTION. Tech-agnostic, harness-NEUTRAL. Single source of truth.
                   Read by Claude Code, PI, AND Devin.
  AGENT.md       ← Devin-only tail: Devin workflow/skills mechanics + how Devin enforces the
                   [PROCESS] gates. Claude Code never loads this.
  .claude/ .pi/  ← Claude Code + PI tail: slash commands, prompts, governance engine, phases.
  .devin/        ← Devin skills/workflows (if Devin uses a folder).
  docs/          ← Project + technology specifics. Loaded on demand by any harness.
    ARCHITECTURE.md   chosen pattern (hexagonal/onion/layered/none), module boundaries, gates
    TECH_STACK.md     stack authority
    SCOPE.md          what to build
    SECURITY.md       security specs
    <LANG>_GUIDE.md   language idioms, forbidden constructs, forbidden-dependency lists
    DATA_MODELS.md    schema
```

Layering is achieved by **harness load semantics**, not by duplication or symlinks:
- Claude/PI see: `CLAUDE.md` (constitution) only.
- Devin sees: `CLAUDE.md` (constitution) **+** `AGENT.md` (Devin tail) — additive, no overlap.

---

## 5. Concepts / ubiquitous language

- **Constitution** — the tech-agnostic, harness-neutral rule set (`CLAUDE.md`). Principles,
  behaviour, escalation, enforcement model, lifecycle. Never names a concrete tech choice.
- **Harness** — an agent runtime (Claude Code, PI, Devin) that loads rules and runs workflow.
- **Harness tail** — the harness-specific workflow/skills file(s) that say *how* the
  constitution's process rules are executed in that runtime.
- **Project docs** — per-project, per-technology specifics that carry the enforced `[GATE]`
  detail (analyzers, schemas, forbidden lists).
- **Enforcement model** — `[GATE]` (tooling fails the build), `[PROCESS]` (enforced by phase
  order/commit history, unfalsifiable from the final diff), `[REVIEW]` (human-judgment).
- **Narration is not evidence** — "verified/tested/should work" is text, not proof.
  Completion = the gate, not the agent's claim.
- **Traceability chain** — AC ← Scenario (Gherkin) ← Test ← Implementation.
- **Feature Box** — the explicit boundary of a task (which modules/files in, what's excluded).
- **Proportionality** — apply only the architectural ceremony the project warrants.

---

## 6. Canonical lifecycle (the spine)

`[PROCESS]` phases each harness maps its own mechanics onto:

1. **preplan** — codebase/context analysis → analysis artifact
2. **plan** — draft plan from `.feature` + analysis
3. **plan-refinement loop** — `iterate` / `enrich` / `adversarial` / `testability`, all
   operate on the **plan artifact** (NOT post-review)
4. **freeze** — lock the plan/scope
5. **write-tests** — author tests, observe **RED**
6. **implement** — minimum code to **GREEN**
7. **review** — verify against gates

Correction logged: `iterate` was previously mis-placed after `review`; it operates on the
plan file and belongs in step 3.

---

## 7. Planned section map of the constitution (`CLAUDE.md`)

The spine (`[GATE]/[PROCESS]/[REVIEW]` + lifecycle) is the *enforcement skeleton*; it sits
alongside and gives teeth to the *substance* sections:

- **Frontmatter** — identity/pointer block (the template's instantiation form). See ADR-004.
- **A. Harness Authority** — the separation rule (ADR-003).
- **B. Agent role + behavioural guardrails** — what the agent IS / IS NOT; red flags.
- **C. Engineering principles** (substance, agnostic) — SOLID, separation of concerns,
  dependency-inversion at boundaries, low coupling/high cohesion, proportionality.
- **D. Requirements & BDD quality** (substance) — Gherkin/BDD scenario quality (declarative,
  one-behaviour, ubiquitous language, observable `Then`); INVEST as a light readiness
  **escalation gate** (agent is implementer, not author).
- **E. TDD discipline** (substance) — traceability chain, RED→GREEN→refactor, anti-gaming
  ("laundering catalogue").
- **F. Enforcement model + canonical lifecycle** (spine) — the gate taxonomy and the 7 phases.
- **G. Escalation protocol** — triggers + escalation format.
- **H. Completion gate** — change is not complete on the agent's assertion.

---

## 8. Decision log (ADRs)

### ADR-001 — Three-layer rule architecture · Accepted
Split into: (1) tech-agnostic, harness-neutral constitution; (2) harness-specific tails;
(3) project/technology docs. Rationale: principles are stable and reusable; tech idioms and
forbidden lists are volatile and project-bound; workflow mechanics differ per harness.

### ADR-002 — File mapping via harness load semantics · Accepted
`CLAUDE.md` = shared constitution (read by all three harnesses). `AGENT.md` = Devin tail.
`.claude/` + `.pi/` = Claude/PI tail. `docs/` = project specifics. No duplication, no
symlink, no generated copies. Devin's behaviour (loads all of `AGENTS.md`/`AGENT.md`/
`CLAUDE.md` identically) makes the layering fall out of load order. Supersedes the earlier
"duplicated CLAUDE.md + AGENTS.md" and "canonical CONSTITUTION.md + thin wrappers" ideas
(the latter dead because Devin doesn't read `constitution.md`).

### ADR-003 — CLAUDE.md must be harness-neutral; Harness Authority enforces separation · Accepted
Because **Devin also reads `CLAUDE.md`**, any Claude/PI-specific workflow detail left in it
(`/implement`, `.pi` phases) leaks into Devin and misleads it. Therefore `CLAUDE.md` states
*what* discipline is required and delegates *how it runs* to the tails. A short **Harness
Authority** section names the split and forbids importing one harness's workflow assumptions
into another. This IS the "make the separation visible and enforced" requirement.

### ADR-004 — Frontmatter as identity/pointer block, not authority · Accepted
YAML frontmatter in `CLAUDE.md` carries descriptive identity + pointers only (name, one-line
scope, stack names, architecture-pattern name, doc links). Authority for scope/stack stays in
`docs/`. Caveat acknowledged: frontmatter does NOT reduce model context (harness loads the
whole file as text) — the benefit is human structure + machine-parseability. For the template,
the frontmatter doubles as the **instantiation form**: the short list of fields filled per
project. `AGENT.md` frontmatter stays minimal (declares itself the Devin tail depending on
`CLAUDE.md`) so identity isn't stated twice.

### ADR-005 — Principles in constitution; concrete patterns in docs; proportionality · Accepted
Constitution names principles ("isolate domain from I/O; depend on abstractions at seams").
The concrete pattern (hexagonal/onion/layered/orthogonal/none) lives in `docs/ARCHITECTURE.md`.
Proportionality clause: "apply the pattern in `docs/ARCHITECTURE.md`; if none defined, use the
simplest structure preserving separation of concerns." Prevents a tiny app inheriting
hexagonal ceremony. Hexagonal does NOT go in the agnostic layer.

### ADR-006 — INVEST as a light readiness gate; Gherkin quality stays · Accepted
Agent works from `.feature` files and is an implementer, not a requirements author, so INVEST
(which judges the requirement, not the Gherkin) is reduced to a one-line `[REVIEW]` escalation
trigger: "if a `.feature` rests on an ambiguous/untestable/oversized requirement, escalate
rather than implement." Gherkin/BDD scenario-quality rules stay in the constitution because
they judge the artifact the agent consumes.

### ADR-007 — Template scope = rules + skeletal workflow for both harnesses · Accepted
The template ships the constitution + `AGENT.md` + `docs/` placeholders PLUS skeletal
workflow/skills for both harnesses (`.pi`/`.claude` prompts, `.devin` skills). Rationale: the
rules↔workflow relationship is the core teaching point; showing only rules omits how they get
enforced. A fully filled-in reference instance (GreaseBook) may be added later for side-by-side
teaching. (Open: see §9.)

### ADR-008 — Spine = gate model + canonical lifecycle; enforce TDD/BDD · Accepted
Keep `[GATE]/[PROCESS]/[REVIEW]` AND a canonical lifecycle in the constitution; each harness
maps its phases to it. Chosen to enforce TDD/BDD-style work and preserve "narration is not
evidence." The spine is the enforcement skeleton; substance sections (C/D/E in §7) are what it
enforces.

### ADR-009 — Canonical lifecycle with `iterate` on the plan artifact · Accepted
See §6. `iterate` (and `enrich`/`adversarial`/`testability`) operate on the plan file in the
refinement loop before `write-tests`, not after `review`.

### ADR-010 — Harness horizon: Claude/PI + Devin now; PI mirrors Claude · Accepted
Design seams for the two current harnesses only; no speculative third-harness abstraction. PI
is a future standalone engine that consumes the SAME `.pi/.claude` artifacts (not its own
tail), so author Claude-side artifacts with that extraction in mind. Keep layering clean enough
that a future harness could drop in as a new tail.

### ADR-011 — Primacy/recency-aware authoring; bookend critical rules · Accepted
The "lost in the middle" attention effect (Liu et al. 2023) is real but weaker for a short
instruction file than for long retrieval contexts — designing for it is cheap insurance, not a
dominant factor. Authoring principle: **bookend critical rules** — a short imperative near the
top + full detail near the bottom; the attention-weak middle holds reference material that is
looked up, not read linearly (precedence lists, trigger tables, principle catalogues).
Consequences: (a) §0 carries a one-line escalation imperative pointing to §12; (b) the document
ENDS on the Completion Gate (reorder tail: §12 escalation → §13 decision principles → §14
completion gate) so recency anchors "not done until the gate passes."

### ADR-012 — "Read fully before judging" = norm + mechanism, split by doc type · Accepted
A bare "read the whole document first" rule is the unenforceable narration the framework
distrusts. Enforce by document type:
- **Auto-loaded constitution** (full text already in context; risk = partial *attention*,
  not partial receipt): §0 reading contract ([PROCESS]) + declared section count + numbered
  sections. **No end-sentinel echo** — decided against: the file is already fully in context,
  a sentinel guards attention not receipt, and its Claude Code enforcement is weak (no model
  turn before the user speaks). (Resolves OQ-6.)
- **On-demand `docs/` files** (pulled via Read; risk = partial offset/limit read): a
  **Read-completeness hook** that rejects a partial read of a governed doc before dependent
  edits ([GATE], real tooling). **Deferred to Claude-tail work** — noted as a tail-level
  [GATE] in the constitution now; the `settings.json` hook is built when we do the Claude
  Code tail (Devin later). (Resolves OQ-7.)
Hooks are harness-specific, so the [GATE] layer lives in the TAILS; the constitution carries
only the norm + count.

### ADR-013 — Document authoring follows a TDD-style spec-first loop · Accepted
Each constitution section is written via a spec-first loop (dogfoods the framework; doubles as
teaching material). Per section:
1. **Spec (RED).** I draft a section spec of *falsifiable* acceptance checks (required content
   points, voice, length cap, tags, must-NOT-includes) → `_WIP/CLAUDE.section-specs.md`. The
   absent/incomplete prose fails it.
2. **Approve spec.** **User holds spec authority** and approves the checks before any prose —
   this is what prevents the agent self-certifying its own writing (spec justifies prose; spec
   is upstream truth).
3. **Prose (GREEN).** I write the section into `_WIP/CLAUDE.draft.md` — minimum prose to satisfy
   the spec, no extra rules. (NOT the repo's live `CLAUDE.md`, which is PurrfectReqs' own and
   must not be touched.)
4. **Verify.** I check prose against each acceptance check, reporting per-check pass/fail — not
   "looks good." Failures fix the prose, never the spec.

Honest framing: this is **spec-first / checklist-driven authoring, TDD-FLAVORED, not TDD** — the
RED is not an executable failing test; verification is `[REVIEW]`, not `[GATE]`. Value: defines
done before doing; blocks prose scope-creep and gaps; traceable. Proportionality: specs stay
lightweight checklists, not essays. Order: §0 first (sets register + tag legend everything
references), then §1→§14 sequentially.

Files: specs → `_WIP/CLAUDE.section-specs.md`; prose → `_WIP/CLAUDE.draft.md`; structure →
`_WIP/CLAUDE.skeleton.md`; decisions → this ADR. Live repo `CLAUDE.md` untouched.

### ADR-014 — Coherence over local terseness; defer trimming to a global pass · Accepted
Drop the hard per-section line cap. A constitution must read as a coherent whole; local trimming
severs connective tissue and produces a disjointed list, and redundancy vs. intentional
bookending (ADR-011) can only be judged against the full draft, not section-by-section. Replace
the cap with:
- **Density, not length.** Every line earns its place; crisp imperative rules; no hedging; no
  redundancy *within* a section. Terseness = density, not brevity. (Preserves the
  "terse/strong-binding" intent without losing information up front.)
- **Length is a flag, not a cap.** Mark a section for the final pass if body > ~60 lines;
  treat > 200 lines as a structural alarm (section doing too much → reconsider scope). Two-tier
  because 200/section alone never fires (sections run ~15–50 lines; whole PurrfectReqs CLAUDE.md
  ≈ 400). Don't trim now — just mark.
- **Global trim + coherence pass** once all 14 sections exist: judge cross-section redundancy
  (bookending vs. accidental repetition), flow, and total size.
- **North-star total** ~450–550 lines for the full constitution (ref PurrfectReqs ≈ 400) — a
  signal, not a gate.
Trade-off: swaps a mechanical check (line count) for a [REVIEW] judgment (coherence); the
60-line flag preserves a mechanical signal. Mirrors the framework's own "defer optimization
until you have global information" (proportionality; working before perfect).

### ADR-015 — Dual-layer sections: lean (binding) + expanded (rationale, strippable) · Accepted
Each section is authored as two blocks: a **LEAN** block (the binding rules that satisfy the
section spec) followed by a delimited **EXPANDED** block (rationale / teaching "why"). Rules:
- **All normative content lives in the lean block only.** Anything tagged
  `[GATE]/[PROCESS]/[REVIEW]` is in the lean block. The expanded block explains; it introduces
  NO new rule — so it can be stripped without losing anything that binds.
- **Delimiters for mechanical strip:** `<!-- EXPANDED:§N ... -->` … `<!-- /EXPANDED:§N -->`,
  rendered as blockquote commentary.
- **Final-review decision deferred:** either strip all expanded blocks to ship the lean
  production constitution, or keep them and let adopters trim per their needs. Not decided now.
Rationale: serves both goals at once (lean = production binding doc; expanded = the
"why"/teaching layer the academic version derives from), and defers the keep/cut call to when
the whole draft is visible. Addresses the density-vs-coherence tension without under-writing.

### ADR-016 — Frontmatter field set; stack stays descriptive; no discipline toggle · Accepted
Realizes ADR-004's instantiation form. **Fields:** `project`, `summary`, a structured `stack:`
map (`backend`/`frontend`/`mobile`/`datastore`/`testing`/free-form `other`, each `none`-able),
`architecture_pattern` (name only, `none` valid), `learning_context` (feeds §3), `harnesses`
(active set; §2 owns tail locations), and a `docs:` map keyed by §1 precedence classes 2–8
(`security`/`specs`/`scope`/`architecture`/`data_models`/`coding_guide`/`glossary`), each a file
or `none`, with `specs` a `.feature` *location* (path, not a single file). Every field a body
section references resolves here (traceability check).
Two forks resolved against the body:
- **No `TECH_STACK.md` precedence class (§1 unchanged).** ADR-004 says "stack authority stays in
  docs/," but a dedicated tech-stack doc is mostly *descriptive*; its genuinely *normative* parts
  already live in ranked classes — approved/forbidden deps in **scope**, idioms/forbidden
  constructs in the **coding guide**, boundaries in **architecture**. So the `stack:` map is
  descriptive orientation only; authority stays distributed across existing §1 classes. Avoids
  adding a precedence rank whose only content is a list of names.
- **No preferred-discipline / methodology toggle.** A `discipline: TDD|BDD|none` field fails on
  two grounds: the template mandates TDD **and** BDD as layers (§4/§6 Gherkin specs, §7 test-first,
  §8 write-tests phase, §14 gate), not a menu; and per §1/ADR-004 the frontmatter is descriptive
  and holds no authority — it structurally cannot toggle a binding rule. A `none` value would be
  an inert claim contradicting five MUST sections.
Frontmatter is GREEN (17/17 checks). Also corrected the §8 review-phase cross-reference, which
pointed at §13 (Decision Principles) instead of §14 (Completion Gate) in both prose and spec.

### ADR-017 — Keep both editions; generate the lean one with a strip target · Accepted
Resolves the keep/cut call ADR-015 deferred. **Keep both editions**, do not choose:
`CLAUDE.draft.md` (lean + expanded, 701 lines) is the source of truth and the teaching artifact;
the production edition is **generated on demand** by stripping the strippable EXPANDED blocks.
`make lean` (in `_WIP/Makefile`, template tooling that travels on extraction — NOT PurrfectReqs'
root Makefile) emits `CLAUDE.lean.md`: strips EXPANDED blocks + WIP scaffolding comments, leaves
the frontmatter as the file head. Output measured at **474 lines — within the ADR-014 ~450–550
north-star**, 15 sections (§0–§14), zero EXPANDED markers.
Rationale: the delimiters already make stripping mechanical, so choosing is unnecessary loss —
keeping both serves both project goals (lean binding doc + teaching "why") with no duplication and
no information discarded. Deleting the expanded layer would only save an already-automated step.
This closes the **whole-draft coherence pass (ADR-014)**: cross-references all resolve (47 checked,
the §8→§14 fix holds), redundancy is all intentional bookending (§0↔§12, §0↔§14, §10 lens, §14
consolidation, §13 disposition), no section exceeds the 60-line flag (§7 largest at 48 lean), and
the lean edition lands in the north-star. No trims required. The constitution is complete.

### ADR-018 — Tail enforcement is ONE tiered tail-contract, not two harness streams · Accepted
Context: T5/T6/T7 (phase-state, feature-box, RED/GREEN attestation) are the load-bearing "unfakeable"
obligations. PI realises them via two out-of-model surfaces in `.pi/extensions/governance.ts`:
`pi.on("tool_call")` returning `{block:true}` (a tool-call veto) + `pi.registerCommand` handlers that
sit *outside* the LLM tool registry (human-only control plane). The question was whether to split the
tails into two streams (Claude/Devin vs PI) because PI's governance is special. **Decision: no split.**
Keep ONE shared **tail-contract** of 11 obligations (T1–T11, see `workstream-a-crosscheck.md` §3),
each declared at the strongest §0 tier the harness can honestly meet (`[GATE]`→`[PROCESS]`→`[REVIEW]`).
**Tiering, not splitting, prevents lowest-common-denominator quality loss** while guaranteeing identical
workflow principles across harnesses. Sharing the *contract* is not the risk; sharing *implementation*
would be — and implementations stay three separate folders (`tails/{claude,pi,devin}`). Supersedes the
"two streams" hypothesis. Full analysis: `workstream-a-tail-streams.md`.

### ADR-019 — Harness affinity is axis-dependent: Claude+PI are siblings, Devin is the outlier · Accepted
The "Claude/Devin vs PI" grouping holds **only on the build/packaging axis** (PI carries the npm
dependency `@earendil-works/pi-coding-agent` + a TS engine; Claude/Devin are markdown + light scripting)
— which is already Workstream B's premise. On the two axes that drive **quality**, Claude pairs with PI:
(1) **enforcement capability** — both have an out-of-model tool-call veto (PI `pi.on("tool_call")`;
Claude `PreToolUse` hook) and a replicable human-only control plane; Devin has neither authored by us;
(2) **workflow-prompt lineage** — the PI prompts are ported Claude commands (stated verbatim in
`iterate.md` Step 3). Therefore: pair **Claude+PI** for shared authoring; **Devin is the outlier** with
honest `[REVIEW]` degradation where it cannot gate. Grouping Claude with Devin would couple the
strongest-enforcement harness to the weakest (the LCD risk, aimed backwards). See
`workstream-a-tail-streams.md` §2.

### ADR-020 — Claude and PI share prompt bodies via a mechanics-injection layer · Accepted
Because the PI prompts ARE the Claude commands (same lineage, ADR-019), the per-phase prompt body
(neutral discipline) lives **once** — in the shared workflow playbook — and each tail's prompt/command
file is a thin wrapper that includes the playbook entry and **injects its own mechanics** (PI: the
`/box`+`/phase` preamble + `run-red/green`; Claude: the hook/state-file wiring per ADR-021). Rejected:
duplicating full copies per tail (drift). This is the three-layer architecture (ADR-001) applied to the
prompt files themselves. Devin does **not** consume these prompts — it consumes the playbook directly.
(Option 1 of `workstream-a-tail-streams.md` §4.)

### ADR-021 — Claude's human-only control plane = hook + state file, NOT a slash command · Accepted
PI's control verbs (`/box`,`/phase`) are human-only by construction because `registerCommand` handlers
sit outside the LLM tool registry. **Claude slash commands do not share this property:** newer Claude
Code exposes a `SlashCommand` tool, so the model can invoke its own slash commands and could promote
its own gates. Therefore Claude's control plane MUST be realised as a **state file mutated only by a
human-run script** (e.g. via the `!` bash prefix) and **read by a `PreToolUse` hook** — or, failing
that, the command MUST be explicitly excluded from the model's `SlashCommand` allowlist. The human-only
guarantee is **engineered, never assumed.** This realises the T5/T6 `[GATE]` tier for Claude (ADR-018)
and extends ADR-012's deferred Read-completeness hook into a fuller Claude governance hook surface.

### ADR-022 — Shared neutral layer = constitution + docs + playbook + tail-contract; only skill-building mechanics diverge · Accepted
Clarifies the divergence boundary (raised 2026-06-26). The harness-neutral layer that is **identical
across all harnesses** (Claude, PI, Devin) is: `CLAUDE.md` (constitution) + `docs/` (project docs) +
`workflow/playbook.md` (per-phase discipline) + `workflow/tail-contract.md` (the T1–T11 obligations).
Every harness consumes these unchanged. Divergence is confined to **how skills/workflow are built** in
each runtime — the tail mechanics. Devin's skill-construction model differs entirely (100%) from
Claude's, yet Devin consumes the same playbook and is checked against the same tail-contract, meeting
each obligation at its honest tier (ADR-018). **"Workflow diverges 100%" applies to the *mechanics*,
never the *discipline*.** Extends ADR-001 (three layers) and ADR-020 (Devin consumes the playbook
directly) by naming the playbook + tail-contract as members of the shared neutral layer, not the
divergent tail. The tail-contract is shared as a single document; only its per-harness *tier column*
differs.

### ADR-023 — GreaseBook validation deferred to post-toolkit; corrections handled as defects · Accepted
**Supersedes** the "generalize via GreaseBook / second-project gate is a pre-completion blocker" stance
(previously in the build plan's validation gates and the RESUME "settled decisions"). **All** GreaseBook
validation — both the PI/config-seam `APP_AGNOSTIC_EXTRACTION_DECISION` "second project" check and the
Devin-Android tail validation — happens **after** the toolkit is complete. The user then adopts the
toolkit on GreaseBook in real use; anything needing change or correction is treated as a **defect**
against the shipped toolkit, not a blocker to completion. Consequences:
1. "Toolkit complete" no longer requires a second-project pass — only the PurrfectReqs-provable gates
   (PI proven on PurrfectReqs; Claude dogfoodable here).
2. The Workstream B config seam (`harness.config.json`) is generalized **by design** from the two known
   references (PurrfectReqs + the PI cross-check) and validated by real use later — the
   highest-rework-risk unvalidated piece, accepted knowingly.
3. OQ-1/2 (GreaseBook stack) and OQ-8 (Devin enforcement model) no longer block toolkit completion;
   both resolve during post-toolkit real use.
This **relaxes** the prior "do not generalize in the abstract" principle to "generalize from known
instances, validate by adoption." Deliberate PO call; the rework risk is owned.

---

## 9. Open questions

- **OQ-1** GreaseBook web/frontend stack — undecided (Android client complicates it). Likely
  two clients: web UI + Devin-built Android app. **No longer blocks toolkit completion (ADR-023)** —
  resolved during post-toolkit GreaseBook adoption.
- **OQ-2** GreaseBook backend — "probably Python," not finalized. **No longer blocks toolkit
  completion (ADR-023).**
- **OQ-3** Where the template physically lives long-term (own repo vs folder) once extracted
  from `purrfectreqs/_WIP/`.
- **OQ-4** PI extraction timeline — affects how much Claude-side workflow is formalized now.
- **OQ-5** Does the template ship a filled-in GreaseBook reference instance (ADR-007 follow-up)?
- ~~**OQ-6** End-sentinel echo ceremony~~ — RESOLVED (ADR-012): skipped; norm + count only.
- ~~**OQ-7** Docs Read-completeness hook timing~~ — RESOLVED (ADR-012): deferred to Claude-tail work.
- **OQ-8** Devin enforcement model unknown — blocks any Devin `[GATE]`, but **does not block toolkit
  completion (ADR-023)**. The Devin tail ships with T5/T6/T7 at `[REVIEW]`; the enforcement story is
  learned during post-toolkit GreaseBook-Android adoption and any tier upgrade is a defect-driven
  correction. This is the principal cross-harness quality exposure; it is labelled, not hidden
  (ADR-018 tiering, ADR-019 outlier).

---

## 10. Next steps

1. ~~Draft the `CLAUDE.md` constitution skeleton~~ — DONE (`_WIP/CLAUDE.skeleton.md`, reviewed).
2. ~~Write constitution prose §0–§14 via the ADR-013 spec-first loop~~ — DONE. All 14 body
   sections individually GREEN (specs in `_WIP/CLAUDE.section-specs.md`; prose in
   `_WIP/CLAUDE.draft.md`). Remaining for the constitution:
   - ~~**2a.** Write the **frontmatter** (identity/pointer block / instantiation form — ADR-004)~~
     — DONE. Written + GREEN (17/17 checks); spec in `CLAUDE.section-specs.md`, prose at the head
     of `CLAUDE.draft.md`. Fields: `project`, `summary`, structured `stack:` map,
     `architecture_pattern`, `learning_context`, `harnesses`, `docs:` map. Two forks resolved: no
     `TECH_STACK.md` precedence class (stack authority stays distributed across scope/guide/
     architecture — §1 unchanged); no preferred-discipline toggle (TDD+BDD is structural; a
     descriptive frontmatter cannot toggle a binding rule). Also fixed the §8→§14 completion-gate
     cross-reference (prose + spec).
   - **2b.** **Whole-draft coherence + trim pass** (ADR-014): verify every `§N` cross-reference
     resolves; judge cross-section redundancy (bookending vs accidental — §10/§14 are intentional);
     check total against the ~450–550 line north-star.
3. ~~Stub `AGENT.md` (Devin tail) after Claude-side work is done~~ — DONE (`_WIP/AGENT.md`).
   Minimal stub: declares itself the Devin tail depending on `CLAUDE.md` (adds no rules), restates
   Devin load semantics + the §2 harness boundary, maps Devin onto the §8 lifecycle, and marks
   every Devin-specific mechanic `<… TBD>` to fill by doing (ADR-007). `[GATE]` Read-completeness
   hook noted deferred (ADR-012).
4. Decide template physical home (OQ-3).
5. Instantiate against GreaseBook to find bad seams. As Devin mechanics are learned, fill the
   `AGENT.md` `<… TBD>`s and log each as an ADR.
