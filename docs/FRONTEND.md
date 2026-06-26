# PurrfectReqs — Frontend & UI/UX Standards

> **Purpose:** This file defines HOW the user interface is structured, styled, and built — information architecture, the app shell, the template/component architecture, design tokens, interaction patterns, and the per-view design checklist. It is the single home for frontend guidance so UI work can be reasoned about (and loaded into context) without dragging in backend code patterns. For backend patterns see `docs/GUIDE.md`; for WHAT to build see `docs/SCOPE.md`.
>
> **Scope:** Server-rendered HTML (Jinja2) enhanced with HTMX, styled with PicoCSS, with Alpine.js (CSP build) for ephemeral client-side state. No SPA, no build step, no npm, no CDN. The stack is locked — see `docs/TECH_STACK.md` → Frontend.
>
> **Authority:** This document is the frontend peer of `docs/GUIDE.md` (rank 8 in `CLAUDE.md` → Document Authority). It is subordinate to `CLAUDE.md`, `docs/SECURITY.md`, the active `.feature` file, `docs/SCOPE.md`, `docs/ARCHITECTURE.md`, and `docs/DATA_MODELS.md`. **Where a security rule and a UI guideline conflict, security wins.** This document never relaxes a constraint from `docs/SECURITY.md` or `docs/TECH_STACK.md` — it points to them.
>
> **Related files (defer to these, do not restate them):**
> - `docs/SECURITY.md` → Security headers & CSP (§8), CSRF (§9), JWT/cookie auth (§3, §5, §14), honeypot (§11), auth error shapes (§13). The security-critical frontend rules live here.
> - `docs/TECH_STACK.md` → Frontend section, Alpine.js Security Constraints, Browser UI Security Model, vendored asset versions & SHA256 checksums.
> - `docs/ARCHITECTURE.md` → Frontend Architecture (structural invariants: template paths, partial naming, no business logic in templates, base.html inheritance).
> - `docs/GUIDE.md` → `ApiResponse[T]` envelope, Error Response Format, Correlation-ID flow — the server payloads HTMX consumes.
> - `docs/GLOSSARY.md` → canonical labels (hierarchy, AC states, roles) and file-naming conventions the UI must use verbatim.
> - `docs/DATA_MODELS.md` → the enum/state value lists that components (badges, trees, filters) render.
> - `docs/SCOPE.md` → the 7 MVP modules — these are the navigation destinations of the app shell.

---

## 1. Design Principles

These are the project-specific principles that orient every UI decision. They are deliberately few.

1. **Professional tool, not a brochure.** PurrfectReqs is a dense, daily-driver tool for POs/PMs managing requirements. Optimise for information density, scanning, and keyboard efficiency over marketing polish or whitespace. (PicoCSS defaults to a comfortable document density — we tune it tighter; see §5 Density.)
2. **The server is authoritative.** Application state lives on the server and is rendered as HTML. HTMX swaps server-rendered fragments; the browser never becomes a second source of truth. Optimistic UI only for trivial, cheap-to-roll-back toggles.
3. **Progressive disclosure for AI output.** NLP/LLM analysis (ambiguity, gaps, similarity, Gherkin validation) is advisory and can be noisy. Surface a summary; reveal detail on demand (the inspector pane). Never let analysis dominate the requirement the user is actually editing.
4. **Domain vocabulary is exact.** UI labels use `docs/GLOSSARY.md` terms verbatim — Epic / Story / Subtask, the four AC states, system vs project roles. No synonyms, no invented labels.
5. **Accessible and keyboard-first by default.** Semantic HTML, visible focus, full keyboard traversal of every flow. This is a baseline, not a later pass — see the UI Design Checklist (§7).
6. **Progressive enhancement.** Pages work as plain HTML forms/links; HTMX and Alpine enhance them. A failed script load degrades to full-page navigation, it does not break the app. **Exception that is not optional:** state-changing actions degrade to a `<form method="post">`, never to a GET link — see §3.

---

## 2. Information Architecture — the App Shell

### Chosen direction: Option D (module rail → master-detail → on-demand inspector)

The post-login application uses a three-zone shell that scales across all seven MVP modules without being replaced:

```
┌────┬──────────┬────────────────────────┐
│ P  │ Reqs     │ Checkout flow          │
│ R  │ ──────── │ Epic · Active          │
│ D  │ Checkout │ Description…           │
│ T  │ Onboard  │ AC (Gherkin)  ▸Analysis│
│ A  │ Login    │ • Given… When… Then…   │
│    │ Search…  │                        │
│ ⚙  │ [+ New]  │ [Analyze] [Validate]   │
└────┴──────────┴────────────────────────┘
 rail    master            detail
                    (inspector slides in on demand)
```

- **Module rail (left):** top-level navigation to the seven modules from `docs/SCOPE.md` — Projects, Requirements, Documents, NLP/Analysis (surfaced contextually), Gherkin, Traceability, Admin. Icons **must** be paired with a text label or accessible name (tooltip + `aria-label`) — icon-alone fails the no-color/icon-only-meaning rule (§7.2).
- **Master (list / tree):** the requirement hierarchy or the list for the active module. The requirement tree (Epic → Story → Subtask) is the spine of the product and lives here.
- **Detail (main):** the selected item — its description and acceptance criteria — and the place editing happens.
- **Inspector (on demand):** AI analysis, Gherkin validation results, traceability links. It slides in beside the detail; it is not permanently present.

### Incremental build path (do not build the whole shell up front)

Reach Option D in stages, building only what a shipped screen needs:

1. **Auth (now):** centred, single-column forms with **no app shell** — the user is not authenticated, so the rail/nav are absent. Login and registration look identical regardless of the shell decision. The shell is therefore **not** a prerequisite for auth work.
2. **First post-login screen (Projects/Requirements):** introduce the **left rail + master-detail** (this is "Option B"). This is the first time the shell exists.
3. **When Module 4 (NLP) produces analysis:** add the **on-demand inspector** pane (the "D" piece). Do not build a three-pane layout before there is analysis data to put in it.

### Responsive behaviour

- The rail collapses to icons, then to a top "hamburger" drawer below ~768 px.
- The master and detail stack vertically on narrow viewports; the inspector becomes a full-width disclosure rather than a side pane.
- Every view must work at 320 px and 1440 px (§7 pre-ship checklist).

### Where the shell lives

The shell is implemented in `app/templates/base.html` (and small included partials for the rail/master). Module templates fill the detail region via `{% block content %}`. Auth templates use a separate minimal layout (or `base.html` with the shell blocks empty) so they render chrome-less.

### Layout Archetypes (closed catalogue)

Every screen is assigned **one** of these five page-level layouts. The spec names the archetype; the implementer applies it — no per-screen layout invention. The set is **closed**: adding a sixth is an escalation (§8), not a default. This is page-level structure only — reusable *components* placed inside an archetype live in `docs/UI_CATALOGUE.md`, not here. **Width follows the content's job, never a blanket setting.**

Each entry declares **shell?** (does the app shell wrap it) · **width** · **responsive collapse** · **primitive** (the sanctioned `app.css` layout rule from §5, if any).

| # | Archetype | Shell? | Width | Collapse (≤ 768 px) | `app.css` primitive |
|---|-----------|--------|-------|---------------------|---------------------|
| 1 | **Centred Form** | no (chrome-less) | centred, `max-width` ~440 px, vertically centred | full-width with side padding | `.auth-layout` wrapper |
| 2 | **Master-Detail** | yes | rail fixed; master/detail fill the rest | rail → drawer; panes stack | shell grid |
| 3 | **Master-Detail + Inspector** | yes | #2 plus an on-demand right pane | inspector → full-width disclosure | shell grid |
| 4 | **Full-width Data** | yes | full container width, no reading cap | scroll the table, not the page | shell grid |
| 5 | **Reading / Content** | yes | centred column, `max-width` ~720 px | full-width with side padding | none (Pico `.container` + width token) |

**1 · Centred Form** — one focused task, nothing else; the empty space *is* the design.

```
┌───────────────────────────────┐
│         ┌───────────┐         │
│         │  [ form ] │         │
│         └───────────┘         │
└───────────────────────────────┘
```

Used by: login, register, password reset. No rail/nav — the user is not authenticated. A full-width form puts the label far from the field and forces the eye across the whole screen; ~440 px keeps label, field, and button in one glance.

**2 · Master-Detail** — list → select → act while the list stays in view (keeps context). The shell diagram at the top of §2 *is* this archetype. Used by: Projects, Requirements.

**3 · Master-Detail + Inspector** — #2 plus the on-demand inspector pane (AI analysis, validation, traceability). Build it only when there is data to put in it (progressive disclosure). Used by: NLP/Analysis (Module 4).

**4 · Full-width Data** — dense tables and dashboards. Deliberately drops the reading-width cap: tables need horizontal room, and constraining them forces wrapping that destroys scanability. Used by: requirement lists, exports, dashboards.

**5 · Reading / Content** — prose read top-to-bottom, held to ~720 px (~60–75 chars/line, §7.3) so the eye does not lose the next line on wide screens. Used by: help, long descriptions.

---

## 3. Navigation Model

**Default: `hx-boost` on the shell.** Boosting intercepts normal `<a>` navigation and `<form>` submission and swaps the body via AJAX, giving an app-like feel (no full-page white flash, preserved scroll) with almost none of the per-element HTMX wiring. With JavaScript disabled it degrades to ordinary full-page navigation — progressive enhancement for free.

**Targeted partial swaps where they earn it.** Reach for explicit `hx-get`/`hx-post` + `hx-target` only where a small swap genuinely beats a boosted page load: the requirement tree (expand/collapse), inline field validation, the inspector pane, search-as-you-type. Swap the **smallest** element that changes (§7.4).

**The read/write rule (this is a security constraint, not a style choice).** Per `docs/SECURITY.md` §9, every state-changing action is `POST`/`PUT`/`PATCH`/`DELETE` — **never** a `GET`. So:

- Navigation and reads → boosted `GET` (or `hx-get`).
- Any mutation → `hx-post`/`hx-put`/`hx-patch`/`hx-delete` (or a real `<form method="post">`). Never `hx-get` on a button that changes data.
- **State-changing actions never degrade to a GET link.** Principle 6 (progressive enhancement) means the no-JS fallback for logout, delete, and similar is a real `<form method="post">` with a submit button — **not** an `<a href="…">` to a mutating endpoint. A GET that mutates is a CSRF hole (`docs/SECURITY.md` §9), even as a "fallback".

CSRF defence for these is `SameSite=Lax` cookies plus the no-state-changing-GET rule — there are no CSRF tokens to thread through forms. See `docs/SECURITY.md` §9.

---

## 4. Template & Component Architecture

This is the part that keeps "lots of components" from becoming chaos. Jinja gives three reuse mechanisms; we use each for a distinct job. (Coming from .NET: `{% include %}` ≈ partial view, `{% macro %}` ≈ a parameterised Razor component / tag helper, `{% block %}` inheritance ≈ master page + sections.)

### The macro vs partial split

| Mechanism | Use for | Fetched directly by an endpoint? | Location |
|-----------|---------|----------------------------------|----------|
| **Macro** (`{% macro %}` + `{% import %}`) | Parameterised reusable atoms/molecules rendered *inside* a page: form field, button, status badge, card, empty-state, pagination, tree-node | No | `app/templates/_macros/*.html` |
| **Partial** (underscore-prefixed template) | A fragment that is an **HTMX swap target** — exactly what one endpoint returns over the wire | Yes — an endpoint renders it | `app/templates/<module>/_name.html` |
| **Block inheritance** (`{% extends %}` / `{% block %}`) | Page-level layout: the shell, slots for content | n/a | `app/templates/base.html` + page templates |

**The rule of thumb:** if a server endpoint returns it as an HTMX response, it is a **partial** (underscore-prefixed, per `docs/GLOSSARY.md` file-naming + `docs/ARCHITECTURE.md`). If it is a reusable building block invoked while rendering some other template, it is a **macro**. They compose: an endpoint renders `_requirement_row.html`, which calls the `badge()` macro inside it.

### Proposed directory layout

```
app/templates/
├── base.html                 # shell: extends-target for every full page
├── _macros/
│   ├── forms.html            # field(), submit_button(), error_text()
│   ├── ui.html               # badge(), card(), empty_state(), pagination()
│   └── tree.html             # tree_node() for the requirement hierarchy
├── auth/                     # login.html, register.html, _login_error.html …
├── projects/
├── documents/
├── nlp/
├── gherkin/
├── traceability/
└── admin/
```

### Component catalogue (build these as the modules need them — do not pre-build)

Atoms/molecules that recur and therefore belong in `_macros/`:

- **`field()`** — label-above-input, `aria-required`, slot for an inline error fragment, optional help text. (Forms rule §7.6.)
- **`submit_button()`** — disables itself in-flight (`hx-disabled-elt="this"`).
- **`badge(status)`** — status pill. Its values map **exactly** to the canonical states in `docs/GLOSSARY.md` / `docs/DATA_MODELS.md`: AC states (`not_covered`, `covered`, `test_passed`, `test_failed`), requirement type/status, project roles. Colour is always paired with a label or icon (§7.2).
- **`card()`**, **`empty_state(message, action)`**, **`pagination()`**, **`toast`** container, **`tree_node()`**.

### A Jinja gotcha to internalise (bites .NET developers)

`{% import "_macros/forms.html" as forms %}` does **not** carry the template context by default — a macro that uses `request`, the current user, or CSRF-ish data will silently receive nothing. When a macro needs request context, import **with context**:

```jinja
{% from "_macros/forms.html" import field with context %}
```

Razor passes ambient context implicitly; Jinja does not. This is the single most common surprise here.

### Hard template rules (authoritative — moved from `docs/GUIDE.md` Rule 9)

- All HTML templates live in `app/templates/<module>/` — never in the module's Python folder.
- Every full page extends `base.html`, which provides the shell, nav, footer, and the HTMX/Alpine scripts.
- Use HTMX attributes (`hx-get`, `hx-post`, `hx-target`, `hx-swap`) for server-driven dynamic interactions. Use Alpine.js (CSP build) for ephemeral client-side state only (show/hide password, toggles, disclosures, local tab switching) — anything where a server round-trip would be wasteful. No custom JavaScript unless neither HTMX nor Alpine can express the interaction **and** the developer approves the exception.
- Partials (HTML fragments for HTMX targets) use the underscore prefix: `_form.html`, `_list.html`, `_criteria.html`.
- Templates must NOT contain business logic — that stays in `service.py`.
- In the browser UI, auth tokens live in HTTP-only cookies set by the server — never in localStorage, sessionStorage, or JavaScript variables. API clients receive bearer tokens in the response body and manage them outside the browser. See `docs/SECURITY.md` §3 and §14.
- Static files (CSS, JS) go in `app/static/`. All assets are served locally — no CDN references.
- HTMX, PicoCSS, and Alpine.js (CSP build) are vendored under `app/static/vendor/<library>/<version>/`. Current pinned versions and SHA256 checksums live in `docs/TECH_STACK.md`. No build-time downloads, no CDN.
- Use PicoCSS semantic classes for all UI styling. Do not write custom CSS unless PicoCSS cannot achieve the required element (see §5 for the only sanctioned uses of `app.css`).
- Alpine usage is bounded by `docs/TECH_STACK.md` → Alpine.js Security Constraints: CSP build only; components registered via `Alpine.data('name', () => ({...}))` in `app/static/js/`; `x-*` attribute values static in templates (never interpolating user input); `x-html` forbidden on any user-derived content. See also the UI Design Checklist (§7).

---

## 5. Design Tokens

The UI Design Checklist (§7) mandates a token layer — a semantic palette, one type scale, one spacing scale, all as CSS custom properties. This is where it lives and how it coexists with the "PicoCSS only" rule.

### The sanctioned uses of `app/static/css/app.css`

Per `docs/TECH_STACK.md`, custom CSS is allowed only where PicoCSS cannot do the job. `app.css` contains exactly these — and nothing else:

1. **The semantic token layer.** PicoCSS is itself built on CSS custom properties (`--pico-*`). We define our semantic names (`--color-bg`, `--color-surface`, `--color-text`, `--color-text-muted`, `--color-border`, `--color-primary`, `--color-danger`, `--color-success`, `--color-warning`; the type scale; the 4-px spacing scale) and, where it makes sense, map them onto Pico's variables. Templates and any custom rules reference the semantic tokens, never raw hex.
2. **Layout-archetype primitives.** The layout primitives named in the §2 archetype catalogue — the chrome-less `.auth-layout` wrapper (Centred Form) and the rail / master / detail / inspector shell grid. PicoCSS provides neither a centred-form wrapper nor an application shell, so these genuinely "cannot be achieved" with Pico semantic classes — they are the sanctioned exception, not a loophole to write arbitrary CSS. **Only the primitives the §2 catalogue names are permitted**; any other layout rule is an escalation (§8).
3. **Security utility rules that cannot be inline.** A small, fixed set of rules required by `docs/SECURITY.md` that the CSP forbids inlining — specifically the honeypot hide rule (§11) and the HTMX `.htmx-indicator` styles (HTMX's auto-injected `<style>` is CSP-blocked). See §6 → Building within the CSP.

Anything beyond these is an escalation (§8): prefer a PicoCSS semantic element first.

### Density tuning

PurrfectReqs is data-dense; PicoCSS defaults to comfortable. Tune density in `app.css` by overriding Pico's own variables (font size, spacing, control padding) toward a compact professional-tool scale — do **not** fork or edit the vendored `pico.min.css`. Keep the type scale to the 5–6 steps and the spacing to the 4-px scale defined in §7.

### Dark mode

One ruleset, two palettes, swapped via `prefers-color-scheme` (§7.2). Define both palettes as token values; never branch colours in templates.

### Loading order

`base.html` loads `pico.min.css` first, then `app/static/css/app.css` (so our tokens/overrides win the cascade), then any Alpine registration JS via `<script src>` (never inline — `docs/TECH_STACK.md` Alpine constraints).

---

## 6. Security & Guardrails (pointers — these are governed elsewhere)

Frontend code is bound by these constraints. They are **not** restated here to avoid drift; this section is the index.

- **Autoescaping & user content** — Jinja autoescaping stays on; no `|safe` on user-controlled content; never build `hx-*`, `x-*`, URLs, or CSS classes from user input. `docs/TECH_STACK.md` → Browser UI Security Model.
- **Alpine CSP build** — CSP build only; static `x-*` attributes; `x-html` forbidden on user data; component registration in `app/static/js/`. `docs/TECH_STACK.md` → Alpine.js Security Constraints; `docs/SECURITY.md` §8.
- **CSP** — no `'unsafe-eval'`, no `'unsafe-inline'` in `script-src` or `style-src`. `docs/SECURITY.md` §8. See "Building within the CSP" below — it has real consequences for this stack.
- **CSRF / unsafe methods** — `SameSite=Lax` + no state-changing GET (incl. no GET-link fallbacks, §3). `docs/SECURITY.md` §9.
- **Auth tokens** — HTTP-only cookies for the browser; never localStorage/sessionStorage/JS. `docs/SECURITY.md` §3, §14.
- **Auth flows use content negotiation** — the browser/HTMX flow sends `Accept: text/html` and receives cookies + a 303 redirect; the API flow receives JSON tokens in the body. HTMX auth requests must ride the HTML flow — never request JSON, because tokens in a response body are unusable and unsafe in the browser. A post-login 303 should land as a full navigation or via an `HX-Redirect` response header, not a partial swap. `docs/SECURITY.md` §4, §14.
- **Enumeration-safe errors** — render the server's generic auth error (e.g. `INVALID_CREDENTIALS`) verbatim. Never add client-side hints that distinguish "no such user" from "wrong password". `docs/SECURITY.md` §13.
- **HTMX partial endpoints** enforce the same auth, RBAC, validation, and audit rules as full-page routes. `docs/TECH_STACK.md` → Browser UI Security Model.
- **Registration honeypot** — a hidden field on the register form, hidden via an `app.css` class (not an inline style — see CSP below), with `tabindex="-1"`, `aria-hidden="true"`, and `autocomplete="off"` so it never traps keyboard or screen-reader users. Server-side handling: `docs/SECURITY.md` §11.
- **UI validation is a usability hint only** — server-side validation is authoritative. `docs/TECH_STACK.md`.

### Building within the Content-Security-Policy

`docs/SECURITY.md` §8 sets a strict CSP — `script-src 'self'`, `style-src 'self'`, with **no** `'unsafe-inline'` and **no** `'unsafe-eval'`. That has concrete consequences for an HTMX + Alpine + Pico UI; build to them from day one:

- **No inline styles.** No `<style>` blocks and no `style="…"` attributes in templates — the browser blocks them. All styling goes through PicoCSS classes and `app/static/css/app.css`. (This is why the honeypot hides via a class, not `style="display:none"`.)
- **Disable HTMX's injected indicator styles.** HTMX adds a `<style>` block for `.htmx-indicator` by default, which the CSP blocks. Turn it off with a CSP-safe meta tag in `base.html` — `<meta name="htmx-config" content='{"includeIndicatorStyles":false}'>` — and define `.htmx-indicator` yourself in `app.css`. Without this, every `hx-indicator` (mandated by §7.4) renders unstyled.
- **No `hx-on`, no `js:` prefixes, no htmx expression/event filters.** These evaluate strings as code (`Function()`), which needs `'unsafe-eval'`. Use Alpine (CSP build) for client-side behavior instead. (`docs/TECH_STACK.md` already bans `js:` in `hx-headers`.)
- **No inline `<script>`.** Alpine components and any JS load from `app/static/js/` via `<script src>` only. Element-style mutations from Alpine (`x-show`, `x-bind:style`) are CSSOM operations and are *not* blocked by `style-src` — those are fine.
- **Same-origin only.** `connect-src 'self'`, `form-action 'self'`, `img-src 'self' data:` — HTMX requests, form posts, and images stay same-origin (no CDN, consistent with the vendoring rule).

---

## 7. UI Design Checklist (HTMX + Jinja2 + Alpine CSP)

This checklist applies to every server-rendered view and every HTMX partial. It is design-level guidance, not a substitute for `docs/SECURITY.md` or the template rules in §4.

### 7.1 Typography

- One type scale, defined as CSS custom properties. Five or six steps (e.g., 12 / 14 / 16 / 20 / 24 / 32 px). Do not use ad-hoc sizes.
- One body font, optionally one display font. No more.
- Line-height: 1.5 for body text, 1.2 for headings.
- Reading measure: 60–75 characters per line for prose blocks. Use a container max-width.
- Numeric data uses `font-variant-numeric: tabular-nums` so columns align.

### 7.2 Color

- Define a semantic palette, not raw hex in templates: `--color-bg`, `--color-surface`, `--color-text`, `--color-text-muted`, `--color-border`, `--color-primary`, `--color-danger`, `--color-success`, `--color-warning`. Template/CSS references go through the variables.
- Contrast: 4.5:1 for body text, 3:1 for large text and UI borders. Verify with a checker — do not eyeball.
- Dark mode via `prefers-color-scheme` swapping the CSS variables. One ruleset, two palettes.
- Color never carries meaning alone. Always pair with an icon or label (colorblind users, printouts, accessibility).

### 7.3 Spacing & layout

- Single 4-px spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64. No `margin: 13px`.
- CSS Grid for page layout, Flexbox for component internals. Do not nest flex containers to simulate grid.
- Reading content: container max-width ~720 px. Data tables and dashboards may go full width.

### 7.4 HTMX interaction patterns

- Every `hx-*` request has a visible loading indicator. Use `hx-indicator` — silent swaps over 200 ms are not acceptable.
- The server is authoritative. Optimistic UI only for trivial toggles where rollback is cheap.
- `hx-target` the smallest element that changes. Small swaps preserve focus and scroll; large swaps do not.
- Preserve focus and scroll across swaps: `hx-preserve` on inputs mid-edit where needed.
- Error swaps have a target too. Define where 4xx/5xx fragments render — do not let errors vanish.
- Debounce text inputs: `hx-trigger="keyup changed delay:300ms"` on search and autocomplete.
- Destructive actions use `hx-confirm` or a modal confirmation swap pattern.

### 7.5 Alpine.js usage patterns

- Use Alpine for ephemeral state: show/hide password, dropdown open state, disclosure panels, local tab state, input masking. Anything the server does not need to know about.
- Register components with `Alpine.data('componentName', () => ({ ... }))` in a file under `app/static/js/`. Reference by name in templates: `<div x-data="componentName">`. Inline logic in `x-data="{...}"` does not work under the CSP build — by design.
- `x-*` attribute values are static in Jinja templates. Never interpolate user input into `x-on`, `x-bind`, `x-init`, `x-effect`, `x-text`, `x-show`, or `x-data`. The attribute value is code, not text — Jinja autoescaping does not protect you.
- Prefer `x-text` over `x-html`. `x-html` is forbidden on any content derived from user input.
- Alpine re-initialises on DOM mutation, so HTMX-swapped fragments containing `x-*` attributes are evaluated as code on arrival. The static-attribute rule above is what keeps this safe.
- Do not duplicate state across HTMX and Alpine. If the server owns it, HTMX drives it; if the browser owns it, Alpine drives it. Fighting this boundary is the main source of bugs.

### 7.6 Forms

- Labels above inputs, not placeholder-as-label (placeholders vanish on focus and fail accessibility).
- Inline validation on `blur`, not on every keystroke. HTMX `hx-post` to a validation endpoint that returns only the error fragment.
- Required fields marked explicitly with text plus `aria-required`, not asterisk alone.
- Disable submit while the request is in flight: `hx-disabled-elt="this"`.
- Error messages next to the field; red plus icon plus text (not color alone).

### 7.7 Motion

- Use transitions only where they clarify a state change. Default 150–250 ms. `ease-out` for entering, `ease-in` for leaving.
- Consider the CSS View Transitions API for HTMX swaps to smooth fragment replacement. Browser support is adequate.
- Respect `prefers-reduced-motion` — wrap non-essential animations in the media query and disable them there.
- No idle motion. Spinners spin only while something is actually loading.

### 7.8 Feedback & status

- Toasts for transient success/error. Auto-dismiss 4–6 seconds. Rendered via `HX-Trigger` response header and a toast container listening for the event.
- Inline status for form submissions; toasts for background operations.
- Empty states explain what is missing and the next action ("No requirements yet. Create one →"). Never show a blank table.
- Destructive confirmations name the specific item, not "Are you sure?"

### 7.9 Accessibility baseline

- Semantic HTML first. `<button>` for actions, `<a>` for navigation. Do not `hx-get` on a `<div role="button">` when a real `<a>` or `<button>` fits.
- Every interactive element reachable by Tab with a visible focus ring. Do not `outline: none` without a replacement.
- ARIA live regions for dynamic content arriving without user action: `aria-live="polite"` for toasts, `aria-live="assertive"` for errors.
- Skip-to-content link at the top of every page.
- Keyboard-only traversal of at least one full user flow before considering a view complete.

### 7.10 Performance

- Keep CSS in the vendored PicoCSS file plus `app/static/css/app.css` (both external, so `style-src 'self'`-compatible). Do **not** inline critical CSS via `<style>` or `style="…"` — the CSP blocks inline styles (§6 → Building within the CSP). Keep `app.css` small so it parses fast as an external file.
- Images below the fold use `loading="lazy"`.
- HTMX fragments should be small. If a swap payload exceeds 50 KB you are probably swapping too much.
- Cache fragment endpoints with `Cache-Control` where the data allows (static lookup lists, enumerations).

### Pre-ship checklist (per view)

- [ ] Every interactive element has visible hover, focus, and active states
- [ ] Every HTMX request shows a loading indicator
- [ ] Every error path has a rendering target
- [ ] Keyboard-only traversal works end to end
- [ ] Contrast passes 4.5:1 for all text
- [ ] Works at 320 px width (mobile) and 1440 px (desktop)
- [ ] `prefers-reduced-motion` honored
- [ ] No color-only meaning
- [ ] No inline `<style>`/`style="…"` and no inline `<script>` (CSP)
- [ ] No Jinja expression interpolated into any `x-*` attribute
- [ ] No `x-html` on user-derived content

---

## 8. Escalation Triggers (frontend)

Stop and request confirmation before any of the following. These are the frontend-specific extensions of the project-wide rules in `CLAUDE.md` → Escalation Protocol and `docs/TECH_STACK.md` → Agent Enforcement Rules. Use the escalation format in `CLAUDE.md`.

- Bumping or adding a vendored frontend asset (HTMX, PicoCSS, Alpine) — version, file, checksum, and template references all change together. `docs/TECH_STACK.md`.
- Introducing custom JavaScript beyond Alpine (CSP build) component registration, or custom CSS beyond the sanctioned `app.css` uses (§5).
- Changing the app shell or the navigation model (§2, §3) — e.g. moving away from Option D or from `hx-boost`.
- Changing static-asset delivery, the CSP, or any security header. `docs/SECURITY.md` §8.
- Changing auth token delivery, CSRF behaviour, or cookie attributes. `docs/SECURITY.md` §3, §9, §14.
- Adding a new frontend environment variable, or any outbound request to a non-same-origin host.

---

## 9. Testing UI Acceptance Criteria

UI acceptance criteria are tested programmatically wherever they are machine-verifiable. This keeps UI ACs inside the same RED → GREEN discipline as backend ACs — a criterion checked only by eye is an unfalsifiable gate.

**A `.feature` file names the archetype; it never states pixel values.** It describes observable behaviour and the **layout archetype** (§2) the screen must conform to. The size/visual contract belongs to the **archetype** and the design tokens (§5) it references — not to the spec. Tests assert **conformance to the archetype's contract**, never a literal duplicated in the `.feature` or the test. A designer changing a token must not break a feature file.

```gherkin
# Wrong — implementation detail, brittle, not stakeholder-readable
Then the registration form has max-width 440px

# Right — observable behaviour + named archetype
When I open the registration page on a desktop-width screen
Then the registration form conforms to the Centred Form archetype
And the page is usable at mobile width with no horizontal scrolling
```

**Three buckets — sort every UI AC at spec-review time:**

| Bucket | Examples | How it is verified |
|--------|----------|--------------------|
| **Structural / contract** | every input has a label; chrome-less base used; honeypot hidden; correct archetype wrapper present | in-process via `TestClient` (fast) |
| **Rendered behaviour / size / interaction** | centred not full-bleed; works at 320 & 1440 px; HTMX swaps without full reload; error preserves entered input | a real browser via the approved browser-tier tool (see `docs/SCOPE.md`) |
| **Irreducibly aesthetic** | "looks professional", brand feel | explicit manual `[REVIEW]` — **never** a faked automated pass |

Buckets 1–2 become executable tests and follow the AC-state lifecycle (`not_covered → covered → test_passed`). Bucket 3 is recorded as manual verification (the §7 pre-ship checklist), not reported as `test_passed`. If a `.feature` leans entirely on bucket-3 criteria for behaviour that *should* be observable, that is a testability smell — escalate at spec review rather than write a green test that asserts nothing.

The BDD chain is preserved: `pytest-bdd` step definitions drive the browser-tier `page`, so `AC ← Scenario ← Step def ← Implementation` holds for UI exactly as it does for services.

**Where browser tests run.** On the macOS host (per `CLAUDE.md` → Testing Discipline — never inside a container), against a **uvicorn live-server fixture bound to the test database**, not the dev container or dev DB. This keeps the app and test sessions isolated (the same discipline as the rest of the suite) and gives each run a clean, known state. Browser binaries install once via `make playwright-install`; browser-tier tests carry `@pytest.mark.ui` and run with `make test-ui`.
