/**
 * Tests for the per-feature audit log.
 *
 * Run from the project root (Node >= 22.18 strips types):
 *   node --test .pi/governance/audit.test.ts
 *
 * Pure helpers are tested directly; recordControlCommand is exercised against a
 * throwaway temp directory so the append/seq/attempt/artefact logic is covered
 * without a live Pi session.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { CONFIG } from "./config.ts";
import {
  classifyAuditOutcome,
  auditBaseName,
  auditFilePath,
  deriveIdentity,
  parseAuditLines,
  attemptNumber,
  diffArtifacts,
  recordControlCommand,
  formatAuditHistory,
} from "./audit.ts";

test("classifyAuditOutcome maps handler strings to outcomes", () => {
  assert.equal(classifyAuditOutcome("Workflow phase set to WRITE_TESTS."), "ok");
  assert.equal(classifyAuditOutcome("PASS: freeze prerequisites satisfied."), "ok");
  assert.equal(classifyAuditOutcome("FAIL:\n- missing testability changelog entry"), "failed");
  assert.equal(classifyAuditOutcome("RED not confirmed: pytest did not show a failing test."), "failed");
  assert.equal(classifyAuditOutcome("No valid writable files found in Section 14."), "failed");
  assert.equal(classifyAuditOutcome("Cannot import allowed files: plan status is DRAFT, not FROZEN."), "blocked");
  assert.equal(classifyAuditOutcome("Rejected: /box allow-file accepts only ..."), "blocked");
  assert.equal(classifyAuditOutcome("Usage: /phase set <IDLE|...>"), "blocked");
});

test("auditBaseName / auditFilePath derive the per-feature path", () => {
  assert.equal(auditBaseName("tests/bdd/plans/auth_20260621_register.plan.md"), "auth_20260621_register");
  assert.equal(auditBaseName("tests/bdd/plans/auth_x.analysis.md"), null);
  assert.equal(auditFilePath("/repo", "tests/bdd/plans/auth_20260621_register.plan.md"), "/repo/.pi/audit/auth_20260621_register.audit.jsonl");
});

test("deriveIdentity splits module and feature, preferring the Feature Box module", () => {
  assert.deepEqual(deriveIdentity("tests/bdd/plans/auth_20260621_register.plan.md", ["auth"]), {
    feature: "20260621_register",
    module: "auth",
    base: "auth_20260621_register",
  });
  // falls back to the first underscore token when no inScope module is given
  assert.deepEqual(deriveIdentity("tests/bdd/plans/auth_login.plan.md", []), {
    feature: "login",
    module: "auth",
    base: "auth_login",
  });
});

test("attemptNumber counts prior invocations of the same command+op", () => {
  const records = [
    { type: "header" },
    { type: "event", command: "/box", op: "freeze-check" },
    { type: "event", command: "/box", op: "run-red" },
    { type: "event", command: "/box", op: "freeze-check" },
  ];
  assert.equal(attemptNumber(records, "/box", "freeze-check"), 3);
  assert.equal(attemptNumber(records, "/box", "run-red"), 2);
  assert.equal(attemptNumber(records, "/phase", "set"), 1);
});

test("diffArtifacts returns only newly added paths", () => {
  assert.deepEqual(diffArtifacts(["a.py"], ["a.py", "b.py"]), ["b.py"]);
  assert.deepEqual(diffArtifacts([], []), []);
  assert.deepEqual(diffArtifacts(["./a.py"], ["a.py"]), []);
});

function box(overrides: object = {}) {
  return {
    phase: "IDLE",
    inScope: [],
    planFile: null,
    allowedTestFiles: [],
    allowedImplementationFiles: [],
    allowedFiles: [],
    ...overrides,
  };
}

test("recordControlCommand writes a header on first attributable command, then events", () => {
  const cwd = mkdtempSync(join(tmpdir(), "audit-"));
  const plan = "tests/bdd/plans/auth_20260621_register.plan.md";
  // create the plan + analysis on disk so the header snapshot can find them
  for (const rel of [plan, "tests/bdd/plans/auth_20260621_register.analysis.md"]) {
    const abs = join(cwd, rel);
    mkdirSync(dirname(abs), { recursive: true });
    writeFileSync(abs, "x", "utf8");
  }

  // first attributable command: /box plan creates the file + header + event
  const before1 = box({ inScope: ["auth"], phase: "ITERATING" });
  const after1 = box({ inScope: ["auth"], phase: "ITERATING", planFile: plan });
  const file = recordControlCommand({
    cwd, cfg: CONFIG, command: "/box", op: "plan", args: plan,
    before: before1, after: after1, planStatus: "DRAFT", result: `Feature Box plan file set to: ${plan}`,
  });
  assert.ok(file);

  // a failed freeze-check, then a passing one (attempt increments)
  const fb = box({ inScope: ["auth"], phase: "ITERATING", planFile: plan });
  recordControlCommand({ cwd, cfg: CONFIG, command: "/box", op: "freeze-check", args: "", before: fb, after: fb, planStatus: "DRAFT", result: "FAIL:\n- consistency" });
  recordControlCommand({ cwd, cfg: CONFIG, command: "/box", op: "freeze-check", args: "", before: fb, after: fb, planStatus: "DRAFT", result: "PASS: freeze prerequisites satisfied." });

  const records = parseAuditLines(readFileSync(file!, "utf8"));
  assert.equal(records[0].type, "header");
  assert.equal(records[0].meta.module, "auth");
  assert.equal(records[0].meta.feature, "20260621_register");
  assert.equal(records[0].artifacts.plan, plan);
  assert.equal(records[0].artifacts.analysis, "tests/bdd/plans/auth_20260621_register.analysis.md");

  const events = records.filter((r) => r.type === "event");
  assert.equal(events.length, 3); // plan, freeze-check(fail), freeze-check(pass)
  const freezes = events.filter((e) => e.op === "freeze-check");
  assert.deepEqual(freezes.map((e) => e.outcome), ["failed", "ok"]);
  assert.deepEqual(freezes.map((e) => e.attempt), [1, 2]);
  // seq is monotonic across all records
  assert.deepEqual(records.map((r) => r.seq), records.map((_, i) => i));
});

test("recordControlCommand logs artifact_registered deltas for newly allowed files", () => {
  const cwd = mkdtempSync(join(tmpdir(), "audit-"));
  const plan = "tests/bdd/plans/auth_login.plan.md";
  mkdirSync(join(cwd, "tests/bdd/plans"), { recursive: true });
  writeFileSync(join(cwd, plan), "x", "utf8");

  const base = box({ inScope: ["auth"], phase: "WRITE_TESTS", planFile: plan });
  // create the file first (header) via an initial command
  recordControlCommand({ cwd, cfg: CONFIG, command: "/box", op: "plan", args: plan, before: box({ inScope: ["auth"] }), after: base, planStatus: "FROZEN", result: "ok" });

  // now allow a test file + an implementation file in one import
  const after = box({
    inScope: ["auth"], phase: "WRITE_TESTS", planFile: plan,
    allowedTestFiles: ["tests/bdd/step_defs/test_login.py"],
    allowedImplementationFiles: ["app/auth/router.py"],
  });
  const file = recordControlCommand({
    cwd, cfg: CONFIG, command: "/box", op: "allow-files-from-plan", args: "",
    before: base, after, planStatus: "FROZEN", result: "Imported 2 allowed file(s) from Section 14:",
  });

  const records = parseAuditLines(readFileSync(file!, "utf8"));
  const arts = records.filter((r) => r.type === "artifact_registered");
  assert.deepEqual(
    arts.map((a) => [a.artifact_kind, a.path]),
    [["test", "tests/bdd/step_defs/test_login.py"], ["implementation", "app/auth/router.py"]],
  );
});

const HISTORY_RECORDS = [
  { type: "header", seq: 0, ts: "2026-06-21T13:00:00Z", meta: { module: "auth", feature: "register", created: "2026-06-21T13:00:00Z" }, artifacts: { feature: "tests/features/auth/register.feature", analysis: "a.analysis.md", plan: "p.plan.md", review: null, tests: [], implementation: [] } },
  { type: "event", seq: 1, ts: "2026-06-21T14:02:11Z", command: "/box", op: "freeze-check", args: "", phase_from: "ITERATING", phase_to: "ITERATING", outcome: "failed", attempt: 1, detail: "consistency" },
  { type: "event", seq: 2, ts: "2026-06-21T14:20:03Z", command: "/box", op: "freeze-check", args: "", phase_from: "ITERATING", phase_to: "ITERATING", outcome: "ok", attempt: 2, detail: "satisfied" },
  { type: "artifact_registered", seq: 3, ts: "2026-06-21T14:30:00Z", artifact_kind: "test", path: "tests/bdd/step_defs/test_register.py" },
  { type: "event", seq: 4, ts: "2026-06-21T14:41:22Z", command: "/phase", op: "set", args: "WRITE_TESTS", phase_from: "ITERATING", phase_to: "WRITE_TESTS", outcome: "ok", attempt: 1, detail: "" },
];

test("formatAuditHistory renders a timeline with phase movement, attempts, and outcomes", () => {
  const out = formatAuditHistory(HISTORY_RECORDS);
  assert.match(out, /auth\/register/);
  assert.match(out, /#1 .*freeze-check.*FAILED/);
  assert.match(out, /#2 .*freeze-check.*OK.*attempt 2/);
  assert.match(out, /#3 .*\+ test: tests\/bdd\/step_defs\/test_register\.py/);
  assert.match(out, /#4 .*\/phase set WRITE_TESTS \[ITERATING→WRITE_TESTS\] OK/);
});

test("formatAuditHistory --failed shows only non-ok events", () => {
  const out = formatAuditHistory(HISTORY_RECORDS, { failed: true });
  assert.match(out, /#1 .*FAILED/);
  assert.equal(/#2 /.test(out), false); // ok event excluded
  assert.equal(/\+ test:/.test(out), false); // artifact registrations excluded
});

test("formatAuditHistory --artifacts lists the registry instead of the timeline", () => {
  const out = formatAuditHistory(HISTORY_RECORDS, { artifactsOnly: true });
  assert.match(out, /feature: tests\/features\/auth\/register\.feature/);
  assert.match(out, /plan: p\.plan\.md/);
  assert.match(out, /tests: tests\/bdd\/step_defs\/test_register\.py/); // folds in artifact_registered
  assert.equal(/freeze-check/.test(out), false); // no event timeline
});

test("formatAuditHistory handles an empty log", () => {
  assert.equal(formatAuditHistory([]), "No audit history.");
});

test("recordControlCommand returns null when no plan file can attribute the command", () => {
  const cwd = mkdtempSync(join(tmpdir(), "audit-"));
  const result = recordControlCommand({
    cwd, cfg: CONFIG, command: "/box", op: "set", args: "auth",
    before: box(), after: box({ inScope: ["auth"] }), planStatus: "MISSING", result: "Feature Box set to module: auth",
  });
  assert.equal(result, null);
});
