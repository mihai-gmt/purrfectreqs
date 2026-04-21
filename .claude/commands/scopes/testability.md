# Scope: Testability Validation

## Question this scope answers

"Can each phase be driven by tests, and do we know what those tests are trying to prove?"

---

## Files to read

| File | Why |
|------|-----|
| The plan file | The artifact under review |
| The `.feature` file | The contract — scenarios define test targets |
| The preplan analysis file | Existing test patterns and fixtures |
| `tests/bdd/conftest.py` | Available fixtures — avoid duplicating what exists |

**Do NOT read:** `docs/SECURITY.md`, `docs/ARCHITECTURE.md`, `docs/GUIDE.md`, or any code in `app/`.

---

## What to look for

For each phase in Section 10 (Implementation Order):

1. **Test signal** — What specific test proves this phase works? If you can't name it, the phase is underspecified.
2. **Scenario coverage** — Which `.feature` scenarios exercise this phase? Are any phases not covered by any scenario?
3. **Fixture requirements** — What test fixtures does this phase need? Do they exist in `conftest.py` or must they be created?
4. **Integration boundaries** — Where does this phase interact with external dependencies (DB, Redis, Ollama)? How will tests handle those boundaries?
5. **Hard-to-test areas** — Are there parts of the plan that will be difficult to test in isolation? Flag them.
6. **Red-green feasibility** — Can the test writer write a failing test for this phase before implementation exists? A phase is too large if it requires more than 2-3 files to exist before any test can assert against it, or if no single `.feature` scenario exercises it in isolation. If a phase is too large because it crosses module boundaries, this is an escalation trigger — the `.feature` file scope needs to be sliced smaller by the developer.
7. **Preconditions** — What must be true in the test database/environment before each scenario runs?

---

## How to present findings

```
TESTABILITY REVIEW: [feature name]

Phase-by-phase assessment:

Phase 1: [name]
  Test signal: [what test proves this works]
  Scenarios: [which .feature scenarios]
  Fixtures needed: [list — note if new or existing]
  Issue: [any problem, or "None"]

Phase 2: ...

Overall assessment:
  Untestable phases: [list or "None"]
  Missing fixtures: [list or "None"]
  Phases too large for red-green: [list or "None"]
  Suggested test environment requirements: [list or "None"]

Proposed plan changes:
  1. [specific change]
  2. ...

Approve these changes?
```

---

## What changes this scope can propose

- Add "test signal" annotations to phases in Section 10
- Split phases that are too large for red-green cycle
- Add fixture requirements to Section 8 (Test Scenarios Breakdown)
- Flag missing preconditions in Section 8
- Add test environment notes to Section 9 (Success Criteria)

## Escalation protocol

If testability analysis reveals any CLAUDE.md escalation trigger, stop the review and escalate using the CLAUDE.md format before continuing. Common triggers from this scope:

- A phase crosses module boundaries and cannot be tested in isolation (trigger: task touches more than one module)
- Fixture requirements imply a library not in `docs/SCOPE.md` approved dependencies (trigger: new dependency required)
- A phase requires changes to `app/core/*` for shared test infrastructure (trigger: modifying `app/core/*`)

```
ESCALATION REQUIRED

Trigger: [which CLAUDE.md trigger]
Context: [which phase and what testability issue surfaced it]
Issue: [why this requires developer confirmation]
Options: [what the choices are]
Recommendation: [if any]

Waiting for confirmation before proceeding.
```

## What this scope must NOT do

- Write actual test code
- Propose new scenarios not in the `.feature` file
- Change the implementation approach
- Modify security or architecture sections
