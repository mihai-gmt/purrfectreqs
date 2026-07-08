# Workstream A — PI prompts ↔ Constitution §8 cross-check

> **Purpose (toolkit-build-plan §A).** Factor the six proven PI prompts against the §8 canonical
> lifecycle and the §0 tag legend, sorting every element into one of three buckets:
> **(P) neutral discipline → shared playbook**, **(M) harness mechanics → tail**,
> **(C) project specifics → config**. Output of this file feeds the *shared playbook* (one entry per
> phase) and the *tail-contract spec* (what any tail must implement to realise a phase).
>
> Status: **DRAFT analysis** for review. Not the playbook itself — this is the line-finding step
> (the open question in §A: "how much genuinely generalizes vs forces a lowest-common-denominator").
> Source prompts read verbatim from `purrfectreqs/.pi/prompts/` on 2026-06-26; §8/§0 from
> `_WIP/CLAUDE.draft.md`.

---

## 0. Phase ↔ prompt mapping

| §8 phase | PI prompt | Boundary tag (§0) | Output artifact |
|---|---|---|---|
| 1 Preplan | `preplan.md` | `[PROCESS]` | analysis doc |
| 2 Plan | `plan.md` | `[PROCESS]` + `[REVIEW]` (approval gate) | plan doc (DRAFT) |
| 3 Refinement loop | `iterate.md` · adversarial / enrich / testability | `[REVIEW]` (approval per lens) | updated plan + changelog |
| 4 Freeze | `iterate.md` · **freeze** scope | `[PROCESS]` (lock boundary) | plan → FROZEN |
| 5 Write tests | `write-tests.md` | `[GATE]` (`run-red`) | test files + RED proof |
| 6 Implement | `implement.md` | `[GATE]` (`run-green`) | source + GREEN proof |
| 7 Review | `review.md` | `[REVIEW]` + `[GATE]` (lint/tests) | review doc |

**Structural finding 1 — six prompts, seven phases.** `freeze` (§8 phase 4) is not its own prompt;
it is the fourth *scope* of `iterate.md`. So `iterate.md` straddles phases 3 and 4: the three review
lenses are the refinement loop, the freeze scope is the lock. A tail need not mirror this packaging —
the *contract* is "a refinement loop that can run repeatedly + a one-way lock step." Whether they're
one command with a scope arg (PI) or four separate commands (the original Claude `scopes/*.md`, per
`iterate.md` Step 3 note) is **mechanics (M)**.

**Structural finding 2 — the prompts already encode §8's temporal discipline.** Each prompt refuses
to run until the prior phase's artifact exists and is in the right state (analysis before plan; FROZEN
plan before tests; RED before implement; GREEN before review). That refusal *is* the `[PROCESS]`
phase-boundary check of §8 ("a `[PROCESS]` rule is verified at the boundary between phases"). It is
**playbook discipline (P)**; the *means* of refusing (read a Status field / call `/box freeze-check`)
is **mechanics (M)**.

---

## 1. Cross-cutting patterns (every prompt) — the playbook spine

These eight appear in all six prompts. They are the per-phase template the shared playbook codifies.

| # | Pattern (P — discipline) | How PI realises it (M — mechanics) | Project-bound part (C — config) |
|---|---|---|---|
| 1 | **Input contract; stop if unmet.** Each phase has a required input; if absent/wrong-type, halt and ask. | `$ARGUMENTS` parse; "stop and ask for the feature file path." | input is a `.feature` path under `tests/features/<module>/`. |
| 2 | **Bounded read-set; forbid reading outside it.** Read the spec + prior artifact + only the governing docs the lens needs; explicitly *do not* read the rest. | "Read these in order"; per-scope "Do not read…" lists; "do not read `app/` directly." | concrete doc names (`SCOPE.md`, `SECURITY.md`, …); `app/` as code root; the `# Type:` taxonomy that selects which docs. |
| 3 | **Role + prohibitions.** Each phase is one job with hard "you do not…" lines (preplan = documentarian not critic; plan = no code/tests; etc.). | prose role block per prompt. | — (role is fully neutral). |
| 4 | **Named output artifact to disk.** Every phase writes one durable artifact at a derived path. | explicit write path. | path scheme `tests/bdd/plans/<module>_<feature>.{analysis,plan,review}.md`; `PLAN_TEMPLATE.md`. |
| 5 | **Boundary gate before advancing.** A check at the phase edge, tagged per §0. | freeze-check; `run-red`/`run-green`; "tests green before review." | the *content* of each check (section list, compliance checklist) is C; the *existence* of a gate is P. |
| 6 | **Escalation hook.** Any trigger → stop, use the constitution's escalation format, wait. | "use the escalation format from `CLAUDE.md`, stop, and wait." | trigger list lives in the constitution (§12) — already neutral. |
| 7 | **Completion report + typed handoff.** End with a structured status block naming the next phase. | fixed-format text block; "clear context"; literal next `/command`. | next-command names; "clear context" is a harness-context concept (M). |
| 8 | **No-scope-creep / no-self-certification.** Don't invent scenarios; don't expand; narration isn't proof (defer to the gate). | per-prompt Rules lists; manual-attestation disabled in favour of `/box run-*`. | — (pure §0/§7 discipline). |

**Reading of the line:** patterns 1–8 generalise cleanly — they are §8/§0 restated per phase. The
**mechanics column is where harnesses diverge** (PI uses prompt-embedded discipline + `/box`+`/phase`
governance; Claude will use slash commands + a Read-completeness hook; Devin TBD). The **config column
is pure PurrfectReqs** and is exactly what `harness.config.json` must carry (matches the Workstream B
punch-list: `CONFIG`/`PATTERNS`/`PROSE_RULES`).

---

## 2. Per-phase classification

Format per phase: **P** = goes to the shared playbook; **M** = goes to the tail; **C** = goes to config.

### Phase 1 — Preplan (`preplan.md`)
- **P:** documentarian-not-critic role; "describe what exists, suggest nothing"; three research passes
  by intent — **Locate** (where things live), **Analyse** (how current code works), **Pattern-find**
  (what to imitate); write a structured analysis with a single interpretive "synthesis" section;
  do not write plans/code/tests; do not read unrelated files.
- **M:** "Pi has no `Agent` tool → run the three passes sequentially and bounded" (a *capability*
  statement — Claude would fan these out as subagents; Devin differently). `$ARGUMENTS`; the completion
  report block; "clear context then `/plan`".
- **C:** `app/<module>/` layout; `alembic/versions/`; `tests/bdd/…` locations; the `# Type:` values;
  the doc-selection rule (read `DATA_MODELS.md` only if API/Core; `FRONTEND.md` only if UI); the
  analysis-doc path + template headings.

> **Note — the three passes are discipline, not PI mechanics.** Locate→Analyse→Pattern is a neutral
> way to bound context analysis. It belongs in the playbook *as intent*; only "do them sequentially
> because no parallel-agent tool" is the M caveat.

### Phase 2 — Plan (`plan.md`)
- **P:** skeptical/thorough planner; **no code/tests**, **never modify the `.feature`**; validate the
  spec before planning (scope / data-model alignment / security completeness / terminology /
  testability / completeness — *flag gaps, never invent scenarios*); **two human feedback loops** —
  (1) present 2–3 approaches with pros/cons + a recommendation, (2) present detailed structure for
  explicit **APPROVE**; **write the plan only after approval**; plan must carry a complete file
  manifest so downstream phases need no exploration.
- **M:** the two report block formats; `$ARGUMENTS`; "clear context between each next step"; literal
  next `/iterate … adversarial`.
- **C:** the governing-doc set + read order; "do not read `app/` directly — the analysis has the
  facts"; `PLAN_TEMPLATE.md`; the *specific* 15 plan sections; Section 14 manifest shape; Section 15
  changelog; DRAFT status token.

> **Finding 3 — the approval gate is the planning phase's real boundary.** §8 calls phase 2 "produce
> the plan"; the prompt shows the binding event is **developer approval before the artifact is
> written**. That is a `[PROCESS]`/`[REVIEW]` gate the playbook must name explicitly (the constitution
> §8 prose is currently silent on *who approves the plan and when*).

### Phase 3 — Refinement loop (`iterate.md` · adversarial / enrich / testability)
- **P:** one invocation = one lens = one question (no blending); each lens has a *purpose* and a
  *bounded read-set*; propose targeted changes, **never rewrite the plan wholesale**; **never modify
  the plan without explicit approval**; record every applied change in the plan's changelog;
  **discovered-scenario rule** — a scenario the `.feature` lacks is *recommended to the developer and
  parked in a backlog*, never written into the contract or invented in the plan (this is §4 `.feature`
  authority enforced at plan time). The three lenses themselves generalise:
  - **adversarial** = what breaks / where is the plan naive (security, coupling, sequencing, migration,
    missing error conditions, constraint violations);
  - **enrich** = is it detailed enough to execute without guessing;
  - **testability** = can each phase be driven by tests and do we know what they prove.
- **M:** scope-as-argument packaging; the per-scope output block formats; "behaviours embedded here
  because Pi can't expose them as sub-slash-commands" (the original Claude tail used
  `.claude/commands/scopes/*.md` — packaging is M); "clear context, then next scope".
- **C:** which concrete docs each lens reads (e.g. adversarial reads `SECURITY.md`+`ARCHITECTURE.md`;
  enrich reads `DATA_MODELS.md`+`GUIDE.md`; testability reads `conftest.py`); the section-number
  references (Section 3/4/5/8/10/11/14); `Backlog.md`; PurrfectReqs integration boundaries
  (DB/Redis/Ollama) in the testability checklist.

> **Finding 4 — the lens read-sets are deliberately disjoint, and that discipline generalises** even
> though the *file names* don't. The playbook should state "each refinement lens reads only what its
> question needs"; the mapping lens→docs is config.

### Phase 4 — Freeze (`iterate.md` · freeze scope)
- **P:** freeze answers "complete, consistent, ready?"; **block freeze unless all three refinement
  lenses have run** (proven from the changelog); run a completeness check (all required plan sections
  present + specific), an **escalation-trigger scan** (cross-module / core-infra / auth-flow /
  out-of-box schema / new dep / new env var), and consistency checks (every spec scenario in the plan;
  every planned file in the manifest; feasible ordering); **freeze is the one-way lock** — once FROZEN,
  only re-freeze is allowed unless a human manually reopens to DRAFT.
- **M:** reading the Status field / writing `FROZEN`; the changelog row format; the block-message
  formats.
- **C:** the 15-section list; the specific escalation triggers (these mirror constitution §12 — mostly
  neutral, but the *examples* `app/core/*`, "new env var" are project-shaped); DRAFT/FROZEN tokens.

> **Finding 5 — freeze is the linchpin `[PROCESS]` gate.** It is the only step that is *unfalsifiable
> from the final diff* (you cannot tell from shipped code whether the plan was frozen before tests).
> The playbook must mark it `[PROCESS]` and require an artifact-level lock + a "refinement actually
> happened" check. The "block unless adversarial+enrich+testability ran" rule is the mechanism that
> stops the loop being skipped — strong candidate for a neutral playbook rule.

### Phase 5 — Write tests (`write-tests.md`)
- **P:** author tests that **fail because impl is absent**, then **observe RED** (RED is proof, not a
  claim); tests are driven by the spec + frozen plan, **not** by reading implementation; **never write
  impl, never modify `.feature`, never add scenarios**; reuse existing fixtures/steps before adding
  new; a test that passes with no impl is a bad test — fix it before recording RED; require the plan be
  FROZEN before starting.
- **M:** the `/box set`/`plan`/`freeze-check`/`allow-files-from-plan` + `/phase set WRITE_TESTS`
  governance preamble; **`/box run-red`** as the RED attestation (the `[GATE]` realisation that makes
  "narration is not evidence" enforceable); `make test-file` invocation; "don't bypass the governance
  layer"; report/next-step blocks; `$ARGUMENTS`.
- **C:** pytest-bdd specifics (sync `def` steps, `parsers.parse`, `context` dict, `ApiResponse`
  assertions, mock-Ollama / never-mock-DB rule, the `import app` name-collision hazard); test file
  locations; UI vs API/Core test rules (HTMX/`HX-Request`, redirect-to-login); `make test-file`
  target; localhost test-DB rule.

> **Finding 6 — `/box run-red` is the canonical example of a `[GATE]` that defeats self-certification.**
> The playbook states the *rule* ("RED must be observed and recorded by tooling, not asserted"); the
> tail supplies the *mechanism*. This is the cleanest P/M split in the whole set and the model for how
> every gate should be written: discipline in the playbook, enforcement in the tail.

### Phase 6 — Implement (`implement.md`)
- **P:** minimum production-quality code to GREEN; **follow the frozen plan precisely**; **plan-mismatch
  → stop and report** (never silently adapt structure); **define the Feature Box before coding**
  (modules in / files create / files modify / what's untouched / escalation?); implement **phase by
  phase in dependency order**, verifying after each; **never modify tests, never expand scope beyond
  failing tests + frozen plan**; RED must already be confirmed before starting; **allowlist grants the
  file, not licence to change anything in it** — out-of-scope edits to a permitted shared file still
  escalate; observe **GREEN** via tooling.
- **M:** the `/box …`+`/phase set IMPLEMENTING` preamble; **`/box run-green`**; the file-granular
  governance gate ("being in the allowlist grants the file, not the whole file"); `make test-file` /
  `make lint-file` / `alembic upgrade head` invocations; plan-checkbox ticking; report blocks.
- **C:** the layer reminders (migration up/down, audit fields, schema `from_attributes`, service
  `correlation_id`+logging+audit, router `ApiResponse[T]`, UI `HTMLResponse`/HTMX, template
  base/partial rules); the self-verification checklist (cross-model imports, `get_current_user` except
  `POST /auth/login`, passlib argon2, no stack traces…); `make` targets; ruff-only-`.py` caveat.

> **Finding 7 — "Feature Box defined before coding" is §9 discipline; the *enforcement* is the tail's
> file-granular allowlist.** Note the explicit warning that the allowlist is *necessary but not
> sufficient* — it can't catch an out-of-scope edit inside a permitted file, so the human escalation
> rule still binds. The playbook should carry that limit-of-tooling honesty (it's a §0 "[GATE] vs
> [REVIEW]" point: a gate that looks total but isn't).

### Phase 7 — Review (`review.md`)
- **P:** review **after GREEN, before commit**; reviewer **cannot change code** — read, assess,
  explain; **run tests first, block if not green**; deliverable = compliance check (PASS/FAIL/N/A) +
  learning notes; **introduced-vs-pre-existing attribution is mandatory** — a gap in a touched file
  isn't this feature's fault unless the diff created/worsened it; only *introduced* failures gate the
  commit; pre-existing defects are logged to backlog, not fixed here; use the **diff**, not just file
  contents, to attribute; the review writes **only** the review artifact.
- **M:** `/phase set REVIEWING`; `/box run-green` as the GREEN precondition; `make test-file` /
  `make lint-file`; the report block formats; "do not re-run `/implement`; fix manually; source fixes
  need `/phase set IMPLEMENTING`, test fixes `WRITE_TESTS`".
- **C:** the entire A–H compliance checklist content (module structure, FastAPI/Pydantic specifics,
  security items, Alembic, observability, ruff, the HTMX/Starlette-`TemplateResponse` UI items);
  `Backlog.md`; the review-doc path; learning-note audience ("junior Python developer").

> **Finding 8 — introduced-vs-pre-existing attribution is a strong neutral discipline** that the
> constitution doesn't currently state. It belongs in the playbook (and arguably as a one-liner in
> §14 Completion Gate / §10 guardrails): *scope of review = the diff, not the file.* The A–H checklist
> *content* is config; the *practice of a tagged compliance gate with diff-scoped attribution* is
> playbook.

---

## 3. Tail-contract obligations (derived)

What any tail (`tails/{claude,pi,devin}`) MUST provide to realise the playbook. Each maps to the M
column above. PI column = how the existing PI tail satisfies it (the proof these are real, not
speculative).

| # | Obligation | PI realisation | Claude (planned) | Devin |
|---|---|---|---|---|
| T1 | **Invoke each phase as a discrete, named unit** | 6 prompts (`/preplan`…/`/review`) | slash commands / skills | session/skill — TBD |
| T2 | **Pass the spec (feature) path into the phase** | `$ARGUMENTS` | command arg | TBD |
| T3 | **Enforce the bounded read-set** (reject reading outside it) | prompt discipline | Read-completeness `[GATE]` hook (ADR-012) | TBD |
| T4 | **Write the phase's output artifact to the agreed path** | prompt write step | same | same |
| T5 | **Phase-state tracking** (which phase are we in; refuse out-of-order) | `/phase set …` (human-only, not in LLM tool registry) | TBD (hook/state file) | TBD |
| T6 | **Feature-box enforcement** (file-granular allowlist) | `/box set/plan/allow-files-from-plan` | TBD | TBD |
| T7 | **Gate attestation that isn't narration** (RED/GREEN recorded by tooling) | `/box run-red` / `/box run-green` (manual attestation disabled) | hook or wrapped test run | TBD |
| T8 | **Freeze lock** (one-way DRAFT→FROZEN, reopened only by a human) | Status field + freeze scope checks | same artifact convention | same |
| T9 | **Escalation surface** (stop + emit the §12 format + wait) | prompt rule | same | same |
| T10 | **Context isolation between phases** ("clear context" / fresh agent) | "clear context" instruction | `/clear` or sub-agent boundary | new session |
| T11 | **Typed handoff** (report block naming the next phase) | fixed report formats | same | same |

> **Finding 9 — T5/T6/T7 are the load-bearing tail obligations and the hardest cross-harness.** They
> are what make `[PROCESS]` and `[GATE]` real rather than narrated. PI implements them as
> *human-only* governance verbs deliberately kept out of the LLM tool registry (`/box`,`/phase`,
> `run-red/green`) — the unfakeable boundary. The tail-contract spec must require an equivalent for
> each harness; where a harness *can't* provide an unfakeable mechanism, the constitution's tag drops
> from `[GATE]` to `[REVIEW]` for that harness (honest degradation, per §0). This is the single most
> important design constraint for the Claude and Devin tails.

---

## 4. The generalize-vs-LCD line (resolves Workstream A's open question)

The cross-check shows the line is **not** a lowest common denominator. It falls cleanly:

- **Everything in the P column generalises** — it is §8 (phases, ordering, boundaries) and §0 (tags,
  narration-isn't-evidence) restated at one level of detail per phase. No phase lost discipline when
  the project specifics were stripped out. The playbook is therefore *richer* than §8, not poorer: it
  adds the per-phase role, input contract, read-discipline, output artifact, the **plan-approval
  gate** (Finding 3), the **refinement-completeness gate** (Finding 5), **diff-scoped review
  attribution** (Finding 8), and the **allowlist-is-not-sufficient** honesty (Finding 7) — all of
  which are currently implicit or absent in §8.
- **The M column is genuinely harness-specific** and small (≈11 obligations, T1–T11). It does not force
  a common denominator because it is a *contract* ("provide an unfakeable RED gate"), not an
  implementation ("call `/box run-red`"). Harnesses that can't meet a gate degrade its tag honestly
  rather than dragging the others down.
- **The C column is entirely PurrfectReqs** and is the Workstream B config payload — no toolkit-level
  decisions live here.

**Conclusion:** the three-layer split (constitution → playbook → tails) holds under the evidence. The
playbook is writable now from the P column; the tail-contract spec is writable now from §3. Neither
needs GreaseBook first — GreaseBook validates the **C extraction** (Workstream B config seam), not the
P/M split.

---

## 5. Feedback to the constitution (§8/§9/§14) — candidate amendments

The cross-check surfaced four things the proven prompts enforce that the constitution §8 prose does
not yet state. Flag for the user; do not edit the constitution unilaterally (ADR-013 spec authority):

1. **Plan-approval gate** (Finding 3): §8 phase 2 should name that the plan is approved by a human
   before it is written/frozen — currently silent on the approval boundary.
2. **Refinement-completeness gate** (Finding 5): §8 phase 4 (freeze) should require evidence that the
   refinement lenses actually ran, else freeze is skippable.
3. **Diff-scoped review attribution** (Finding 8): §8 phase 7 / §14 should state that review is scoped
   to the diff (introduced vs pre-existing), so review doesn't balloon into fixing the whole file.
4. **"A gate can be necessary but not sufficient"** (Finding 7): §0/§9 honesty note — a file-granular
   allowlist permits the file, not arbitrary edits within it; the human escalation rule still binds.

These are *additions consistent with* the existing spine, not contradictions. Whether they land in the
constitution or stay playbook-only is a user call.

---

## 6. Recommended next step

1. **User reviews this cross-check** — especially §4 (the line holds) and §5 (the four candidate
   constitution amendments: in-constitution vs playbook-only?).
2. Then author the **shared playbook** (`workflow/playbook.md`) — one entry per §8 phase, P column
   only, spec-first per ADR-013 (I draft falsifiable acceptance checks → you approve → I write).
3. In parallel, author the **tail-contract spec** (`workflow/tail-contract.md`) from §3 (T1–T11).
4. These two unblock Workstream C (Claude/Devin tails *derive from* the playbook + contract, not from
   scratch) and give Workstream B the C-column inventory to push into `harness.config.json`.
</content>
</invoke>
