# Governance Implementation Assessment

Reviewed current Pi governance implementation against:

```text
.pi/_wip/governance-improvement-plan.md
.pi/_wip/governance-future-improvements-plan.md
```

Files reviewed:

```text
.pi/extensions/governance.ts
.pi/governance/config.ts
.pi/governance/engine.ts
```

## Summary

Implementation is broadly aligned and most planned behavior is present. Main discrepancies are around:

1. app-agnostic configurability still being partial
2. manual RED/GREEN attestations still being agent-callable
3. phase-entry gates not enforced on `/phase set`
4. some docs/comments stale after file move
5. bash write parsing can over-block or miss nuanced shell cases

---

## Issues / discrepancies

### 1. `createGovernanceEngine(config)` is effectively overwritten on every tool call

Current behavior:

```ts
export function createGovernanceEngine(config: GovernanceConfig = CONFIG) {
  governanceConfig = config;
  ...
  governanceConfig = loadHarnessConfig(cwd);
}
```

Problem:

- If another project calls `createGovernanceEngine(customConfig)`, the first `tool_call` resets config to `loadHarnessConfig(cwd)`.
- If no `.pi/harness.config.json` exists, that returns default PurrfectReqs `CONFIG`, not the passed custom config.

Conflicts with:

- Phase 9: “same engine can load different configs”
- Future Improvement 3: “Refactor `createGovernanceEngine(config = CONFIG)`”

Severity: **Medium**

Suggested fix:

- Store the engine default config in a closure.
- Change loader to merge JSON over the engine default config, not always over global `CONFIG`.

---

### 2. Config JSON support is partial

The future plan says JSON config may include:

```json
{
  "sourceRoots": [],
  "testRoots": [],
  "featurePatterns": [],
  "planDir": "",
  "coreDirs": [],
  "migrationDirs": [],
  "dependencyFiles": []
}
```

Current loader meaningfully supports only:

```ts
appRoot
coreDir / coreDirs[0]
authDirs
migrationsDir / migrationDirs[0]
featureBoxPath
authorityDocs
bannedDeps
```

Ignored or not wired:

- `testRoots`
- `featurePatterns`
- `planDir`
- `dependencyFiles`

Conflicts with:

- Future Improvement 3 optional fields
- Phase 9 “Keep path classifiers configurable”

Severity: **Medium**

Suggested fix:

- Extend `CONFIG` shape with explicit classifier fields such as `planDir`, `testDirs`, `docsDir`, `featureDirs`, and dependency file globs/patterns.
- Wire these into `classifyPath()` and config matching.

---

### 3. PurrfectReqs paths still hardcoded in engine

Examples in `engine.ts`:

```ts
tests/bdd/plans
tests/bdd/step_defs
tests/unit
docs/
```

These are still embedded in `classifyPath()` and review/phase rules.

Conflicts with:

- Phase 9: “Keep hardcoded PurrfectReqs values only in CONFIG”
- Phase 9: “Keep path classifiers configurable”

Severity: **Medium**

Suggested fix:

- Move plan, review, analysis, test, docs path definitions into `config.ts`.
- Have `classifyPath()` use config values rather than literal paths.

---

### 4. Manual `/box mark-red` and `/box mark-green` are still agent-callable

Current code allows:

```text
/box mark-red <note>
/box mark-green <note>
```

without UI confirmation or actor/source validation.

This conflicts with the original plan’s validation matrix:

```text
Agent runs /box mark-green itself | Disallowed (human-only)
```

Future Improvement 2 added safer automatic commands:

```text
/box run-red ...
/box run-green ...
```

but manual commands remain a bypass if the agent invokes them.

Severity: **High conceptually**, though partially mitigated by `/box run-red` and `/box run-green`.

Suggested fix options:

1. Disable manual mark commands entirely.
2. Require UI confirmation for manual mark commands.
3. Allow manual mark commands only when Pi exposes reliable human/source metadata.
4. Prefer `/box run-red` and `/box run-green` in normal workflow.

Recommended fix:

- Require UI confirmation for `/box mark-red` and `/box mark-green` immediately.
- In no-UI contexts, block them.

---

### 5. Phase-entry gates are not enforced on `/phase set`

Current behavior:

```text
/phase set WRITE_TESTS
/phase set IMPLEMENTING
/phase set REVIEWING
```

mutates state without checking:

- plan FROZEN
- RED confirmed
- GREEN confirmed

The gates are enforced when writing, not when entering phase.

Potential conflict:

- Phase 4 says entering or operating in `WRITE_TESTS` / `IMPLEMENTING` requires `FROZEN`.
- Phase 5 acceptance says attempting to enter or write in `IMPLEMENTING` without RED blocks.
- But Phase 5 also says `/box` and `/phase` commands only mutate state.

So this is an **internal plan ambiguity**. Current implementation follows the later “commands only mutate state” interpretation.

Severity: **Low/Medium**

Suggested fix options:

1. Keep current behavior and document explicitly that phase commands only mutate state; write operations enforce gates.
2. Add hard phase-entry validation to `/phase set`.

Recommended fix:

- Decide deliberately. If operational clarity matters more, enforce on `/phase set`. If flexibility matters more, document current behavior.

---

### 6. Bash `cp` / `mv` / `install` target extraction may over-block

Current `extractBashWriteTargets()` collects all path-like arguments for commands such as:

```ts
cp
mv
dd
install
```

That means source paths may be treated as write targets.

Example:

```bash
cp app/auth/source.py /tmp/out.py
```

Could route `app/auth/source.py` through write rules even though it is only being read.

Conflicts mildly with:

- Phase 1 bash write-target extraction intent

Severity: **Low/Medium**

Suggested fix:

- For `cp`, `mv`, and `install`, identify the destination argument only.
- For `dd`, parse `of=<path>` specifically.

---

### 7. Bash write parsing is still heuristic

The plan asked to catch common cases, and many are handled:

- redirection
- `tee`
- `sed -i`
- `perl -i`
- `cp`
- `mv`
- `dd`
- `install`
- Python `open(..., "w")`

But shell parsing remains regex-based. It may miss or misread complex shell syntax, quoted heredocs, unusual `dd of=...`, etc.

No direct conflict; just a known limitation.

Severity: **Low**

Suggested fix:

- Keep conservative behavior.
- Add targeted tests for newly discovered bypasses.
- Consider confirming any shell command with write intent that cannot be parsed confidently.

---

### 8. Adapter comments are stale after moving helper files

Current `.pi/extensions/governance.ts` comment says:

```text
governance-config.ts
governance-engine.ts
```

But actual files are:

```text
.pi/governance/config.ts
.pi/governance/engine.ts
```

No behavior issue.

Severity: **Low**

Suggested fix:

- Update comments in `.pi/extensions/governance.ts`.

---

### 9. `allowedReadFiles` and `allowedWriteFiles` exist but are not enforced

Future Improvement 1 requested adding these fields. They exist and clear correctly, but enforcement uses:

```ts
allowedTestFiles
allowedImplementationFiles
```

This is mostly expected because later improvements focused on exact test/implementation files. But the names `allowedReadFiles` / `allowedWriteFiles` may imply functionality that does not exist yet.

Severity: **Low**

Suggested fix:

- Either document these fields as reserved for future read/write governance, or remove them until implemented.

---

## Areas aligned with the plans

These appear aligned:

- Pi adapter uses typed `ExtensionAPI`
- correct `event.toolName` / `event.input`
- correct `ctx.ui.confirm("Governance confirmation", message)`
- correct `before_agent_start` return shape
- only one `.ts` extension entrypoint under `.pi/extensions`
- `.feature` hard block
- protected paths block
- no-UI confirm becomes block
- phase write rules
- FROZEN gate on write operations
- exact file enforcement for `WRITE_TESTS` and `IMPLEMENTING`
- Section 14 parser is structured and stricter
- `/box freeze-check`
- `/box status --verbose`
- `/box run-red` / `/box run-green`

---

## Recommended fix order

1. **Hardening:** make manual `/box mark-red` and `/box mark-green` require UI confirmation or disable them when `ctx.hasUI === false`.
2. **Config correctness:** preserve passed `createGovernanceEngine(config)` instead of overwriting with default `CONFIG`.
3. **Phase documentation or behavior:** decide whether `/phase set IMPLEMENTING` should block without RED, or document that only writes are gated.
4. **Config extraction:** move hardcoded path patterns from `engine.ts` into `config.ts`.
5. **Bash parsing:** improve `cp` / `mv` target handling to identify destination only.
