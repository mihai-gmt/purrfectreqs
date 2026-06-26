---
title: PurrfectReqs Backlog — Uncovered Scenarios
description: >
  Scenarios and behaviors discovered during BDD planning that are NOT covered by any
  .feature contract. This is the parking lot for product-owner triage. Entries here are
  proposals only — they are not authoritative and must never be auto-promoted into a
  .feature file or a plan.
schema_version: 1
maintained_by: product-owner
populated_by: "pi /iterate enrich (proposes entries only; never edits .feature or plan)"
authority: "non-authoritative — outranked by every doc in CLAUDE.md's authority order"
updated: 2026-06-21
id_prefix: BL
next_id: BL-0005
status_values: [proposed, accepted, scheduled, rejected, promoted]
entry_field_order: [id, status, discovered, source_feature, source_phase, module, type, priority, security_refs, proposed_by]
type_values: [scenario, edge-case, security-control, nfr]
---

# Backlog — Uncovered Scenarios

How this file works (read before adding an entry):

- **One entry per `## BL-NNNN — <title>` heading.** IDs are stable and never reused.
  Increment `next_id` in the frontmatter when you add one.
- **Field block is machine-parseable.** Each entry opens with a fenced ```yaml block
  using the keys in `entry_field_order`. Keep the keys and their order identical across
  entries so the file can be parsed without bespoke logic.
- **`status` transitions:** `proposed` (agent suggested) → `accepted` (PO agrees it
  belongs) → `scheduled` (slotted into a future feature) → `promoted` (a `.feature` now
  covers it; record the file) — or `rejected` (with a one-line reason). Only the
  product owner changes status.
- **Proposed Gherkin is a DRAFT.** It is illustrative, never the contract. A scenario is
  only real once the PO writes it into a `.feature` by hand and sets status `promoted`.
- **The agent may append a `proposed` entry only when explicitly instructed.** It must
  never edit a `.feature` or a plan to "fix" a gap; it parks the gap here instead.

---

## BL-0001 — Registration page renders a CSP-safe public form (GET /auth/register)

```yaml
id: BL-0001
status: proposed
discovered: 2026-06-21
source_feature: tests/features/auth/20260621_basic_register_user_ui.feature
source_phase: /iterate enrich
module: auth
type: scenario
priority: TBD
security_refs: docs/SECURITY.md §4, §11, §14; docs/FRONTEND.md
proposed_by: gpt-5.5
```

**Gap:** The feature covers submitting the form (happy/duplicate/honeypot) but has no
scenario asserting the GET render of the page itself — status 200, `Content-Type:
text/html`, correlation ID echoed, `method="post"` / `action="/auth/register"`, labelled
inputs, password not echoed, honeypot hidden by CSS class (not inline style) with
`tabindex="-1"` / `aria-hidden="true"` / `autocomplete="off"`, and no inline scripts or
styles (CSP).

**Proposed Gherkin (DRAFT — not authoritative; PO must author the real scenario before any `.feature` edit):**

```gherkin
@auth @new_user_registration @ui @render
Scenario: Registration page renders a CSP-safe public form
  Given I am an unauthenticated visitor
  And my browser sends the header "Accept" with value "text/html"
  When I open the registration page at "/auth/register"
  Then I receive an HTTP 200 response
  And the response Content-Type is "text/html"
  And the registration form method is "post"
  And the registration form action is "/auth/register"
  And the hidden honeypot field is hidden by a CSS class, not an inline style
  And the page does not contain inline scripts or inline styles
```

**Disposition:** Pending PO decision. Note: adding this is new scope beyond the three
authored scenarios — decide implement-now vs defer before promoting.

---

## BL-0002 — Browser registration with a duplicate username returns a rendered 409, not a 500

```yaml
id: BL-0002
status: proposed
discovered: 2026-06-21
source_feature: tests/features/auth/20260621_basic_register_user_ui.feature
source_phase: /implement
module: auth
type: edge-case
priority: TBD
security_refs: docs/SECURITY.md §4
proposed_by: claude-opus-4-8
```

**Gap:** The browser branch of `POST /auth/register` catches `EmailAlreadyExistsError` and
re-renders `auth/register.html` with HTTP 409, but does **not** catch
`UsernameAlreadyExistsError`. A browser submission with a duplicate username would let that
exception propagate uncaught and surface as a 500 instead of a user-facing 409 with the
form re-rendered. The implementation is correct against the current `.feature` — the three
authored scenarios cover happy-path, duplicate-**email**, and honeypot only, so the
implementer wrote the minimum and did not handle duplicate-username (no scenario, no test).
This is a latent real-world gap, not a contract defect.

**Proposed Gherkin (DRAFT — not authoritative; PO must author the real scenario before any `.feature` edit):**

```gherkin
@auth @new_user_registration @ui
Scenario: Registration is rejected when the username is already taken
  Given a user already exists with username "existing_user"
  And I am an unauthenticated visitor
  And my browser sends the header "Accept" with value "text/html"
  When I submit the registration form with username "existing_user" and a new email
  Then I receive an HTTP 409 response
  And the response Content-Type is "text/html"
  And the registration form is re-rendered with an error message
  And the submitted field values are preserved except the password
```

**Disposition:** Pending PO decision. Mirrors the existing duplicate-email handling; low
implementation cost (add a second `except` clause in the browser branch). Decide whether
duplicate-username belongs in this feature's scope or a follow-up before promoting.

---

## BL-0003 — Registration API response is not wrapped in the `ApiResponse[T]` envelope

```yaml
id: BL-0003
status: proposed
discovered: 2026-06-21
source_feature: tests/features/auth/20260407_basic_register_user_api.feature
source_phase: /review
module: auth
type: nfr
priority: TBD
security_refs: docs/GUIDE.md (Success Response Format); CLAUDE.md (API response envelope)
proposed_by: pi /review (gpt-5.5); triaged by claude-opus-4-8
```

**Pre-existing defect (NOT introduced by the UI feature):** `POST /auth/register`
(`app/auth/router.py`) is declared `response_model=UserRegisterResponse, status_code=201`
and returns a bare `UserRegisterResponse` (`{message}`) for JSON clients. CLAUDE.md's API
response envelope rule and `docs/GUIDE.md` require all API success responses to use
`ApiResponse[T]` (top-level `message` + `correlation_id` + `data`). `POST /auth/login` in
the same router already complies (`ApiResponse[LoginData]`); registration never did. This
originates in the 20260407 **API** feature, not the 20260621 UI feature, which was
explicitly told to *preserve* existing JSON behaviour. The `/review` of the UI feature
surfaced it because it touched the same endpoint.

**Why it was not fixed in the UI feature:** changing the JSON shape would alter the API
contract and break the 11 passing API BDD tests, which assert the bare `{message}` shape —
out of scope for a UI feature whose plan said "preserve existing JSON behaviour."

**Required change (when scheduled):** wrap the JSON success path in
`ApiResponse[UserRegisterResponse]` (or an auth data payload) with `correlation_id`, and
update the 20260407 API feature's `.feature`/tests to assert the enveloped shape. This is an
**API-contract change** and should be its own feature/fix cycle, not a side edit.

**Disposition:** Pending PO decision. Confirm whether registration was intentionally exempt
from the envelope (e.g. 201-created convention) or is a genuine standards violation to
remediate. If remediating, schedule against the registration **API** endpoint with its own
test updates.

---

## BL-0004 — User creation is application-logged, not audit-logged

```yaml
id: BL-0004
status: proposed
discovered: 2026-06-21
source_feature: tests/features/auth/20260407_basic_register_user_api.feature
source_phase: /review
module: auth
type: security-control
priority: TBD
security_refs: CLAUDE.md (Audit fields / "Always write audit logs for CREATE/UPDATE/DELETE")
proposed_by: pi /review (gpt-5.5); triaged by claude-opus-4-8
```

**Pre-existing defect (NOT introduced by the UI feature):** user creation in `register_user`
(`app/auth/service.py`) is recorded only via structured application logging, not a
dedicated audit-log write. CLAUDE.md requires an audit log for every CREATE/UPDATE/DELETE.
The user-creation code lives in the 20260407 **API** feature; the UI feature reused
`register_user` and did not introduce the gap. The `/review` hedged ("use the approved
audit-log mechanism *when available*"), which suggests the audit-log infrastructure may not
exist yet — making this partly an **infrastructure** item, not just a code fix.

**Required change (when scheduled):** (1) confirm whether an approved audit-log mechanism
exists; if not, that infra is a prerequisite. (2) Emit an audit-log record on user CREATE
(actor, correlation_id, no PII beyond user id, UTC timestamp). (3) Decide whether other
existing CREATE/UPDATE/DELETE paths share the gap and need the same treatment.

**Disposition:** Pending PO decision. Likely blocked on the audit-log mechanism existing.
If the mechanism is not yet built, record a formal deferred-audit exception rather than
treating the application log as the audit log. Schedule against the auth module (or a
shared audit-infra feature), not as a side edit to the UI feature.
