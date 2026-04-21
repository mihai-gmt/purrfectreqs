# Scope: Adversarial Review

## Question this scope answers

"What could break, and where is the plan naive?"

---

## Files to read

| File | Why |
|------|-----|
| The plan file | The artifact under review |
| The `.feature` file | The contract — check plan against it |
| `docs/SECURITY.md` | Security constraints that could be missed |
| `docs/ARCHITECTURE.md` | Module boundaries and structural invariants |
| `CLAUDE.md` | Loaded automatically — architectural invariants section |

**Do NOT read:** `docs/GUIDE.md`, `docs/DATA_MODELS.md`, the preplan analysis, or any code in `app/`.

---

## What to look for

Review the plan for these failure categories:

1. **Architecture violations** — Does any phase cross module boundaries without flagging it? Are there implicit imports between modules?
2. **Security gaps** — Missing auth on endpoints? Missing rate limiting where SECURITY.md requires it? Password/token handling that breaks rules?
3. **Coupling risks** — Does the plan create dependencies between modules that don't currently exist? Will this be hard to change later?
4. **Migration/data risks** — Could the Alembic migration fail on existing data? Is there a rollback path? Does the migration lock tables?
5. **Sequencing problems** — Are phases in the wrong order? Does Phase 3 depend on something Phase 4 creates?
6. **Scope creep triggers** — Does the plan include work not covered by the `.feature` file? Are there "while we're here" additions?
7. **Missing error conditions** — Does the `.feature` file imply error scenarios the plan doesn't address?
8. **Constraint violations** — Does the plan contradict any CLAUDE.md architectural invariant?

---

## How to present findings

```
ADVERSARIAL REVIEW: [feature name]

Findings:

1. [RISK LEVEL: HIGH/MEDIUM/LOW] [Category from list above]
   What: [specific issue]
   Why it matters: [concrete consequence]
   Impacted phase: [which phase number]
   Suggested fix: [specific change to the plan]

2. ...

Plan changes required: [Yes — list which sections / No — plan holds up]

Approve these changes? (I will update the plan after your confirmation)
```

If no issues found (rare — be skeptical):
```
ADVERSARIAL REVIEW: [feature name]

No significant risks identified. The plan aligns with architectural invariants,
security requirements, and feature scope.

Recommend proceeding to next iteration scope or freeze.
```

---

## What changes this scope can propose

- Add missing security considerations to Section 6
- Reorder phases in Section 10
- Add missing error conditions to Section 11
- Flag scope issues in Section 12
- Add risk notes to any affected section
- Flag cross-module escalation triggers

## Escalation protocol

If any finding maps to a CLAUDE.md escalation trigger (cross-module change, auth flow change, new dependency, `app/core/*` modification, new env var, core invariant affected, MVP scope conflict), present it using the CLAUDE.md escalation format — not the adversarial finding format:

```
ESCALATION REQUIRED

Trigger: [which CLAUDE.md trigger]
Context: [what the plan proposes]
Issue: [why this requires developer confirmation]
Options: [what the choices are]
Recommendation: [if any]

Waiting for confirmation before proceeding.
```

Standard findings (risks, gaps, sequencing issues) that don't hit an escalation trigger use the adversarial finding format as normal.

## What this scope must NOT do

- Rewrite the implementation approach
- Add new endpoints or features
- Modify test scenarios (Section 8)
- Change the file manifest (Section 14) — that follows from other changes
