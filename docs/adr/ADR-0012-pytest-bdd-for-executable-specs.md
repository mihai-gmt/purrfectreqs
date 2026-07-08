---
id: ADR-0012
title: pytest-bdd with .feature files as the executable specification
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [testing, process, dependencies]

supersedes: []
superseded_by: null
depends_on: []
related_to: []
affects_modules: [tests/bdd]
governed_by: [CLAUDE.md, docs/TECH_STACK.md, docs/GUIDE.md]
rejected_alternatives: [behave, cucumber]
---

# ADR-0012: pytest-bdd with .feature files as the executable specification

## Context

The project enforces BDD/TDD: the developer writes Gherkin `.feature` files
before any code, and those files are the contract the implementation must
satisfy. The BDD runner must integrate with the rest of the Python test stack
rather than exist beside it.

## Decision

`pytest-bdd` connects `.feature` files to Python step definitions, running
inside the ordinary pytest suite. `.feature` files are the sole source of
truth for feature behaviour: tests are written from them (RED), then the
minimum implementation makes them pass (GREEN). Agents must never modify a
`.feature` file to make tests pass. `gherkin-official` validates Gherkin
syntax at application runtime (the product itself manages Gherkin ACs).

## Rationale

pytest-bdd was "chosen over `behave` for native pytest integration and Python
3.12 support" (`docs/TECH_STACK.md`, Testing): one runner, one fixture model,
one command (`make test`) for BDD, unit, and integration tests.

## Consequences

### Positive

- BDD scenarios share pytest fixtures, plugins, and reporting with all other
  tests; no second test runner to maintain.
- The `.feature` authority rule gives specs teeth (`CLAUDE.md`, .feature File
  Authority).

### Negative

- pytest-bdd's step-binding style is less known than Cucumber's; step
  definitions live per test module rather than in a global registry.

## Alternatives considered

### behave

BDD runner without native pytest integration; would require a separate test
run and duplicate fixtures.

### cucumber

JVM/Node ecosystem; incompatible with a Python-native test stack.
