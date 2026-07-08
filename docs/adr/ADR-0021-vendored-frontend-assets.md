---
id: ADR-0021
title: Vendor frontend assets into git with version paths and SHA256 checksums
status: accepted
date: 2026-04-21
backfilled: true
deciders: [mihai]
tags: [supply-chain, frontend, security]

supersedes: []
superseded_by: null
depends_on: [ADR-0020]
related_to: [ADR-0013]
affects_modules: [app/static]
governed_by: [docs/TECH_STACK.md]
rejected_alternatives: [cdn-at-build-time, pinned-url-checksum]
---

# ADR-0021: Vendor frontend assets into git with version paths and SHA256 checksums

## Context

HTMX and PicoCSS were being pulled from `unpkg.com` at Docker build time with
no version pin and no checksum — a direct violation of the policy
TECH_STACK.md was being expanded to state (journal 2026-04-21).

## Decision

Frontend assets (HTMX, PicoCSS, Alpine.js CSP build) are vendored into the
repository under `app/static/vendor/<library>/<version>/` and committed to
git. TECH_STACK.md records each pinned version and SHA256. No CDN references,
no build-time downloads, no npm — the Docker build simply `COPY`s the repo.
Bumping a vendored asset is an escalation trigger: file, version folder,
checksum table, and template references change together.

## Rationale

From the journal: "Vendoring is not pessimism; it is refusal to depend on the
upstream's uptime." Every build-time fetch bets that a third party serves the
expected bytes at the expected URL. The project is offline-first by design,
the files total ~70KB, and vendoring drops the build-time network surface to
zero.

## Consequences

### Positive

- Deterministic builds with no network; checksums make tampering detectable;
  same-origin serving satisfies the strict CSP.

### Negative

- Version bumps are manual, multi-touch operations (by design — that is the
  escalation).
- Binary-ish minified blobs live in git history.

## Alternatives considered

### cdn-at-build-time

The prior state (curl from unpkg in the Dockerfile): unpinned, checksum-free,
and network-dependent at every build. Strictly worse on all three axes.

### pinned-url-checksum

Pinned URL + checksum verification at build time was TECH_STACK-approved but
rejected: it still requires a network call at every Docker build — an
avoidable failure mode when the files are this small.
