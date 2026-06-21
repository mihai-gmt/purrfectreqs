# 05 — Add Context-Routing Instructions to Prompts

## Purpose

Make each Pi prompt tell the agent which docs and files to read for that phase.

## Why this matters

Good context routing prevents both context bloat and missing required constraints.

## Recommended strategy

Use prompt-only context routing first. Do not build a custom context-router tool yet.

## Routing matrix

### `/preplan`

Read:

- `CLAUDE.md`
- target `.feature`
- `docs/SCOPE.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODELS.md` if API/data work
- `docs/SECURITY.md`
- `docs/FRONTEND.md` if UI work
- `docs/GLOSSARY.md`

### `/plan`

Read:

- `CLAUDE.md`
- target `.feature`
- preplan analysis
- relevant docs from `/preplan`

Do not read implementation files unless the workflow explicitly allows it.

### `/iterate`

Read:

- frozen/draft plan
- relevant scope file:
  - adversarial
  - enrich
  - testability
  - freeze
- target `.feature`

### `/write-tests`

Read:

- `CLAUDE.md`
- target `.feature`
- frozen plan
- Section 14 files approved for test writing
- relevant testing guidance

Do not read or write implementation files unless listed as read-only context.

### `/implement`

Read:

- `CLAUDE.md`
- target `.feature`
- frozen plan
- Section 14 implementation files
- relevant docs only:
  - `docs/GUIDE.md`
  - `docs/SECURITY.md`
  - `docs/DATA_MODELS.md` if DB work
  - `docs/FRONTEND.md` if UI work

### `/review`

Read:

- `CLAUDE.md`
- target `.feature`
- frozen plan
- changed files
- `docs/SECURITY.md`
- `docs/GUIDE.md`
- `docs/ARCHITECTURE.md`

Write only review artifact.

## Validation

- Prompts do not instruct reading all docs every time.
- Prompts explain why each doc is needed.
- Implementation prompt emphasizes Section 14.
- Review prompt remains read-only except review artifact.

## Stop conditions

Stop if context routing conflicts with `CLAUDE.md` mandatory pre-task steps or feature-file authority.
