# Research Synthesis & Extraction — Discipline (harness-neutral)

> Single source of truth for the `/research-synth` skill. The Claude command and the Pi
> prompt are thin tails that bind to this file (mirrors `freeze.md` → `workflow/playbook.md`).
> Harness-specific mechanics live in the tails; the discipline lives here, once.

## What this skill does

Consolidate the raw Deep Research reports produced during the requirements-UX research phase
into ONE evidence-gated, structured findings set. It does **not** browse and does **not** add
outside knowledge — the input reports are the sole source of truth (same discipline as a
`.feature` file: synthesize what is there, invent nothing).

## Inputs

- `$ARGUMENTS` = a directory or glob of **≥2** saved research reports (`.md`/`.txt`) — e.g. the
  outputs of the base + Variant A (PM) + Variant B (business) runs across models. Default input
  dir: `_TEMP/ux_research/reports/`.
- The product thesis under test: read the **"Product bet under test"** block from
  `_TEMP/20260710_requirements_ux_research_prompt.md`. Do not restate a thesis from memory.

**Halt conditions (report and stop — never proceed on one source):** fewer than 2 readable
reports; no thesis block found; a report is empty or unreadable.

## Procedure

### 1 — Extract atomic findings
Read every report. Break each into atomic findings — one claim each. Record per finding:

| field | meaning |
|---|---|
| `id` | stable slug |
| `claim` | one tool-agnostic sentence |
| `category` | pain-point / loved-pattern / tool-fact / unmet-need / ui-ux-good / ui-ux-bad / gherkin-tooling / bdd-critique |
| `verbatim` | representative user quote, if the report gives one |
| `source_url` | primary citation from the report |
| `source_report` | which input file it came from |
| `frequency` | how often it recurs *within the reports* (do NOT infer real-world frequency) |
| `intensity` | how strongly users feel, read from their language |
| `evidence_strength` | STRONG only if ≥2 independent sources; otherwise THIN |

### 2 — Cite-or-drop gate
A finding with no `source_url` AND no attributed `verbatim` **fails the gate**: move it to
`dropped.md` with the reason. Do not keep it, and do not silently delete it. "Dropped" is
information — a claim the reports asserted but did not evidence. This is the "narration is not
evidence" rule applied to the research itself.

### 3 — Cross-source reconciliation
Cluster findings that state the same claim across different reports. Count *independent* reports
per cluster. Cluster in ≥2 independent reports → confidence HIGH; single-report → confidence LOW.
Rank pain-points by (independent-report count × intensity). Never upgrade a single-source claim
to STRONG/HIGH.

### 4 — Contradiction log
Where reports disagree (e.g. "business users happily read Gherkin" vs "business users bounce off
Gherkin"), record BOTH sides with their sources in `contradictions.md`. Do NOT resolve the
contradiction by choosing a side — surfacing it is the deliverable.

### 5 — Thesis scorecard (falsification discipline)
For each pillar of the product thesis (anti-grid / explorer navigation, Gherkin-first authoring,
best-in-class Gherkin editing, business-intake persona) list:
- supporting evidence (with sources);
- **challenging evidence (with sources) — MANDATORY.** A pillar with no challenge listed means
  you did not look hard enough, not that none exists;
- verdict: SUPPORTED / CHALLENGED / UNRESOLVED.

Do not drop challenging evidence to make a pillar look supported.

## Outputs (write all four)
Into `<output-dir>` (default `_TEMP/ux_research/synthesis/<YYYYMMDD>/`):
- `findings.yaml` — the structured rows from step 1 (machine-consumable; later seeds UX
  requirements / `.feature` files).
- `synthesis.md` — human report: exec summary, ranked pain-points, unmet needs, thesis scorecard.
- `contradictions.md` — step 4.
- `dropped.md` — step 2 audit trail.

## Self-check — stop if you notice yourself
- Adding a finding not present in any report (outside knowledge is not a finding).
- Resolving a contradiction by picking the side that flatters the thesis.
- Marking a single-source claim STRONG, or inferring real-world frequency beyond the reports.
- Omitting challenging evidence from a thesis pillar because the supporting evidence is stronger.
- Skipping `dropped.md` because "those claims were probably fine."

## Rules
- The reports are the source of truth; synthesize, do not invent.
- Every retained finding carries a source (URL or attributed quote), or it is dropped.
- Contradictions are surfaced, never silently resolved.
- Challenging evidence is mandatory in the scorecard.
- Write all four output files before presenting any summary.
