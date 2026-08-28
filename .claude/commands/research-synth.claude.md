---
description: Consolidate the UX-research Deep Research reports into one evidence-gated findings set
argument-hint: "<reports-dir-or-glob>"
---
# /research-synth — Research Synthesis & Extraction (Claude tail)

User argument: $ARGUMENTS

## Binding discipline
Thin wrapper. The discipline lives once in **`_TEMP/skills_draft/research-synth.spec.md`**
(update this path when you promote the files). Read that file now — it is the contract. This
tail adds only Claude mechanics.

## Claude mechanics
- Read reports with Read; write the four outputs with Write. No input report is modified.
- **Optional citation spot-check:** you have WebSearch. After the cite-or-drop gate, spot-verify
  a random ~10% sample of the `source_url`s backing HIGH-confidence pain-points. If a sampled URL
  does not support its claim, downgrade that finding to THIN and note it in `synthesis.md`. This
  is a sample check, not full verification — do not block the run on it.
- If `$ARGUMENTS` is missing or resolves to fewer than 2 reports, halt and ask (spec halt conditions).

## Deliverable
The four files named in the spec, under the spec's output dir. Present a short summary LAST:
counts (findings kept / dropped / contradictions), the top 5 ranked pain-points, and each thesis
pillar's verdict (SUPPORTED / CHALLENGED / UNRESOLVED).
