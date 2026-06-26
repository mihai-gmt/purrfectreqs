# Pi Harness — Real-World Testing Observations

**Date:** 2026-06-21
**Context:** First end-to-end dry run of the governed workflow on a real feature
(`tests/features/auth/20260621_basic_register_user_ui.feature` — Register User UI,
2 scenarios). First run after switching the harness model to `gpt-5.5` via
`openai-codex` (was `claude-sonnet-4`). Observations are from the `/preplan` →
`/plan` stage; later stages (`/iterate` → `/review`) not yet exercised at time of
writing.

**Status legend:** `[verified]` = confirmed against code/docs this session.
`[observed]` = seen in the live Pi run. `[inferred]` = reasoned from code but not
executed end-to-end. Each item has a severity and a concrete fix.

---

## A. Prompt / phase design

### A1. `/plan` Step 2 validation gate does not surface higher-authority-doc conflicts — HIGH
`[observed]`

During `/plan`, the agent's visible reasoning correctly identified that
`docs/SECURITY.md` §11 mandates server-side honeypot handling on public forms, and
that this **outranks** the `.feature` file (CLAUDE.md authority: SECURITY rank 2 >
`.feature` rank 3). But that conflict never made it into the output — the agent went
straight to the IMPLEMENTATION APPROACHES block. The honeypot was rendered in the
form but its mandated server-side behavior was not raised as an issue or open
question.

**Root cause:** Step 3's `IMPLEMENTATION APPROACHES` template has no slot for
"validation findings," so conflicts the model reasons about have nowhere to land and
get dropped.

**Fix:** Add a mandatory, structured validation block that must be emitted *before*
approaches, e.g.:

```text
VALIDATION FINDINGS: <feature>
- Higher-authority conflicts (SECURITY/DATA_MODELS/ARCHITECTURE vs .feature): <list or None>
- Behaviors mandated by docs but not covered by any scenario: <list or None>
- Data-model/field mismatches: <list or None>
- Cross-module / Feature Box impact: <list or None>
Blocking? <Yes — stop / No — proceed>
```

Make "a doc ranked above the `.feature` requires behavior no scenario covers" an
explicit blocking condition.

### A2. Step 2's "list issues and stop" is not enforced — MEDIUM
`[observed]`

The `/plan` prompt says: "If issues are found, list them and stop. Do not produce a
plan until the developer resolves them." The agent skipped this gate and produced
approaches directly, folding only the login-page dependency into an Open Questions
line. The gate is currently advisory prose the model can glide past.

**Fix:** Restructure so Step 2 output is a separate required turn. The approaches
block should be reachable only after the validation block reports `Blocking? No` or
the developer clears the findings. (Pairs with A1.)

**Note:** May be partly model-specific — this was the first run on `gpt-5.5`. Worth
checking whether `claude-sonnet` honored the gate more faithfully. Either way the
prompt should not depend on model goodwill.

### A3. No "SECURITY.md extends the feature" prompt for UI features — MEDIUM
`[observed]`

UI features routinely pull in security controls that scenarios don't test (honeypot,
CSP-safe asset wiring, content negotiation, cookie attributes). The `/plan` and
`/preplan` prompts read `docs/FRONTEND.md` "only if the feature type is UI" but give
no instruction to reconcile FRONTEND/SECURITY mandates against the scenario set.

**Fix:** For `Type: UI`, add an explicit checklist item: "List every
SECURITY.md/FRONTEND.md control that applies to this surface but is not exercised by
a scenario, and decide implement-now vs defer for each."

### A4. `enrich` has no channel for a scenario the `.feature` lacks — LOW
`[observed]`

During `/iterate ... enrich`, the agent decided a render scenario (`GET /auth/register`)
was missing and tried to write it **into the `.feature` file**. The engine's `.feature`
hard gate blocked the write (correct — see D3), and `iterate.md` already forbids it four
times (Role, enrich output, Step 4, Rules). The defect is not that the agent was told to
edit the contract — it wasn't. The defect is that `enrich` gives the model **nowhere
sanctioned to put a discovered scenario gap**. Its "Look for" item 4 only checks whether
*existing* `.feature` scenarios are represented in the plan's Section 8 — it says nothing
about what to do when a *new* scenario surfaces. With no defined channel, the model
improvised by editing the contract (also scope creep — CLAUDE.md `.feature` Authority:
"MUST NOT … add scenarios not present").

**Fix (applied 2026-06-21):** Added an explicit instruction to the `enrich` scope: if a
scenario gap is found, recommend it to the developer, ask how to treat it, and propose
recording it in `Backlog.md` (the uncovered-scenarios TODO) — never write it to the
`.feature` and never invent it in the plan. Created `Backlog.md` at the project root with
AI-friendly frontmatter + entry schema. Engine write class added — see B8.

### A5. `freeze` consistency check blocks on no-change files — LOW
`[observed]`

`freeze` (iterate.md line 320) checks "Every file in Section 5 appears in Section 14."
The intent is that every file slated to be **created or modified** must be in the manifest
so the implementer's allowlist is complete. But the model reads it literally: Section 5
listed `app/auth/models.py` and `app/auth/dependencies.py` as **"No changes,"** and the
model blocked freeze because those paths were not enumerated in Section 14 — even though
no-change files correctly do not belong in the create/modify manifest and are already
covered by Section 14's "Files NOT touched: everything not listed above."

This is a false positive, and the exact mirror image of the behavior the gates are
*meant* to stop: the same literalness that prevents the model inventing files here makes
it over-apply a prose check and block a clean plan. The gate is doing its job too
strictly because the wording is ambiguous.

**Fix:** Tighten the check wording so no-change files don't trigger it, e.g.: "Every file
Section 5 marks to *create or modify* appears in Section 14's create/modify tables; files
marked 'No changes' are covered by 'Files NOT touched' and need no manifest row." Until
the prompt is fixed, the workaround is to list the no-change files explicitly under
"Files NOT touched" so the literal check passes. (Observed live on the register-UI plan
freeze: it was the only failed check; all three iteration scopes were present.)

### A6. `/review` over-applies whole-codebase rules to pre-existing code in touched files — HIGH — RESOLVED

`[verified]`

> **RESOLVED 2026-06-21.** Added a mandatory "introduced vs pre-existing" attribution rule to
> `review.md` Step 3 (decide per candidate FAIL using the git diff; only INTRODUCED gaps
> block; PRE-EXISTING gaps are noted, attributed to their origin, and recommended for
> `Backlog.md`, not counted as FAILs or fixed in-feature). Updated the Step 4 summary format
> to split `FAILED (introduced)` from `PRE-EXISTING (logged, not blocking)` and to gate the
> commit only on the introduced count.



The register-UI `/review` returned 5 FAILs; on triage only ~2 were attributable to the
feature. The endpoint `POST /auth/register` was **modified** by the feature (added a browser
branch), so the whole file fell "in scope," and the review flagged two **pre-existing**
gaps as blocking FAILs:
- missing `ApiResponse[T]` envelope on the JSON path (predates the UI feature; from the
  20260407 API feature — see Backlog BL-0003), and
- user CREATE logged but not audit-logged (lives in `register_user`, reused not authored —
  Backlog BL-0004).

Both are real codebase observations, but blocking the *UI* feature on them is wrong: the
plan said "preserve existing JSON behaviour," and fixing either would change the API
contract and/or break the 11 passing API tests. The review has no notion of "introduced by
this change" vs "pre-existing in a touched file," so it scores them identically.

**Fix:** `review.md` should require each finding to be tagged **introduced** (this feature)
vs **pre-existing** (already in a touched file), and only `introduced` findings block;
`pre-existing` ones are reported as "log to backlog / separate defect," not FAILs. The
compliance summary should separate the two counts. (This is item (c) from the live triage.)

### A7. `review.md` UI checklist encodes a deprecated Starlette convention → false positive — MEDIUM — RESOLVED

`[verified]`

> **RESOLVED 2026-06-21.** Rewrote the §H `TemplateResponse` checklist item to the current
> Starlette signature (`request` positional; explicitly "do NOT require `"request": request`
> in the context dict — deprecated pre-0.29 pattern"). Rewrote the `response_class`/
> `response_model` item to distinguish HTML-only routes from **dual-purpose** content-
> negotiating routes (which keep their JSON `response_model` and must not add
> `response_class=HTMLResponse`), so the deliberately-mixed `POST /auth/register` is no longer
> flagged.



`review.md` §H line ~150 lists `"request": request in TemplateResponse context` as a
required checklist item. That is the **pre-Starlette-0.29** pattern. The project runs
**Starlette 1.0 / FastAPI 0.135**, where the signature is `TemplateResponse(request, name,
context)` — `request` is passed positionally and must **not** be in the context dict. The
implementation correctly used the modern form, the 3 UI tests passed, yet the review raised
FAIL #5 ("contexts do not include 'request': request") purely because its own checklist is
outdated. A checklist item that contradicts the installed framework manufactures false
positives every UI review.

Related: §H line ~141 (`response_class=HTMLResponse`, no API `response_model` on UI routes)
does not account for **dual-purpose** routes (one endpoint serving both JSON API and browser
HTML via content negotiation), so it flags the deliberately-mixed `POST /auth/register` as
non-compliant (FAIL #4) without a way to express "mixed by design."

**Fix:** update the §H checklist to the current Starlette signature (request positional, not
in context); add a dual-purpose-route note so content-negotiating endpoints are evaluated as
intended rather than as pure-UI routes.

### A8. No review-remediation path within the phase model — MEDIUM — MITIGATED

`[verified]`

> **MITIGATED 2026-06-21 (Option a — documented loop).** `review.md`'s "if introduced
> failures exist" guidance now spells out the supported remediation loop: source fixes via
> `/phase set IMPLEMENTING`, test fixes via `/phase set WRITE_TESTS`, then back to
> `/phase set REVIEWING` to re-run; pre-existing defects go to `Backlog.md`, not fixed here.
> Option (b) (a dedicated remediation mode that re-opens the frozen allowlist for the named
> files) remains a possible future enhancement but is not implemented — the documented loop
> is sufficient for now.



After `/review` writes findings, the developer is told to "fix the specific issues
manually." But in `REVIEWING` the phase gate permits only `review` (and now `status`)
writes — the Pi agent cannot edit `source` to apply a fix. Worse, finding #1 spanned a
`source` file (`router.py`) **and** test step-defs: `source` is writable only in
`IMPLEMENTING`, test files only in `WRITE_TESTS`, so a single review's fixes cannot be
applied by the agent in any one phase. There is no first-class "remediation" loop:
review → fix → re-review.

**Fix (options):** (a) document the supported loop — `/phase set IMPLEMENTING` to fix
source, `/phase set WRITE_TESTS` to adjust tests, then back to `REVIEWING` and re-run; or
(b) add a remediation phase/mode that re-opens the frozen allowlist for the specific files a
review named, scoped to the review's findings. (a) is zero-code and probably sufficient;
(b) is more guided but more machinery.

---

## B. Governance engine / `config.ts`

> **B1–B4 RESOLVED 2026-06-21.** Implemented a new `frontend` path class for
> `app/templates/**` and `app/static/**`, made `moduleOf` layout-aware, wired
> `frontend` into the manifest set / IMPLEMENTING gate / `allow-file` validator, and
> added `docs/FRONTEND.md` to `authorityDocs`. Changes in `.pi/governance/engine.ts`
> + `config.ts`; covered by `engine.test.ts` (17 tests green). Design decisions
> taken: new class (not folded into `source`); shared frontend assets (`app/static`,
> `app/templates/base.html`, `_`-prefixed dirs) resolve to `null` module = app-shared,
> ungated by the Feature Box.

### B1. `app/templates/**` classifies as `unknown` — HIGH — RESOLVED
`[verified]`

`classifyPath` returns `source` only for paths under `appRoot` that end in `.py`.
Template files (`app/templates/auth/register.html`) end in `.html`, so they fall
through every branch to `unknown`. The engine has no concept of a template or static
asset. This means UI work is invisible to the path-class-based phase gates.

**Fix:** Add classes (or extend existing ones) for `app/templates/**` and
`app/static/**`, and decide which phase may write them (presumably `IMPLEMENTING`).

### B2. `moduleOf` mis-resolves template paths — HIGH — RESOLVED
`[verified]`

`moduleOf` is `^app/([^/]+)/`, so `app/templates/auth/register.html` resolves to
module **`templates`**, not `auth`. With `/box set auth`, the cross-module gate
(`featureBoxRules`) sees `templates ∉ [auth]` and would block a legitimate template
write for the auth feature.

**Fix:** Teach `moduleOf` that `app/templates/<module>/` and `app/static/...` belong
to `<module>` (or are app-shared), so Feature Box scope maps correctly onto UI files.

### B3. `parseAllowedFilesFromPlan` drops non-`.py` files — HIGH — RESOLVED
`[verified]`

The Section 14 manifest parser imports only `.py` files into the implementation
allowlist (the engine test confirms it skips `.feature` and `docs/*.md`; `.html`/
`.css` are in the same bucket). So `/box allow-files-from-plan` will silently omit
templates and stylesheets, and `/implement` will block the first template write even
when the plan lists it. Every UI asset would need a manual `/box allow-file`.

**Fix:** Extend the parser to accept frontend file types (`.html`, `.css`, `.js`
under `app/static/js/`) from Section 14's implementation subsection. Until then,
document the manual `allow-file` step for UI features.

### B4. `docs/FRONTEND.md` missing from `authorityDocs` — LOW — RESOLVED
`[verified]`

`authorityDocs` lists CLAUDE/WORKFLOW/SECURITY/DATA_MODELS/ARCHITECTURE/SCOPE/
TECH_STACK but **not** `docs/FRONTEND.md`, despite it being rank 8 in CLAUDE.md's
authority order. Edits to FRONTEND.md therefore skip the "authority document, confirm
intent" soft confirm that the other docs get.

**Fix:** Add `docs/FRONTEND.md` to `authorityDocs`.

### B5. No deterministic enforcement of FRONTEND.md escalation triggers — INFO (by design, document it)
`[verified]`

The FRONTEND.md escalation triggers (vendored-asset bump, custom JS/CSS beyond
sanctioned uses, app-shell/nav changes, CSP/header changes) are **prose only** — the
engine has no gate for them and `PROSE_RULES` doesn't mention them. Whether the agent
escalates is pure model judgment. This is consistent with the harness's "encode
structure, leave judgment as prose" principle, but it should be stated plainly so it
isn't mistaken for an enforced control. (I made exactly this error earlier in the
session and had to retract it.)

**Fix:** Add a line to `PROSE_RULES` naming the FRONTEND.md triggers as
escalation-required judgment calls, so at least the system prompt carries them.

### B6. Status line has no analysis indicator — `Plan: MISSING` reads as failure during preplan — MEDIUM
`[observed]`

The footer status line (`formatGovernanceStatusLine`, `engine.ts:558`) shows
`Gov <phase> | Plan: <status> | RED | GREEN | Box`. The `Plan:` field
(`readPlanStatus`, `engine.ts:131`) is `MISSING` until a plan file is registered via
`/box plan` **and** that file has a `Status: DRAFT|FROZEN` line — neither of which
happens during `/preplan` or `/plan` (registration is a Stage 2 step). So through the
entire planning stage the status correctly but unhelpfully reads `Plan: MISSING`,
with no positive signal that `/preplan` produced its `.analysis.md`. A user reasonably
reads `MISSING` as "something failed." (Observed live: prompted a defect report that
turned out to be expected behavior.)

The value is accurate; the gap is missing feedback. **Fix options:** (a) add an
`Analysis: present/missing` segment driven by the existence of
`<plan-dir>/<module>_<feature>.analysis.md`; or (b) render `Plan: n/a (preplan)`
while phase is `PREPLAN`/`PLANNING` so the field doesn't imply failure before a plan
is expected to exist.

### B7. `/phase set` silently no-ops on an invalid phase value — LOW
`[verified]`

`handlePhaseSet` (`engine.ts:608`) rejects any value not in `VALID_PHASES` by
returning a usage string and **not** changing the phase. The phase is left unchanged
(typically `IDLE`). The rejection is correct, but the feedback is easy to miss — a
typo like `/phase set PREPLANNING` (valid value is `PREPLAN`) leaves the user
believing the phase advanced when it did not. (Observed live: exactly this typo.)

**Fix:** Make the rejection explicit, e.g. `Phase NOT changed — '<value>' is not a
valid phase. Current phase: <phase>. Valid: <list>.` so the no-op is unmistakable.

---

### B8. No write class for `Backlog.md` — MEDIUM — RESOLVED
`[verified]`

> **RESOLVED 2026-06-21.** Added `backlogFile: "Backlog.md"` to `config.ts`; added a
> `backlog` path class to `classifyPath`; allowed `backlog` writes in `PREPLAN`,
> `PLANNING`, and `ITERATING` only. Excluded from `ALLOWED_MANIFEST_CLASSES`. Covered by
> `engine.test.ts` (18 tests green). RED→GREEN verified via `node --test`.


A4's fix routes discovered scenarios to `Backlog.md`, but the engine had no write class
for it: a project-root `.md` classifies as `unknown` (`classifyPath`), so every planning
phase's gate (`PREPLAN`/`PLANNING`/`ITERATING` each allow only their one class) would
block the agent from appending an entry. The agent could only propose; a human had to
write the file.

**Fix:** Add a dedicated `backlog` path class for `governanceConfig.backlogFile`
(`Backlog.md`) and allow it to be written in the three planning phases (`PREPLAN`,
`PLANNING`, `ITERATING`) — the phases where scenario gaps surface. It stays blocked in
`WRITE_TESTS`/`IMPLEMENTING`/`REVIEWING`, and is intentionally **excluded** from
`ALLOWED_MANIFEST_CLASSES` so it can never be imported as a writable test/implementation
file via the plan manifest. `moduleOf` already returns `null` for it (not under `app/`),
so no cross-module gate applies, and it is not an authority doc, so no soft-confirm fires.

### B9. `parseAllowedFilesFromPlan` does not match the canonical `PLAN_TEMPLATE.md` — HIGH — RESOLVED
`[verified]`

> **RESOLVED 2026-06-21.** Parser now recognises the template's `Files to CREATE`/`Files
> to MODIFY` tables (new `byclass` section kind, routed by `classifyPath`); old header
> format retained; added a fixture mirroring the real `PLAN_TEMPLATE.md`. `engine.test.ts`
> 19 tests green; RED→GREEN verified via `node --test`.


`/box allow-files-from-plan` imported **zero** files from a plan that correctly followed
`PLAN_TEMPLATE.md`, reporting "Section 14 found, but no recognized test or implementation
write subsection was found."

**Root cause:** the template's Section 14 organises files as `Files to READ before writing
tests` / `Files to READ before implementing` / `Files to CREATE` / `Files to MODIFY`
(markdown tables, with the test-vs-impl signal in an **Agent** column). But
`manifestSectionKind` only recognises headers literally containing "test files …
create/modify" or "implementation files … create/modify" (bullet-list format). It returns
`null` for `Files to CREATE`/`Files to MODIFY`, so the parser sees no write subsection and
imports nothing.

**Why B1–B4 didn't catch it:** the engine-test fixtures (`SECTION_14`, `SECTION_14_UI`)
were written in the parser's bullet format, not the template's table format, so the tests
were green against a format the real template never produces. False confidence.

**Fix (applied 2026-06-21):** taught the parser the template format — `Files to
CREATE`/`Files to MODIFY` are recognised as write sections and each row is routed **by
`classifyPath`** (`test` class → test allowlist; any other writable class → implementation
allowlist; non-writable classes such as `doc` skipped). The Agent column stays as human
documentation; file class is the authoritative signal. The old header-based recognition is
retained for backward compatibility, and a new fixture mirroring the actual
`PLAN_TEMPLATE.md` was added so the tests track the template. Covered by `engine.test.ts`.

**Note:** `docs/PROJECT_STATUS.md` (listed under `Files to MODIFY` for the implement
agent) classifies as `doc` and is intentionally NOT imported — it is also blocked by the
IMPLEMENTING phase gate, so this is consistent, not a regression.

### B10. Per-feature control-plane audit log (JSONL) — ENHANCEMENT — RESOLVED
`[verified]`

> **RESOLVED 2026-06-21.** Implemented `.pi/governance/audit.ts` + wiring in
> `runBoxCommand`/`runPhaseCommand`. Covered by `audit.test.ts` (8 tests: pure helpers +
> temp-dir integration) and a live end-to-end smoke test through `createGovernanceEngine`
> (header + events, pure reads skipped, blocked/ok outcomes, attempt counter, phase
> movement all verified). Full governance suite green (27 tests).


`feature-box.json` holds only current state (one `redCommand`, current phase); it cannot
show the *trajectory* of a feature's workflow — failed freeze attempts, RED/GREEN re-runs,
phase back-steps. Added an append-only, per-feature audit log so the control plane records
its own actions deterministically (the engine writes it, not the model).

**Design (agreed with developer 2026-06-21):**
- One file per feature: `.pi/audit/<module>_<feature>.audit.jsonl` (keyed off the plan
  basename), in its own folder, surviving `/box clear`.
- JSONL, one record per line. Three record types: `header` (once, schema + identity +
  initial artefact snapshot), `event` (one per state-changing `/box` or `/phase` command;
  pure reads like `/box status` are not logged), `artifact_registered` (one per workflow
  file that appears after the header — dated).
- **Normalized** artefacts: full registry on the header, then `artifact_registered` deltas;
  every line still carries compact `meta` (feature, module).
- Event fields make retracing first-class: `seq` (monotonic), `attempt` (Nth run of this
  op), `outcome` (`ok|failed|blocked|noop`), `phase_from`/`phase_to` (captures back-steps),
  `plan_status` at command time, `detail` (handler's one-liner).
- New `.pi/governance/audit.ts`; pure helpers unit-tested; `recordControlCommand` wired
  into `runBoxCommand`/`runPhaseCommand` (wrapped in try/catch so logging never blocks a
  command). Logging is skipped until a `planFile` exists (can't attribute to a feature
  before then — early `/box set`/`/phase set PREPLAN` are not captured; acceptable).

### B11. `/box run-red` / `run-green` execute bare `pytest` via PATH (no venv) — HIGH — RESOLVED

`[verified]`

> **RESOLVED 2026-06-21.** Added a pure `resolveTestExecutable(executable, cwd)` helper
> that rewrites `pytest`→`.venv/bin/pytest` and `python`→`.venv/bin/python` when the venv
> binary exists (bare name otherwise; non-interpreters never touched), and wired it into
> `runPytest` before the `spawnSync`. `parsePytestCommand` is unchanged (contract/tests
> intact). Covered by a new `engine.test.ts` case using a fake `.venv` layout in a temp
> dir; full governance suite green (34 tests). `/box run-red`/`run-green` now hit the venv
> interpreter regardless of activation, matching the Makefile.

The authoritative RED/GREEN gates run the test command through `runPytest`
(`engine.ts`), which does `spawnSync(parsed.executable, parsed.args, { shell: false })`.
`parsePytestCommand` only accepts `pytest …` or `python -m pytest …` and returns the
**bare** executable (`"pytest"` / `"python"`). With `shell: false`, `spawnSync` resolves
that name against the `PATH` of the process that launched Pi. So if the developer did not
`source .venv/bin/activate` *before* starting Pi, `/box run-red` fails to find `pytest`
(or worse, finds a system interpreter without the project's deps). This is the same
PATH/activation dependency C6 removed from the Makefile path — but on the gate that
actually decides RED/GREEN, so it matters more.

Discovered while wiring C6: the `make test-file` change fixes the *exploratory* run in
`write-tests.md` Step 5, but the engine's gate bypasses the Makefile entirely. The
`/box run-red` examples in the prompt must stay as `pytest …` (the parser rejects
`make …`), so the fix belongs in the engine, not the prompt.

**Fix:** in `runPytest`, resolve the parsed executable to the venv binary when it exists,
falling back to PATH otherwise — `pytest` → `.venv/bin/pytest`, `python` →
`.venv/bin/python`. `parsePytestCommand` stays pure (its exported contract and tests are
unchanged); only the spawn target is rewritten. Same philosophy as the Makefile: name the
venv interpreter explicitly, fall back if `.venv` is absent.

### B12. Allowlist is file-granular — cannot stop in-file scope drift — MEDIUM — MITIGATED

`[observed]`

> **MITIGATED 2026-06-21 (no structural fix — judgment boundary).** Added an `implement.md`
> Rules entry: for shared/app-shell files (`base.html`, `app/static/**`) change only what
> Section 14's "What changes" column authorizes; being in the allowlist grants the file,
> not the whole file; any CSP/`<meta>`/header/nav/app-shell change beyond the plan MUST be
> escalated even when the file is allowed. This is mitigation (a)+(b) from the options
> below; region-level gating remains impractical, so this stays a documented judgment
> boundary, not a structural guarantee.



Observed live during `/implement` of the register-UI feature: the model reasoned about
editing the **CSP `<meta>`** in `app/templates/base.html`. The plan's Section 14 grants
`base.html` for exactly one change — "load `app.css` after PicoCSS; no shell/navigation"
— and a CSP change is a SECURITY.md/FRONTEND.md escalation trigger. But the engine's
allowlist (`allowedImplementationFiles`) is **file-granular, not region-granular**: once a
file is in the allowlist, the IMPLEMENTING gate accepts *any* edit to it. So a CSP-meta
edit inside an otherwise-sanctioned `base.html` write would pass the structural gate even
though it exceeds what the plan authorized for that file. The model didn't (yet) make the
edit — this is about the gate's reach, not a confirmed bad write.

Contrast with `app/core/*`, where the gate *does* catch drift because the whole class is
out of scope. The weak spot is specifically a partially-authorized file: the manifest's
per-file "What changes" column is prose the engine never reads.

**Fix:** no clean structural fix — region-level gating is impractical. Mitigations:
(a) keep the manifest's "What changes" description as the human review anchor and call
out CSP/security-relevant shared files (`base.html`) for manual eyeballing; (b) consider a
prompt rule that any change to a shared/app-shell file (`base.html`, `app/static/**`)
touching CSP/headers/nav must be escalated even when the file is in the allowlist;
(c) optionally, a soft-confirm (not a hard block) when an allowed write modifies a
security-sensitive region (CSP meta) — diff-based, best-effort. Lowest-cost path is (a)+(b):
treat this as a known judgment boundary, documented, not a structural guarantee.

### B13. IMPLEMENTING doc-gate blocks the `docs/PROJECT_STATUS.md` update the plan + CLAUDE.md require — MEDIUM — RESOLVED

`[verified]`

> **RESOLVED 2026-06-21 (Option 1).** Added a dedicated `status` path class for
> `docs/PROJECT_STATUS.md` (`config.ts` `statusDoc`; `classifyPath` checks it before the
> generic `doc` rule). It is writable in IMPLEMENTING and REVIEWING **without** an
> allowlist entry (phase-gated, not manifest-gated — same pattern as `backlog`), and is
> excluded from `ALLOWED_MANIFEST_CLASSES`, so it is never imported as a writable manifest
> file and `/box allow-file` still rejects it. Authority docs and non-allowlisted source
> files stay blocked. RED→GREEN verified (reverted the `classifyPath` line → 2 tests fail
> → restored → 35 green); covered by a `classifyPath` case + a temp-dir integration test
> driving `handleToolCall`. No edit to `PLAN_TEMPLATE.md`/CLAUDE.md needed — Option 1 keeps
> their existing text correct.



Observed live at the end of the register-UI `/implement` run: the agent tried to update
`docs/PROJECT_STATUS.md` (mark the feature 🟢) and the engine blocked it — *"In
IMPLEMENTING, source, frontend (template/static), migration, or plan checkbox updates may
be written. 'docs/PROJECT_STATUS.md' is doc."* The agent surfaced the block correctly
rather than forcing it.

But the write is **mandated by two higher-authority sources**:
- the plan's Section 14 lists `docs/PROJECT_STATUS.md` under *Files to MODIFY* for the
  implement agent (it comes from `PLAN_TEMPLATE.md`); and
- CLAUDE.md's Mandatory Pre-Task self-verify checklist: "`docs/PROJECT_STATUS.md` updated
  if a feature was completed."

So the plan template and the constitution both instruct an update the IMPLEMENTING phase
gate forbids — the same plan-vs-engine mismatch class as B9 (parser) and B8 (backlog write
class). The gate is doing its job (no arbitrary doc edits mid-implement), but there is no
sanctioned path for the one doc the workflow explicitly expects to change on completion.

**Why the generic `doc` class is too blunt:** blocking doc writes in IMPLEMENTING is
correct for authority docs (SECURITY/ARCHITECTURE/etc.) — those must not drift during
implementation. `PROJECT_STATUS.md` is not an authority doc; it is a workflow ledger whose
whole purpose is to be updated when a feature completes. It is miscategorised by sharing the
`doc` class.

**Fix options:**
1. **Dedicated `status` path class** for `docs/PROJECT_STATUS.md` (config entry, e.g.
   `statusDoc`), writable in IMPLEMENTING and REVIEWING only, excluded from
   `ALLOWED_MANIFEST_CLASSES` so it is never imported as a writable manifest file — mirrors
   the B8 backlog approach. **Recommended.**
2. Make the status update a **human control-plane action** (a `/box` subcommand, or
   hand-edited), and drop it from the implement agent's Section 14 to remove the false
   expectation.
3. Allow `doc` writes (or just `PROJECT_STATUS.md`) in **REVIEWING** only, and move the
   "mark complete" step to the review phase.

Whichever path is chosen, `PLAN_TEMPLATE.md` Section 14 and CLAUDE.md's checklist must
agree with the engine — right now they contradict it. (Option 1 keeps the template/CLAUDE
text as-is; options 2–3 require editing them too.)

---

## C. Tooling / config

### C1. No per-step model selection — INFO
`[verified]`

Pi's prompt-template parser reads only `description` and `argument-hint` from
frontmatter; there is no `model` key on `PromptTemplate`. Model is session-wide
(`.pi/settings.json` → `defaultModel`, or the `--model` launch flag). If the workflow
ever wants different models per phase (e.g. a cheaper model for read-only `/review`),
there is no in-prompt mechanism — it would require switching the setting / relaunch
between steps.

**Fix:** Document the limitation in the README. If per-phase models become desirable,
consider a launcher wrapper that sets `--model` per command.

### C2. `/model` referenced in MODEL_POLICY.md but not verified to exist — LOW
`[inferred]`

`MODEL_POLICY.md`'s validation checklist step 1 says "`/model` shows the local
model." Confirmed built-ins this session: `/compact`, `/new`, `/quit`. `/model` was
not confirmed to exist.

**Fix:** Verify whether `/model` is a real command; if not, correct the checklist.

### C3. "Clear context between steps" means `/new`, not `/clear` — INFO
`[verified]`

There is no `/clear`. The workflow report tells users to "clear context between
each" step; the actual lever is `/new` (fresh session, zero context) or `/compact`.
Because governance state is file-backed in `.pi/feature-box.json`, a `/new` between
steps should preserve phase/box gates — but this should be stated explicitly so users
trust it, and confirmed in testing.

**Fix:** README: replace "clear context" with "`/new` between steps; governance state
persists in `.pi/feature-box.json` across sessions." Verify the persistence claim in
a live run.

### C4. No `/box history` view for the audit log — ENHANCEMENT (follow-up to B10) — RESOLVED
`[verified]`

> **RESOLVED 2026-06-21.** Added `formatAuditHistory` (pure formatter) + `/box history`
> subcommand with `--failed` / `--artifacts` flags; logged as a pure read (not audited).
> Covered by `audit.test.ts` (timeline/failed/artifacts/empty cases) and a live engine
> smoke test. Usage string updated.


B10 writes a per-feature JSONL audit log but there is no human-readable view command.
Reading raw JSONL mid-workflow is awkward.

**Fix:** add a `/box history` control command that reads
`.pi/audit/<module>_<feature>.audit.jsonl` for the active feature and pretty-prints a
timeline: one line per event with `seq`, time, `command op args`, `phase_from→phase_to`,
`outcome`, `attempt`, and `detail`; artefact registrations folded in by date. Optional
flags: `--failed` (only non-`ok` outcomes), `--artifacts` (registry only). Pure formatter
over the parsed records — testable like the other helpers.

### C5. Engine code changes require a full Pi restart, not `/new` — INFO (operational) — RESOLVED
`[verified]`

> **RESOLVED 2026-06-21.** Added stale-engine detection: the status line fingerprints
> `.pi/governance/{engine,config,audit}.ts` (mtime-based, FNV-1a) and appends
> `⚠ ENGINE STALE — restart Pi` when the on-disk build drifts from the build loaded into
> the running process. `buildFingerprint`/`staleSuffix` covered by `engine.test.ts`; live
> smoke test confirmed the marker appears on an on-disk edit. (Doc note for the README
> still worth adding; the runtime signal is the substantive fix.) **Self-referential
> caveat:** the detector only helps once *this* build is loaded — your current running Pi
> still has the old status line, so it won't flag the pending B8/B9/B10/C4/C5 changes.
> After the next restart, all future engine edits will be flagged automatically.


The governance extension is loaded once at Pi process start. `/new` resets the session
(zero context) but keeps the already-loaded extension code, and governance *state* is
file-backed in `.pi/feature-box.json`. So edits to `engine.ts`/`config.ts`/`audit.ts` do
**not** take effect until Pi is quit and relaunched. Observed live: after the B9 parser
fix, `/box allow-files-from-plan` still imported zero files (old parser in memory) and
`/write-tests` blocked on an empty `allowedTestFiles`. The fix landed on disk and passed
its tests; it was simply not loaded.

**Fix:** document prominently — "after any change under `.pi/governance/`, `/quit` and
relaunch Pi; `/new` is not enough." Consider a startup banner that prints the engine
build/version so a stale process is obvious.

### C6. Test invocation depended on venv activation / interpreter guessing — MEDIUM — RESOLVED

`[verified]`

> **RESOLVED 2026-06-21.** Made the Makefile name the venv interpreter explicitly
> (`VENV ?= .venv`, `PYTEST := $(VENV)/bin/pytest`, `RUFF := $(VENV)/bin/ruff`; `test`/
> `test-file`/`lint`/`format` use them) so `make` works whether or not the venv is
> activated — verified `make test-file` runs `.venv/bin/python3.13` with no activation.
> Updated `write-tests.md` Step 5 to use `make test-file f=…` (narrow run) instead of bare
> `pytest`, with an explicit note not to guess at interpreters/activation. Single source of
> truth for the interpreter now lives in the Makefile.

`write-tests.md` Step 5 told the agent to run bare `pytest …`, which resolves against
`$PATH` — so success depended on the developer having activated the venv in the shell that
launched Pi (or on the agent guessing `python -m pytest`/activation). The full-suite
`make test` was the wrong granularity for a RED run, and also called bare `pytest`.

**Note:** this fixes the *exploratory* Step-5 run only. The authoritative `/box run-red`
gate has the same root problem inside the engine — tracked and fixed separately as B11.

### C7. `implement.md` still runs bare `pytest` — C6 was incomplete — MEDIUM — RESOLVED

`[verified]`

> **RESOLVED 2026-06-21.** `implement.md` Step 1.2 and Step 5 now use `make test-file
> f=…` (and `make lint-file f="…"`) instead of bare `pytest`/`ruff`, with the same
> "do not guess interpreters" note as `write-tests.md`. Added a `lint-file` Makefile
> target (mirrors `test-file`; resolves `.venv/bin/ruff`) so narrow per-file linting stays
> venv-explicit; `.PHONY` + help text updated. The `/box run-red`/`run-green` examples stay
> as `pytest` (parser rejects `make`; B11 makes those gates venv-proof at the engine level).
>
> **Follow-up 2026-06-21:** `review.md` was a *third* instance of the same gap — its Step 1
> "Run tests first" ran bare `pytest` and blocked the review with `pytest: command not
> found` even though the tests were green. Fixed Step 1 to `make test-file f=…` and the
> Code-quality checklist to `make lint-file f="…"`. Swept all of `.pi/prompts/`: the only
> remaining `pytest`/`ruff` mentions are prose, not command invocations. The bare-`pytest`
> pattern was present in every prompt that runs tests (write-tests, implement, review) —
> worth a lint/CI check that no prompt invokes a bare interpreter.
>
> **Refinement 2026-06-21:** live `/review` showed the `make lint-file f="<changed files>"`
> guidance was too loose — for a UI feature the changed set includes `.html`/`.css`, and
> ruff errored (exit 2, ~50KB output) on the templates before the model self-corrected to
> Python-only. Tightened both `implement.md` and `review.md` to `f="<changed Python files>"`
> with an explicit note that ruff lints only `.py` (templates/stylesheets are not
> ruff-checkable). Not a bug in the target — ruff is Python-only by nature — but the prompt
> shouldn't invite passing non-Python paths.



C6 fixed the test invocation in `write-tests.md` only. `implement.md` has the identical
bare-`pytest` instruction in several places (lines ~58, ~145–146 for exploratory runs;
~40, ~196, ~225 for the `/box run-red`/`run-green` examples). Confirmed live during the
register-UI `/implement` run: the model tried `pytest …` (`command not found`), then
`python -m pytest` (pyenv interpreter — `No module named pytest`), then a `find` for the
venv, and only then `.venv/bin/python -m pytest …`, which produced the correct RED
(3 failed). So the model burned three failed attempts (plus an anomalous **104-second
`ls`** — cause unknown, recovered on its own) guessing the interpreter that C6 was meant
to make unnecessary.

This also re-confirms C5/B11 operationally: the running Pi predates B11, so when this run
reaches GREEN the `/box run-green` gate will hit bare `pytest` via PATH and likely fail to
find it the same way until Pi is restarted.

**Fix (mirror C6, not yet applied — holding per developer):** in `implement.md`, switch
the *exploratory* run lines to `make test-file f=…`; keep the `/box run-red`/`run-green`
examples as `pytest …` (the engine parser rejects `make …`, and B11 makes those gates
venv-proof at the engine level once Pi is restarted). Editing the prompt on disk is safe
mid-run — the active session already has its prompt loaded; the change applies to the next
invocation.

---

## E. Model fit / instruction-following (gpt-5.5)

### E1. gpt-5.5 repeatedly ignored explicit prose gates this run — HIGH (model-fit)
`[observed]`

Three independent instances in a single dry run where `gpt-5.5` did not honor an
explicit, written instruction in a prompt:

1. **A1/A2** — skipped the `/plan` "list issues and stop" validation gate and went
   straight to implementation approaches, despite reasoning about a SECURITY §11
   conflict that the gate exists to surface.
2. **A4** — during `/iterate ... enrich`, tried to **edit the `.feature` contract**,
   which `iterate.md` forbids in four separate places (Role, enrich output, Step 4,
   Rules).
3. (Same enrich run) **invented a new scenario** (`@render`) beyond the three the
   developer authored — scope creep CLAUDE.md explicitly prohibits.

In every case the **structural enforcement compensated**: the validation gate is being
re-prompted (A1/A2), and the `.feature` hard gate blocked the contract write (A4/D3).
That is strong validation of the harness's "encode structure, don't trust prose"
principle — but it is also a clear signal that **gpt-5.5's prose-instruction adherence
is unreliable** for this workflow. The harness should not lean on prose where a gate is
possible, and the prompts may need the key constraints made far more prominent (top of
file, repeated, imperative) rather than buried in a Rules footer.

**Decision needed:** tighten prompts (promote critical constraints, add structural gates
where feasible) and/or re-evaluate the model. Re-run the same feature on a second model
to separate model-fit from prompt design before investing heavily in either.

---

## D. What worked (preserve these)

### D1. Escalation broke flow instead of auto-resolving — GOOD
`[observed]`

The agent correctly identified that the happy-path assertion "my browser lands on the
login page" depends on a `GET /auth/login` route that no feature has built yet, and
surfaced it as an open question rather than silently inventing a login page. This is
the intended behavior — the harness paused for a human decision on a genuine scope
boundary. Whatever in the `/plan` prompt produced this (the explicit Open Questions
slot + "do not invent scenarios" rule) should be retained.

### D2. Approach analysis was accurate and spec-grounded — GOOD
`[observed]`

The three approaches were correctly evaluated against `SECURITY.md` §4 content
negotiation; the recommended approach (reuse the existing endpoint + service) and the
rejection of the over-scoped HTMX variant were both sound and cited the right docs.

### D3. `.feature` hard gate caught a model that ignored its prompt — GOOD
`[observed]`

In `/iterate ... enrich` the agent attempted to rewrite the `.feature` contract (add a
scenario, edit comments and steps). The engine blocked it: "`…feature` is a `.feature`
contract and must not be modified by the agent," and the agent degraded gracefully to
proposing suggestions for manual application. This is defense-in-depth working exactly as
intended: the prose said "never modify the `.feature`," the model ignored it, and the
**structural** gate stopped the write anyway. The contrast with A1/A2 (a prose-only gate
the model glided past) is the argument for encoding constraints structurally wherever
possible. See E1.

---

### D4. `/review` surfaced genuine pre-existing defects and produced sound learning notes — GOOD

`[observed]`

Despite the attribution problem (A6), the register-UI `/review` did real work: it correctly
identified the missing `ApiResponse[T]` envelope and the audit-log gap (both genuine
codebase defects, now BL-0003/BL-0004), correctly PASSED 26 checks, and the "Learning notes"
(content negotiation at the edge, silent honeypots, shared validation, redirect-after-POST,
response models on mixed endpoints) were accurate and well-reasoned. As a safety net it
works — it just needs the introduced-vs-pre-existing distinction (A6) so its FAIL count is
trustworthy, and a checklist refresh (A7) so it stops raising framework-outdated nits.

---

## Priority order for fixes

1. ~~**B1 + B2 + B3**~~ — DONE 2026-06-21. The UI/template blind spot.
2. ~~**B4**~~ — DONE 2026-06-21.
3. **A1 + A2** — OPEN, held deliberately. The validation gate is the highest-leverage
   prompt fix, but it is being left open so the restarted run (now that the `.feature`
   has a honeypot scenario) can be observed: does `/plan` surface the SECURITY §11
   conflict on its own, or was the miss structural? Fix the prompt *after* observing.
4. **E1** — OPEN, model-fit. Re-run on a second model to separate model behavior from
   prompt design before over-investing in prompt rewrites.
5. **B6** — OPEN, status-line feedback gap (medium; reads as a false failure).
6. **A3, A5, B5, B7** — OPEN, alignment and consistency (A5: tighten the freeze
   consistency-check wording so no-change files don't trip it).
7. ~~**A4 + B8**~~ — DONE 2026-06-21. Enrich routes discovered scenarios to `Backlog.md`,
   and the engine now grants a `backlog` write class in the planning phases.
8. ~~**B9**~~ — DONE 2026-06-21. Manifest parser now matches the canonical
   `PLAN_TEMPLATE.md` table format.
9. ~~**B10**~~ — DONE 2026-06-21. Per-feature JSONL control-plane audit log
   (`.pi/audit/<module>_<feature>.audit.jsonl`).
10. **C1–C3** — OPEN, documentation accuracy.
11. ~~**C4**~~ — DONE 2026-06-21. `/box history` view for the B10 audit log.
12. ~~**C5**~~ — DONE 2026-06-21. Stale-engine detection on the status line (README note
    still pending).
13. ~~**C6**~~ — DONE 2026-06-21. Makefile names the venv interpreter; `write-tests.md`
    Step 5 uses `make test-file` (exploratory run only).
14. ~~**B11**~~ — DONE 2026-06-21. `runPytest` resolves to `.venv/bin/<exe>` so the
    `/box run-red`/`run-green` gates are venv-proof (the authoritative half of C6).
15. ~~**C7**~~ — DONE 2026-06-21. `implement.md` uses `make test-file`/`make lint-file`;
    added the `lint-file` Makefile target.
16. **B12** — MITIGATED 2026-06-21 (prompt rule; judgment boundary, no structural fix).
    File-granular allowlist can't stop in-file scope drift; shared/app-shell CSP/header/nav
    changes beyond the plan must be escalated.
17. ~~**B13**~~ — DONE 2026-06-21. Dedicated `status` write class for
    `docs/PROJECT_STATUS.md`, writable in IMPLEMENTING/REVIEWING, never manifest-importable.
18. ~~**A6**~~ — DONE 2026-06-21. `/review` now tags findings introduced vs pre-existing;
    only introduced ones block; summary counts split.
19. ~~**A7**~~ — DONE 2026-06-21. `review.md` §H checklist updated to the current Starlette
    `TemplateResponse` signature and dual-purpose-route handling.
20. **A8** — MITIGATED 2026-06-21 (documented remediation loop in `review.md`). Optional
    future: a remediation mode that re-opens the frozen allowlist for review-named files.
