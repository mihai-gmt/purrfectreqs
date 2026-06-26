/**
 * Tests for the governance engine's pure functions.
 *
 * Run from the project root with zero dependencies (Node >= 22.18 strips types):
 *   node --test .pi/governance/engine.test.ts
 *
 * These cover the parsing/classification logic that the gates depend on. They do
 * NOT cover the stateful feature-box file I/O or the Pi adapter wiring (those need
 * a live Pi session). The classifiers read the default PurrfectReqs CONFIG, since
 * no engine is instantiated here.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  classifyPath,
  moduleOf,
  parsePytestCommand,
  resolveTestExecutable,
  isValidRed,
  isValidGreen,
  extractBashWriteTargets,
  freezeCheck,
  parseAllowedFilesFromPlan,
  buildFingerprint,
  staleSuffix,
  createGovernanceEngine,
} from "./engine.ts";

test("classifyPath maps paths to the correct class", () => {
  assert.equal(classifyPath("tests/features/auth/login.feature"), "feature");
  assert.equal(classifyPath("tests/bdd/plans/auth_login.analysis.md"), "analysis");
  assert.equal(classifyPath("tests/bdd/plans/auth_login.plan.md"), "plan");
  assert.equal(classifyPath("tests/bdd/plans/auth_login.review.md"), "review");
  assert.equal(classifyPath("tests/bdd/step_defs/test_login.py"), "test");
  assert.equal(classifyPath("tests/unit/test_service.py"), "test");
  assert.equal(classifyPath("app/core/security.py"), "core");
  assert.equal(classifyPath("app/auth/service.py"), "source");
  assert.equal(classifyPath("alembic/versions/0001_init.py"), "migration");
  assert.equal(classifyPath("docs/SECURITY.md"), "doc");
  assert.equal(classifyPath("docs/PROJECT_STATUS.md"), "status");
  assert.equal(classifyPath("pyproject.toml"), "config");
  assert.equal(classifyPath(".env"), "config");
  assert.equal(classifyPath("README.md"), "unknown");
});

test("classifyPath maps templates and static assets to frontend", () => {
  assert.equal(classifyPath("app/templates/auth/register.html"), "frontend");
  assert.equal(classifyPath("app/templates/base.html"), "frontend");
  assert.equal(classifyPath("app/templates/_macros/forms.html"), "frontend");
  assert.equal(classifyPath("app/static/css/app.css"), "frontend");
  assert.equal(classifyPath("app/static/js/register.js"), "frontend");
  // a .py file anywhere under app/ is still source, never frontend
  assert.equal(classifyPath("app/auth/service.py"), "source");
});

test("classifyPath maps the project backlog file to backlog", () => {
  assert.equal(classifyPath("Backlog.md"), "backlog");
  assert.equal(classifyPath("./Backlog.md"), "backlog");
  // case-insensitive match on the configured backlog file name
  assert.equal(classifyPath("backlog.md"), "backlog");
  // a backlog file nested elsewhere is not the project backlog
  assert.equal(classifyPath("docs/Backlog.md"), "doc");
  // the project backlog is app-shared, not module-scoped
  assert.equal(moduleOf("Backlog.md"), null);
});

test("classifyPath ignores leading ./ and treats nested plan paths as non-plan", () => {
  assert.equal(classifyPath("./tests/bdd/plans/x.plan.md"), "plan");
  // nested under a subdir is not a direct child -> not a plan file
  assert.equal(classifyPath("tests/bdd/plans/sub/x.plan.md"), "unknown");
});

test("moduleOf resolves module-scoped template paths and treats shared frontend assets as app-shared", () => {
  // module source
  assert.equal(moduleOf("app/auth/service.py"), "auth");
  // templates organised by module
  assert.equal(moduleOf("app/templates/auth/register.html"), "auth");
  // files directly under app/templates and underscore-prefixed shared dirs are app-shared (null)
  assert.equal(moduleOf("app/templates/base.html"), null);
  assert.equal(moduleOf("app/templates/_macros/forms.html"), null);
  // static assets are app-shared (null)
  assert.equal(moduleOf("app/static/css/app.css"), null);
  // paths outside app/ have no module
  assert.equal(moduleOf("tests/unit/test_x.py"), null);
});

test("PROJECT_STATUS.md is writable in IMPLEMENTING/REVIEWING but authority docs stay blocked", async () => {
  const cwd = mkdtempSync(join(tmpdir(), "status-"));
  mkdirSync(join(cwd, ".pi"), { recursive: true });
  // a FROZEN plan on disk so the IMPLEMENTING plan-frozen gate passes
  const plan = "tests/bdd/plans/auth_x.plan.md";
  mkdirSync(join(cwd, "tests/bdd/plans"), { recursive: true });
  writeFileSync(join(cwd, plan), "Status: FROZEN\n", "utf8");

  const base = {
    inScope: ["auth"], allowCore: false,
    allowedTestFiles: [], allowedImplementationFiles: ["app/auth/router.py"], allowedFiles: [],
    redConfirmed: true, greenConfirmed: true, planFile: plan,
  };
  const engine = createGovernanceEngine();
  const writeBox = (phase: string) => writeFileSync(join(cwd, ".pi", "feature-box.json"), JSON.stringify({ ...base, phase }), "utf8");
  const tryWrite = async (phase: string, path: string) => {
    writeBox(phase);
    return engine.handleToolCall({ toolName: "write", input: { file_path: path } }, { cwd });
  };

  // status ledger is allowed (no allowlist entry needed) in both completion phases
  assert.equal(await tryWrite("IMPLEMENTING", "docs/PROJECT_STATUS.md"), undefined);
  assert.equal(await tryWrite("REVIEWING", "docs/PROJECT_STATUS.md"), undefined);
  // an authority doc is still blocked in IMPLEMENTING
  const blockedDoc = await tryWrite("IMPLEMENTING", "docs/SECURITY.md");
  assert.equal(blockedDoc?.block, true);
  // a source file not in the allowlist is still blocked (status bypass is status-only)
  const blockedSource = await tryWrite("IMPLEMENTING", "app/auth/service.py");
  assert.equal(blockedSource?.block, true);
});

test("parsePytestCommand accepts only plain pytest invocations", () => {
  const a = parsePytestCommand("pytest tests/unit -v");
  assert.equal(a.ok, true);
  assert.equal(a.ok && a.executable, "pytest");

  const b = parsePytestCommand("python -m pytest tests/bdd/step_defs/test_login.py");
  assert.equal(b.ok, true);
  assert.equal(b.ok && b.executable, "python");
});

test("resolveTestExecutable prefers the venv binary when present, falls back to PATH", () => {
  const cwd = mkdtempSync(join(tmpdir(), "venv-"));
  // no .venv yet -> bare name (resolved against PATH by spawn)
  assert.equal(resolveTestExecutable("pytest", cwd), "pytest");
  assert.equal(resolveTestExecutable("python", cwd), "python");

  // a real venv layout -> the explicit venv binary, no activation needed
  mkdirSync(join(cwd, ".venv", "bin"), { recursive: true });
  writeFileSync(join(cwd, ".venv", "bin", "pytest"), "", "utf8");
  writeFileSync(join(cwd, ".venv", "bin", "python"), "", "utf8");
  assert.equal(resolveTestExecutable("pytest", cwd), join(cwd, ".venv", "bin", "pytest"));
  assert.equal(resolveTestExecutable("python", cwd), join(cwd, ".venv", "bin", "python"));

  // an unrelated executable is never rewritten even if a venv exists
  assert.equal(resolveTestExecutable("make", cwd), "make");
});

test("parsePytestCommand rejects shell control and non-pytest commands", () => {
  assert.equal(parsePytestCommand("pytest && rm -rf /").ok, false);
  assert.equal(parsePytestCommand("pytest tests | head").ok, false);
  assert.equal(parsePytestCommand("pytest tests > out.txt").ok, false);
  assert.equal(parsePytestCommand("ls").ok, false);
  assert.equal(parsePytestCommand("").ok, false);
});

test("isValidRed requires a genuine assertion failure, not an infra error", () => {
  assert.equal(isValidRed({ exitCode: 1, output: "1 failed in 0.2s" }), true);
  assert.equal(isValidRed({ exitCode: 1, output: "E   assert 1 == 2" }), true);
  // infra failures must NOT count as RED (would let you skip real test writing)
  assert.equal(isValidRed({ exitCode: 1, output: "ModuleNotFoundError: no module app" }), false);
  assert.equal(isValidRed({ exitCode: 2, output: "ERROR collecting test_x.py" }), false);
  assert.equal(isValidRed({ exitCode: 1, output: "collected 0 items" }), false);
  // passing tests are not RED
  assert.equal(isValidRed({ exitCode: 0, output: "3 passed" }), false);
});

test("isValidGreen requires a clean pass", () => {
  assert.equal(isValidGreen({ exitCode: 0, output: "3 passed in 0.5s" }), true);
  assert.equal(isValidGreen({ exitCode: 1, output: "1 failed, 2 passed" }), false);
  assert.equal(isValidGreen({ exitCode: 0, output: "no tests ran in 0.01s" }), false);
  assert.equal(isValidGreen({ exitCode: 0, output: "ImportError while loading" }), false);
});

test("extractBashWriteTargets detects redirects, tee, sed -i, cp/mv destinations", () => {
  const redir = extractBashWriteTargets("echo hi >> app/auth/notes.py");
  assert.equal(redir.writeIntent, true);
  assert.ok(redir.targets.includes("app/auth/notes.py"));

  const tee = extractBashWriteTargets("echo x | tee app/auth/y.py");
  assert.equal(tee.writeIntent, true);
  assert.ok(tee.targets.includes("app/auth/y.py"));

  const sed = extractBashWriteTargets("sed -i 's/a/b/' app/auth/z.py");
  assert.equal(sed.writeIntent, true);
  assert.ok(sed.targets.includes("app/auth/z.py"));

  // cp/mv should target the destination (last arg), not the source
  const cp = extractBashWriteTargets("cp src_template.py app/auth/dest.py");
  assert.equal(cp.writeIntent, true);
  assert.ok(cp.targets.includes("app/auth/dest.py"));

  const dd = extractBashWriteTargets("dd if=/dev/zero of=app/auth/out.bin");
  assert.equal(dd.writeIntent, true);
  assert.ok(dd.targets.includes("app/auth/out.bin"));
});

test("extractBashWriteTargets reports no write intent for read-only commands", () => {
  assert.equal(extractBashWriteTargets("pytest tests/unit -v").writeIntent, false);
  assert.equal(extractBashWriteTargets("cat app/auth/service.py").writeIntent, false);
  assert.equal(extractBashWriteTargets("git status").writeIntent, false);
});

const PLAN_HEADER = `# Some Plan\n\n**Status**: FROZEN\n\n`;

function changelog(entries: string[]): string {
  return `## 14 File Manifest\n- ignored\n\n## 15 Changelog\n${entries.map((e) => `- ${e}`).join("\n")}\n\n## 16 Notes\n- end\n`;
}

test("freezeCheck passes when all three scopes ran and no escalation is unresolved", () => {
  const content = PLAN_HEADER + changelog(["adversarial scope complete", "enrich scope complete", "testability scope complete", "escalations: none"]);
  const res = freezeCheck(content);
  assert.equal(res.ok, true);
});

test("freezeCheck fails when a required scope entry is missing", () => {
  const content = PLAN_HEADER + changelog(["adversarial scope complete", "enrich scope complete", "escalations: none"]);
  const res = freezeCheck(content);
  assert.equal(res.ok, false);
  assert.match(res.report, /testability/);
});

test("freezeCheck fails on an unresolved escalation", () => {
  const content = PLAN_HEADER + changelog(["adversarial done", "enrich done", "testability done", "escalation: unresolved cross-module question"]);
  const res = freezeCheck(content);
  assert.equal(res.ok, false);
  assert.match(res.report, /unresolved escalation/i);
});

test("freezeCheck fails when there is no Section 15 changelog", () => {
  const content = PLAN_HEADER + "## 14 File Manifest\n- nothing\n";
  const res = freezeCheck(content);
  assert.equal(res.ok, false);
  assert.match(res.report, /Section 15/);
});

const SECTION_14 = `## 14 File Manifest

### Files to READ before writing tests
- \`app/auth/service.py\`

### Test files to CREATE/MODIFY during test writing
- \`tests/bdd/step_defs/test_login.py\`
- \`docs/NOTE.md\`

### Implementation files to CREATE/MODIFY during implementation
- \`app/auth/service.py\`
- \`app/auth/router.py\`
- \`tests/features/auth/login.feature\`

## 15 Changelog
- done
`;

test("parseAllowedFilesFromPlan separates test vs implementation and skips non-writable entries", () => {
  const parsed = parseAllowedFilesFromPlan(SECTION_14);
  assert.deepEqual(parsed.testFiles, ["tests/bdd/step_defs/test_login.py"]);
  assert.deepEqual(parsed.implementationFiles, ["app/auth/service.py", "app/auth/router.py"]);
  // READ-section files are not imported as writable
  assert.equal(parsed.implementationFiles.includes("app/auth/service.py"), true);
  // docs and .feature files are skipped, not imported
  assert.ok(parsed.skipped.some((s) => s.includes("docs/NOTE.md")));
  assert.ok(parsed.skipped.some((s) => s.includes("login.feature")));
});

const SECTION_14_UI = `## 14 File Manifest

### Test files to CREATE/MODIFY during test writing
- \`tests/bdd/step_defs/test_register_user_ui.py\`

### Implementation files to CREATE/MODIFY during implementation
- \`app/auth/router.py\`
- \`app/templates/auth/register.html\`
- \`app/static/css/app.css\`

## 15 Changelog
- done
`;

test("parseAllowedFilesFromPlan imports frontend (template/static) files into the implementation manifest", () => {
  const parsed = parseAllowedFilesFromPlan(SECTION_14_UI);
  assert.deepEqual(parsed.testFiles, ["tests/bdd/step_defs/test_register_user_ui.py"]);
  assert.deepEqual(parsed.implementationFiles, [
    "app/auth/router.py",
    "app/templates/auth/register.html",
    "app/static/css/app.css",
  ]);
  // frontend files must NOT be skipped
  assert.equal(parsed.skipped.length, 0);
});

const SECTION_14_TEMPLATE = `## 14. File Manifest

### Files to READ before writing tests

| File | Why |
|------|-----|
| \`tests/features/auth/login.feature\` | The contract |
| \`tests/bdd/conftest.py\` | Reuse fixtures |

### Files to READ before implementing

| File | Why |
|------|-----|
| \`app/auth/router.py\` | routes |

### Files to CREATE

| File | Agent | Purpose |
|------|-------|---------|
| \`tests/bdd/step_defs/test_login.py\` | write-tests | BDD step definitions |
| \`app/templates/auth/login.html\` | implement | login page |
| \`app/static/css/app.css\` | implement | css |

### Files to MODIFY

| File | Agent | What changes |
|------|-------|--------------|
| \`app/auth/router.py\` | implement | add routes |
| \`app/auth/service.py\` | implement | logic |
| \`docs/PROJECT_STATUS.md\` | implement | status |

### Files NOT touched

Everything not listed above.

## 15 Changelog
- done
`;

test("parseAllowedFilesFromPlan handles the canonical PLAN_TEMPLATE table format (CREATE/MODIFY + Agent column)", () => {
  const parsed = parseAllowedFilesFromPlan(SECTION_14_TEMPLATE);
  // routed by class: the only test-class file lands in testFiles
  assert.deepEqual(parsed.testFiles, ["tests/bdd/step_defs/test_login.py"]);
  // CREATE then MODIFY, by class; READ-section files excluded; router.py deduped
  assert.deepEqual(parsed.implementationFiles, [
    "app/templates/auth/login.html",
    "app/static/css/app.css",
    "app/auth/router.py",
    "app/auth/service.py",
  ]);
  // a doc under MODIFY is not writable in IMPLEMENTING — skipped, not imported
  assert.ok(parsed.skipped.some((s) => s.includes("docs/PROJECT_STATUS.md")));
  // READ-section feature/conftest entries are never imported
  assert.equal(parsed.testFiles.includes("tests/bdd/conftest.py"), false);
});

test("parseAllowedFilesFromPlan errors when Section 14 is absent", () => {
  const parsed = parseAllowedFilesFromPlan("# Plan\n\n## 1 Goal\n- x\n");
  assert.ok(parsed.error);
});

test("buildFingerprint is deterministic, order-independent, and mtime-sensitive", () => {
  const a = buildFingerprint([{ name: "engine.ts", mtimeMs: 100 }, { name: "config.ts", mtimeMs: 200 }]);
  const b = buildFingerprint([{ name: "config.ts", mtimeMs: 200 }, { name: "engine.ts", mtimeMs: 100 }]);
  assert.equal(a, b); // order-independent
  const c = buildFingerprint([{ name: "engine.ts", mtimeMs: 101 }, { name: "config.ts", mtimeMs: 200 }]);
  assert.notEqual(a, c); // a changed mtime changes the fingerprint
});

test("staleSuffix flags a drift between loaded and on-disk builds", () => {
  assert.equal(staleSuffix("abc123", "abc123"), "");
  assert.match(staleSuffix("abc123", "def456"), /ENGINE STALE/);
  // unknown on either side suppresses the marker (don't cry wolf on read errors)
  assert.equal(staleSuffix("unknown", "def456"), "");
  assert.equal(staleSuffix("abc123", "unknown"), "");
  assert.equal(staleSuffix("", "def456"), "");
});
