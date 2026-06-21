/**
 * governance.ts — Pi ExtensionAPI adapter for PurrfectReqs governance.
 *
 * Pi loads every .ts file directly under .pi/extensions/ as an extension
 * entrypoint, so this directory should contain only adapter entrypoints.
 * Internal helper modules live outside .pi/extensions/.
 *
 * Current layout:
 *   - .pi/extensions/governance.ts: Pi adapter only
 *   - .pi/governance/config.ts: PurrfectReqs configuration/prose seam
 *   - .pi/governance/engine.ts: reusable governance rule engine
 *
 * Two distinct surfaces, wired to two distinct Pi mechanisms:
 *   1. Enforcement gates  -> pi.on("tool_call"): block/confirm edits, writes, bash.
 *      The agent's tool calls flow through here; returning { block: true } vetoes them.
 *   2. Control plane (/box, /phase) -> pi.registerCommand(): mutate workflow state.
 *      Registered slash commands are NOT in the LLM tool registry, so only the human
 *      can invoke them. This makes phase/box/RED-GREEN/allow-core transitions
 *      human-only by construction — the agent cannot promote its own gates.
 *
 * Phase 9B backup:
 *   .pi/_wip/governance.ts.phase9b.bak
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { createGovernanceEngine } from "../governance/engine.ts";

export default function (pi: ExtensionAPI) {
  const engine = createGovernanceEngine();

  const updateGovernanceStatus = (ctx: any) => {
    if (!ctx.hasUI) return;
    try {
      const status = engine.getStatusLine(ctx.cwd ?? process.cwd());
      ctx.ui.setStatus("governance", ctx.ui.theme?.fg ? ctx.ui.theme.fg("dim", status) : status);
    } catch {
      // Footer status is best-effort; never let a UI/theme API mismatch break the session.
    }
  };

  // Route a command result string to the user. Failure-ish results render as warnings.
  const report = (ctx: any, result: string) => {
    const isProblem = /^(FAIL|Rejected|DISABLED|Cannot|RED not confirmed|GREEN not confirmed|Unknown|Usage:)/.test(result) || /BLOCKED/.test(result);
    if (ctx.hasUI) ctx.ui.notify(result, isProblem ? "warning" : "info");
    else console.log(`[governance] ${result}`);
  };

  pi.on("session_start", async (_event, ctx) => {
    engine.handleSessionStart();
    updateGovernanceStatus(ctx);
  });

  // Enforcement only. Control commands are NOT handled here anymore.
  pi.on("tool_call", async (event, ctx) => engine.handleToolCall(event, ctx));

  pi.on("before_agent_start", async (event) => engine.handleBeforeAgentStart(event));

  pi.registerCommand("box", {
    description: "Feature Box / phase-gate control: set module scope, plan, freeze-check, allow files, run RED/GREEN.",
    handler: async (args, ctx) => {
      const cwd = ctx.cwd ?? process.cwd();
      report(ctx, engine.runBoxCommand(args, cwd));
      updateGovernanceStatus(ctx);
    },
  });

  pi.registerCommand("phase", {
    description: "Set or inspect the governed workflow phase (IDLE..REVIEWING).",
    handler: async (args, ctx) => {
      const cwd = ctx.cwd ?? process.cwd();
      report(ctx, engine.runPhaseCommand(args, cwd));
      updateGovernanceStatus(ctx);
    },
  });
}
