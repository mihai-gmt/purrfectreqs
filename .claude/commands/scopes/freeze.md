# Scope: Freeze

## Question this scope answers

"Is this plan complete, consistent, and ready for test writing and implementation?"

---

## Files to read

| File | Why |
|------|-----|
| The plan file | The artifact to validate and freeze |
| The `.feature` file | Verify plan covers all scenarios |

**Do NOT read:** Any other docs, the preplan analysis, or any code. The plan should stand on its own at this point.

---

## What to check

This is a completeness and consistency check, not a review. Do not propose new content — only flag missing or contradictory content.

### Iteration check

All three non-freeze scopes must have been run. Check Section 15 (Changelog) for entries from each:

- [ ] `adversarial` — at least one changelog entry
- [ ] `enrich` — at least one changelog entry
- [ ] `testability` — at least one changelog entry

If any scope is missing, block the freeze:
```
FREEZE BLOCKED: Required iteration scopes not completed.

Missing scopes: [list missing]
Completed scopes: [list completed]

Run the missing scopes before freezing:
  /iterate tests/features/<module>/<feature_name>.feature <missing_scope>

Recommended order: adversarial -> enrich -> testability -> freeze
```

### Completeness checklist

- [ ] Section 1 (Feature Summary) — present and specific
- [ ] Section 2 (Scope Confirmation) — feature type, MVP, scenario count filled
- [ ] Section 3 (API Endpoints) — all endpoints listed with method/path/auth/role (or 3b for UI)
- [ ] Section 4 (Database Changes) — explicit Yes/No, migration described if needed
- [ ] Section 5 (Module Breakdown) — every file has specific functions/classes listed
- [ ] Section 6 (Security Considerations) — all questions answered
- [ ] Section 7 (Audit Logging) — actions listed or explicitly "None"
- [ ] Section 8 (Test Scenarios) — every `.feature` scenario has an entry
- [ ] Section 9 (Success Criteria) — automated and manual checks listed
- [ ] Section 10 (Implementation Order) — phases are specific and ordered
- [ ] Section 11 (Edge Cases) — error conditions with HTTP status and error_code
- [ ] Section 12 (Out of Scope) — at least one entry or explicit "Nothing excluded"
- [ ] Section 13 (Codebase Analysis Reference) — links to analysis doc
- [ ] Section 14 (File Manifest) — all four subsections filled
- [ ] Section 15 (Changelog) — has at least the draft entry

### Escalation trigger scan

Before checking consistency, verify the plan does not contain unacknowledged escalation triggers. For each phase in Section 10 and each file in Section 14, check:

- [ ] No phase touches more than one module (or an escalation was acknowledged in the changelog)
- [ ] No phase modifies `app/core/*` (or acknowledged)
- [ ] No phase changes authentication or authorization flows (or acknowledged)
- [ ] No phase requires a schema change outside the Feature Box (or acknowledged)
- [ ] No phase implies a new dependency not in `docs/SCOPE.md` (or acknowledged)
- [ ] No phase requires a new environment variable (or acknowledged)

"Acknowledged" means the changelog contains an escalation entry from a prior `/iterate` scope where the developer confirmed the trigger.

If any unacknowledged trigger is found, block the freeze:
```
FREEZE BLOCKED: Unacknowledged escalation trigger(s)

1. [Trigger]: [specific detail — which phase, which file]
   ...

Run /iterate with the appropriate scope to surface and resolve these,
or acknowledge them manually in the changelog before re-freezing.
```

### Consistency checks

- Every endpoint in Section 3 appears in a phase in Section 10
- Every `.feature` scenario appears in Section 8
- Every file in Section 5 appears in Section 14
- Phases in Section 10 are in a feasible order (no forward dependencies)
- Error conditions in Section 11 match error scenarios in the `.feature` file
- Security requirements in Section 6 are reflected in the implementation phases

---

## How to present findings

If all checks pass:
```
FREEZE VALIDATION: [feature name]

All completeness checks: PASS
All consistency checks: PASS

Freezing plan. Status updated to FROZEN.

Next steps:
  1. Clear context
  2. Run: /write-tests tests/features/<module>/<feature_name>.feature
```

If checks fail:
```
FREEZE VALIDATION: [feature name]

Failed checks:

1. [COMPLETENESS/CONSISTENCY] [specific issue]
   Section: [which section]
   What's missing: [specific gap]

Plan NOT frozen. Fix the issues above, then run freeze again.
Options:
  - /iterate ... enrich (if detail is missing)
  - /iterate ... adversarial (if consistency issues suggest deeper problems)
  - Fix manually and re-run /iterate ... freeze
```

---

## What this scope does on success

1. Change the Status field from `DRAFT` to `FROZEN`
2. Append a changelog entry: `| <date> | freeze | — | Plan frozen for implementation |`
3. Report ready for `/write-tests`

## What this scope must NOT do

- Add new content to the plan
- Propose implementation changes
- Rewrite any section
- Skip failed checks to force a freeze
