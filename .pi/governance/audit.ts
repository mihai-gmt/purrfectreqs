/**
 * Per-feature control-plane audit log.
 *
 * Append-only JSONL, one file per feature at `.pi/audit/<module>_<feature>.audit.jsonl`.
 * Records every state-changing /box and /phase command (human control plane), so a
 * feature's full workflow trajectory — including failed freeze attempts, RED/GREEN
 * re-runs, and phase back-steps — is reconstructable. The engine writes this; the model
 * never does.
 *
 * Record types (one per line):
 *  - header              : written once; schema, identity, initial artefact snapshot.
 *  - event               : one per logged command; outcome/attempt/phase movement.
 *  - artifact_registered : one per workflow file that appears after the header.
 */
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import type { GovernanceConfig } from "./config.ts";

export type AuditOutcome = "ok" | "failed" | "blocked" | "noop";

const SCHEMA_VERSION = 1;
const PLAN_SUFFIX = ".plan.md";
const norm = (p: string) => p.replace(/^\.?\//, "").replace(/\\/g, "/");

/** Map a handler's result string to a coarse outcome. Brittle by nature — the full
 *  `detail` line is preserved for humans, so this only needs to be roughly right. */
export function classifyAuditOutcome(result: string): AuditOutcome {
  const r = result.trim().toLowerCase();
  if (r.startsWith("rejected") || r.startsWith("usage:") || r.startsWith("disabled:") || r.includes("cannot ")) return "blocked";
  if (
    r.startsWith("fail") ||
    r.includes(": fail") ||
    r.includes("not confirmed") ||
    r.includes("no valid writable") ||
    r.includes("not set") ||
    r.includes("not found")
  )
    return "failed";
  return "ok";
}

/** `<module>_<feature>` from a plan path, or null if it is not a plan file. */
export function auditBaseName(planFile: string): string | null {
  const b = basename(norm(planFile));
  return b.endsWith(PLAN_SUFFIX) ? b.slice(0, -PLAN_SUFFIX.length) : null;
}

export function auditFilePath(cwd: string, planFile: string): string | null {
  const base = auditBaseName(planFile);
  return base ? join(cwd, ".pi", "audit", `${base}.audit.jsonl`) : null;
}

export function deriveIdentity(planFile: string, inScope: string[] = []): { feature: string; module: string; base: string } | null {
  const base = auditBaseName(planFile);
  if (!base) return null;
  const module = inScope[0] || base.split("_")[0];
  const feature = base.startsWith(`${module}_`) ? base.slice(module.length + 1) : base;
  return { feature, module, base };
}

export function parseAuditLines(content: string): any[] {
  return content
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter((record) => record != null);
}

/** Nth invocation of this command+op (counting this one). */
export function attemptNumber(records: any[], command: string, op: string): number {
  return records.filter((r) => r.type === "event" && r.command === command && r.op === op).length + 1;
}

/** Paths in `after` that were not in `before` (normalized). */
export function diffArtifacts(before: string[] = [], after: string[] = []): string[] {
  const seen = new Set(before.map(norm));
  return after.map(norm).filter((path) => !seen.has(path));
}

function firstLine(text: string): string {
  return (text.split(/\r?\n/)[0] ?? "").trim().slice(0, 300);
}

function shortTs(ts: string): string {
  const m = /(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(ts ?? "");
  return m ? `${m[2]}-${m[3]} ${m[4]}:${m[5]}` : (ts ?? "");
}

/**
 * Human-readable timeline over parsed audit records (drives `/box history`).
 * `failed`: only non-ok events. `artifactsOnly`: artefact registry instead of the timeline.
 */
export function formatAuditHistory(records: any[], opts: { failed?: boolean; artifactsOnly?: boolean } = {}): string {
  if (records.length === 0) return "No audit history.";
  const header = records.find((r) => r.type === "header");
  const lines: string[] = [];
  if (header) lines.push(`Audit: ${header.meta?.module}/${header.meta?.feature} (created ${shortTs(header.meta?.created)})`);

  if (opts.artifactsOnly) {
    const a = header?.artifacts ?? {};
    const regs = records.filter((r) => r.type === "artifact_registered");
    const tests = [...(a.tests ?? []), ...regs.filter((r) => r.artifact_kind === "test").map((r) => r.path)];
    const impl = [...(a.implementation ?? []), ...regs.filter((r) => r.artifact_kind === "implementation").map((r) => r.path)];
    lines.push("Artifacts:");
    lines.push(`  feature: ${a.feature ?? "-"}`);
    lines.push(`  analysis: ${a.analysis ?? "-"}`);
    lines.push(`  plan: ${a.plan ?? "-"}`);
    lines.push(`  review: ${a.review ?? "-"}`);
    lines.push(`  tests: ${tests.length ? tests.join(", ") : "-"}`);
    lines.push(`  implementation: ${impl.length ? impl.join(", ") : "-"}`);
    return lines.join("\n");
  }

  const headerLineCount = lines.length;
  for (const r of records) {
    if (r.type === "header") continue;
    if (r.type === "artifact_registered") {
      if (opts.failed) continue;
      lines.push(`  #${r.seq} ${shortTs(r.ts)} + ${r.artifact_kind}: ${r.path}`);
      continue;
    }
    if (r.type === "event") {
      if (opts.failed && r.outcome === "ok") continue;
      const phase = r.phase_from !== r.phase_to ? ` [${r.phase_from}→${r.phase_to}]` : "";
      const args = r.args ? ` ${r.args}` : "";
      const attempt = r.attempt && r.attempt > 1 ? ` (attempt ${r.attempt})` : "";
      const detail = r.detail ? ` — ${r.detail}` : "";
      lines.push(`  #${r.seq} ${shortTs(r.ts)} ${r.command} ${r.op}${args}${phase} ${String(r.outcome).toUpperCase()}${attempt}${detail}`);
    }
  }
  if (lines.length === headerLineCount) lines.push(opts.failed ? "  (no failed/blocked events)" : "  (no events)");
  return lines.join("\n");
}

function allowedTestPaths(box: any): string[] {
  return [...(box.allowedFiles ?? []), ...(box.allowedTestFiles ?? [])];
}

function artifactRecord(seq: number, kind: string, path: string, meta: object) {
  return { type: "artifact_registered", schema_version: SCHEMA_VERSION, seq, ts: new Date().toISOString(), artifact_kind: kind, path: norm(path), meta };
}

export type RecordParams = {
  cwd: string;
  cfg: GovernanceConfig;
  command: "/box" | "/phase";
  op: string;
  args: string;
  before: any;
  after: any;
  planStatus: string;
  result: string;
};

/**
 * Append a command event (and any artefact deltas) to the feature's audit log.
 * Returns the audit file path written, or null when the command cannot yet be
 * attributed to a feature (no planFile set). Never throws on logging concerns —
 * callers still wrap it defensively.
 */
export function recordControlCommand(p: RecordParams): string | null {
  const planFile = p.after.planFile ?? p.before.planFile;
  if (!planFile) return null;
  const file = auditFilePath(p.cwd, planFile);
  const inScope = (p.after.inScope?.length ? p.after.inScope : p.before.inScope) ?? [];
  const id = deriveIdentity(planFile, inScope);
  if (!file || !id) return null;

  const planDir = norm(p.cfg.planDir);
  const featureDir = norm(p.cfg.featureDirs[0] ?? "tests/features");
  const featurePath = `${featureDir}/${id.module}/${id.feature}${p.cfg.featureExt}`;
  const analysisPath = join(planDir, `${id.base}${p.cfg.analysisSuffix}`);
  const reviewPath = join(planDir, `${id.base}${p.cfg.reviewSuffix}`);

  const headerJustCreated = !existsSync(file);
  if (headerJustCreated) {
    mkdirSync(dirname(file), { recursive: true });
    const now = new Date().toISOString();
    const header = {
      type: "header",
      schema_version: SCHEMA_VERSION,
      seq: 0,
      ts: now,
      meta: { feature: id.feature, module: id.module, feature_file: featurePath, created: now },
      artifacts: {
        feature: featurePath,
        analysis: existsSync(join(p.cwd, analysisPath)) ? norm(analysisPath) : null,
        plan: norm(planFile),
        tests: allowedTestPaths(p.after).map(norm),
        implementation: (p.after.allowedImplementationFiles ?? []).map(norm),
        review: existsSync(join(p.cwd, reviewPath)) ? norm(reviewPath) : null,
      },
    };
    writeFileSync(file, JSON.stringify(header) + "\n", "utf8");
  }

  const records = parseAuditLines(readFileSync(file, "utf8"));
  const meta = { feature: id.feature, module: id.module };
  let seq = records.length;
  const toAppend: object[] = [
    {
      type: "event",
      schema_version: SCHEMA_VERSION,
      seq: seq++,
      ts: new Date().toISOString(),
      actor: "human",
      command: p.command,
      op: p.op,
      args: p.args,
      phase_from: p.before.phase,
      phase_to: p.after.phase,
      plan_status: p.planStatus,
      outcome: classifyAuditOutcome(p.result),
      attempt: attemptNumber(records, p.command, p.op),
      detail: firstLine(p.result),
      meta,
    },
  ];

  // Artefacts that appeared after the header was written get their own dated records.
  if (!headerJustCreated) {
    if (!p.before.planFile && p.after.planFile) {
      toAppend.push(artifactRecord(seq++, "plan", norm(p.after.planFile), meta));
      if (existsSync(join(p.cwd, analysisPath))) toAppend.push(artifactRecord(seq++, "analysis", analysisPath, meta));
    }
    for (const f of diffArtifacts(allowedTestPaths(p.before), allowedTestPaths(p.after))) toAppend.push(artifactRecord(seq++, "test", f, meta));
    for (const f of diffArtifacts(p.before.allowedImplementationFiles, p.after.allowedImplementationFiles)) toAppend.push(artifactRecord(seq++, "implementation", f, meta));
  }

  appendFileSync(file, toAppend.map((record) => JSON.stringify(record)).join("\n") + "\n", "utf8");
  return file;
}
