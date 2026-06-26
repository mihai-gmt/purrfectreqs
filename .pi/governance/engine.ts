import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { CONFIG, PATTERNS, PROSE_RULES, loadHarnessConfig, type GovernanceConfig } from "./config.ts";
import { recordControlCommand, auditFilePath, parseAuditLines, formatAuditHistory } from "./audit.ts";

type Decision =
  | { action: "allow" }
  | { action: "block"; reason: string }
  | { action: "confirm"; reason: string };

const ALLOW: Decision = { action: "allow" };
const block = (reason: string): Decision => ({ action: "block", reason });
const confirm = (reason: string): Decision => ({ action: "confirm", reason });
const RANK = { allow: 0, confirm: 1, block: 2 } as const;
const escalate = (a: Decision, b: Decision): Decision => (RANK[b.action] > RANK[a.action] ? b : a);

let governanceConfig: GovernanceConfig = CONFIG;

const VALID_PHASES = ["IDLE", "PREPLAN", "PLANNING", "ITERATING", "WRITE_TESTS", "IMPLEMENTING", "REVIEWING"] as const;
const BOX_USAGE =
  "Usage: /box <status|history [--failed|--artifacts]|set <module>|clear|plan <plan-file>|freeze-check|allow-file <path>|allow-files-from-plan|clear-allowed-files|run-red <pytest-command>|run-green <pytest-command>|clear-test-state|allow-core <reason>|disallow-core|phase <PHASE>>";
type WorkflowPhase = (typeof VALID_PHASES)[number];
type PlanStatus = "DRAFT" | "FROZEN" | "UNKNOWN" | "MISSING";
type PathClass = "feature" | "analysis" | "plan" | "review" | "test" | "source" | "core" | "migration" | "doc" | "status" | "config" | "frontend" | "backlog" | "unknown";

type FeatureBoxState = {
  featureFile?: string | null;
  planFile?: string | null;
  phase: WorkflowPhase;
  inScope: string[];
  allowCore: boolean;
  allowCoreReason?: string | null;
  allowedFiles?: string[];
  allowedReadFiles?: string[];
  allowedWriteFiles?: string[];
  allowedTestFiles?: string[];
  allowedImplementationFiles?: string[];
  redConfirmed?: boolean;
  greenConfirmed?: boolean;
  redCommand?: string | null;
  greenCommand?: string | null;
  redCheckedAt?: string | null;
  greenCheckedAt?: string | null;
  redSummary?: string | null;
  greenSummary?: string | null;
  escalationApprovals?: string[];
};

const ALLOWED_MANIFEST_CLASSES: PathClass[] = ["test", "source", "core", "migration", "plan", "frontend"];
const FREEZE_REQUIRED_CHECKS = ["adversarial", "enrich", "testability"] as const;
const ESCALATION_RE = /escalation/i;
const UNRESOLVED_ESCALATION_RE = /(unresolved|unacknowledged|pending|open)/i;
const RESOLVED_ESCALATION_RE = /\b(no|none|resolved|acknowledged|closed)\b/i;

let editedPaths = new Set<string>();

const norm = (p: string) => p.replace(/^\.?\//, "").replace(/\\/g, "/");
const underAny = (path: string, dirs: string[]) => dirs.some((d) => norm(path).startsWith(norm(d) + "/") || norm(path) === norm(d));
const matchesAny = (path: string, res: RegExp[]) => res.some((re) => re.test(norm(path)));
const uniqueNorm = (paths: string[] = []) => [...new Set(paths.map(norm).filter(Boolean))];

export function moduleOf(path: string): string | null {
  const n = norm(path);
  // Static assets are app-shared, not module-scoped.
  if (n.startsWith(norm(governanceConfig.staticDir) + "/")) return null;
  // Templates are organised by module under app/templates/<module>/. Files directly
  // under app/templates (e.g. base.html) and underscore-prefixed shared dirs
  // (_macros, partials per FRONTEND.md §4) are app-shared, not module-scoped.
  if (n.startsWith(norm(governanceConfig.templatesDir) + "/")) {
    const t = n.match(new RegExp(`^${norm(governanceConfig.templatesDir)}/([^/]+)/.+`));
    if (!t || t[1].startsWith("_")) return null;
    return t[1];
  }
  const m = n.match(new RegExp(`^${governanceConfig.appRoot}/([^/]+)/`));
  return m ? m[1] : null;
}

function defaultFeatureBox(): FeatureBoxState {
  return {
    phase: "IDLE",
    inScope: [],
    allowCore: false,
    allowCoreReason: null,
    allowedFiles: [],
    allowedReadFiles: [],
    allowedWriteFiles: [],
    allowedTestFiles: [],
    allowedImplementationFiles: [],
    redConfirmed: false,
    greenConfirmed: false,
    redCommand: null,
    greenCommand: null,
    redCheckedAt: null,
    greenCheckedAt: null,
    redSummary: null,
    greenSummary: null,
    escalationApprovals: [],
  };
}

function featureBoxPath(cwd: string): string {
  return join(cwd, governanceConfig.featureBoxPath);
}

function readFeatureBox(cwd: string): FeatureBoxState {
  const fp = featureBoxPath(cwd);
  if (!existsSync(fp)) return defaultFeatureBox();
  try {
    const raw = JSON.parse(readFileSync(fp, "utf8"));
    const phase = VALID_PHASES.includes(raw.phase) ? raw.phase : "IDLE";
    return {
      ...defaultFeatureBox(),
      ...raw,
      phase,
      inScope: raw.inScope ?? raw.modules ?? [],
      allowCore: !!(raw.allowCore ?? raw.protectedOverride),
    };
  } catch {
    return defaultFeatureBox();
  }
}

function writeFeatureBox(cwd: string, patch: Partial<FeatureBoxState>): FeatureBoxState {
  const fp = featureBoxPath(cwd);
  mkdirSync(dirname(fp), { recursive: true });
  const next = { ...readFeatureBox(cwd), ...patch };
  writeFileSync(fp, JSON.stringify(next, null, 2) + "\n", "utf8");
  return next;
}

function readPlanStatus(cwd: string, box: FeatureBoxState): PlanStatus {
  if (!box.planFile) return "MISSING";
  const fp = join(cwd, norm(box.planFile));
  if (!existsSync(fp)) return "MISSING";
  try {
    const content = readFileSync(fp, "utf8");
    const match = content.match(/^\s*(?:\*\*)?Status(?:\*\*)?\s*:\s*(?:\*\*)?\s*(DRAFT|FROZEN)\b/im);
    return match ? (match[1].toUpperCase() as PlanStatus) : "UNKNOWN";
  } catch {
    return "MISSING";
  }
}

function planFrozenGate(cwd: string, box: FeatureBoxState): Decision | null {
  if (box.phase !== "WRITE_TESTS" && box.phase !== "IMPLEMENTING") return null;
  const status = readPlanStatus(cwd, box);
  if (status === "FROZEN") return null;
  return block(
    `PLAN IS NOT FROZEN\nThe plan must be frozen before writing tests or implementing.\n` +
      `Current plan status: ${status}. Plan file: ${box.planFile || "(not set)"}.\n` +
      `Run: /iterate <feature-file> freeze`,
  );
}

function loadFeatureBox(cwd: string): { inScope: string[]; allowCore: boolean } | null {
  const box = readFeatureBox(cwd);
  return box.inScope.length > 0 || box.allowCore ? { inScope: box.inScope, allowCore: box.allowCore } : null;
}

function allowedTestFiles(box: FeatureBoxState): string[] {
  return uniqueNorm([...(box.allowedFiles ?? []), ...(box.allowedTestFiles ?? [])]);
}

function allowedImplementationFiles(box: FeatureBoxState): string[] {
  return uniqueNorm([...(box.allowedFiles ?? []), ...(box.allowedImplementationFiles ?? [])]);
}

function isDirectChildWithSuffix(path: string, dir: string, suffix: string): boolean {
  const p = norm(path).toLowerCase();
  const d = norm(dir).toLowerCase();
  const s = suffix.toLowerCase();
  if (!p.startsWith(d + "/") || !p.endsWith(s)) return false;
  return !p.slice(d.length + 1).includes("/");
}

export function classifyPath(path: string): PathClass {
  const p = norm(path).toLowerCase();
  if (p.endsWith(governanceConfig.featureExt) && (governanceConfig.featureDirs.length === 0 || underAny(p, governanceConfig.featureDirs) || p.endsWith(governanceConfig.featureExt))) return "feature";
  if (isDirectChildWithSuffix(p, governanceConfig.planDir, governanceConfig.analysisSuffix)) return "analysis";
  if (isDirectChildWithSuffix(p, governanceConfig.planDir, governanceConfig.planSuffix)) return "plan";
  if (isDirectChildWithSuffix(p, governanceConfig.planDir, governanceConfig.reviewSuffix)) return "review";
  if (underAny(p, governanceConfig.testDirs) && p.endsWith(".py")) return "test";
  if (underAny(p, [governanceConfig.coreDir])) return "core";
  if (p.startsWith(governanceConfig.appRoot + "/") && p.endsWith(".py")) return "source";
  if (p.startsWith(norm(governanceConfig.templatesDir).toLowerCase() + "/") || p.startsWith(norm(governanceConfig.staticDir).toLowerCase() + "/")) return "frontend";
  if (p.startsWith(governanceConfig.migrationsDir + "/")) return "migration";
  if (p === norm(governanceConfig.statusDoc).toLowerCase()) return "status";
  if (p.startsWith(norm(governanceConfig.docsDir).toLowerCase() + "/") && p.endsWith(".md")) return "doc";
  if (p === norm(governanceConfig.backlogFile).toLowerCase()) return "backlog";
  if (matchesAny(p, governanceConfig.depFiles) || matchesAny(p, governanceConfig.configFiles)) return "config";
  return "unknown";
}

function hardPathBlock(p: string): Decision | null {
  const path = norm(p);
  if (path.endsWith(governanceConfig.featureExt)) return block(`'${path}' is a .feature contract and must not be modified by the agent.`);
  if (matchesAny(path, governanceConfig.protectedPaths)) return block(`'${path}' is a protected path (.env / .git / .venv / node_modules) and cannot be edited.`);
  return null;
}

function phaseRules(p: string, cwd: string): Decision | null {
  const path = norm(p);
  const box = readFeatureBox(cwd);
  const phase = box.phase;
  const klass = classifyPath(path);

  const frozenGate = planFrozenGate(cwd, box);
  if (frozenGate) return frozenGate;

  if (phase === "IMPLEMENTING" && !box.redConfirmed) {
    return block(`IMPLEMENTING requires RED confirmation. Run failing tests with /box run-red <pytest-command>.`);
  }
  if (phase === "REVIEWING" && !box.greenConfirmed) {
    return block(`REVIEWING requires GREEN confirmation. Run passing tests with /box run-green <pytest-command>.`);
  }

  if (phase === "IDLE") return null;
  if (phase === "PREPLAN") return klass === "analysis" || klass === "backlog" ? null : block(`In PREPLAN, only ${governanceConfig.planDir}/*${governanceConfig.analysisSuffix} or ${governanceConfig.backlogFile} may be written. '${path}' is ${klass}.`);
  if (phase === "PLANNING") return klass === "plan" || klass === "backlog" ? null : block(`In PLANNING, only ${governanceConfig.planDir}/*${governanceConfig.planSuffix} or ${governanceConfig.backlogFile} may be written. '${path}' is ${klass}.`);
  if (phase === "ITERATING") return klass === "plan" || klass === "backlog" ? null : block(`In ITERATING, only ${governanceConfig.planDir}/*${governanceConfig.planSuffix} or ${governanceConfig.backlogFile} may be written. '${path}' is ${klass}.`);
  if (phase === "WRITE_TESTS") {
    if (klass !== "test") return block(`In WRITE_TESTS, only Python test files under ${governanceConfig.testDirs.join(" or ")} may be written. '${path}' is ${klass}.`);
    const files = allowedTestFiles(box);
    if (files.length === 0) return block(`WRITE_TESTS has no allowedTestFiles configured. Use /box allow-file <path> for each test file approved by the frozen plan.`);
    if (!files.includes(path)) return block(`WRITE_TESTS blocked: '${path}' is not listed in allowedTestFiles. Use /box allow-file <path> if approved by the frozen plan.`);
    return null;
  }
  if (phase === "IMPLEMENTING") {
    // The project status ledger is phase-gated, not manifest-gated: it is the one doc
    // the workflow expects to change on completion (plan Section 14 + CLAUDE.md), so it
    // is writable here without an allowlist entry and is never manifest-importable.
    if (klass === "status") return null;
    if (!(klass === "source" || klass === "core" || klass === "migration" || klass === "plan" || klass === "frontend")) {
      return block(`In IMPLEMENTING, source, frontend (template/static), migration, plan checkbox updates, or ${governanceConfig.statusDoc} may be written. '${path}' is ${klass}.`);
    }
    const files = allowedImplementationFiles(box);
    if (files.length === 0) return block(`IMPLEMENTING has no allowedImplementationFiles configured. Use /box allow-file <path> for each implementation file approved by the frozen plan.`);
    if (!files.includes(path)) return block(`IMPLEMENTING blocked: '${path}' is not listed in allowedImplementationFiles. Use /box allow-file <path> if approved by the frozen plan.`);
    return null;
  }
  if (phase === "REVIEWING") return klass === "review" || klass === "status" ? null : block(`In REVIEWING, only ${governanceConfig.planDir}/*${governanceConfig.reviewSuffix} or ${governanceConfig.statusDoc} may be written. '${path}' is ${klass}.`);
  return block(`Unknown workflow phase '${phase}'. Use /phase set <phase> or /phase clear.`);
}

function featureBoxRules(p: string, cwd: string): Decision | null {
  const path = norm(p);
  const box = loadFeatureBox(cwd);
  const mod = moduleOf(path);
  if (underAny(path, [governanceConfig.coreDir])) {
    if (!box?.allowCore) return block(`'${path}' is under ${governanceConfig.coreDir}. Use /box allow-core <reason> or escalate.`);
    return null;
  }
  if (box && mod && mod !== "core" && box.inScope.length > 0 && !box.inScope.includes(mod)) {
    return block(`Cross-module edit: '${path}' is in module '${mod}', not in Feature Box [${box.inScope.join(", ")}].`);
  }
  return null;
}

function softPathConfirm(p: string): Decision | null {
  const path = norm(p);
  if (governanceConfig.authorityDocs.some((d) => path === norm(d))) return confirm(`'${path}' is an authority document. Confirm intent.`);
  if (matchesAny(path, governanceConfig.depFiles)) return confirm(`Changing a dependency file ('${path}'). New dependencies require approval.`);
  if (matchesAny(path, governanceConfig.configFiles)) return confirm(`Editing config/env ('${path}') may introduce a new env var. Confirm intent.`);
  if (underAny(path, governanceConfig.authDirs)) return confirm(`Editing auth flow ('${path}') is security-critical. Confirm intent.`);
  return null;
}

function contentRules(p: string, content: string): Decision | null {
  const path = norm(p);
  if (PATTERNS.utcUtcnow.test(content)) return block(`Uses the deprecated naive utcnow() call. Use the timezone-aware now(UTC) form.`);
  if (PATTERNS.utcNowNaive.test(content)) return block(`Uses a naive now() with no tz argument. Use the timezone-aware now(UTC) form.`);
  if (PATTERNS.storageToken.test(content)) return block(`Stores a token in browser storage — forbidden by SECURITY.md.`);

  const mod = moduleOf(path);
  let cm: RegExpExecArray | null;
  PATTERNS.crossModelImport.lastIndex = 0;
  while ((cm = PATTERNS.crossModelImport.exec(content))) {
    const importedMod = cm[1];
    if (mod && importedMod !== mod && importedMod !== "core") return block(`Cross-module model import: module '${mod}' imports app.${importedMod}.models.`);
  }

  const depFile = matchesAny(path, governanceConfig.depFiles);
  for (const dep of governanceConfig.bannedDeps) {
    const tok = dep.replace(/[-/]/g, "[-_]");
    const inCode = new RegExp(`\\b(import|from)\\s+${tok}\\b`).test(content);
    const inDeps = depFile && new RegExp(`(^|\\n)\\s*${tok}\\b`, "i").test(content);
    if (inCode || inDeps) return block(`Adds banned dependency '${dep}' (not approved — see SCOPE.md).`);
  }

  if (PATTERNS.hardcodedSecret.test(content)) return confirm(`Possible hardcoded secret/credential in '${path}'. Confirm this is not real.`);
  return null;
}

function evaluateEdit(path: string, content: string, cwd: string): Decision {
  const p = norm(path);
  const hard = hardPathBlock(p);
  if (hard) return hard;
  const inv = contentRules(p, content);
  if (inv && inv.action === "block") return inv;
  const phase = phaseRules(p, cwd);
  if (phase) return phase;
  const boxd = featureBoxRules(p, cwd);
  if (boxd) return boxd;
  if (inv) return inv;
  const soft = softPathConfirm(p);
  if (soft) return soft;
  if (p.endsWith(governanceConfig.modelsFileHint)) {
    editedPaths.add(p);
    const hasMigration = [...editedPaths].some((x) => norm(x).startsWith(norm(governanceConfig.migrationsDir)));
    if (!hasMigration) return confirm(`Editing a model file ('${p}') without a migration under ${governanceConfig.migrationsDir} this session.`);
  }
  editedPaths.add(p);
  return ALLOW;
}

function evaluateWritePath(path: string, cwd: string): Decision {
  const p = norm(path);
  return hardPathBlock(p) ?? phaseRules(p, cwd) ?? featureBoxRules(p, cwd) ?? softPathConfirm(p) ?? ALLOW;
}

export function extractBashWriteTargets(command: string): { targets: string[]; writeIntent: boolean; unparseable: boolean } {
  const targets = new Set<string>();
  let writeIntent = false;
  let unparseable = false;
  const unquote = (s: string) => s.replace(/^["']|["']$/g, "");
  const pathLike = /(?:^|\s)((?:\.\/)?[\w.@+-]*\/[\w./@+-]+)/g;
  const collectPathLike = () => {
    let m: RegExpExecArray | null;
    pathLike.lastIndex = 0;
    while ((m = pathLike.exec(command))) targets.add(unquote(m[1]));
  };
  const addLastNonOptionArg = (tokens: string[]) => {
    const args = tokens.slice(1).filter((token) => token && !token.startsWith("-"));
    const target = args.at(-1);
    if (target) targets.add(unquote(target));
    else unparseable = true;
  };
  const addDdOutputArg = (tokens: string[]) => {
    const output = tokens.slice(1).find((token) => token.startsWith("of="));
    if (output?.slice(3)) targets.add(unquote(output.slice(3)));
    else unparseable = true;
  };
  const redir = /(?:^|\s)\d*>>?\s*("[^"]+"|'[^']+'|[^\s|&;<>]+)/g;
  let r: RegExpExecArray | null;
  while ((r = redir.exec(command))) { writeIntent = true; targets.add(unquote(r[1])); }
  if (/\btee\b/.test(command)) { writeIntent = true; collectPathLike(); }
  if (/\b(sed|perl)\s+-\S*i/.test(command)) { writeIntent = true; collectPathLike(); }
  const tokens = tokenizeCommand(command);
  if (tokens && ["cp", "mv", "install"].includes(tokens[0])) { writeIntent = true; addLastNonOptionArg(tokens); }
  if (tokens && tokens[0] === "dd") { writeIntent = true; addDdOutputArg(tokens); }
  const openWrite = /open\(\s*["']([^"']+)["']\s*,\s*["'][^"']*[wax][^"']*["']/g;
  let o: RegExpExecArray | null;
  while ((o = openWrite.exec(command))) { writeIntent = true; targets.add(o[1]); }
  const list = [...targets].filter(Boolean);
  return { targets: list, writeIntent, unparseable: unparseable || (writeIntent && list.length === 0) };
}

function evaluateBashWrite(command: string, cwd: string): Decision {
  const { targets, writeIntent, unparseable } = extractBashWriteTargets(command);
  if (!writeIntent) return ALLOW;
  let decision: Decision = ALLOW;
  for (const t of targets) decision = escalate(decision, evaluateWritePath(t, cwd));
  if (unparseable) decision = escalate(decision, confirm(`Command appears to write a file but target could not be parsed safely.`));
  return decision;
}

function evaluateBash(command: string, cwd: string): Decision {
  const c = command.trim();
  for (const re of governanceConfig.bashDangerous) if (re.test(c)) return confirm(`Potentially dangerous command: '${c}'. Confirm before running.`);
  const writeDecision = evaluateBashWrite(c, cwd);
  if (writeDecision.action !== "allow") return writeDecision;
  const allowed = governanceConfig.bashAllowlist.some((prefix) => c === prefix || c.startsWith(prefix + " "));
  if (allowed) return ALLOW;
  return confirm(`'${c.split(/\s+/)[0]}' is not on the governance allowlist. Approve this command?`);
}

function extractToolContent(input: any): string {
  const parts: string[] = [];
  for (const key of ["content", "new_string", "newString", "newText", "text"]) if (input?.[key] != null) parts.push(String(input[key]));
  if (Array.isArray(input?.edits)) {
    for (const edit of input.edits) {
      for (const key of ["newText", "new_string", "newString", "replacement", "text", "content"]) if (edit?.[key] != null) parts.push(String(edit[key]));
    }
  }
  return parts.join("\n");
}

function extractManifestPath(line: string): string | null {
  const backtick = line.match(/`([^`]+)`/);
  const candidate = backtick ? backtick[1] : line.replace(/^\s*[-*]\s+/, "").trim().split(/\s+[-–—]\s+|\s+#\s+/)[0];
  const path = norm(candidate.replace(/^["']|["']$/g, ""));
  if (!path || path.includes(":")) return null;
  if (!/[./]/.test(path)) return null;
  return path;
}

function numberedSectionLines(content: string, sectionNumber: number): string[] | null {
  const lines = content.split(/\r?\n/);
  const start = lines.findIndex((line) => new RegExp(`^\\s*(?:#{1,6}\\s*)?(?:section\\s+)?${sectionNumber}\\b`, "i").test(line));
  if (start < 0) return null;
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    if (new RegExp(`^\\s*(?:#{1,6}\\s*)?(?:section\\s+)?${sectionNumber + 1}\\b`, "i").test(lines[i])) { end = i; break; }
  }
  return lines.slice(start + 1, end);
}

function section14Lines(content: string): string[] | null { return numberedSectionLines(content, 14); }

export function freezeCheck(content: string): { ok: boolean; report: string } {
  const lines = numberedSectionLines(content, 15);
  if (!lines) return { ok: false, report: "FAIL: Section 15 changelog not found." };
  const body = lines.join("\n");
  const checks = FREEZE_REQUIRED_CHECKS.map((name) => ({ name, ok: new RegExp(name, "i").test(body) }));
  const unresolvedEscalations = lines.filter((line) => ESCALATION_RE.test(line) && UNRESOLVED_ESCALATION_RE.test(line) && !RESOLVED_ESCALATION_RE.test(line));
  const failures = checks.filter((check) => !check.ok).map((check) => `missing ${check.name} changelog entry`);
  if (unresolvedEscalations.length) failures.push(`unresolved escalation text: ${unresolvedEscalations.join(" | ")}`);
  if (failures.length) return { ok: false, report: `FAIL:\n- ${failures.join("\n- ")}` };
  return { ok: true, report: "PASS: freeze prerequisites satisfied (adversarial, enrich, testability, no unresolved escalations)." };
}

type ManifestSectionKind = "test" | "implementation" | "byclass" | null;

type PlanManifestParseResult = {
  testFiles: string[];
  implementationFiles: string[];
  skipped: string[];
  warnings: string[];
  error?: string;
};

function isManifestSectionLabel(line: string): boolean {
  return /^\s*#{1,6}\s+/.test(line) || /\b(files?|implementation files?|test files?)\b.*\b(read|create|modify|before|during|while)\b/i.test(line);
}

function manifestSectionKind(line: string): ManifestSectionKind {
  const lower = line.toLowerCase();
  if (/\bread\b|before\s+(?:writing\s+tests|implementing|implementation)/i.test(lower)) return null;
  if (/test files?.*(?:create|modify)|(?:create|modify|create\/modify|create or modify).*(?:writing tests|test writing|tests)/i.test(lower)) return "test";
  if (/implementation files?.*(?:create|modify)|(?:create|modify|create\/modify|create or modify).*(?:implementing|implementation)/i.test(lower)) return "implementation";
  // Canonical PLAN_TEMPLATE.md format: "Files to CREATE" / "Files to MODIFY" tables that
  // mix test and implementation files. Route each row by its path class instead of header.
  if (/\bfiles?\s+to\s+(?:create|modify)\b/i.test(lower)) return "byclass";
  return null;
}

export function parseAllowedFilesFromPlan(content: string): PlanManifestParseResult {
  const lines = section14Lines(content);
  if (!lines) return { testFiles: [], implementationFiles: [], skipped: [], warnings: [], error: "Section 14 not found in plan file." };
  const testFiles = new Set<string>();
  const implementationFiles = new Set<string>();
  const skipped: string[] = [];
  const warnings: string[] = [];
  let currentKind: ManifestSectionKind = null;
  let sawWriteSection = false;

  for (const line of lines) {
    if (isManifestSectionLabel(line)) {
      currentKind = manifestSectionKind(line);
      if (currentKind) sawWriteSection = true;
      continue;
    }
    if (!currentKind) continue;
    if (!/^\s*[-*]\s+|`[^`]+`/.test(line)) continue;
    const path = extractManifestPath(line);
    if (!path) continue;
    const hard = hardPathBlock(path);
    if (hard) { skipped.push(`${path} (${hard.reason})`); continue; }
    const klass = classifyPath(path);
    if (currentKind === "test") {
      if (klass !== "test") { skipped.push(`${path} (${klass} listed in test write section)`); continue; }
      testFiles.add(path);
      continue;
    }
    // "byclass" (template CREATE/MODIFY): a test file routes to the test allowlist.
    if (currentKind === "byclass" && klass === "test") { testFiles.add(path); continue; }
    // "implementation": a test file here is a manifest error and is skipped.
    if (currentKind === "implementation" && klass === "test") { skipped.push(`${path} (test file listed in implementation write section)`); continue; }
    if (!ALLOWED_MANIFEST_CLASSES.includes(klass)) { skipped.push(`${path} (${klass})`); continue; }
    implementationFiles.add(path);
  }

  if (!sawWriteSection) warnings.push("Section 14 found, but no recognized test or implementation write subsection was found.");
  if (sawWriteSection && testFiles.size === 0 && implementationFiles.size === 0) warnings.push("Recognized write subsection(s), but no valid writable files were found.");
  return { testFiles: [...testFiles], implementationFiles: [...implementationFiles], skipped, warnings };
}

function hasShellControl(command: string): boolean {
  return /(;|&&|\|\||\||>>?|`|\$\()/.test(command);
}

function tokenizeCommand(command: string): string[] | null {
  const tokens: string[] = [];
  const re = /"([^"]*)"|'([^']*)'|(\S+)/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(command))) tokens.push(match[1] ?? match[2] ?? match[3]);
  return tokens.length > 0 ? tokens : null;
}

export function parsePytestCommand(command: string): { ok: true; executable: string; args: string[] } | { ok: false; reason: string } {
  const trimmed = command.trim();
  if (!trimmed) return { ok: false, reason: "Missing pytest command." };
  if (hasShellControl(trimmed)) return { ok: false, reason: "Rejected shell control operator. Use a plain pytest command without pipes, redirects, command chaining, or command substitution." };
  const tokens = tokenizeCommand(trimmed);
  if (!tokens) return { ok: false, reason: "Could not parse pytest command." };
  if (tokens[0] === "pytest") return { ok: true, executable: "pytest", args: tokens.slice(1) };
  if (tokens[0] === "python" && tokens[1] === "-m" && tokens[2] === "pytest") return { ok: true, executable: "python", args: tokens.slice(1) };
  return { ok: false, reason: "Only commands starting with 'pytest' or 'python -m pytest' are allowed." };
}

function compactOutput(output: string): string {
  return output
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(-12)
    .join("\n")
    .slice(0, 2000);
}

/**
 * Resolve a test command's interpreter to the project venv binary when one exists,
 * so RED/GREEN gates work whether or not the developer activated the venv before
 * launching Pi. Only the known interpreters (`pytest`, `python`) are rewritten;
 * anything else is returned unchanged. Falls back to the bare name (PATH lookup)
 * when `.venv/bin/<exe>` is absent. Mirrors the Makefile's venv-explicit invocation.
 */
export function resolveTestExecutable(executable: string, cwd: string): string {
  if (executable !== "pytest" && executable !== "python") return executable;
  const venvBin = join(cwd, ".venv", "bin", executable);
  return existsSync(venvBin) ? venvBin : executable;
}

function runPytest(command: string, cwd: string): { ok: true; exitCode: number | null; output: string; summary: string } | { ok: false; reason: string } {
  const parsed = parsePytestCommand(command);
  if (!parsed.ok) return parsed;
  const executable = resolveTestExecutable(parsed.executable, cwd);
  const result = spawnSync(executable, parsed.args, { cwd, encoding: "utf8", timeout: 120_000, shell: false });
  const output = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
  if (result.error) return { ok: false, reason: `Could not run pytest command: ${result.error.message}` };
  return { ok: true, exitCode: result.status, output, summary: compactOutput(output) };
}

function isInfrastructureFailure(output: string): boolean {
  return /(ImportError|ModuleNotFoundError|SyntaxError|collected 0 items|ERROR collecting)/i.test(output);
}

export function isValidRed(result: { exitCode: number | null; output: string }): boolean {
  return result.exitCode !== 0 && !isInfrastructureFailure(result.output) && /(FAILED|failed|assert)/.test(result.output);
}

export function isValidGreen(result: { exitCode: number | null; output: string }): boolean {
  return result.exitCode === 0 && /\bpassed\b/i.test(result.output) && !/no tests ran/i.test(result.output) && !isInfrastructureFailure(result.output);
}

function handleRunRed(args: string, cwd: string): { result: string } {
  const result = runPytest(args, cwd);
  if (!result.ok) return { result: `RED not confirmed: ${result.reason}` };
  if (!isValidRed(result)) return { result: `RED not confirmed: pytest did not show a valid failing test. Exit code: ${result.exitCode}.\n${result.summary}` };
  writeFeatureBox(cwd, {
    redConfirmed: true,
    greenConfirmed: false,
    redCommand: args,
    greenCommand: null,
    redCheckedAt: new Date().toISOString(),
    redSummary: result.summary,
  });
  return { result: `RED confirmed by pytest execution. Exit code: ${result.exitCode}.\n${result.summary}` };
}

function handleRunGreen(args: string, cwd: string): { result: string } {
  const result = runPytest(args, cwd);
  if (!result.ok) return { result: `GREEN not confirmed: ${result.reason}` };
  if (!isValidGreen(result)) return { result: `GREEN not confirmed: pytest did not pass cleanly. Exit code: ${result.exitCode}.\n${result.summary}` };
  writeFeatureBox(cwd, {
    greenConfirmed: true,
    greenCommand: args,
    greenCheckedAt: new Date().toISOString(),
    greenSummary: result.summary,
  });
  return { result: `GREEN confirmed by pytest execution. Exit code: ${result.exitCode}.\n${result.summary}` };
}

function formatGovernanceStatusLine(cwd: string): string {
  const box = readFeatureBox(cwd);
  const planStatus = readPlanStatus(cwd, box);
  const scope = box.inScope.length ? box.inScope.join(",") : "-";
  const red = box.redConfirmed ? "yes" : "no";
  const green = box.greenConfirmed ? "yes" : "no";
  return `Gov ${box.phase} | Plan: ${planStatus} | RED: ${red} | GREEN: ${green} | Box: ${scope}`;
}

function formatFeatureBoxStatus(cwd: string): string {
  const box = readFeatureBox(cwd);
  const planStatus = readPlanStatus(cwd, box);
  const tests = allowedTestFiles(box);
  const impl = allowedImplementationFiles(box);
  const gates: string[] = [];
  if (box.phase === "WRITE_TESTS") {
    gates.push(`plan frozen: ${planStatus === "FROZEN" ? "PASS" : `BLOCKED (${planStatus})`}`);
    gates.push(`allowed test files: ${tests.length || "BLOCKED (none)"}`);
  } else if (box.phase === "IMPLEMENTING") {
    gates.push(`plan frozen: ${planStatus === "FROZEN" ? "PASS" : `BLOCKED (${planStatus})`}`);
    gates.push(`RED: ${box.redConfirmed ? "PASS" : "BLOCKED"}`);
    gates.push(`allowed implementation files: ${impl.length || "BLOCKED (none)"}`);
  } else if (box.phase === "REVIEWING") {
    gates.push(`GREEN: ${box.greenConfirmed ? "PASS" : "BLOCKED"}`);
    gates.push(`write mode: review artifact only (${governanceConfig.planDir}/*${governanceConfig.reviewSuffix})`);
  } else {
    gates.push("no RED/GREEN phase gate active");
  }

  const lines = [
    "Governance Feature Box Status",
    `phase: ${box.phase}`,
    `inScope: ${box.inScope.length ? box.inScope.join(", ") : "(none)"}`,
    `allowCore: ${box.allowCore}${box.allowCoreReason ? ` (${box.allowCoreReason})` : ""}`,
    `planFile: ${box.planFile || "(not set)"}`,
    `planStatus: ${planStatus}`,
    `RED: ${box.redConfirmed ? "confirmed" : "not confirmed"}${box.redCommand ? ` — ${box.redCommand}` : ""}`,
    `GREEN: ${box.greenConfirmed ? "confirmed" : "not confirmed"}${box.greenCommand ? ` — ${box.greenCommand}` : ""}`,
    `allowedTestFiles (${tests.length}):`,
    ...(tests.length ? tests.map((file) => `  - ${file}`) : ["  (none)"]),
    `allowedImplementationFiles (${impl.length}):`,
    ...(impl.length ? impl.map((file) => `  - ${file}`) : ["  (none)"]),
    "active gates:",
    ...gates.map((gate) => `  - ${gate}`),
  ];
  return lines.join("\n");
}

function handlePhaseSet(args: string, cwd: string): { result: string } {
  const phase = args.trim().toUpperCase();
  if (!VALID_PHASES.includes(phase as WorkflowPhase)) return { result: `Usage: /phase set <${VALID_PHASES.join("|")}>` };
  writeFeatureBox(cwd, { phase: phase as WorkflowPhase });
  return { result: `Workflow phase set to ${phase}.` };
}

function handleBoxCommand(cmdText: string, cwd: string): { result: string } | undefined {
  const m = cmdText.match(/^\/box\s+([\w-]+)(?:\s+(.*))?$/);
  if (!m) return undefined;
  const sub = m[1].toLowerCase();
  const args = String(m[2] ?? "").trim();
  if (sub === "status") {
    if (args === "--verbose") return { result: formatFeatureBoxStatus(cwd) };
    if (args) return { result: "Usage: /box status [--verbose]" };
    return { result: JSON.stringify(readFeatureBox(cwd), null, 2) };
  }
  if (sub === "history") {
    const box = readFeatureBox(cwd);
    if (!box.planFile) return { result: "No active feature (no planFile). Run /box plan <plan-file> first." };
    const file = auditFilePath(cwd, box.planFile);
    if (!file || !existsSync(file)) return { result: `No audit log yet for this feature.${file ? ` Expected: ${file}` : ""}` };
    const flags = args.split(/\s+/).filter(Boolean);
    const opts = { failed: flags.includes("--failed"), artifactsOnly: flags.includes("--artifacts") };
    return { result: formatAuditHistory(parseAuditLines(readFileSync(file, "utf8")), opts) };
  }
  if (sub === "set") { if (!args || args.split(/\s+/).length > 1) return { result: "Usage: /box set <module>" }; writeFeatureBox(cwd, { inScope: [args] }); return { result: `Feature Box set to module: ${args}` }; }
  if (sub === "clear") { writeFeatureBox(cwd, defaultFeatureBox()); return { result: "Feature Box cleared." }; }
  if (sub === "plan") { if (!args || args.split(/\s+/).length > 1) return { result: "Usage: /box plan <plan-file>" }; writeFeatureBox(cwd, { planFile: norm(args) }); return { result: `Feature Box plan file set to: ${norm(args)}` }; }
  if (sub === "allow-file") {
    if (!args || args.split(/\s+/).length > 1) return { result: "Usage: /box allow-file <path>" };
    const file = norm(args);
    const hard = hardPathBlock(file);
    if (hard) return { result: `Rejected: ${hard.reason}` };
    const klass = classifyPath(file);
    if (!ALLOWED_MANIFEST_CLASSES.includes(klass)) return { result: `Rejected: /box allow-file accepts only test, source, frontend, core, migration, or plan files. '${file}' is ${klass}.` };
    const box = readFeatureBox(cwd);
    if (klass === "test") {
      const allowedTestFiles = uniqueNorm([...(box.allowedTestFiles ?? []), file]);
      writeFeatureBox(cwd, { allowedTestFiles });
      return { result: `Allowed test file: ${file}` };
    }
    const allowedImplementationFiles = uniqueNorm([...(box.allowedImplementationFiles ?? []), file]);
    writeFeatureBox(cwd, { allowedImplementationFiles });
    return { result: `Allowed implementation file: ${file} (${klass})` };
  }
  if (sub === "clear-allowed-files") {
    writeFeatureBox(cwd, { allowedFiles: [], allowedReadFiles: [], allowedWriteFiles: [], allowedTestFiles: [], allowedImplementationFiles: [] });
    return { result: "Allowed file manifests cleared." };
  }
  if (sub === "freeze-check") {
    const box = readFeatureBox(cwd);
    if (!box.planFile) return { result: "FAIL: planFile is not set. Use /box plan <plan-file>." };
    const fp = join(cwd, norm(box.planFile));
    if (!existsSync(fp)) return { result: `FAIL: plan file not found: ${box.planFile}` };
    return { result: freezeCheck(readFileSync(fp, "utf8")).report };
  }
  if (sub === "allow-files-from-plan") {
    const box = readFeatureBox(cwd);
    if (!box.planFile) return { result: "Cannot import allowed files: planFile is not set. Use /box plan <plan-file>." };
    const status = readPlanStatus(cwd, box);
    if (status !== "FROZEN") return { result: `Cannot import allowed files: plan status is ${status}, not FROZEN.` };
    const fp = join(cwd, norm(box.planFile));
    if (!existsSync(fp)) return { result: `Cannot import allowed files: plan file not found: ${box.planFile}` };
    const parsed = parseAllowedFilesFromPlan(readFileSync(fp, "utf8"));
    if (parsed.error) return { result: parsed.error };
    const importedFiles = [...parsed.testFiles, ...parsed.implementationFiles];
    if (importedFiles.length === 0) {
      return { result: `No valid writable files found in Section 14.` + (parsed.warnings.length ? `\nWarnings:\n${parsed.warnings.map((warning) => `- ${warning}`).join("\n")}` : "") + (parsed.skipped.length ? `\nSkipped:\n${parsed.skipped.map((file) => `- ${file}`).join("\n")}` : "") };
    }
    const allowedTestFiles = uniqueNorm([...(box.allowedTestFiles ?? []), ...parsed.testFiles]);
    const allowedImplementationFiles = uniqueNorm([...(box.allowedImplementationFiles ?? []), ...parsed.implementationFiles]);
    writeFeatureBox(cwd, { allowedTestFiles, allowedImplementationFiles });
    return { result: `Imported ${importedFiles.length} allowed file(s) from Section 14:\n` + importedFiles.map((file) => `- ${file}`).join("\n") + `\nTest files: ${parsed.testFiles.length}. Implementation files: ${parsed.implementationFiles.length}.` + (parsed.warnings.length ? `\nWarnings:\n${parsed.warnings.map((warning) => `- ${warning}`).join("\n")}` : "") + (parsed.skipped.length ? `\nSkipped:\n${parsed.skipped.map((file) => `- ${file}`).join("\n")}` : "") };
  }
  if (sub === "run-red") { if (!args) return { result: "Usage: /box run-red <pytest-command>" }; return handleRunRed(args, cwd); }
  if (sub === "run-green") { if (!args) return { result: "Usage: /box run-green <pytest-command>" }; return handleRunGreen(args, cwd); }
  if (sub === "mark-red") return { result: "DISABLED: /box mark-red is not available. Use /box run-red <pytest-command> to confirm RED by executing pytest." };
  if (sub === "mark-green") return { result: "DISABLED: /box mark-green is not available. Use /box run-green <pytest-command> to confirm GREEN by executing pytest." };
  if (sub === "clear-test-state") { writeFeatureBox(cwd, { redConfirmed: false, greenConfirmed: false, redCommand: null, greenCommand: null, redCheckedAt: null, greenCheckedAt: null, redSummary: null, greenSummary: null }); return { result: "RED/GREEN test state cleared." }; }
  if (sub === "allow-core") { writeFeatureBox(cwd, { allowCore: true, allowCoreReason: args || null }); return { result: `Core edits allowed. Reason: ${args || "(none provided)"}` }; }
  if (sub === "disallow-core") { writeFeatureBox(cwd, { allowCore: false, allowCoreReason: null }); return { result: "Core edits disallowed." }; }
  if (sub === "phase") return handlePhaseSet(args, cwd);
  return { result: BOX_USAGE };
}

function handlePhaseCommand(cmdText: string, cwd: string): { result: string } | undefined {
  const m = cmdText.match(/^\/phase\s+([\w-]+)(?:\s+(.*))?$/);
  if (!m) return undefined;
  const sub = m[1].toLowerCase();
  const args = String(m[2] ?? "").trim();
  if (sub === "status") {
    if (args === "--verbose") return { result: formatFeatureBoxStatus(cwd) };
    if (args) return { result: "Usage: /phase status [--verbose]" };
    const box = readFeatureBox(cwd);
    return { result: JSON.stringify({ phase: box.phase, inScope: box.inScope, allowCore: box.allowCore, allowCoreReason: box.allowCoreReason ?? null, redConfirmed: !!box.redConfirmed, greenConfirmed: !!box.greenConfirmed }, null, 2) };
  }
  if (sub === "set") return handlePhaseSet(args, cwd);
  if (sub === "clear") { writeFeatureBox(cwd, { phase: "IDLE" }); return { result: "Workflow phase cleared to IDLE." }; }
  return { result: `Usage: /phase <status|set <${VALID_PHASES.join("|")}>|clear>` };
}

// --- Stale-engine detection (C5) -------------------------------------------
// The governance extension is loaded once at Pi process start; /new does not
// reload it. If the source under .pi/governance changes on disk, the running
// process keeps the old code. We fingerprint the source files and surface a
// "restart Pi" marker on the status line when the on-disk build drifts from the
// build that was loaded into this process.
const ENGINE_SOURCE_FILES = ["engine.ts", "config.ts", "audit.ts"] as const;
let loadedEngineBuild: string | null = null;

/** Order-independent, mtime-sensitive fingerprint (FNV-1a 32-bit) for the source set. */
export function buildFingerprint(entries: { name: string; mtimeMs: number }[]): string {
  const canon = entries.map((e) => `${e.name}@${Math.floor(e.mtimeMs)}`).sort().join(";");
  let h = 2166136261;
  for (let i = 0; i < canon.length; i++) {
    h ^= canon.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

export function staleSuffix(loaded: string, current: string): string {
  if (!loaded || !current || loaded === "unknown" || current === "unknown") return "";
  return loaded === current ? "" : " | ⚠ ENGINE STALE — restart Pi";
}

function readGovernanceBuild(cwd: string): string {
  try {
    const dir = join(cwd, ".pi", "governance");
    const entries = ENGINE_SOURCE_FILES.map((name) => ({ name, mtimeMs: statSync(join(dir, name)).mtimeMs }));
    return buildFingerprint(entries);
  } catch {
    return "unknown";
  }
}

function auditControl(command: "/box" | "/phase", args: string, cwd: string, before: FeatureBoxState, result: string): void {
  const trimmed = args.trim();
  const op = (trimmed.split(/\s+/)[0] || "").toLowerCase();
  if (!op || op === "status" || op === "history") return; // pure reads are not logged
  const subargs = trimmed.slice(op.length).trim();
  const after = readFeatureBox(cwd);
  try {
    recordControlCommand({
      cwd,
      cfg: governanceConfig,
      command,
      op,
      args: subargs,
      before,
      after,
      planStatus: readPlanStatus(cwd, after),
      result,
    });
  } catch {
    // Logging must never break a command.
  }
}

export function createGovernanceEngine(config: GovernanceConfig = CONFIG) {
  const baseConfig = config;
  governanceConfig = baseConfig;
  return {
    handleSessionStart() {
      editedPaths = new Set();
    },
    getStatusLine(cwd: string) {
      governanceConfig = loadHarnessConfig(cwd, baseConfig);
      const currentBuild = readGovernanceBuild(cwd);
      // Baseline = the build observed on this process's first status render (≈ start).
      if (loadedEngineBuild === null) loadedEngineBuild = currentBuild;
      return formatGovernanceStatusLine(cwd) + staleSuffix(loadedEngineBuild, currentBuild);
    },
    async handleToolCall(event: any, ctx: any) {
      const tool = String(event.toolName ?? "").toLowerCase();
      const cwd: string = ctx.cwd ?? process.cwd();
      governanceConfig = loadHarnessConfig(cwd, baseConfig);
      const input: any = event.input ?? {};
      let decision: Decision = ALLOW;
      if (tool === "edit" || tool === "write" || tool === "multiedit") {
        const path: string | undefined = input.path ?? input.file_path ?? input.filePath;
        if (path) decision = evaluateEdit(path, extractToolContent(input), cwd);
      } else if (tool === "bash") {
        decision = evaluateBash(String(input.command ?? ""), cwd);
      }
      if (decision.action === "block") return { block: true, reason: `[governance] ${decision.reason}` };
      if (decision.action === "confirm") {
        if (!ctx.hasUI) return { block: true, reason: `[governance] ${decision.reason} (no UI for confirmation — blocked)` };
        const ok = await ctx.ui.confirm("Governance confirmation", `[governance] ${decision.reason}`);
        if (!ok) return { block: true, reason: `[governance] Denied by user: ${decision.reason}` };
      }
      return undefined;
    },
    handleBeforeAgentStart(event: any) {
      return { systemPrompt: event.systemPrompt + "\n\n" + PROSE_RULES };
    },
    // Invoked by pi.registerCommand handlers (human-initiated only — the LLM
    // cannot call slash commands). `args` is the text after "/box".
    runBoxCommand(args: string, cwd: string): string {
      governanceConfig = loadHarnessConfig(cwd, baseConfig);
      const before = readFeatureBox(cwd);
      const handled = handleBoxCommand(`/box ${args}`.trim(), cwd);
      const result = handled?.result ?? BOX_USAGE;
      auditControl("/box", args, cwd, before, result);
      return result;
    },
    runPhaseCommand(args: string, cwd: string): string {
      governanceConfig = loadHarnessConfig(cwd, baseConfig);
      const before = readFeatureBox(cwd);
      const handled = handlePhaseCommand(`/phase ${args}`.trim(), cwd);
      const result = handled?.result ?? `Usage: /phase <status|set <${VALID_PHASES.join("|")}>|clear>`;
      auditControl("/phase", args, cwd, before, result);
      return result;
    },
  };
}
