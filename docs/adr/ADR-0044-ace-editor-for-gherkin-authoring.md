---
id: ADR-0044
title: Ace is the Gherkin editing surface; CodeMirror 6 and ProseMirror are refused
status: accepted
date: 2026-08-28
backfilled: false
deciders: [mihai]
tags: [frontend, dependencies, security, csp]

supersedes: []
superseded_by: null
depends_on: [ADR-0021, ADR-0038]
related_to: [ADR-0041, ADR-0043]
affects_modules: [app/static, app/templates]
governed_by: [docs/SCOPE.md, docs/TECH_STACK.md, docs/FRONTEND.md]
rejected_alternatives: [codemirror-5, codemirror-6-with-csp-nonce, prosemirror, textarea-only]
---

# ADR-0044: Ace is the Gherkin editing surface; CodeMirror 6 and ProseMirror are refused

## Context

ADR-0041 made a Gherkin scenario a separate artifact, and ADR-0043 made writing
one an MVP user action. A plain `<textarea>` is a poor surface for Gherkin: no
keyword colour, no line number for an error to point at, and no indent
discipline. The shell prototype answers this with a deep-edit state that holds
an editor island, but no editor was an approved dependency.

Two rules constrain the choice. ADR-0021 requires a vendored asset with no build
step, no npm, and no CDN. ADR-0038 sets `script-src 'self'` and `style-src
'self'` with neither `'unsafe-inline'` nor `'unsafe-eval'`. Four candidates were
checked against the published distributions on 2026-08-28.

## Decision

Ace (`ace-builds`, version 1.44.0) is the Gherkin editing surface. Four files are
vendored: the `src-min-noconflict` core, the Gherkin mode, the TextMate theme,
and `css/ace.css`. `ace.config.set("useStrictCSP", true)` is mandatory before the
first `ace.edit(...)` call, and the stylesheet loads through a `<link>`. Ace is
the only custom-JavaScript island permitted beyond Alpine CSP component
registration. No language worker is enabled; Gherkin validation stays
server-side through `gherkin-official`.

## Rationale

Ace is the only candidate that passes both rules while it is still maintained.
It ships prebuilt and minified with no npm dependencies, so nothing is bundled.
It contains no `eval` and no `Function` constructor. It writes a `<style>`
element in exactly one place, and `useStrictCSP` turns that off, with the same
rules supplied as a file the page can link. The Gherkin mode ships in the package
and has no worker, so the Blob-worker question never arises.

CodeMirror 5 also passes, and it is safe by default rather than by
configuration, which is the stronger property. It was refused because its
upstream is in maintenance only, and the deep-edit surface is expected to
outlive that. The configuration risk is answered by the mandatory rule in
`docs/TECH_STACK.md` and by the ADR itself, not by hope.

## Consequences

### Positive

- No build step, no npm, no bundler. The vendoring rule stays intact.
- `docs/SECURITY.md` §8 is unchanged. No CSP nonce, no middleware change.
- The Gherkin mode and the theme are upstream artifacts, so each vendored file's
  SHA256 can be re-derived from the published package.

### Negative

- A missing `useStrictCSP` fails silently: the editor renders with no gutter and
  no cursor, and nothing throws. This must be covered by a browser-tier test.
- The wire cost is about 135 KB gzipped on the deep-edit view only.
- Ace's API predates ES modules, so the island file is plain script, not a module.

## Alternatives considered

### codemirror-5

CodeMirror 5.65.21 passes every rule and is CSP-safe with no flag. It was refused
because its upstream ships security fixes only, so adopting it accepts a known
future migration.

### codemirror-6-with-csp-nonce

CodeMirror 6 was rejected on two counts. It publishes only ESM and CJS packages,
so a single browser file needs a bundler, which ADR-0021 removed. And its
`style-mod` dependency creates a `<style>` element at runtime; avoiding the CSP
block needs a per-request nonce, which turns `docs/SECURITY.md` §8 from a
constant header into middleware state.

### prosemirror

ProseMirror edits structured rich text on `contenteditable`. It has no language
mode and no Gherkin support, so the syntax colour, the gutter, and the indent
rules would all be ours to write. It also ships ESM only across four packages.
Rejected on fit before the CSP question was reached.

### textarea-only

A plain `<textarea>` with server-side validation needs no dependency at all. It
was rejected because ADR-0043 made scenario authoring a first-class MVP action,
and an unaided textarea makes that action unpleasant for the one artifact the
product exists to get right.
