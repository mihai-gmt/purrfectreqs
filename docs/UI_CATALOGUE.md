# PurrfectReqs — UI Component Catalogue

> **Purpose:** The registry of reusable UI components (Jinja macros and partials). One entry per component: what it is, its contract, and how to use it. This is a **reference** document — consult it while building a screen; it is not a rulebook.
>
> **Authority:** Reference tier, subordinate to `docs/FRONTEND.md` (rank 9 in `CLAUDE.md` → Document Authority). FRONTEND.md governs *how* components are built (the macro/partial architecture §4, tokens §5, security §6). This catalogue records *which* components exist and their contracts. Where the two disagree, FRONTEND.md wins.

---

## How this catalogue is maintained

- **One entry per component**, added **when its macro/partial is written** — never before. An entry for a component that does not yet exist is documenting vapour and will rot. (Same discipline as "the test exists when the behaviour exists.")
- **Page-level layouts are not components.** Those are the closed archetype catalogue in `docs/FRONTEND.md` §2. This file holds only the atoms/molecules placed *inside* an archetype.
- Component files live under `app/templates/_macros/` (macros) and `app/templates/<module>/_*.html` (partials), per `docs/FRONTEND.md` §4.

---

## Entry schema

Every component entry uses exactly these fields:

| Field | Meaning |
|-------|---------|
| **Name** | The macro/partial name as called in templates, e.g. `form_field(...)`. |
| **Type** | `macro` or `partial`. |
| **File** | Path to its definition. |
| **Signature** | Parameters with types and defaults. |
| **When to use** | The single job it does; when *not* to use it. |
| **Accessibility** | Required ARIA / label / focus behaviour. |
| **Example** | A minimal call and its rendered intent. |

---

## Components

_None registered yet._ The auth screens currently use raw PicoCSS-styled elements; entries are added here as those elements are extracted into macros.

### Template for a new entry (copy this shape)

- **Name:** `form_field(label, name, type="text", value="", error=None, required=False)`
- **Type:** macro
- **File:** `app/templates/_macros/forms.html`
- **Signature:** `label: str`, `name: str`, `type: str = "text"`, `value: str = ""`, `error: str | None = None`, `required: bool = False`
- **When to use:** a single labelled input inside a form. Not for grouped or compound inputs.
- **Accessibility:** `<label for>` paired with the input `id`; error text linked via `aria-describedby`; `required` sets `aria-required`.
- **Example:** `{{ form_field("Email", "email", type="email", required=True) }}`

> The entry above is an **illustration of the schema**, not a registered component — it is not implemented. Promote it (or write the real first entry) when the macro lands.
