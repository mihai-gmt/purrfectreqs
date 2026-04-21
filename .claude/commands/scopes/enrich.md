# Scope: Enrich

## Question this scope answers

"Is the plan detailed enough for the test writer and implementer to execute without guessing?"

---

## Files to read

| File | Why |
|------|-----|
| The plan file | The artifact under review |
| The `.feature` file | The contract — verify plan covers all scenarios |
| `docs/DATA_MODELS.md` | Verify DB schema details are correct and complete |
| `docs/GUIDE.md` | Verify plan references correct patterns |

**Do NOT read:** `docs/SECURITY.md`, `docs/ARCHITECTURE.md`, the preplan analysis, or any code in `app/`.

---

## What to look for

Check each plan section for completeness — not correctness (that's adversarial's job), but whether downstream agents have enough information.

1. **Section 3 (API Endpoints)** — Are all endpoints listed with method, path, auth, role? Would the implementer know exactly what to wire up?
2. **Section 4 (Database Changes)** — Are column names, types, constraints, and defaults specified? Or does it say "add necessary fields" (too vague)?
3. **Section 5 (Module Breakdown)** — For each file, is it clear what functions/classes are added or modified? Vague entries like "add service logic" are not actionable.
4. **Section 8 (Test Scenarios)** — Does every `.feature` scenario have an entry? Are fixtures and expected HTTP statuses specified?
5. **Section 10 (Implementation Order)** — Are phases specific enough? "Implement service" is not a phase — "Add create_project() to service.py with validation and audit logging" is.
6. **Section 11 (Edge Cases)** — Are error codes and HTTP statuses specified for each condition? Do they match the `.feature` file's error scenarios?
7. **Section 14 (File Manifest)** — Are all files to create/modify listed? Would the agents know exactly which files to touch without exploring?

---

## How to present findings

```
ENRICHMENT REVIEW: [feature name]

Sections needing more detail:

Section [N]: [name]
  Gap: [what's missing or vague]
  Suggested addition: [specific text to add]

Section [N]: ...

Sections that are complete: [list section numbers]

Proposed plan changes:
  1. [specific change]
  2. ...

Approve these changes?
```

If all sections are sufficiently detailed:
```
ENRICHMENT REVIEW: [feature name]

All sections contain sufficient detail for downstream agents.
No changes needed. Recommend proceeding to freeze.
```

---

## What changes this scope can propose

- Add missing detail to any plan section (specifics, not prose)
- Fill in vague entries with concrete values
- Flag missing `.feature` scenarios in Section 8 — do not fill in the details, trigger escalation protocol (plan phase produced an incomplete Section 8, developer must resolve)
- Complete the file manifest in Section 14
- Add missing error conditions to Section 11

## Escalation protocol

Enrichment can surface details that reveal CLAUDE.md escalation triggers the draft plan was too vague to expose. If enriching a section reveals any of the following, stop and escalate using the CLAUDE.md format before adding the detail:

- Section 3 (Endpoints): enrichment reveals the plan implies changes to authentication or authorization flows (trigger: auth/authz flow would change)
- Section 4 (Database): enrichment reveals schema changes to tables owned by another module (trigger: schema outside Feature Box must change)
- Section 5 (Module Breakdown): enrichment reveals functions or classes in `app/core/*` must be added or modified (trigger: modifying `app/core/*`)
- Section 14 (File Manifest): enrichment reveals files outside the Feature Box must be touched (trigger: task touches more than one module)
- Any section: enrichment reveals the plan needs a library not in `docs/SCOPE.md` approved dependencies (trigger: new dependency required)

```
ESCALATION REQUIRED

Trigger: [which CLAUDE.md trigger]
Context: [which section was being enriched and what was discovered]
Issue: [why this requires developer confirmation]
Options: [what the choices are]
Recommendation: [if any]

Waiting for confirmation before proceeding.
```

## What this scope must NOT do

- Change the implementation approach
- Add new features or endpoints not in the `.feature` file
- Modify security considerations
- Reorder phases
- Second-guess architectural decisions
