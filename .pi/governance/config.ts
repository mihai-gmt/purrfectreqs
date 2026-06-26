import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

export const CONFIG = {
  appRoot: "app",
  coreDir: "app/core",
  templatesDir: "app/templates",
  staticDir: "app/static",
  backlogFile: "Backlog.md",
  statusDoc: "docs/PROJECT_STATUS.md",
  authDirs: ["app/auth"],
  modelsFileHint: "models.py",
  migrationsDir: "alembic/versions",
  planDir: "tests/bdd/plans",
  analysisSuffix: ".analysis.md",
  planSuffix: ".plan.md",
  reviewSuffix: ".review.md",
  testDirs: ["tests/bdd/step_defs", "tests/unit"],
  docsDir: "docs",
  featureDirs: ["tests/features"],
  depFiles: [/(^|\/)requirements[^/]*\.txt$/, /(^|\/)pyproject\.toml$/],
  configFiles: [/(^|\/)app\/core\/config\.py$/, /(^|\/)\.env(\.|$)/],
  bannedDeps: ["openai", "langchain", "semantic_kernel", "semantic-kernel", "nltk", "textblob", "gensim"],
  featureBoxPath: ".pi/feature-box.json",
  protectedPaths: [/(^|\/)\.env($|\.)/, /(^|\/)\.git\//, /(^|\/)\.venv\//, /(^|\/)node_modules\//],
  featureExt: ".feature",
  authorityDocs: [
    "CLAUDE.md",
    "WORKFLOW.md",
    "docs/SECURITY.md",
    "docs/DATA_MODELS.md",
    "docs/ARCHITECTURE.md",
    "docs/SCOPE.md",
    "docs/TECH_STACK.md",
    "docs/FRONTEND.md",
  ],
  bashAllowlist: [
    "pytest",
    "python -m pytest",
    "ruff",
    "black",
    "flake8",
    "mypy",
    "make test",
    "git status",
    "git diff",
    "git log",
    "git show",
    "git branch --show-current",
    "alembic current",
    "alembic heads",
    "alembic history",
    "alembic upgrade head",
  ],
  bashDangerous: [
    /\brm\s+(-[a-z]*r|-[a-z]*f|--recursive|--force)/i,
    /\bsudo\b/i,
    /\b(chmod|chown)\b.*\b777\b/i,
    /\bchown\b/i,
    /\bgit\s+reset\s+--hard\b/i,
    /\bgit\s+clean\s+-[a-z]*f/i,
    /\bgit\s+push\b/i,
    /\bpip\s+install\b/i,
    /\bpip3\s+install\b/i,
    /\buv\s+add\b/i,
    /\bpoetry\s+add\b/i,
    /\bnpm\s+install\b/i,
    /\bnpm\s+i\b/i,
    /\balembic\s+downgrade\b/i,
  ],
};

export type GovernanceConfig = typeof CONFIG;

type HarnessConfigJson = Partial<{
  projectName: string;
  sourceRoots: string[];
  testRoots: string[];
  featurePatterns: string[];
  planDir: string;
  analysisSuffix: string;
  planSuffix: string;
  reviewSuffix: string;
  testDirs: string[];
  docsDir: string;
  featureDirs: string[];
  coreDirs: string[];
  migrationDirs: string[];
  dependencyFiles: string[];
  authorityDocs: string[];
  bannedDeps: string[];
  appRoot: string;
  coreDir: string;
  authDirs: string[];
  migrationsDir: string;
  featureBoxPath: string;
}>;

function firstString(values: unknown): string | undefined {
  return Array.isArray(values) && typeof values[0] === "string" ? values[0] : undefined;
}

function stringArray(values: unknown): string[] | undefined {
  return Array.isArray(values) && values.every((value) => typeof value === "string") ? values : undefined;
}

export function loadHarnessConfig(cwd: string, baseConfig: GovernanceConfig = CONFIG): GovernanceConfig {
  const fp = join(cwd, ".pi/harness.config.json");
  if (!existsSync(fp)) return baseConfig;
  try {
    const raw = JSON.parse(readFileSync(fp, "utf8")) as HarnessConfigJson;
    return {
      ...baseConfig,
      appRoot: raw.appRoot ?? firstString(raw.sourceRoots) ?? baseConfig.appRoot,
      coreDir: raw.coreDir ?? firstString(raw.coreDirs) ?? baseConfig.coreDir,
      authDirs: stringArray(raw.authDirs) ?? baseConfig.authDirs,
      migrationsDir: raw.migrationsDir ?? firstString(raw.migrationDirs) ?? baseConfig.migrationsDir,
      planDir: raw.planDir ?? baseConfig.planDir,
      analysisSuffix: raw.analysisSuffix ?? baseConfig.analysisSuffix,
      planSuffix: raw.planSuffix ?? baseConfig.planSuffix,
      reviewSuffix: raw.reviewSuffix ?? baseConfig.reviewSuffix,
      testDirs: stringArray(raw.testDirs) ?? stringArray(raw.testRoots) ?? baseConfig.testDirs,
      docsDir: raw.docsDir ?? baseConfig.docsDir,
      featureDirs: stringArray(raw.featureDirs) ?? baseConfig.featureDirs,
      featureBoxPath: raw.featureBoxPath ?? baseConfig.featureBoxPath,
      authorityDocs: stringArray(raw.authorityDocs) ?? baseConfig.authorityDocs,
      bannedDeps: stringArray(raw.bannedDeps) ?? baseConfig.bannedDeps,
    };
  } catch (error) {
    console.warn(`[governance] Invalid .pi/harness.config.json; using base config. ${error instanceof Error ? error.message : String(error)}`);
    return baseConfig;
  }
}

export const PATTERNS = {
  utcNowNaive: /datetime\.now\(\s*\)/,
  utcUtcnow: /datetime\.utcnow\s*\(/,
  crossModelImport: /from\s+app\.([a-zA-Z_][\w]*)\.models\s+import/g,
  storageToken: /(localStorage|sessionStorage)\.setItem\([^)]*(token|jwt|access_token|refresh_token)/i,
  hardcodedSecret: /(password|secret|api[_-]?key|secret[_-]?key)\s*=\s*["'][^"']+["']/i,
};

export const PROSE_RULES = `
PurrfectReqs governance — judgment rules the harness CANNOT enforce in code (follow them strictly):
- Propagate the correlation ID through every endpoint, service, audit log, and error response.
- All API success responses use the ApiResponse[T] envelope from app/core/schemas.py.
- Business logic lives in service.py; routers call services, never the reverse.
- Every endpoint requires get_current_user and require_role() where RBAC applies (except POST /auth/login).
- Every table includes the audit fields; user-content tables also include is_deleted/deleted_at/deleted_by.
- Read ONLY the files the plan lists; do analysis before planning; respect plan approval loops.
- STOP and escalate if the task conflicts with MVP scope, or you are unsure how to proceed.
- Structural rules (.feature contracts, Feature Box, app/core, banned deps, UTC, cross-module imports,
  protected paths, dangerous/write bash, phase write classes, plan FROZEN gates, RED/GREEN gates,
  Section 14 write manifests, freeze checks, and review-only rules) are ENFORCED by this extension.
`.trim();
