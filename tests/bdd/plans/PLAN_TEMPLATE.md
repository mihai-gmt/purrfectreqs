# Plan: [Feature Name]

**Feature file:** `tests/features/<module>/<feature_name>.feature`
**Module(s) affected:** [list]
**Date:** [today's date]
**Status:** DRAFT

---

## 1. Feature Summary

[2-3 sentences describing what this feature does and why it exists, in plain language.]

---

## 2. Scope Confirmation

- Feature type: [API / UI]
- MVP: [Yes / No — if No, this plan should not exist]
- Scenarios count: [N]
- Modules touched: [list — note if cross-module escalation applies]

---

## 3. API Endpoints

**API features:** list every endpoint this feature requires.
**UI features:** mark this section N/A — see Section 3b instead.

| Method | Path | Auth required | Role required | Description |
|--------|------|---------------|---------------|-------------|
| POST | /auth/login | No | None | Authenticate user |

Include endpoints that already exist and will be modified, not just new ones.

---

## 3b. API Dependencies *(UI features only — omit for API features)*

List every existing API endpoint this UI feature calls. Confirm each is fully implemented and tested. A UI feature must never be planned against an API endpoint that does not yet exist.

| Method | Path | Purpose in this UI feature |
|--------|------|---------------------------|

If a required API endpoint does not exist: stop, note it here, tell the developer which API feature must be built first.

---

## 4. Database Changes

### New tables
[Table name, link to DATA_MODELS.md section, reason — or "None"]

### Modified tables
[Table name, which columns change, reason — or "None"]

### Alembic migration required?
[Yes — describe what the migration does / No]

---

## 5. Module Breakdown

For each module being touched:

### app/<module_name>/
- **router.py:** [what endpoints are added or modified]
- **service.py:** [what functions are added or modified]
- **models.py:** [what SQLAlchemy models are added or modified — or "No changes"]
- **schemas.py:** [what Pydantic data payload schemas are needed — these define the `data` field for `ApiResponse[T]`. Do NOT add `message` or `correlation_id` to module schemas. Or "No changes"]
- **dependencies.py:** [any new FastAPI dependencies — or "No changes"]

**UI features only:**

### app/templates/<module_name>/
- **[page_name].html:** [full page template — extends base.html]
- **[_partial_name].html:** [partial template — bare fragment, no base.html]

---

## 6. Security Considerations

- Does any endpoint require JWT auth? [Yes/No — which ones]
- Does any endpoint require a specific role? [Yes/No — which role, which endpoint]
- Are there rate limiting requirements? [Yes/No — cite docs/SECURITY.md section]
- Does this feature handle passwords or tokens? [Yes/No — cite relevant rules]
- Does this feature require CSRF protection? [Yes/No]
- What security events must be logged? [list from docs/SECURITY.md]

---

## 7. Audit Logging

| Action | Table | action_type | Notes |
|--------|-------|-------------|-------|
| Admin creates user | users | CREATE | |

---

## 8. Test Scenarios Breakdown

For each scenario in the `.feature` file:

### Scenario: [name from .feature file]
- **Test type:** BDD step def / unit test / both
- **Fixtures needed:** [e.g., authenticated admin user, existing project record]
- **What it verifies:** [specific assertion]
- **Expected HTTP status:** [e.g., 200, 201, 401, 403, 422, 423]

---

## 9. Success Criteria

### Automated verification
- [ ] `pytest tests/bdd/step_defs/test_<feature_name>.py -v` — all scenarios pass
- [ ] `pytest tests/unit/<module>/ -v` — all unit tests pass
- [ ] `alembic upgrade head` runs cleanly (if DB changes)
- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes

### Manual verification
- [ ] [Specific UI or functional check]
- [ ] [Edge case that is hard to automate]

---

## 10. Implementation Order

Each phase is a checkbox. The implementation agent ticks each as it completes.

**API feature track:**

- [ ] **Phase 1: Alembic migration** (if needed) — `alembic/versions/`
  - Test signal: [added by /iterate testability, or "N/A"]
- [ ] **Phase 2: SQLAlchemy model(s)** — `app/<module>/models.py`
  - Test signal: [added by /iterate testability, or "N/A"]
- [ ] **Phase 3: Pydantic schemas** — `app/<module>/schemas.py`
  - Test signal: [added by /iterate testability, or "N/A"]
- [ ] **Phase 4: Service function(s)** — `app/<module>/service.py`
  - Test signal: [added by /iterate testability, or "N/A"]
- [ ] **Phase 5: Router endpoint(s)** — `app/<module>/router.py`
  - Test signal: [added by /iterate testability, or "N/A"]

**UI feature track:**

- [ ] **Phase 1: Router endpoint** (HTMLResponse) — `app/<module>/router.py`
  - Test signal: [added by /iterate testability, or "N/A"]
- [ ] **Phase 2: Full page template** — `app/templates/<module>/<page_name>.html`
  - Test signal: [added by /iterate testability, or "N/A"]
- [ ] **Phase 3: Partial template** — `app/templates/<module>/_<partial_name>.html`
  - Test signal: [added by /iterate testability, or "N/A"]

Note: UI features depend on API features being fully implemented and tested first.

---

## 11. Edge Cases and Error Conditions

| Condition | HTTP status | error_code |
|-----------|-------------|------------|
| Invalid credentials | 401 | INVALID_CREDENTIALS |

---

## 12. Out of Scope

- [e.g., "Password reset — separate feature"]

---

## 13. Codebase Analysis Reference

Full analysis: `tests/bdd/plans/<module>_<feature_name>.analysis.md`

### Key findings (from analysis doc synthesis)
[Copy relevant bullet points from the analysis doc's synthesis section.]

### Patterns to follow
[Reference specific patterns with file:line references for /write-tests and /implement to read. Include both test patterns (BDD step defs, fixtures) and implementation patterns (endpoints, services, schemas).]

---

## 14. File Manifest

Explicit file lists that `/write-tests` and `/implement` MUST follow.
These agents should read ONLY the files listed here — no broad codebase exploration.

### Files to READ before writing tests

| File | Why |
|------|-----|
| `tests/features/<module>/<feature_name>.feature` | The contract |
| This plan file | Scenarios, fixtures, success criteria |
| `tests/bdd/conftest.py` | Reuse existing fixtures |
| `docs/GUIDE.md` | Error response format (only if testing error shapes) |

### Files to READ before implementing

| File | Why |
|------|-----|
| `tests/features/<module>/<feature_name>.feature` | The contract |
| This plan file | Implementation order, phases |
| `tests/bdd/step_defs/test_<feature_name>.py` | What tests expect |
| `docs/DATA_MODELS.md` | DB schema (only if DB changes) |
| `docs/SECURITY.md` | Security rules (only if auth/passwords) |
| `docs/GUIDE.md` | Code patterns |

### Files to CREATE

| File | Agent | Purpose |
|------|-------|---------|
| `tests/bdd/step_defs/test_<feature_name>.py` | write-tests | BDD step definitions |

### Files to MODIFY

| File | Agent | What changes |
|------|-------|--------------|

### Files NOT touched

Everything not listed above. No broad exploration needed.

---

## 15. Changelog

| Date | Phase | Scope | Changes |
|------|-------|-------|---------|
| [today's date] | draft | — | Initial plan created |
