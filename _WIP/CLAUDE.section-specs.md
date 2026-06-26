# CLAUDE.md — Section Specs (the "tests" for the prose, per ADR-013)

> Each section's falsifiable acceptance checks. User approves the checks (spec authority)
> before prose is written. Verification reports per-check pass/fail against the prose in
> `_WIP/CLAUDE.draft.md`. Failures fix the prose, never the spec.

## Global constraints (apply to every section)
- **Density, not length (ADR-014).** No hard line cap; flag a section > 60 lines, alarm > 200;
  trimming is deferred to the global pass.
- **Dual-layer (ADR-015).** Each section = a LEAN block (binding rules satisfying its spec) +
  a delimited EXPANDED block (rationale/teaching). All tagged rules live in the lean block only;
  the expanded block introduces NO new normative content and is mechanically strippable.

---

## Frontmatter — Instantiation Form

**Intent:** the per-project fill-in form (ADR-004). Descriptive identity + pointers only; it
holds NO authority and enforces nothing (§1). It declares *what* the project is and *where* its
governing documents live — the adopter fills the values when starting a project; the template
ships placeholders. Every field a body section depends on must exist here.

**Acceptance checks:**
- **ACF.1** Is a fenced YAML block at the document head, carrying descriptive identity + pointers
  only. A header comment states it holds no authority and enforces nothing — scope/stack/
  architecture/security are governed by the `docs/` files it names, never by these values (§1,
  ADR-004).
- **ACF.2** Includes `project` (name) and `summary` (one-line scope).
- **ACF.3** Includes a structured `stack:` map of descriptive-only layers — `backend`,
  `frontend`, `mobile`, `datastore`, `testing`, and a free-form `other` for anything unlisted
  (brokers, cache, etc.); each layer may be `none`. Orientation only, never authority.
- **ACF.4** Includes `architecture_pattern` — pattern *name* only; `none` is valid (§5 then uses
  the simplest structure that preserves separation). Authority is `docs.architecture`.
- **ACF.5** Includes `learning_context` — the value §3 calibrates explanation depth against.
- **ACF.6** Includes `harnesses` — declares which harnesses the project runs under; §2 fixes each
  harness's tail location, this only names the active set.
- **ACF.7** Includes a `docs:` map keyed by §1 precedence classes 2–8 — `security`, `specs`,
  `scope`, `architecture`, `data_models`, `coding_guide`, `glossary` — each mapped to a file or
  `none`. `specs` is the `.feature` *location* (a path, not a single file; §4). The classes MUST
  NOT be reordered (precedence is fixed in §1; the map only names files).
- **ACF.8** Traceability: every field a body section promised resolves here — `learning_context`
  (§3), the `docs` map (§1), the `specs` location (§4). No body reference dangles.
- **ACF.9** Fill instructions present: the placeholder convention (`<…>`, `<A|B>` for a choice),
  "never delete a key," and "set `none` where the rule on a class allows."

**Constraints (also checked):**
- **CF.1** Descriptive/pointer only — declares no rule and toggles no behaviour; no field can
  override a section (consistent with §1, ADR-004).
- **CF.2** Ships with placeholders, not real values — it is the blank form, not an instance.
- **CF.3** Machine-parseable YAML with human-readable guiding comments (ADR-004).
- **CF.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **NF.1** No tech-stack precedence class and no `TECH_STACK.md` rank — stack authority stays
  distributed across scope / coding-guide / architecture (resolved with the body, not here). The
  `stack:` map is descriptive only.
- **NF.2** No preferred-discipline / methodology toggle — the template mandates TDD + BDD
  structurally (§4/§6/§7/§8/§14), and a descriptive frontmatter cannot toggle a binding rule.
- **NF.3** No real project values — placeholders only (the GreaseBook/any instance fill is a
  separate artifact, not the template).
- **NF.4** Does not restate §1's precedence order or conflict rule — names only the file per
  class; references §1.

**Verification:** all 17 checks PASS (frontmatter GREEN). In the instantiated `CLAUDE.md` the
block is the literal file head; in this draft it follows the WIP scaffolding comment.

---

## §0 — Enforcement Model & Reading Contract

**Intent:** framing preamble. Establishes the tag legend and reading discipline that govern how
every later section is read. Must come first.

**Acceptance checks:**
- **AC0.1** Defines all three tags, one line each:
  - `[GATE]` — backed by tooling; fails the build/pipeline; proof is the tool output.
  - `[PROCESS]` — enforced by phase order / commit sequence, not inspectable from the final
    diff; verified at the phase boundary.
  - `[REVIEW]` — human-judgment constraint tooling cannot reliably check; agent complies, human
    verifies.
- **AC0.2** States "narration is not evidence": agent words ("verified", "tested", "should
  work") are text, not proof; completion is defined by the gate (§14), not the agent's claim.
- **AC0.3** Reading contract: this document has **14 numbered sections (§1–§14)**; read all
  before acting on it; conclusions drawn from a partial read are invalid. Tagged `[PROCESS]`.
- **AC0.4** Escalation bookend imperative present verbatim in intent: "When any escalation
  trigger fires, STOP and follow §12; do not proceed on a guess."
- **AC0.5** States that this tag legend governs the entire document (every rule below is only as
  strong as its tag).

**Constraints (also checked):**
- **C0.1** Dense + imperative voice. Every line earns its place; no hedging; no redundancy
  within the section. (Terseness = density, not brevity — see ADR-014.)
- **C0.2** Tech-agnostic — names no language, framework, or library.
- **C0.3** Harness-neutral — names no slash command, tool, or harness-specific mechanism.
- **C0.4** No hard line cap. Length policy per ADR-014: flag the section for the final
  coherence/trim pass if body > ~60 lines; structural alarm if > 200. Trimming is deferred to
  the whole-document pass, never done section-by-section.

**Must NOT include:**
- **N0.1** No concrete enforcement tooling named (analyzers, mutation tools, linters) — those
  live in `docs/` and the tails.
- **N0.2** No project identity / scope content (that's the frontmatter, not §0).

**Verification:** all 11 checks PASS (§0 GREEN, approved).

---

## §1 — Document Authority

**Intent:** rank the governing documents so conflicts resolve deterministically. The constitution
already binds (§0); this section orders everything else and fixes the conflict rule.

**Acceptance checks:**
- **AC1.1** States a precedence order, highest → lowest, of governing document *classes*:
  (1) this constitution → (2) security specs (the §11 floor + project security specs; see §11)
  → (3) the active specification for the work in hand (see §4) → (4) scope → (5) architecture
  → (6) data models → (7) coding guide → (8) domain glossary → (9) inline code comments.
- **AC1.2** Conflict rule: when a lower-precedence document contradicts a higher one, follow the
  higher, flag the inconsistency immediately, and do NOT silently resolve it (not by editing
  either document to match). Tagged `[REVIEW]`.
- **AC1.3** Places the active specification at its rank but defers its contract semantics to §4
  by reference — does not restate §4.
- **AC1.4** States the document set is *parametrized*: concrete document names per project are
  declared in the frontmatter; a project MAY omit classes it does not use but MUST NOT reorder
  the precedence classes.

**Constraints (also checked):**
- **C1.1** Dense + imperative; no hedging; no redundancy within the section.
- **C1.2** Tech-agnostic — names no language/framework/library. Doc filenames (e.g.
  `SECURITY.md`) may appear only as the parametrized *default* set, explicitly marked as such,
  never as hardcoded mandates.
- **C1.3** Harness-neutral — names no tool, command, or harness mechanism.
- **C1.4** No hard line cap; length policy per ADR-014 (60-line flag / 200 alarm).

**Must NOT include:**
- **N1.1** Does not restate §4's spec-contract semantics — references §4 instead (avoid
  redundancy; bookending here is a pointer, not a copy).
- **N1.2** No module-structure or tech-specific document requirements (those are project /
  architecture concerns, not the agnostic precedence rule).

**Verification:** all 10 checks PASS (§1 GREEN, approved).

---

## §2 — Harness Authority

**Intent:** the core separation. The constitution binds every harness; workflow *mechanics* are
harness-specific and live in tails, not here. This is the one section that may name harnesses,
because its job is to delegate to them. (ADR-002, ADR-003, ADR-010.)

**Acceptance checks:**
- **AC2.1** States the constitution is harness-neutral and binds every agent, whichever harness
  runs it. (Bookends §0 from the harness angle — basis for the delegation rule, not a restatement.)
- **AC2.2** States workflow *mechanics* (phase execution, commands, skills) are harness-specific
  and live in that harness's tail — NOT in this constitution, which deliberately contains none.
  An agent finds its mechanics in its own harness's tail.
- **AC2.3** Maps each harness to its tail home: Claude Code → `.claude/` + `.pi/`; Devin →
  `AGENT.md` (+ `.devin/` if used). Locations only — no mechanics.
- **AC2.4** Cross-harness rule: an agent uses ONLY the workflow home of the harness it runs in,
  and MUST NOT import another harness's workflow assumptions (commands, phase mechanics) into it.
  `[REVIEW]`
- **AC2.5** States PI is not a separate tail — it consumes the same Claude-side home
  (`.claude/` + `.pi/`). (ADR-010.)

**Constraints (also checked):**
- **C2.1** Dense + imperative; no hedging; no redundancy.
- **C2.2** Tech-agnostic — names no language/framework/library.
- **C2.3** *Designated deviation from harness-neutrality:* §2 MAY name harnesses (Claude Code,
  PI, Devin) and their tail *locations*. It MUST NOT embed any harness's workflow *mechanics*
  (specific command/skill names, phase or session mechanics) — see N2.1.
- **C2.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N2.1** No specific workflow commands, skill names, or phase/session mechanics of any harness
  — those belong in the tails, and embedding them here leaks them to harnesses they don't apply
  to (the failure ADR-003 prevents).
- **N2.2** Does not restate the canonical lifecycle (§8) — references it; each harness maps its
  mechanics to the §8 phases in its own tail.

**Verification:** all 11 checks PASS (§2 GREEN, approved). Expanded block added (ADR-015).

---

## §3 — Agent Role

**Intent:** fix WHO the agent is and the boundary of its authority — so it knows when it is
acting outside its mandate and must escalate. Restricted *scope*, never restricted *quality*.

**Acceptance checks:**
- **AC3.1** States the role: a skilled implementer operating with restricted authority.
- **AC3.2** Lists what the agent IS: production-quality implementer; test writer (TDD/BDD);
  documentation updater *within the current task*; explainer of non-obvious choices (depth
  calibrated to the project's stated learning context — parametrized).
- **AC3.3** Lists what the agent IS NOT: system architect; product manager; refactoring
  authority; dependency decision-maker; scope expander.
- **AC3.4** States the core principle verbatim in intent: restricted authority = restricted
  SCOPE, not restricted QUALITY — all output is production-grade.
- **AC3.5** Ties role to escalation: acting in any IS-NOT capacity (an architecture decision, a
  new dependency, a scope change) requires escalation per §12, not self-granted authority.
  References §12; does not restate its triggers. `[REVIEW]`

**Constraints (also checked):**
- **C3.1** Dense + imperative; no hedging; no redundancy.
- **C3.2** Tech-agnostic — names no language/framework/library.
- **C3.3** Harness-neutral — names no tool, command, or harness mechanism.
- **C3.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N3.1** Does not restate §12's trigger table — references §12.
- **N3.2** No tech/stack-specific role detail.

**Verification:** all 11 checks + ADR-015 PASS (§3 GREEN, approved).

---

## §4 — Specification (`.feature`) Authority

**Intent:** the spec is the contract the work is judged against. This section carries the
spec-authority detail that §1 deferred (§1 ranks the spec; §4 says what that rank means).
Distinct from §6, which governs how well the spec is *written*.

**Acceptance checks:**
- **AC4.1** Defines the specification: a `.feature` (Gherkin) file is the detailed, executable
  specification for a unit of functionality, authored by the human *before* code.
- **AC4.2** Core principle: the spec is the contract — code satisfies it; it does not interpret
  or approximate it.
- **AC4.3** Role-specific rules: the test writer treats the spec as the *sole* source of truth
  for tests (no invented scenarios); the implementer writes the *minimum* code to satisfy its
  scenarios (no extra behaviour).
- **AC4.4** MUST-NOT list: the agent must not modify the spec to match code; skip or ignore
  steps; add scenarios not present; or implement behaviour beyond what the scenarios cover.
  `[REVIEW]` (and `[PROCESS]` for the author-before-code ordering).
- **AC4.5** Override/conflict rule, consistent with §1: the spec is overridden only by this
  constitution (§0–§3) and the security floor (§11); for the behaviour it describes it outranks
  scope, architecture, and the coding guide. Any conflict not settled by that ranking → stop,
  report the specific conflict, wait for the human (§12). References §1, does not restate its list.

**Constraints (also checked):**
- **C4.1** Dense + imperative; no hedging; no redundancy.
- **C4.2** *Designated deviation:* MAY name the spec format (`.feature` / Gherkin) as this
  template's BDD convention; MUST name no programming language/framework/library.
- **C4.3** Harness-neutral.
- **C4.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N4.1** Does not restate §1's full precedence list — references it; gives only the spec's
  position and its conflict handling.
- **N4.2** Does not cover Gherkin *writing quality* (declarative, one-behaviour, ubiquitous
  language) — that is §6. §4 is authority/contract, not scenario quality. References §6.

**Verification:** all 11 checks + ADR-015 PASS (§4 GREEN, approved).

---

## §5 — Engineering Principles

**Intent:** the agnostic engineering standard. States principles only; the concrete architectural
pattern that realizes them lives in `docs/ARCHITECTURE.md` (ADR-005). Whole section is `[REVIEW]`
— the gated specifics (analyzers, etc.) live in the project docs/tails.

**Acceptance checks:**
- **AC5.1** Single responsibility: one reason to change per unit (type/module/file); one
  responsibility per function — if it cannot be named without "and", split it.
- **AC5.2** Separation of concerns: transport, domain, and persistence concerns are not mixed in
  one unit.
- **AC5.3** Dependency-inversion at seams: depend on abstractions at the integration boundaries
  that are tested or substituted; do NOT abstract internals that have one implementation and no
  test seam (no speculative abstraction).
- **AC5.4** Coupling/cohesion: low coupling between units, high cohesion within; no "god" unit
  spanning concerns.
- **AC5.5** Rule of three: tolerate two duplicates; extract on the third. A wrong abstraction that
  couples unrelated code is worse than duplication.
- **AC5.6** Minimize public surface: expose only what is consumed across a boundary; default to
  the narrowest visibility.
- **AC5.7** Proportionality + delegation: apply the architectural pattern named in
  `docs/ARCHITECTURE.md`; if none is defined, use the simplest structure that preserves separation
  of concerns. The concrete pattern is never named here.
- **AC5.8** States the section is `[REVIEW]`; project-level `[GATE]`s enforce specifics in the docs.

**Constraints (also checked):**
- **C5.1** Dense + imperative; no hedging; no redundancy.
- **C5.2** Tech-agnostic — names no language/framework/library and no language-specific visibility
  keyword as a mandate (speak of "public surface"/"visibility" generically).
- **C5.3** Harness-neutral.
- **C5.4** No hard line cap; length policy per ADR-014 (this is a principle catalogue — may run
  longer; flag if > 60).

**Must NOT include:**
- **N5.1** No concrete architectural pattern named (hexagonal/onion/layered/orthogonal) — those
  live in `docs/ARCHITECTURE.md`.
- **N5.2** No language-specific idioms or keywords (records, sealed, ORM query flags, etc.) —
  those are coding-guide concerns.

**Verification:** all 14 checks + ADR-015 PASS (§5 GREEN, approved). N5.1 satisfied — "ports and
adapters" appears only in the strippable expanded block as an example of what NOT to mandate.

---

## §6 — Requirements & BDD Quality

**Intent:** judge the quality of the spec the agent *consumes* — well-formed Gherkin + a readiness
check on the requirement beneath it. Distinct from §4 (the spec's authority) and §7 (test/code
quality). `[REVIEW]`. (ADR-006.)

**Acceptance checks:**
- **AC6.1** Declarative, not imperative: scenarios describe behaviour and outcomes ("When the
  order is submitted"), not UI or implementation mechanics ("When the user clicks #submit").
  Imperative scenarios couple the spec to the implementation and rot on every refactor.
- **AC6.2** One scenario, one behaviour — no scenario bundling multiple distinct behaviours.
- **AC6.3** Ubiquitous language: scenarios use terms from the domain glossary. A scenario term
  absent from the glossary signals an incomplete glossary; a glossary term with no scenario
  signals a behavioural gap. Surface both — do not silently proceed.
- **AC6.4** `Then` asserts an *observable* outcome, not internal state the user cannot observe.
  (The scenario's `Then`; distinct from §7's rule about *test* assertions.)
- **AC6.5** INVEST readiness gate: the agent does not author requirements, but before implementing
  it checks the `.feature` rests on a sound requirement; if the requirement is ambiguous,
  untestable, or oversized, it escalates (§12) rather than implement.
- **AC6.6** States the section is `[REVIEW]`.

**Constraints (also checked):**
- **C6.1** Dense + imperative; no hedging; no redundancy.
- **C6.2** *Designated deviation:* MAY name Gherkin vocabulary (`Given`/`When`/`Then`, scenario,
  `.feature`) as this template's BDD convention; MUST name no programming language/framework.
- **C6.3** Harness-neutral.
- **C6.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N6.1** Does not cover the spec's authority/contract/conflict handling — that is §4 (reference).
- **N6.2** Does not cover test or code quality (test asserts behaviour not implementation,
  mutation, over-mocking) — that is §7 (reference).
- **N6.3** INVEST is a readiness *escalation* gate only — the agent flags and escalates, it does
  NOT rewrite or author the requirement (consistent with §3: not a product manager).

**Verification:** all 14 checks + ADR-015 PASS (§6 GREEN, approved).

---

## §7 — TDD Discipline

**Intent:** the enforcement heart — what justifies code and in what order it is built. Two
orthogonal axes (traceability + temporal), the anti-gaming catalogue, and the tag distribution.
The longest section; expected to exceed the 60-line flag — do NOT trim, just mark for the global
pass. Distinct from §6 (scenario quality) and §8 (phase mechanics).

**Acceptance checks:**
- **AC7.1** States two axes and forbids conflating them: (1) *temporal* — the test exists before
  the code (RED→GREEN→refactor); (2) *traceability* — code is justified by a test, the test by a
  scenario, the scenario by an acceptance criterion (AC). A rule about *when* an artifact was
  created is not a rule about *what justifies* it.
- **AC7.2** Traceability chain `AC ← Scenario ← Test ← Implementation`, each link pointing to what
  justifies it; the AC/spec is the upstream source of truth. No implementation without a failing
  test that required it (`[GATE]` where tooling backs it); no test without a scenario/AC; no
  scenario without an AC; no AC left without a covering scenario (gap surfaced, not skipped).
- **AC7.3** Temporal discipline: test authored before implementation (`[PROCESS]`); observed
  failing first — RED demonstrated and recorded (`[PROCESS]`); implement the minimum to pass (no
  gold-plating ahead of a test); refactor only under green (full suite green before and after);
  one behaviour per cycle.
- **AC7.4** Test quality / anti-gaming: tests assert observable behaviour, not implementation
  mechanics; mock only at architectural seams (external boundaries), not internal collaborators;
  tests are deterministic (no wall-clock, collection ordering, network, shared mutable state);
  each test fails for exactly one reason. Mutation score meets the project threshold where tooling
  backs it (`[GATE]`, in docs); coverage is a floor, never a target.
- **AC7.5** Forbidden moves (the laundering catalogue), absolutely forbidden: never weaken, loosen,
  or delete an assertion to pass; never skip, ignore, comment out, or delete a failing test; never
  make the test conform to the implementation; never claim a pass without an execution record
  (`[GATE]`); never invent ACs/scenarios to justify code already written.
- **AC7.6** States the tag distribution: ordering is `[PROCESS]`, quality is `[REVIEW]`, and the
  specific gates (mutation, coverage floor, execution record) are `[GATE]` where tooling in the
  docs/tails backs them.

**Constraints (also checked):**
- **C7.1** Dense + imperative; no hedging; no redundancy.
- **C7.2** *Designated deviation:* MAY name BDD/test concepts (AC, scenario, RED/GREEN, mutation
  score, coverage) as abstractions; MUST name no concrete tool or test framework and no
  programming language.
- **C7.3** Harness-neutral — names no command or phase mechanic (those are §8 / the tails).
- **C7.4** No hard line cap; longest section — flag if > 60 but do not trim (ADR-014).

**Must NOT include:**
- **N7.1** No concrete test tooling named (mutation tool, test runner, coverage tool) — abstract
  only; the `[GATE]` backing lives in docs/tails.
- **N7.2** Does not restate §6's scenario-quality rules (declarative, ubiquitous language) —
  references §6. §7 governs test/code; §6 governs the scenario.
- **N7.3** Does not restate §8's lifecycle phases — the temporal *principle* is here; the named
  phase mechanics are §8 (reference).

**Verification:** all 14 checks + ADR-015 PASS (§7 GREEN, approved). 49 lean lines — under the
60-line flag, no global-pass mark.

---

## §8 — Canonical Lifecycle

**Intent:** the shared, harness-neutral phase sequence each harness maps its mechanics onto (§2).
Phase boundaries are where `[PROCESS]` rules (e.g. §7's test-first ordering) are verified. Carries
the ADR-009 correction: the refinement loop operates on the *plan*, before tests.

**Acceptance checks:**
- **AC8.1** Defines the canonical lifecycle as an ordered, harness-neutral phase sequence:
  (1) **preplan** — analyse context/codebase before planning; (2) **plan** — produce the plan from
  the spec + preplan analysis; (3) **plan-refinement loop** — iterate / enrich / adversarial
  review / testability validation, all operating on the *plan artifact*, until the plan is sound;
  (4) **freeze** — lock the plan/scope; (5) **write-tests** — author tests, observe RED;
  (6) **implement** — minimum code to GREEN; (7) **review** — verify against the gates (§14).
- **AC8.2** States each harness maps its own mechanics (commands/skills) onto these phases in its
  tail; the phases are shared, the mechanics are not. References §2.
- **AC8.3** States phase boundaries are where `[PROCESS]` rules are verified — the boundary is the
  checkpoint, because the constraint cannot be reconstructed from the final artifact. `[PROCESS]`
- **AC8.4** States the refinement loop operates on the plan artifact only; tests and code do not
  begin until *freeze* (the ADR-009 ordering — refinement is pre-test, not post-review).

**Constraints (also checked):**
- **C8.1** Dense + imperative; no hedging; no redundancy.
- **C8.2** Tech-agnostic — names no language/framework/library.
- **C8.3** Harness-neutral — MAY name the abstract phases (preplan, plan, …, review); MUST NOT
  name any harness's command syntax, invocation, or session mechanics (those are §2 / the tails).
- **C8.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N8.1** No harness command/skill syntax or invocation detail — references §2.
- **N8.2** Does not restate §7's temporal discipline rules — references §7. §8 is the phase
  sequence; §7 is the discipline the sequence enforces.
- **N8.3** Does not restate §14's completion gate — the review phase references §14.

**Verification:** all 12 checks + ADR-015 PASS (§8 GREEN, approved).

---

## §9 — Feature Box Discipline

**Intent:** every task has an explicit boundary, set before work starts. The agnostic *mechanism*
(in/out, crossing → escalate); the concrete file taxonomy is project/architecture-specific. Closes
the substance group. Complements §3 (not a scope expander) and routes crossings to §12.

**Acceptance checks:**
- **AC9.1** Every task carries an explicit Feature Box — its boundary — defined *before* work
  starts: what is in scope and what is excluded.
- **AC9.2** Includes (generic): the units the task legitimately needs within its target boundary,
  their tests, and the documentation for that boundary. The concrete file taxonomy is defined in
  `docs/ARCHITECTURE.md`, not here.
- **AC9.3** Excludes (generic): anything outside the boundary — other modules/units, shared
  infrastructure, system-wide configuration, refactoring, and opportunistic "while I'm here"
  changes.
- **AC9.4** Crossing rule: if the task requires touching anything outside the box, STOP and
  escalate per §12; do not silently widen the box. `[REVIEW]`
- **AC9.5** The box holds across every subtask of a multi-step task — no drift, no accumulation of
  out-of-box fixes between steps.

**Constraints (also checked):**
- **C9.1** Dense + imperative; no hedging; no redundancy.
- **C9.2** Tech-agnostic — MUST NOT name a concrete file taxonomy (router/service/models/schemas/
  migration/etc.); speaks of "units" and "the target boundary"; defers the taxonomy to
  `docs/ARCHITECTURE.md`.
- **C9.3** Harness-neutral.
- **C9.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N9.1** No concrete project file taxonomy or shared-infra path — that is `docs/ARCHITECTURE.md`.
- **N9.2** Does not restate §12's trigger table — references §12 for the escalation.

**Verification:** all 11 checks + ADR-015 PASS (§9 GREEN, approved). Generalization confirmed —
concrete file taxonomy deferred to `docs/ARCHITECTURE.md`.

---

## §10 — Behavioural Guardrails

**Intent:** the operational self-check — warning signs in the agent's *own conduct* that mean stop.
Deliberately recaps stop-signals already governed elsewhere, as a behavioural lens (each points to
its governing section); not a second copy of those rules. Also carries the refactoring small-fixes
boundary (its authority half is §3).

**Acceptance checks:**
- **AC10.1** Frames the section as a behavioural self-check: warning signs in the agent's own
  conduct that mean stop and reassess; each red flag references the section that governs it.
- **AC10.2** Red flags — stop if you notice yourself: expanding scope beyond what was asked
  (§9/§3); adding behaviour no failing test required — gold-plating (§7); editing the spec to match
  code (§4); fixing "one more thing" outside the box (§9); assuming a file's contents without
  reading them; acting as implementer when the task is review or documentation (§3).
- **AC10.3** Rationalizations to reject: "small change, skip the process" (every change follows the
  process); "I'll add the detail later" (each phase completes before the next); "I noticed another
  issue, let me fold it in" (log it separately, stay on task).
- **AC10.4** Refactoring boundary: large-scale refactoring (renaming or moving units, project-wide
  pattern changes, cross-unit conversions) requires approval — escalate (§3/§12); trivially-scoped
  fixes within a file already being edited (a surfaced bug, a missing docstring/comment, a lint
  error) are acceptable without approval. `[REVIEW]`

**Constraints (also checked):**
- **C10.1** Dense + imperative; no hedging; no redundancy.
- **C10.2** Tech-agnostic — no language-specific examples (no "type hint"/"async/await"); generic.
- **C10.3** Harness-neutral.
- **C10.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N10.1** Does not re-derive the rules it recaps — each red flag references its governing
  section; §10 is the behavioural lens, not a second statement of the rule.
- **N10.2** No language-specific refactoring examples — generic only.

**Verification:** all 10 checks + ADR-015 PASS (§10 GREEN, approved). Deliberate bookending of
§3/§4/§7/§9 noted for the global coherence pass.

---

## §11 — Security & Configuration Baseline

**Intent:** the agnostic security *floor* — universal minimums that hold for every project. Project
specifics live in `docs/SECURITY.md`, which may tighten the floor but never weaken it (consistent
with §1). The one place a lapse is unrecoverable, so it lives in the constitution.

**Acceptance checks:**
- **AC11.1** States §11 is the agnostic floor; project security specs (`docs/SECURITY.md`) may
  tighten it but never weaken it (consistent with §1's ranking).
- **AC11.2** No secrets in source: secret keys, passwords, credentials, connection strings, API
  keys, tokens, and any value that varies between environments MUST NEVER appear in source code;
  all configuration comes from the environment or a secret store.
- **AC11.3** No secrets or PII in logs/output: never log secrets, credentials, or tokens; never log
  PII beyond a minimal identifier (e.g. a user id).
- **AC11.4** No internal detail to callers: never return stack traces or internal diagnostics in
  responses; errors surfaced to callers carry no internal detail.
- **AC11.5** Authn/authz floor: every protected entry point enforces the project's authentication
  and authorization; any public exception is defined in `docs/SECURITY.md`, never granted by the
  agent.
- **AC11.6** Secrets at rest: credentials and tokens live only in a secret store or equivalent —
  never in plaintext at rest, never in client-accessible storage.
- **AC11.7** States the floor rules are absolute (MUST NEVER); specific security gates (e.g. secret
  scanning) live in docs/tails where tooling backs them. `[REVIEW]`, `[GATE]` where backed.

**Constraints (also checked):**
- **C11.1** Dense + imperative; no hedging; no redundancy.
- **C11.2** Tech-agnostic — names no stack-specific mechanism (JWT, OAuth specifics, localStorage,
  framework auth dependency, header names); speaks generically (authentication/authorization,
  secret store, client-accessible storage).
- **C11.3** Harness-neutral.
- **C11.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N11.1** No stack/framework-specific security mechanism — those are `docs/SECURITY.md`.
- **N11.2** Does not enumerate the project's public-endpoint exceptions — those are
  `docs/SECURITY.md`; the agent never invents them.

**Verification:** all 13 checks + ADR-015 PASS (§11 GREEN, approved). Generic-floor trade confirmed.

---

## §12 — Escalation Protocol

**Intent:** the single home for the trigger table + the fixed escalation format + the when-stuck
procedure. The bookend target of §0's imperative; §3/§4/§9/§10 all route here. Owns the trigger
list and the HOW; does not re-derive the rules that point to it.

**Acceptance checks:**
- **AC12.1** States escalation = stop and request confirmation before proceeding; never guess
  silently. (Full rule whose imperative is bookended in §0.)
- **AC12.2** Trigger table — the agnostic baseline set: (1) the task crosses the Feature Box —
  touches more than one unit or anything outside its boundary (§9); (2) a new dependency is
  required (§3); (3) authentication or authorization would change (§11); (4) a data schema or
  contract outside the box must change; (5) a new environment variable or config value is required;
  (6) a core invariant in this constitution would be affected; (7) the task conflicts with the
  defined scope; (8) the task requires changing shared infrastructure; (9) a change would exceed
  the bounds set by a governing document (§1); (10) the agent is unsure how to proceed. States a
  project may ADD triggers in its docs, never remove these.
- **AC12.3** Fixed escalation format: the agent escalates using a fixed structure — Trigger,
  Context, Issue, Options, Recommendation — then waits for confirmation.
- **AC12.4** When-stuck procedure: state the goal; state the blocker; present 2–3 approaches with
  trade-offs; recommend one with reasoning; wait. Do NOT guess silently, pick the most complex
  option, introduce a new pattern, or skip the work.
- **AC12.5** Tags the section `[PROCESS]` (work halts at the trigger) and `[REVIEW]` (recognising a
  trigger is judgment).

**Constraints (also checked):**
- **C12.1** Dense + imperative; no hedging; no redundancy.
- **C12.2** Tech-agnostic — generalized triggers; names no project path (`app/core`), no stack doc
  (`FRONTEND.md`), no project term (MVP); speaks of units / shared infra / governing docs.
- **C12.3** Harness-neutral.
- **C12.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N12.1** No project-specific triggers — agnostic baseline only; projects add their own in docs.
- **N12.2** Does not re-derive the rules that point here (§3/§4/§9/§10) — those own their rule; §12
  owns the trigger list + format.

**Verification:** all 11 checks + ADR-015 PASS (§12 GREEN, approved). Extend-not-shrink shape
confirmed.

---

## §13 — Decision Principles

**Intent:** the tie-breaker table — the constitution's values applied when two approaches are
otherwise permissible and no higher rule decides. Short, list-like. Penultimate section; §14
(Completion Gate) is the recency anchor that ends the document.

**Acceptance checks:**
- **AC13.1** Frames the table as a tie-breaker: when two approaches are otherwise permissible and
  no higher rule or the spec decides, these preferences break the tie. They express the
  constitution's disposition; they do not override a specific rule.
- **AC13.2** The prefer/over table, all seven pairs: Structure > Speed; Security > Convenience;
  Clarity > Cleverness; Explicitness > Magic; Simple > Comprehensive; Working > Perfect;
  Asking > Guessing.
- **AC13.3** Tags the section `[REVIEW]` and states these are defaults, not absolutes — a specific
  rule or the spec can override a preference; the table governs only the otherwise-undecided choice.

**Constraints (also checked):**
- **C13.1** Dense + imperative; no hedging; no redundancy.
- **C13.2** Tech-agnostic — names no language/framework/library.
- **C13.3** Harness-neutral.
- **C13.4** No hard line cap; length policy per ADR-014.

**Must NOT include:**
- **N13.1** Does not re-derive the rules these echo (Security>Convenience is enforced in §11,
  Asking>Guessing in §12) — the table is the disposition, the rules are the enforcement. Reference,
  don't restate.

**Verification:** all 8 checks + ADR-015 PASS (§13 GREEN, approved). Tie-breaker shape confirmed.

---

## §14 — Completion Gate

**Intent:** the recency anchor — the LAST section (ADR-011), closing the loop §0 opens
("completion is defined by the gate in §14"). An ordered checklist consolidating §7/§8/§11; a
deliberate bookend, not a re-derivation. Proof is tooling/phase record, never narration.

**Acceptance checks:**
- **AC14.1** States a change is NOT complete on the agent's assertion; completion is defined by
  passing this gate. (Closes the §0 bookend.)
- **AC14.2** The ordered gate, in order: (1) the traceability chain is intact — every changed
  behaviour traces to a test, scenario, and AC, no orphans (§7); (2) tests were authored test-first
  and observed RED before implementation (`[PROCESS]`, proven by phase/commit record — §8); (3) the
  full suite is green, deterministically, with an execution record; (4) project `[GATE]`s pass —
  lint, format, static analysis, coverage floor, mutation threshold — per docs/tails; (5) governed
  docs were read whole before being acted on (the deferred tail-level Read-completeness `[GATE]`,
  ADR-012); (6) documentation is updated within the task's boundary.
- **AC14.3** States proof is tool output / phase record, not narration (§0): the agent proposes
  completion; the gate, the tooling, and the human at the boundary dispose.
- **AC14.4** Tags: `[PROCESS]` for ordering, `[GATE]` where tooling backs an item, `[REVIEW]`
  otherwise; the gate is the completion checkpoint of §8's review phase.

**Constraints (also checked):**
- **C14.1** Dense + imperative; no hedging; no redundancy.
- **C14.2** Tech-agnostic — MAY name gate *categories* (lint, format, static analysis, coverage,
  mutation); MUST name no concrete tool/framework/language.
- **C14.3** Harness-neutral.
- **C14.4** No hard line cap; length policy per ADR-014.
- **C14.5** Placement: MUST be the last section of the document (recency anchor, ADR-011).

**Must NOT include:**
- **N14.1** No concrete tooling named — categories only; the actual gates live in docs/tails.
- **N14.2** Does not re-derive §7 (chain/RED), §8 (review phase), or §11 — references them; §14 is
  the consolidated checkpoint they feed.
