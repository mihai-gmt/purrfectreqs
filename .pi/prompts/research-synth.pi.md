---
description: Consolidate the UX-research Deep Research reports into one evidence-gated findings set
argument-hint: "<reports-dir>"
---
# /research-synth — Research Synthesis & Extraction (Pi tail)

User argument: $ARGUMENTS

## Binding discipline
Thin wrapper. The discipline lives once in **`_TEMP/skills_draft/research-synth.spec.md`**
(update this path when you promote the files). Read that file now — it is the contract. This
tail adds only Pi mechanics.

## Pi mechanics
- Pi tools are `bash` / `write` / `edit` only, and there is **no browse tool**. Read reports via
  `bash` (e.g. `cat`); write the four outputs via `write`. Do not `edit` any input report.
- **No live citation check** — Pi cannot browse. The cite-or-drop gate is therefore STRUCTURAL: a
  finding passes only if `source_url` is present and well-formed, OR an attributed `verbatim` quote
  is present. Live verification is out of scope — defer it to the Claude tail's spot-check or a
  separate bounded-retrieval pass. State in `synthesis.md` that URLs are unverified.
- The governance engine gates `write`/`bash`: outputs go under `_TEMP/…` (not a protected/core
  path), so the default output dir is allowed. If a write is blocked, stop and report — do NOT
  relocate outputs into a governed path to dodge the gate.
- If `$ARGUMENTS` resolves to fewer than 2 reports, halt and report (spec halt conditions).

## Deliverable
The four files named in the spec, under the spec's output dir, plus a short final summary: counts
(kept / dropped / contradictions), top 5 pain-points, and thesis-pillar verdicts.
