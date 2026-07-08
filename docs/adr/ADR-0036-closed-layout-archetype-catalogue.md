---
id: ADR-0036
title: Closed catalogue of five layout archetypes; every screen is assigned one
status: accepted
date: 2026-06-14
backfilled: true
deciders: [mihai]
tags: [frontend, ux, governance]

supersedes: []
superseded_by: null
depends_on: [ADR-0035]
related_to: []
affects_modules: [app/templates, app/static]
governed_by: [docs/FRONTEND.md]
rejected_alternatives: [per-screen-layout]
---

# ADR-0036: Closed catalogue of five layout archetypes; every screen is assigned one

## Context

With specs written by the developer and screens implemented by agents,
per-screen layout invention would produce drift: every new view a fresh
negotiation about width, structure, and responsive collapse.

## Decision

Five page-level archetypes form a closed catalogue (`docs/FRONTEND.md` §2):
Centred Form, Master-Detail, Master-Detail + Inspector, Full-width Data, and
Reading/Content. Each declares shell presence, width, responsive collapse,
and its sanctioned `app.css` primitive. A spec names the archetype; the
implementer applies it. Adding a sixth archetype is an escalation, not a
default. Width follows the content's job — never a blanket setting.

## Rationale

A closed set turns layout from a per-screen judgment call into a lookup,
which is what makes UI specs terse and implementations consistent. The
catalogue is also what UI acceptance criteria anchor to (see the UI-AC
testing ADR): a `.feature` can say "conforms to the Centred Form archetype"
precisely because the archetype, not the spec, owns the size contract.

## Consequences

### Positive

- Layout consistency by construction; specs reference archetypes instead of
  pixels; custom layout CSS is bounded to named primitives.

### Negative

- A genuinely novel screen must go through escalation to extend the
  catalogue — deliberate friction.

## Alternatives considered

### per-screen-layout

Letting each spec/implementation define its own layout was rejected: it
reopens every width/structure decision per screen and makes UI ACs
untestable against anything stable.
