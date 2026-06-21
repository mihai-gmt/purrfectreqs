# Governance Future Improvements Implementation Plan

> Scope: follow-up hardening for the Pi governance harness after Phase 0–9B.
>
> Current structure:
>
> ```text
> .pi/extensions/governance.ts      # Pi adapter only
> .pi/governance/config.ts          # PurrfectReqs-specific config/prose seam
> .pi/governance/engine.ts          # governance rule engine
> ```
>
> Rule: implement one improvement at a time and validate after each. Do not combine these into one large change.

---

## Improvement 1 — Split `allowedFiles` into explicit manifests

### Goal

Replace the single overloaded field:

```json
{
  "allowedFiles": []
}
```

with clearer fields:

```json
{
  "allowedReadFiles": [],
  "allowedWriteFiles": [],
  "allowedTestFiles": [],
  "allowedImplementationFiles": []
}
```

### Why this helps

The current `allowedFiles` field works, but it is ambiguous. A file imported from Section 14 may be intended for test-writing or implementation, and the current phase rules infer meaning from phase context. Explicit fields make enforcement, debugging, and status output clearer.

### Detailed implementation steps

1. **Extend `FeatureBoxState`**
   - Add optional fields:
     - `allowedReadFiles?: string[]`
     - `allowedWriteFiles?: string[]`
     - `allowedTestFiles?: string[]`
     - `allowedImplementationFiles?: string[]`
   - Keep `allowedFiles?: string[]` temporarily for migration/backward compatibility.

2. **Update `defaultFeatureBox()`**
   - Add empty arrays for the new fields.

3. **Add compatibility helper**
   - Add helper functions:

   ```ts
   function allowedTestFiles(box: FeatureBoxState): string[]
   function allowedImplementationFiles(box: FeatureBoxState): string[]
   ```

   - During transition, these should merge:
     - new explicit arrays
     - legacy `allowedFiles`

4. **Update `WRITE_TESTS` enforcement**
   - Use `allowedTestFiles(box)` instead of `box.allowedFiles`.
   - Error message should reference `allowedTestFiles`.

5. **Update `IMPLEMENTING` enforcement**
   - Use `allowedImplementationFiles(box)` instead of `box.allowedFiles`.
   - Error message should reference `allowedImplementationFiles`.

6. **Update `/box allow-file <path>`**
   - If path class is `test`, add it to `allowedTestFiles`.
   - If path class is `source`, `core`, `migration`, or `plan`, add it to `allowedImplementationFiles`.
   - Do not add to legacy `allowedFiles` anymore.

7. **Update `/box clear-allowed-files`**
   - Clear all manifest fields:
     - `allowedFiles`
     - `allowedReadFiles`
     - `allowedWriteFiles`
     - `allowedTestFiles`
     - `allowedImplementationFiles`

8. **Update `/box status` output naturally**
   - It already serializes the whole feature box; verify the new fields appear.

### Validation matrix

| Test | Expected |
|---|---|
| Legacy `allowedFiles` still works | Backward compatible |
| `/box allow-file tests/unit/x.py` | Adds to `allowedTestFiles` |
| `/box allow-file app/auth/service.py` | Adds to `allowedImplementationFiles` |
| `WRITE_TESTS` listed test file | Allowed |
| `WRITE_TESTS` implementation file | Blocked |
| `IMPLEMENTING` listed implementation file | Allowed subject to other gates |
| `IMPLEMENTING` test file | Blocked |
| `/box clear-allowed-files` | Clears all manifest arrays |

### Stop conditions

Stop and report if existing `.pi/feature-box.json` data cannot be migrated safely or if behavior changes for current projects.

---

## Improvement 2 — Automatic RED/GREEN pytest execution

### Goal

Replace or supplement manual attestations:

```text
/box mark-red <note>
/box mark-green <note>
```

with governance-run commands:

```text
/box run-red <pytest-command>
/box run-green <pytest-command>
```

### Why this helps

Manual RED/GREEN is useful but trust-based. Automatic execution reduces theater: the extension can verify whether tests actually failed before implementation and passed before review.

### Detailed implementation steps

1. **Add command validation**
   - Only allow commands that start with:
     - `pytest`
     - `python -m pytest`
   - Reject anything containing shell control operators:
     - `;`
     - `&&`
     - `||`
     - `|`
     - `>`
     - `>>`
     - backticks
     - `$(`

2. **Add command runner helper**
   - Use Node `child_process.spawnSync` or `execFileSync` safely.
   - Prefer `spawnSync(command, args, { cwd, encoding: "utf8", timeout })`.
   - Do not invoke a shell.

3. **Add parser for pytest output**
   - For GREEN:
     - require exit code `0`
     - output should contain `passed` or pytest success summary
   - For RED:
     - require non-zero exit code
     - output should indicate test failure, not infrastructure failure
     - accept patterns like:
       - `FAILED`
       - `failed`
       - `assert`
     - reject likely setup errors if output contains:
       - `ImportError`
       - `ModuleNotFoundError`
       - `SyntaxError`
       - `collected 0 items`
       - `ERROR collecting`

4. **Implement `/box run-red <pytest-command>`**
   - Run command.
   - If valid RED:
     - set `redConfirmed: true`
     - set `greenConfirmed: false`
     - set `redCommand`
     - set `redCheckedAt`
     - store a short output summary, not full logs.
   - If not valid RED:
     - do not mutate RED state
     - return failure report.

5. **Implement `/box run-green <pytest-command>`**
   - Run command.
   - If valid GREEN:
     - set `greenConfirmed: true`
     - set `greenCommand`
     - set `greenCheckedAt`
   - If not valid GREEN:
     - do not mutate GREEN state
     - return failure report.

6. **Keep manual commands**
   - Keep `/box mark-red` and `/box mark-green` as fallback developer attestations.
   - Update result strings to clarify they are manual attestations.

### Validation matrix

| Test | Expected |
|---|---|
| `/box run-red pytest tests/unit/x.py` with failing assertion | Sets RED |
| `/box run-red pytest tests/unit/x.py` with passing tests | Does not set RED |
| `/box run-red pytest missing/path.py` | Does not set RED |
| `/box run-green pytest tests/unit/x.py` with passing tests | Sets GREEN |
| `/box run-green pytest tests/unit/x.py` with failures | Does not set GREEN |
| Command with `; rm -rf` | Rejected before execution |
| Command with `>` redirection | Rejected before execution |

### Stop conditions

Stop and report if safe command parsing requires a shell, if pytest output cannot reliably distinguish assertion failure from environment failure, or if command execution would be too slow/unbounded.

---

## Improvement 3 — Load config from `.pi/harness.config.json`

### Goal

Make PurrfectReqs-specific values data-driven instead of TypeScript-only.

Future config example:

```json
{
  "projectName": "PurrfectReqs",
  "sourceRoots": ["app"],
  "testRoots": ["tests/bdd/step_defs", "tests/unit"],
  "featurePatterns": ["tests/features/**/*.feature"],
  "planDir": "tests/bdd/plans",
  "coreDirs": ["app/core"],
  "migrationDirs": ["alembic/versions"],
  "dependencyFiles": ["pyproject.toml", "requirements*.txt"],
  "phases": {}
}
```

### Why this helps

The config/engine split is done, but `config.ts` is still code. JSON config would make the engine easier to retarget to another project without rewriting TypeScript.

### Detailed implementation steps

1. **Define JSON schema informally in docs/comment**
   - Required fields:
     - `projectName`
     - `sourceRoots`
     - `testRoots`
     - `coreDirs`
     - `migrationDirs`
   - Optional fields:
     - `featurePatterns`
     - `planDir`
     - `dependencyFiles`
     - `authorityDocs`
     - `bannedDeps`

2. **Add config loader**
   - Add helper:

   ```ts
   function loadHarnessConfig(cwd: string): GovernanceConfig
   ```

   - If `.pi/harness.config.json` exists:
     - parse and merge with defaults from `config.ts`
   - If missing:
     - use `config.ts` defaults.

3. **Avoid dynamic regex in JSON where possible**
   - JSON cannot hold RegExp objects.
   - Use glob-like strings or simple path prefixes.
   - Keep complex regex defaults in `config.ts` until a safe conversion exists.

4. **Thread config into engine**
   - Current engine imports `CONFIG` directly.
   - Refactor `createGovernanceEngine(config = CONFIG)`.
   - The Pi adapter can pass loaded config later.

5. **Keep backwards compatibility**
   - Existing behavior must be identical if no JSON file exists.

### Validation matrix

| Test | Expected |
|---|---|
| No `.pi/harness.config.json` | Current behavior unchanged |
| Minimal JSON config | Loads and merges defaults |
| Invalid JSON | Clear governance error or fallback with warning |
| Custom source root | Classifier uses custom root |
| Custom core dir | Core rule uses custom dir |

### Stop conditions

Stop if JSON config would require unsafe eval/RegExp construction from untrusted strings, or if config loading changes current behavior without an explicit migration.

---

## Improvement 4 — Stricter and more flexible Section 14 parser

### Goal

Improve `/box allow-files-from-plan` so it reliably imports only intended write targets from Section 14 across common heading variations.

### Why this helps

Current parsing is conservative and works for expected headings, but heading text in plans may vary. A stricter parser reduces false imports and makes plan-driven enforcement more trustworthy.

### Detailed implementation steps

1. **Define accepted Section 14 heading variants**
   - Support:
     - `## 14. Handoff Manifest`
     - `## Section 14`
     - `## 14`
     - `# 14 — Handoff`

2. **Define accepted write subsection variants**
   - Test write sections:
     - `Files to CREATE/MODIFY while writing tests`
     - `Files to create or modify while writing tests`
     - `Files to create/modify during test writing`
     - `Test files to create/modify`
   - Implementation write sections:
     - `Files to CREATE/MODIFY while implementing`
     - `Files to create or modify during implementation`
     - `Implementation files to create/modify`

3. **Explicitly ignore read sections**
   - Ignore headings containing:
     - `READ`
     - `before writing tests`
     - `before implementing`

4. **Return structured parse result**
   - Instead of a single `files` array, return:

   ```ts
   {
     testFiles: string[],
     implementationFiles: string[],
     skipped: string[],
     warnings: string[]
   }
   ```

5. **Use explicit manifest fields**
   - Best implemented after Improvement 1.
   - Populate:
     - `allowedTestFiles`
     - `allowedImplementationFiles`

6. **Improve error messages**
   - Distinguish:
     - Section 14 missing
     - Section 14 found but no write subsections
     - write subsections found but no valid files
     - files skipped due to unsupported class

7. **Add parser tests via mocked plan strings**
   - Keep tests as inline mocked harness checks unless a formal test runner is added for `.pi` extensions.

### Validation matrix

| Test | Expected |
|---|---|
| Standard Section 14 headings | Imports files |
| `Section 14` heading variant | Imports files |
| `create or modify during implementation` | Imports files |
| Read-only sections only | Imports none with clear warning |
| `.feature` listed | Skipped |
| docs file listed | Skipped unless explicitly supported later |
| source file in test section | Skipped or warned depending chosen policy |
| test file in implementation section | Skipped or warned depending chosen policy |

### Stop conditions

Stop if parser starts importing ambiguous prose lines or if heading variations make it impossible to distinguish read vs write sections safely.

---

## Improvement 5 — `/box status --verbose` style output

### Goal

Improve operator visibility into governance state.

Current `/box status` dumps JSON. That is useful but not very readable. Verbose status should summarize active gates and what is currently blocking progress.

### Why this helps

When governance blocks work, the developer needs quick answers:

- What phase am I in?
- Is the plan frozen?
- Are RED/GREEN confirmed?
- Which files are allowed?
- Why is my write blocked?

### Detailed implementation steps

1. **Add argument parsing for `/box status`**
   - Support:
     - `/box status`
     - `/box status --verbose`

2. **Keep default JSON output**
   - Do not break existing behavior.

3. **Implement verbose formatter**
   - Include:
     - phase
     - inScope modules
     - allowCore and reason
     - planFile
     - plan status
     - redConfirmed / redCommand
     - greenConfirmed / greenCommand
     - allowed test files
     - allowed implementation files

4. **Add active gate summary**
   - For current phase:
     - `WRITE_TESTS`: show FROZEN status + allowed tests count
     - `IMPLEMENTING`: show FROZEN + RED + allowed implementation count
     - `REVIEWING`: show GREEN + review-only mode

5. **Optional: add `/phase status --verbose`**
   - Can reuse the same formatter.

### Validation matrix

| Test | Expected |
|---|---|
| `/box status` | JSON output unchanged |
| `/box status --verbose` | Human-readable summary |
| Missing planFile | Shows plan missing |
| DRAFT plan | Shows FROZEN gate blocked |
| WRITE_TESTS with no allowed files | Shows no allowed test files |
| IMPLEMENTING without RED | Shows RED gate blocked |
| REVIEWING without GREEN | Shows GREEN gate blocked |

### Stop conditions

Stop if argument parsing conflicts with existing slash command parsing or if verbose status requires expensive operations beyond reading current feature box and plan status.
