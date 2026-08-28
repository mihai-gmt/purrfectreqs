# PurrfectReqs — Defect Log

> **Purpose:** Track defects (things that work incorrectly or violate a spec) from discovery to verified fix. This is a working artifact, not governance.
>
> **Scope:** Defects only — observed-vs-expected gaps in existing behaviour. *New* work goes in `Backlog.md`; *missing* behaviour the specs never covered is a backlog item, not a bug.

---

## How to use this log

1. **One entry per defect.** Assign the next `BUG-NNN` id. **Ids are never reused**, even after a bug is closed or rejected — so commits and `.feature` files can cite a stable reference.
2. **Add a row to the index table** (top) and a **detailed entry** (below). Keep them in sync.
3. **Fixing a defect follows the same RED → GREEN discipline as a feature.** Write a test that *reproduces* the defect (it fails — that proves the bug), then fix until it passes. Record that test in **Regression test** so the bug cannot silently return. Never modify a test to make a bug "go away" — fix the implementation (CLAUDE.md → Testing Discipline).
4. **Where a clean automated test is artificial** (pure CSS/visual layout), record honest manual verification instead: *"Manual — FRONTEND.md §7 checklist at 320 px and 1440 px."* Do not fabricate a unit test that does not really assert the behaviour.
5. **The fix stays inside the Feature Box** of the affected area and respects the governing doc named in **Expected**. A fix that would exceed it is an escalation, logged in the entry.
6. **A defect is addressed by a new, dedicated `.feature` file** (date-stamped, citing the `BUG-NNN` id), **never** by adding scenarios to the original feature's `.feature` file. That original file is the feature's contract; modifying it to cover a defect violates `CLAUDE.md` → `.feature` File Authority ("MUST NOT add scenarios not present"). The new file gives the defect its own traceable spec.

### Severity (impact — drives order in the index)

| Severity | Meaning |
|----------|---------|
| **Critical** | Data loss/corruption, security hole, or core flow unusable for all users. Drop everything. |
| **High** | A primary flow is broken or blocked; no reasonable workaround. |
| **Medium** | Works but degraded — usability impaired, or a documented spec is violated, with a workaround or non-blocking impact. |
| **Low** | Cosmetic or minor; no functional impact. |

### Status lifecycle

`Open` → `In Progress` → `Fixed` (code changed, awaiting verification) → `Verified` (reproduction test/manual check confirms fixed) → closed.
Terminal off-ramps: `Won't Fix` (with reason), `Duplicate` (→ cite the surviving id).

---

## Index

| ID | Title | Area | Severity | Status |
|----|-------|------|----------|--------|
| [BUG-006](#bug-006) | pip-audit fails CI: `click` 8.3.1 and `setuptools` 81.0.0 have published advisories | Tooling / build | High | Fixed |
| [BUG-001](#bug-001) | Registration screen renders full-bleed on desktop | Frontend / auth | Medium | Open |
| [BUG-002](#bug-002) | mypy: incompatible reassignment of `request_body` in register_user | Backend / auth | Medium | Verified |
| [BUG-003](#bug-003) | Local `make lint` runs no type checker — type errors escape to CI | Tooling / build | Medium | Verified |
| [BUG-004](#bug-004) | Local `make lint` runs no security linter (bandit) — findings escape to CI | Tooling / build | Medium | Verified |
| [BUG-005](#bug-005) | Bandit emits spurious "Test in comment" warnings — `# nosec:` reason prose parsed as test IDs | Tooling / build | Low | Verified |

---

## Entries

### BUG-001
**Title:** Registration screen renders full-bleed (full width and height) on desktop
**Status:** Open
**Severity:** Medium — registration is fully functional and correct on mobile, but on desktop the form spans the whole viewport, looks broken, and violates the documented Centred Form archetype. Degraded usability + spec violation, not a blocked flow.
**Area / Module:** Frontend / auth (`app/templates/auth/register.html`, `app/static/css/app.css`)
**Discovered:** 2026-06-25 — manual review of the first built UI screen.
**Environment:** Desktop/laptop viewport (≥ ~1024 px). Correct on mobile widths.
**Observed:** The registration form and its inputs stretch edge-to-edge across the full width (and height) of the browser window.
**Expected:** A **Centred Form** layout — centred, `max-width` ~440 px, vertically centred, chrome-less (no rail/nav). Governed by `docs/FRONTEND.md` §2 (Layout Archetype #1) and §2:62.
**Steps to reproduce:**
1. Run the app and open `/auth/register` in a desktop-width browser (~1440 px).
2. Observe the form filling the entire viewport instead of a centred card.
**Root cause:** `register.html` places the form in `<main class="container">` with no width constraint, so PicoCSS stretches inputs to the container width; the `.auth-layout` primitive does not yet exist; and the template extends `base.html`, which renders the nav (not chrome-less).
**Fix:** _(pending — Open)_ Implement the `.auth-layout` primitive in `app.css` (now sanctioned by FRONTEND.md §2/§5), provide a chrome-less auth base, and apply the Centred Form archetype to `register.html`.
**Regression test:** Two layers, both automated (no manual-only step remains):
1. **Structural** (`TestClient`, in-process) — assert `/auth/register` renders the chrome-less auth base and the `.auth-layout` wrapper, and that no app-shell nav is present.
2. **Rendered / visual** (Playwright, `@pytest.mark.ui`) against a uvicorn live-server fixture bound to the **test DB** — at 1440 px assert the form is centred and width-constrained (computed `max-width` matches the design token; rendered width well below the viewport); at 320 px assert no horizontal overflow. This is conformance to the **Centred Form** archetype contract (FRONTEND.md §2/§9), not a literal pixel value.
**Notes:** The governing archetype and sanctioned primitive were added 2026-06-25 (FRONTEND.md §2 catalogue, §5 sanctioned uses), so the fix is in-bounds and needs no further escalation. Playwright was approved as a dependency 2026-06-25, so the visual surface is now automatable (was previously manual `[REVIEW]`). Browser binary install: `make playwright-install`.

---

### BUG-002
**Title:** mypy: incompatible reassignment of `request_body` in `register_user`
**Status:** Verified
**Severity:** Medium — no runtime impact (the two branches never coexist), but it fails the mypy CI gate, blocking the merge/scan. A documented quality gate is violated; runtime behaviour is unaffected.
**Area / Module:** Backend / auth (`app/auth/router.py`)
**Discovered:** 2026-06-26 — GitHub CI `mypy app/ --ignore-missing-imports` step.
**Environment:** Static type check (mypy). N/A at runtime.
**Observed:** `app/auth/router.py:120: error: Incompatible types in assignment (expression has type "UserRegisterRequest", variable has type "UserRegisterFormRequest") [assignment]`.
**Expected:** mypy passes cleanly on `app/`.
**Steps to reproduce:**
1. Run `mypy app/ --ignore-missing-imports`.
2. Observe the one error at `app/auth/router.py:120`.
**Root cause:** The single local `request_body` is first bound to `UserRegisterFormRequest` (line 108, HTML branch) and later rebound to `UserRegisterRequest` (line 120, JSON branch). mypy fixes the variable's declared type from the first assignment and rejects the second, even though the HTML branch returns at line 118 — so the two never coexist at runtime. mypy does not narrow across the early return for variable type inference.
**Fix:** _(2026-07-08 — Verified)_ Renamed the two branch locals in `register_user` (`app/auth/router.py`) so each binds its own variable: the HTML branch uses `form_request` (`UserRegisterFormRequest`), the JSON branch uses `json_request` (`UserRegisterRequest`). No shared name to fix a type against, no behaviour change.
**Regression test:** `mypy app/ --ignore-missing-imports` passes (the CI scan step). This is a static-check gate, not a pytest test — no reproducing unit test is meaningful; the type checker *is* the regression guard. Per ADR-0033 a defect fix gets a new `.feature`, but that governs *behavioural* defects; this is a type-annotation defect with zero runtime behaviour, so a Gherkin scenario would be a fabricated test (violating rule 4 above). Behaviour was instead confirmed unchanged by the existing contracts: `tests/bdd/step_defs/test_20260407_basic_register_user_api.py` + `test_20260621_basic_register_user_ui.py` (14 passed on 2026-07-08).
**Verification (2026-07-08):** RED reproduced locally (`mypy app/ --ignore-missing-imports` → same error at `router.py:120`); after the rename GREEN confirmed — mypy `Success: no issues found in 22 source files`, `ruff check`/`ruff format --check` clean, and the two registration BDD suites pass (14 tests). A GitHub CI re-run resurfaced this same error, confirming it was this still-Open defect, not a new one — no duplicate entry was created.
**Notes:** Surfaced by the GitHub scan, not local `make test`/`make lint` (mypy is not yet wired into the local Makefile lint target — see BUG-003, still Open: wiring mypy into `make lint` would have caught this before push).

---

### BUG-003
**Title:** Local `make lint` runs no type checker — type errors escape local gates and only surface in CI
**Status:** Verified
**Severity:** Medium — no runtime impact, but the local quality gate is weaker than CI, so a whole class of defect (type errors) is invisible until after push. BUG-002 is the first escape through this gap; it will not be the last.
**Area / Module:** Tooling / build (`Makefile`, possibly `pyproject.toml`)
**Discovered:** 2026-06-26 — while triaging BUG-002, which CI caught but `make lint`/`make test` did not.
**Environment:** Local developer workflow vs GitHub CI.
**Observed:** `make lint` runs `ruff check` + `ruff format --check` only. Ruff is **not** a type checker — it does style, imports, and annotation-presence checks but performs no type inference, so it cannot detect type errors (e.g. incompatible assignment). mypy runs only in GitHub CI (`mypy app/ --ignore-missing-imports`), so type defects are detected only after push.
**Expected:** The local gate matches CI — type errors are catchable before push. Specifically, `make lint` (or a dedicated `make typecheck` folded into it) runs mypy with the same flags as CI.
**Steps to reproduce:**
1. Introduce a type error in `app/` (see BUG-002).
2. Run `make lint` — it passes.
3. Push — only then does CI's mypy step fail.
**Root cause:** mypy was wired into CI but never into the local Makefile lint target.
**Fix:** _(2026-07-08 — Verified)_ Folded mypy into the local gate (`Makefile`). Added a `MYPY := $(VENV)/bin/mypy` variable and a `typecheck` target (`mypy app/ --ignore-missing-imports`, matching CI verbatim); `lint` now runs `ruff check` + `ruff format --check` + `$(MAKE) typecheck`, so `make lint` == CI's type gate. `help` text and `.PHONY` updated. **No dependency or config change was needed** — contrary to this entry's original speculation, mypy `1.20.0` was already a pinned dev dependency (`pyproject.toml` `[project.optional-dependencies] dev`) and a `[tool.mypy]` block (with `ignore_missing_imports = true`) already existed. The escalation was confirmed by the developer before implementing.
**Regression test:** RED→GREEN proven with a throwaway probe file (`app/_bug003_probe.py`, a function annotated `-> int` returning a `str`, then deleted): (1) RED — with the CURRENT ruff-only `make lint`, the probe's type error slipped through (exit 0), while `mypy` flagged it — reproducing the gap. (2) GREEN — after wiring mypy in, `make lint` failed at the `typecheck` step on the same probe (exit 2). (3) Clean — probe removed, `make lint` passes all three gates (exit 0, `Success: no issues found in 22 source files`). The gate itself is the guard; no pytest test is meaningful for a build-tooling change.
**Notes:** Pairs with BUG-002 — BUG-002 was the instance (a code defect), BUG-003 was the gate gap (why it escaped). Both now closed. **Remaining gap (not part of BUG-003):** CI's lint job also runs `bandit -r app/ -c pyproject.toml`, which `make lint` still does NOT run — the same local-vs-CI class of gap, for the security linter rather than the type checker. Left untouched to stay in this defect's box; log a separate bug if the bandit gate should also be mirrored locally.

---

### BUG-004
**Title:** Local `make lint` runs no security linter (bandit) — findings escape local gates and only surface in CI
**Status:** Verified
**Severity:** Medium — no runtime impact, but the local quality gate is weaker than CI. CI's lint job runs bandit; `make lint` does not, so a whole class of finding (security issues bandit detects — hardcoded secrets, `eval`, `subprocess(shell=True)`, etc.) is invisible until after push. Same class of gap as BUG-003, for the security linter rather than the type checker.
**Area / Module:** Tooling / build (`Makefile`)
**Discovered:** 2026-07-08 — while fixing BUG-003, comparing CI's lint job against `make lint`.
**Environment:** Local developer workflow vs GitHub CI.
**Observed:** After BUG-003, `make lint` runs `ruff check` + `ruff format --check` + `mypy`. CI's lint job runs those **plus** `bandit -r app/ -c pyproject.toml`. Bandit runs only in CI, so security-linter findings are detected only after push.
**Expected:** The local gate matches CI — bandit findings are catchable before push. `make lint` (or a dedicated `make security` folded into it) runs `bandit -r app/ -c pyproject.toml`, the same command and config as CI.
**Steps to reproduce:**
1. Introduce a bandit finding in `app/` (e.g. a hardcoded password string, B105).
2. Run `make lint` — it passes (ruff + mypy don't cover it; ruff's `S` family is not selected).
3. Push — only then does CI's bandit step fail.
**Root cause:** bandit was wired into CI but never into the local Makefile lint target. Bandit `1.8.3` is already a pinned dev dependency (`pyproject.toml` `[project.optional-dependencies] dev`) and `[tool.bandit]` config already exists — only the Makefile wiring was missing.
**Fix:** _(2026-07-08 — Verified)_ Added to `Makefile`: a `BANDIT := $(VENV)/bin/bandit` variable and a `security` target (`bandit -r app/ -c pyproject.toml`, matching CI verbatim); `lint` now runs `ruff check` + `ruff format --check` + `$(MAKE) security` + `$(MAKE) typecheck`. `help` text and `.PHONY` updated. No dependency or config change needed — bandit `1.8.3` was already a pinned dev dependency and `[tool.bandit]` already existed.
**Regression test:** RED→GREEN with a throwaway probe (`app/_bug004_probe.py`, a module-level `password = "..."` string → bandit B105; ruff-clean because the `S` family isn't selected, mypy-clean), then deleted: (1) RED — current `make lint` (ruff + mypy, no bandit) passed despite the B105 finding, which bandit independently flagged — reproducing the gap. (2) GREEN — after wiring, `make lint` failed at the `security` step on the same probe (exit 2). (3) Clean — probe removed, `make lint` passes all four gates (exit 0; bandit `No issues identified`, mypy `Success: no issues found in 22 source files`). The gate itself is the guard; no pytest test is meaningful for a build-tooling change.
**Notes:** Third in the local-vs-CI gate family (BUG-002 instance → BUG-003 type gate → BUG-004 security gate). `make lint` now == CI's full lint job (ruff check, ruff format, bandit, mypy). Observed harmless bandit `WARNING Test in comment: … is not a test name` lines during the run — bandit misreading ordinary `#` comments in existing `app/` code as `# nosec`-style hints; pre-existing, no finding, not addressed here.

---

### BUG-005
**Title:** Bandit emits spurious "Test in comment" warnings — `# nosec:` reason prose is parsed as test IDs
**Status:** Verified
**Severity:** Low — cosmetic. No finding, no functional impact; the suppression works correctly. Bandit prints seven `WARNING Test in comment: … is not a test name or id` lines per run, cluttering `make lint` / CI output and eroding signal.
**Area / Module:** Tooling / build (`app/auth/schemas.py`). Convention documented in `docs/adr/ADR-0025-suppression-discipline.md` and `.pre-commit-config.yaml`.
**Discovered:** 2026-07-08 — noticed in bandit output while verifying BUG-004.
**Environment:** `bandit -r app/ -c pyproject.toml` (local `make security` and CI).
**Observed:** Bandit prints `WARNING Test in comment: user is not a test name or id, ignoring` (and: `facing`, `error`, `message`, `not`, `a`, `credential`) on every run.
**Expected:** Bandit runs clean — the suppression is honoured with no spurious warnings.
**Steps to reproduce:**
1. `bandit -r app/ -c pyproject.toml` (or `make security`).
2. Observe the seven `Test in comment` warnings.
**Root cause:** The sole suppression, `app/auth/schemas.py:44`, is `# nosec: B105 — user-facing error message, not a credential`. Bandit's parser (`bandit/core/manager.py`) is `NOSEC_COMMENT = re.compile(r"#\s*nosec:?\s*(?P<tests>[^#]+)?#?")` — the `tests` group captures everything after `nosec:` **up to the next `#`**. With no second `#`, the whole reason prose is captured, then `NOSEC_COMMENT_TESTS` (`(B\d+|[a-z\d_]+)`) treats every prose word as a candidate test ID, warning on each. **This is not a stray comment — it is exactly the canonical format ADR-0025 prescribes** (its example is this line verbatim). The project's suppression-discipline convention and bandit's own parser disagree.
**Fix:** _(2026-07-08 — Verified)_ Shielded the prose from bandit's parser with a second `#` at `app/auth/schemas.py:44`: `# nosec: B105  # user-facing error message, not a credential`. Bandit now captures only `B105` (stops at the 2nd `#`) → zero warnings, B105 still suppressed. Confirmed to still pass the `suppression-discipline` pygrep hook regex (colon + reason present). **Governance flag (resolved 2026-07-08):** the un-shielded form was ADR-0025's documented canonical example and appeared in `.pre-commit-config.yaml`'s hook comments. With the developer's approval (Option 1), both were amended to the shielded form: ADR-0025 Decision section corrected + dated amendment note added citing this BUG; `.pre-commit-config.yaml` hook-comment example updated with a one-line explanation. Ruff's `# noqa` parser was verified to have no equivalent quirk (prose after codes is fine), so only the `# nosec` example changed.
**Regression test:** RED→GREEN on the real file: RED — current line yields the 7 warnings; GREEN — shielded form yields `No issues identified.` with `skipped due to specifically being disabled: 1` (B105 still suppressed) and no `Test in comment` lines. The bandit run is the guard; no pytest test is meaningful for a comment-format fix.
**Notes:** Follows the BUG-002→004 gate family but is a distinct defect (a convention/tool conflict, not a missing gate). Only one `# nosec` exists in the codebase, so this single-line fix clears all current noise; the durable prevention is the ADR-0025 amendment above.

---

### BUG-006
**Title:** pip-audit fails CI: pinned `click` 8.3.1 and `setuptools` 81.0.0 have published vulnerability advisories
**Status:** Fixed
**Severity:** High — two pinned runtime dependencies carry published advisories and the CI dependency-vulnerability gate fails (`exit code 1`), blocking the pipeline on every push and on PRs that touch `requirements.txt`/`pyproject.toml`. Not Critical: exploitability of these specific advisories in this app's context is unassessed, and the app itself runs correctly.
**Area / Module:** Tooling / build (`requirements.txt`; gate in `.github/workflows/ci.yml` `pip-audit` job and `.github/workflows/scheduled.yml` weekly scan)
**Discovered:** 2026-08-28 — GitHub CI `pip-audit` job failure.
**Environment:** GitHub Actions, `pip-audit==2.9.0` against `requirements.txt` (with `en_core_web_sm` filtered out). Local venv carries the same pinned versions.
**Observed:** pip-audit reports two vulnerabilities and exits 1:
```
Name       Version ID              Fix Versions
---------- ------- --------------- ------------
click      8.3.1   PYSEC-2026-2132 8.3.3
setuptools 81.0.0  PYSEC-2026-3447 83.0.0
Error: Process completed with exit code 1.
```
**Expected:** The dependency scan passes — no pinned dependency has a published advisory. Governed by `docs/SECURITY.md` (supply-chain/dependency hygiene) and CLAUDE.md → Approved Dependencies.
**Steps to reproduce:**
1. Run `grep -v "en_core_web_sm" requirements.txt | pip-audit -r /dev/stdin` (same command as CI), or push any commit.
2. Observe the two findings above and exit code 1.
**Root cause:** `requirements.txt` pins `click==8.3.1` (line 14) and `setuptools==81.0.0` (line 73). Both versions have since received published advisories (PYSEC-2026-2132, PYSEC-2026-3447); the pins were never bumped. Note: `click` is a transitive constraint surface (Flask/uvicorn depend on it) — the bump must stay within dependent packages' accepted ranges.
**Fix:** _(2026-08-28 — Fixed, awaiting pipeline verification)_ Bumped the two pins in `requirements.txt`: line 14 `click==8.3.1` → `click==8.3.3`, line 73 `setuptools==81.0.0` → `setuptools==83.0.0` (the fix versions named by the advisories). No code changes — neither package is imported directly in `app/`. `pyproject.toml` `[build-system] requires = ["setuptools>=68"]` remains satisfied by 83.0.0. No local verification per developer decision — the CI pipeline is the gate.
**Regression test:** The CI `pip-audit` job is the guard: RED — the old pins produced the two findings above (exit 1); GREEN — the same command (`grep -v "en_core_web_sm" requirements.txt | pip-audit -r /dev/stdin`) reports no vulnerabilities (exit 0) on the next pipeline run. No pytest test is meaningful for a dependency-pin change; CI's install + test jobs confirm no behavioural regression from the version bumps. **Verification deferred to the pipeline:** flip to `Verified` only after a green CI run.
**Notes:** Per CLAUDE.md, bumping these pins is not a new-dependency decision — both are already approved and pinned; only versions change. If either fix version conflicts with a dependent's constraint (e.g. Flask's `click` range), escalate rather than silently picking an older/newer version. The weekly `scheduled.yml` scan would have surfaced this even without a push — check whether it fired before this CI failure.

---

## Entry template (copy this shape)

```
### BUG-NNN
**Title:**
**Status:** Open
**Severity:**            <!-- Critical | High | Medium | Low, with one-line justification -->
**Area / Module:**
**Discovered:**          <!-- YYYY-MM-DD — how it was found -->
**Environment:**         <!-- browser/viewport/env, if relevant; omit if N/A -->
**Observed:**            <!-- what actually happens -->
**Expected:**            <!-- correct behaviour + the governing doc/spec -->
**Steps to reproduce:**
1.
**Root cause:**          <!-- fill when known -->
**Fix:**                 <!-- what changed + commit/PR/.feature link -->
**Regression test:**     <!-- the reproducing test (RED→GREEN), or honest manual verification -->
**Notes:**
```
