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
| [BUG-001](#bug-001) | Registration screen renders full-bleed on desktop | Frontend / auth | Medium | Open |
| [BUG-002](#bug-002) | mypy: incompatible reassignment of `request_body` in register_user | Backend / auth | Medium | Verified |
| [BUG-003](#bug-003) | Local `make lint` runs no type checker — type errors escape to CI | Tooling / build | Medium | Open |

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
**Status:** Open
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
**Fix:** _(pending — Open)_ Fold mypy into the local gate. Preferred: add a `typecheck` target (`mypy app/ --ignore-missing-imports`, flags matching CI) and have `lint` invoke ruff + mypy, so `make lint` == the CI quality gate. **Escalation note:** this changes a project-wide quality gate (Makefile + likely a mypy config block in `pyproject.toml`, and mypy must be a pinned dev dependency) — requires confirmation before implementing. Expect the first full run to surface more than BUG-002 across `app/`.
**Regression test:** After the fix, reproduce BUG-002's pattern locally and confirm `make lint` fails on it (gate now catches type errors). The gate itself is the guard.
**Notes:** Pairs with BUG-002 — BUG-002 is the instance (a code defect), BUG-003 is the gate gap (why it escaped). Fixing BUG-003 prevents the *class*; fixing BUG-002 clears the *instance*. Confirm whether mypy is already a pinned dev dependency before wiring the target.

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
