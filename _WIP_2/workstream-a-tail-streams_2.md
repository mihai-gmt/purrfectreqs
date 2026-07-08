# Workstream A — Tail enforcement surfaces & the "two streams" question

> **Question raised (2026-06-26).** Should the toolkit split into two tail streams —
> **Claude/Devin** vs **PI** — because PI's unfakeable governance (T5/T6/T7) is special? Investigate
> the common surfaces; if sharing is risky to quality, keep them separate but hold the same workflow
> principles. Companion to `workstream-a-crosscheck.md` (T1–T11 tail-contract).
>
> Status: **analysis for decision.** Grounded in the actual PI adapter (`.pi/extensions/governance.ts`)
> + Claude Code hook model + Devin (stub/unknown).

---

## 1. The enforcement primitives, harness by harness

PI's adapter exposes **two surfaces** (governance.ts:13-19), not one. They must be compared
separately, because the harnesses differ on each.

| Capability | **PI** | **Claude Code** | **Devin** |
|---|---|---|---|
| **(a) Out-of-model tool-call veto** | `pi.on("tool_call")` → `{block:true}` (engine code) | **PreToolUse hook** → `deny` (hook script, settings.json) | **Unknown / none** authored by us |
| **(b) Human-only control plane** (mutate phase/box state; agent can't self-promote) | `pi.registerCommand` — handler runs *outside* the LLM tool registry | hook + **state file** mutated only by a human-run script; **NOT** a plain slash command (see ⚠) | Unknown |
| **(c) Phase/box state persistence** | engine writes `feature-box.json` | a state file the hook reads | would need a convention; no enforcement |
| **(d) Authored enforcement code** | TS engine + npm dep (`@earendil-works/pi-coding-agent`) | hook scripts (bash/python) | prose + skills only |
| **(e) Workflow invocation** | `prompts/*.md` (model-read) | `.claude/commands/*.md` (model-read) | sessions / `.devin` skills |

⚠ **Claude control-plane subtlety.** A Claude *slash command* is a prompt, and newer Claude Code
exposes a `SlashCommand` tool — meaning **the model can invoke its own slash commands**. So a control
plane built as a slash command is *not* human-only and would let the agent promote its own gates —
exactly what PI's `registerCommand` design prevents. To replicate PI's guarantee, Claude's control
plane must be a **state file mutated by a human-run script** (e.g. via the `!` bash prefix) and read by
a **PreToolUse hook**, OR the command must be explicitly excluded from the model's `SlashCommand`
allowlist. Achievable, but it must be engineered deliberately — it is not free.

---

## 2. The grouping is axis-dependent — and the proposed axis is the weak one

"Claude/Devin vs PI" is one of **three** possible cleavages, and they disagree:

| Axis | Natural grouping | Implication |
|---|---|---|
| **Enforcement capability** (can it realise `[GATE]`?) | **{PI, Claude}** have out-of-model veto+control-plane; **{Devin}** doesn't | For real gates, **Claude is PI's sibling, not Devin's.** |
| **Workflow-prompt lineage** | **{PI, Claude}** — the PI prompts are *ported Claude commands* (iterate.md Step 3 says so verbatim); **{Devin}** uses a different invocation model | Claude↔PI can share prompt bodies; Devin can't reuse them. |
| **Build / packaging substrate** | **{PI}** carries an npm dependency + a TS engine; **{Claude, Devin}** are markdown + light scripting | On *this* axis the proposed "PI separate" is correct. |

So the user's instinct is **half right**: PI genuinely stands apart on **build/packaging** (npm dep +
TS engine) — which is already Workstream B's entire premise (*depend on the package; the engine lives
in `tails/pi/`*). But on the two axes that decide **quality** — enforcement strength and prompt reuse —
**Claude pairs with PI, and Devin is the outlier.** Grouping Claude with Devin would couple the
strongest-enforcement harness to the weakest and risk dragging Claude down to Devin's discipline-only
level (the LCD risk the user wants to avoid — but pointed the wrong way).

---

## 3. Two different things are being conflated

The "two streams" worry collapses once you separate the **contract** from the **implementation**:

- **The tail-CONTRACT (T1–T11) should stay ONE shared spec — and it does not force an LCD, because it
  is *tiered*.** Each obligation is declared at the strongest tier the harness can honestly meet:
  `[GATE]` (out-of-model enforced) → `[PROCESS]` (boundary-checked by convention) → `[REVIEW]`
  (discipline only). This is exactly §0's honesty mechanism. A shared *tiered* contract lets every
  harness be as strong as it can be **while holding identical principles** — which is precisely the
  "same principles on how the workflow works" the user wants to preserve. Sharing the contract is
  therefore **not** the quality risk.

- **The tail-IMPLEMENTATIONS are already three separate folders** (`tails/{claude,pi,devin}`). Nothing
  forces PI's TS engine into Claude/Devin land. The risk would only appear if we shared
  *implementation* (engine code or hook scripts) across harnesses — and we don't.

Tiered example (the load-bearing T5/T6/T7):

| Obligation | PI | Claude | Devin |
|---|---|---|---|
| T5 phase-state | `[GATE]` `/phase` (engine) | `[GATE]` state-file + PreToolUse hook | `[REVIEW]` convention |
| T6 feature-box | `[GATE]` `/box` allowlist | `[GATE]` hook reads allowlist | `[REVIEW]` prose |
| T7 RED/GREEN attestation | `[GATE]` `/box run-red/green` | `[GATE]` hook-wrapped test run | `[REVIEW]` / `[PROCESS]` commit-order |

Same three obligations, same principle ("narration is not evidence"), **honestly different tiers**.
Devin's degradation to `[REVIEW]` is the *real* quality exposure — and it is visible and labelled,
not hidden. That is the right outcome, not a reason to split the contract.

---

## 4. The one real coupling decision: Claude↔PI prompt bodies

Because the PI prompts **are** the Claude commands (same lineage), there's a genuine choice for
Workstreams B/C:

- **Option 1 — shared prompt bodies + a mechanics-injection layer.** One canonical per-phase prompt
  (the playbook discipline), with harness mechanics (the `/box`+`/phase` preamble for PI; the
  hook/`SlashCommand` wiring for Claude) injected per tail. DRY; the proven prompt text lives once.
- **Option 2 — duplicate per tail.** `tails/claude/commands/*.md` and `tails/pi/prompts/*.md` each
  hold a full copy. Simpler build, but two copies drift.

Devin doesn't participate in either — it consumes the **playbook**, not these prompts.

Recommendation: **Option 1**, realised as the playbook (P column) being the single source, with each
tail's prompt/command file being a thin wrapper that pulls in the playbook entry + injects its
mechanics. This is just the three-layer architecture applied to the prompt files themselves.

---

## 5. Recommendation

1. **Do not split the tail-contract into two streams.** Keep **one tiered tail-contract** (T1–T11 ×
   `[GATE]/[PROCESS]/[REVIEW]` per harness). Tiering — not splitting — is what prevents the LCD
   quality loss and is what guarantees "same principles."
2. **Keep PI separate where it genuinely is: build/packaging** (npm dependency + TS engine in
   `tails/pi/`). That is Workstream B and is already settled (extend-not-fork). The user's "PI
   separate" instinct is correct *on this axis only*.
3. **If we stream the authoring effort, pair Claude+PI, not Claude+Devin** — they share enforcement
   capability *and* prompt lineage. Devin is the outlier (weakest enforcement, different invocation):
   give it its own track and accept honest `[REVIEW]` degradation where it can't gate.
4. **Engineer Claude's control plane deliberately** (state file + PreToolUse hook, or `SlashCommand`
   exclusion) so its human-only guarantee matches PI's `registerCommand` — do not assume a slash
   command is human-only.
5. **Resolve the Devin unknown before promising any Devin `[GATE]`.** Until we know Devin's hook/veto
   story, the Devin tail's T5/T6/T7 are `[REVIEW]` at best. This is the actual quality risk and should
   be stated, not papered over.

**Net:** the architecture does not need two streams. It needs **one tiered contract + three separate
implementations**, with Claude and PI as the close pair and Devin as the honestly-weaker outlier.
</content>
