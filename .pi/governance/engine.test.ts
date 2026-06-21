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
import {
  classifyPath,
  parsePytestCommand,
  isValidRed,
  isValidGreen,
  extractBashWriteTargets,
  freezeCheck,
  parseAllowedFilesFromPlan,
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
  assert.equal(classifyPath("pyproject.toml"), "config");
  assert.equal(classifyPath(".env"), "config");
  assert.equal(classifyPath("README.md"), "unknown");
});

test("classifyPath ignores leading ./ and treats nested plan paths as non-plan", () => {
  assert.equal(classifyPath("./tests/bdd/plans/x.plan.md"), "plan");
  // nested under a subdir is not a direct child -> not a plan file
  assert.equal(classifyPath("tests/bdd/plans/sub/x.plan.md"), "unknown");
});

test("parsePytestCommand accepts only plain pytest invocations", () => {
  const a = parsePytestCommand("pytest tests/unit -v");
  assert.equal(a.ok, true);
  assert.equal(a.ok && a.executable, "pytest");

  const b = parsePytestCommand("python -m pytest tests/bdd/step_defs/test_login.py");
  assert.equal(b.ok, true);
  assert.equal(b.ok && b.executable, "python");
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

test("parseAllowedFilesFromPlan errors when Section 14 is absent", () => {
  const parsed = parseAllowedFilesFromPlan("# Plan\n\n## 1 Goal\n- x\n");
  assert.ok(parsed.error);
});
