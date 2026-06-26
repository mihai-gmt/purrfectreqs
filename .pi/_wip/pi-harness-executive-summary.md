# PurrfectReqs Pi Harness — Executive Summary

## 2-Minute Pitch

```text
┌──────────────────────────────────────────────────────────────────┐
│              PURRFECTREQS PI HARNESS — DEV TEAM PITCH            │
│                                                                  │
│      “AI coding, but with seatbelts, gates, and audit trails.”    │
└──────────────────────────────────────────────────────────────────┘
```

The PurrfectReqs Pi harness turns AI coding into a governed development workflow.

The goal is simple:

```text
Keep the speed of AI coding,
but make scope drift, unsafe edits, and fake test gates hard.
```

---

## One-Slide Graphic

```text
        HUMAN OWNS INTENT                  AI DOES WORK                  HARNESS ENFORCES RULES
┌──────────────────────────┐       ┌──────────────────────────┐       ┌──────────────────────────┐
│  .feature file            │       │  Preplan                 │       │  Phase gates              │
│  Frozen plan              │──────▶│  Plan                    │──────▶│  File allowlists          │
│  Phase approvals          │       │  Write tests             │       │  RED/GREEN checks         │
│  Review decisions         │       │  Implement               │       │  Protected paths          │
│                           │       │  Review                  │       │  Audit log                │
└──────────────────────────┘       └──────────────────────────┘       └──────────────────────────┘
```

---

## Core Workflow

```text
┌──────────────┐
│  .feature    │  Human-written source of truth
└──────┬───────┘
       ▼
┌──────────────┐
│  /preplan    │  AI analyzes existing code
└──────┬───────┘
       ▼
┌──────────────┐
│  /plan       │  AI proposes plan, human approves
└──────┬───────┘
       ▼
┌──────────────┐
│  /iterate    │  Risk, detail, testability, freeze checks
└──────┬───────┘
       ▼
┌──────────────┐
│  WRITE TESTS │  AI writes tests only
└──────┬───────┘
       ▼
┌──────────────┐
│  RED GATE    │  Harness runs pytest and confirms real failure
└──────┬───────┘
       ▼
┌──────────────┐
│  IMPLEMENT   │  AI edits only approved files
└──────┬───────┘
       ▼
┌──────────────┐
│  GREEN GATE  │  Harness runs pytest and confirms pass
└──────┬───────┘
       ▼
┌──────────────┐
│  REVIEW      │  AI can only write review artifact
└──────────────┘
```

---

## What Makes This Different

```text
Traditional AI Coding                         This Harness
─────────────────────                         ─────────────────────

Prompt the model                              Human writes contract

Model edits broad codebase                    Model edits approved files only

Trust model discipline                        Phase gates enforce discipline

“Tests passed?” by claim                      Harness runs RED/GREEN pytest

Review may drift into fixes                   Review is mechanically read-only

Little workflow trace                         JSONL audit trail per feature
```

---

## Safety Model

```text
┌──────────────────────────────────────────────────────────────────┐
│                     GOVERNANCE ENGINE                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Blocks:                                                         │
│  - .feature edits                                                │
│  - .env / .git / .venv / node_modules                            │
│  - source edits during test-writing                              │
│  - test edits during implementation                              │
│  - source/test edits during review                               │
│  - files outside the frozen plan manifest                        │
│  - cross-module model imports                                    │
│  - banned dependencies                                           │
│  - unsafe token storage                                          │
│  - naive UTC datetime patterns                                   │
│                                                                  │
│  Confirms:                                                       │
│  - authority-doc edits                                           │
│  - dependency/config changes                                     │
│  - dangerous bash commands                                       │
│  - auth/security-sensitive files                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## One-Slide Pitch Version

```text
┌────────────────────────────────────────────────────────────────────┐
│             AI CODING WORKFLOW WITH HARD GOVERNANCE                │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. Human writes the contract                                      │
│     .feature file + approved frozen plan                           │
│                                                                    │
│  2. AI works in narrow roles                                       │
│     preplan → plan → tests → implement → review                    │
│                                                                    │
│  3. Harness enforces boundaries                                    │
│     phase gates + file manifests + protected paths                 │
│                                                                    │
│  4. Tests are real gates                                           │
│     RED and GREEN are confirmed by pytest execution                │
│                                                                    │
│  5. Every workflow action is traceable                             │
│     per-feature JSONL audit log                                    │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Goal: keep AI fast, but make scope drift and unsafe edits hard.   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Talk Track

> This harness turns Pi from a general coding assistant into a governed development workflow.
>
> The key idea is that the human owns intent. We start with a `.feature` file and a frozen implementation plan. The AI cannot rewrite that contract.
>
> Then the AI moves through narrow roles: preplanning, planning, test writing, implementation, and review. Each phase has different file permissions.
>
> During test writing, source edits are blocked. During implementation, test edits are blocked. During review, source and test edits are blocked.
>
> The frozen plan’s Section 14 becomes the file manifest. If a file is not listed, the AI cannot modify it.
>
> RED and GREEN are not based on the model claiming tests passed. The harness runs pytest itself and records whether tests genuinely failed before implementation and passed afterward.
>
> On top of that, the governance engine blocks protected paths, `.feature` edits, banned dependencies, unsafe token storage, cross-module model imports, and other structural violations.
>
> Finally, every `/box` and `/phase` control action is logged to a per-feature audit trail, so we can reconstruct how a feature moved through the workflow.
>
> So the pitch is simple: we keep the speed of AI coding, but add deterministic guardrails around scope, tests, security, and review.

---

## Key Takeaway

```text
This is not “trust the AI to behave.”

This is:

- human-authored intent
- AI execution
- deterministic workflow gates
- real test verification
- file-level scope control
- auditability
```

The harness makes the safe path the easy path.
