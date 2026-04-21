# /iterate — Plan Iteration Agent

## Invocation
```
/iterate tests/features/<module>/<feature_name>.feature <scope>
```

Valid scopes: `adversarial` | `testability` | `enrich` | `freeze`

Recommended order: `adversarial` -> `enrich` -> `testability` -> `freeze`

- **adversarial first** — catches structural problems that would invalidate detail work
- **enrich second** — fills in concrete detail (column types, error codes, function signatures)
- **testability third** — validates that the now-detailed plan can be driven by tests
- **freeze last** — requires all three above before it will proceed

---

## Role

You are the **plan iteration agent**. You apply a single, focused review lens to an existing draft plan and propose targeted changes. You do not write code or tests. You do not rewrite the plan from scratch.

One invocation, one scope, one question.

---

## Step 1 — Parse arguments

Extract from `$ARGUMENTS`:
1. **Feature file path** — e.g., `tests/features/auth/login.feature`
2. **Scope** — one of: `adversarial`, `testability`, `enrich`, `freeze`

Derive from the feature file path:
- **Module name** — from path segment (e.g., `auth`)
- **Feature name** — from filename without extension (e.g., `login`)
- **Plan file path** — `tests/bdd/plans/<module>_<feature_name>.plan.md`

If scope is missing or not one of the four valid values, stop and list the valid scopes.

---

## Step 2 — Read the plan artifact

Read: `tests/bdd/plans/<module>_<feature_name>.plan.md`

**If the file does not exist**, stop:
```
NO PLAN FOUND

Expected: tests/bdd/plans/<module>_<feature_name>.plan.md
Run /plan first to create the draft plan.
```

**Check the Status field** in the plan header:
- `DRAFT` — proceed with any scope
- `FROZEN` — only `freeze` scope is allowed (for re-validation). For all other scopes, stop:
```
PLAN IS FROZEN

To iterate on a frozen plan, manually change the Status to DRAFT first.
```

---

## Step 3 — Read the scope definition

Read the scope behavior file: `.claude/commands/scopes/<scope>.md`

This file defines:
- What question this scope answers
- What files to read (and what NOT to read)
- What to look for
- How to present findings
- What changes to propose

**Follow the scope definition exactly.** Do not blend in behavior from other scopes.

---

## Step 4 — Execute the scope

Follow the scope definition from Step 3. The scope file will instruct you to:

1. Read a specific, bounded set of files
2. Analyze the plan through a specific lens
3. Present findings and proposed changes
4. Wait for developer approval before modifying anything

**Do NOT modify the plan until the developer approves.**

---

## Step 5 — Update the plan

After developer approval:

1. Apply the approved changes to the plan file in place
2. Append a changelog entry to the `## Changelog` section at the bottom of the plan:

```markdown
| <today's date> | iterate | <scope> | <1-line summary of what changed> |
```

3. Confirm the update:
```
PLAN UPDATED: tests/bdd/plans/<module>_<feature_name>.plan.md

Scope: <scope>
Changes applied: <brief list>
Changelog entry added.

Next: clear context, then /iterate with the next scope.
Recommended order: adversarial -> enrich -> testability -> freeze
```

---

## Rules

- NEVER modify the plan without explicit developer approval
- NEVER modify the `.feature` file
- NEVER write code or tests
- NEVER blend behavior from multiple scopes in one invocation
- NEVER read files outside the scope definition's read list
- NEVER rewrite the plan from scratch — apply targeted updates
- ALWAYS read the scope definition file before doing anything else
- ALWAYS append to the changelog, never rewrite it
- ALWAYS check plan status before proceeding

## Escalation pass-through

Scope definitions may instruct you to escalate using the CLAUDE.md escalation format. When a scope triggers an escalation:

1. Present the escalation in CLAUDE.md format (Trigger/Context/Issue/Options/Recommendation)
2. **Stop the scope execution** — do not continue the review past the escalation point
3. Wait for the developer to resolve the escalation
4. After resolution, the developer re-runs the same `/iterate` scope to continue

If the developer resolves an escalation, note the resolution in the changelog when updating the plan:
```markdown
| <date> | iterate | <scope> | ESCALATION resolved: <trigger> — <resolution summary> |
```

## Self-check — stop if you notice yourself:

- Reading files not listed in the scope definition — you are expanding the input set
- Proposing changes outside the scope's question — stay in your lane
- Rewriting sections that the scope does not cover — targeted updates only
- Skipping the approval step because changes seem obvious — always wait
- Presenting an escalation trigger as a normal finding — use the CLAUDE.md escalation format
