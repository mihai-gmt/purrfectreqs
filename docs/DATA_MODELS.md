# PurrfectReqs — Data Models

### Complete Database Schema Reference

---

## Purpose

This file defines every database table, its fields, relationships, and constraints. It is the single source of truth for all data models in the system.

**When creating or modifying SQLAlchemy models, this document is authoritative.** If generated code diverges from this spec, this spec is correct.

> **Related files:**
> - `docs/ARCHITECTURE.md` → structural rules for models and migration order
> - `docs/SECURITY.md` → auth-specific model details
> - `docs/GUIDE.md` → code patterns for model implementation

---

## Global Rules (Apply to Every Model)

### Mandatory Audit Fields

Every table MUST include:

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer, PK, auto-increment | Primary key |
| `created_at` | DateTime(timezone=True), default=now, NOT NULL | When the record was created (UTC) |
| `updated_at` | DateTime(timezone=True), default=now, onupdate=now, NOT NULL | When the record was last modified (UTC) |
| `created_by` | Integer, FK → `users.id`, nullable | Who created the record |
| `updated_by` | Integer, FK → `users.id`, nullable | Who last modified the record |

### Soft Delete Convention

Tables that store user-created content use soft deletes:

| Field | Type | Description |
|-------|------|-------------|
| `is_deleted` | Boolean, default=False | Soft delete flag |
| `deleted_at` | DateTime(timezone=True), nullable | When the record was soft-deleted (UTC) |
| `deleted_by` | Integer, FK → `users.id`, nullable | Who deleted the record |

**Hard deletes are only used for:** refresh tokens, expired session data, and temporary processing records.

### Naming Conventions

- Table names: `snake_case`, plural (e.g., `users`, `projects`, `requirements`)
- Column names: `snake_case` (e.g., `created_at`, `user_id`)
- Foreign keys: `<referenced_table_singular>_id` (e.g., `user_id`, `project_id`)
- Indexes: `ix_<table>_<column>` (e.g., `ix_users_email`)
- Unique constraints: `uq_<table>_<column>` (e.g., `uq_users_email`)

---

## Module 1: Auth — `app/auth/models.py`

### Table: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `email` | String(255) | UNIQUE, NOT NULL, indexed | Login identifier |
| `username` | String(100) | UNIQUE, NOT NULL | Display name |
| `hashed_password` | String(255) | NOT NULL | passlib argon2/bcrypt hash |
| `role` | Enum(`admin`, `super_user`, `user`) | NOT NULL, default=`user` | RBAC role |
| `status` | Enum(`active`, `suspended`, `locked`, `inactive`, `pending`) | NOT NULL, default=`pending` | Account status |
| `failed_login_attempts` | Integer | NOT NULL, default=0 | Lockout counter |
| `locked_until` | DateTime(timezone=True) | nullable | Lockout expiry (NULL = not locked, UTC) |
| `last_password_change` | DateTime(timezone=True) | nullable | For password age tracking (UTC) |
| `last_activity_at` | DateTime(timezone=True) | nullable | For session timeout (30-min inactivity, UTC) |
| `created_at` | DateTime(timezone=True) | NOT NULL, default=now | (UTC) |
| `updated_at` | DateTime(timezone=True) | NOT NULL, default=now, onupdate=now | (UTC) |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |
| `first_name` | String(50) | nullable | |
| `last_name` | String(50) | nullable | |

**Indexes:** `ix_users_email`, `ix_users_username`, `ix_users_status`

**Notes:**
- `super_user` uses underscore in the database enum (Python convention), displayed as "super-user" in the UI.
- First admin user is created via seed script. Subsequent users may self-register via the registration form (default role: `super_user`, default status: `active`) or be created directly by an admin.

### Table: `refresh_tokens`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `user_id` | Integer | FK → `users.id`, NOT NULL, indexed | Token owner |
| `token_hash` | String(255) | NOT NULL, indexed | SHA-256 hash of the token |
| `is_revoked` | Boolean | NOT NULL, default=False | Revocation flag |
| `expires_at` | DateTime | NOT NULL | Token expiry |
| `created_at` | DateTime | NOT NULL, default=now | When issued |
| `replaced_by` | Integer | FK → `refresh_tokens.id`, nullable | Points to the rotated replacement |

**Indexes:** `ix_refresh_tokens_user_id`, `ix_refresh_tokens_token_hash`

**Notes:**
- Raw refresh tokens are NEVER stored. Only the SHA-256 hash is persisted.
- On rotation: old token's `is_revoked` = True, `replaced_by` = new token's ID.
- On logout: ALL tokens for the user are revoked (single-session enforcement).

---

## Module 2: Projects — `app/projects/models.py`

### Table: `projects`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `name` | String(255) | NOT NULL | Project name |
| `description` | Text | nullable | Project description |
| `status` | Enum(`active`, `archived`, `draft`) | NOT NULL, default=`draft` | Project status |
| `owner_id` | Integer | FK → `users.id`, NOT NULL | Project owner |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_projects_owner_id`, `ix_projects_status`

### Table: `project_members`

Association table for user-project assignments.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `project_id` | Integer | FK → `projects.id`, NOT NULL | |
| `user_id` | Integer | FK → `users.id`, NOT NULL | |
| `role_in_project` | Enum(`owner`, `editor`, `viewer`) | NOT NULL, default=`viewer` | Per-project role |
| `created_at` | DateTime | NOT NULL, default=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |

**Constraints:** UNIQUE(`project_id`, `user_id`)

---

## Module 2 (continued): Requirements — `app/projects/models.py`

### Table: `requirements`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `project_id` | Integer | FK → `projects.id`, NOT NULL, indexed | Parent project |
| `raw_input_id` | Integer | FK → `raw_inputs.id`, nullable, indexed | The raw input this requirement was derived from. NULL when a person typed the requirement directly |
| `title` | String(500) | NOT NULL | Short title |
| `description` | Text | nullable | Full requirement description |
| `status` | Enum(`draft`, `in_review`, `approved`, `in_progress`, `done`, `rejected`) | NOT NULL, default=`draft` | Workflow status |
| `priority` | Enum(`critical`, `high`, `medium`, `low`) | nullable | Requirement priority |
| `assigned_to` | Integer | FK → `users.id`, nullable | Assigned user |
| `order_index` | Integer | NOT NULL, default=0 | Sort order within the project |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_requirements_project_id`, `ix_requirements_raw_input_id`, `ix_requirements_status`, `ix_requirements_assigned_to`

**Structure rules:**

There is no requirement hierarchy. A requirement cannot contain a requirement.
Every requirement is a direct child of its project. The object chain is fixed:

    project → requirement → acceptance criterion → gherkin scenario

- All requirements in a project are siblings. There is no parent, no depth, and no move-within-hierarchy operation.
- Grouping is done with labels. See the `labels` table. A label is a view axis, not structure. One requirement can carry labels from several namespaces.
- A relation between two requirements is a `traceability_links` row, never a containment. Use `relates_to` when one requirement is split into two.
- `raw_input_id` records provenance: which raw input produced this requirement. A raw input is a pasted note or a parsed document, so one field covers both sources. Reach the document through `raw_inputs.document_id`. `raw_input_id` is NOT the same as `requirement_documents`, which records every document a user attached as relevant. One is history; the other is reference.

**Derived state — the coverage mark.**
A requirement is **covered** when at least one of its acceptance criteria has at least one `gherkin_scenarios` row with `state = 'accepted'` and `is_deleted = false`. It is otherwise **not covered**. There is no column. The outline computes it in the same query that loads a group, and the table lens computes it in the same query that loads a page. A stored flag goes out of date the moment a scenario changes — the same reason the stale rule is derived.

### Table: `acceptance_criteria`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `requirement_id` | Integer | FK → `requirements.id`, NOT NULL, indexed | Parent requirement |
| `title` | String(500) | NOT NULL | Short label for the criterion. Shown in lists |
| `text` | Text | NOT NULL | The criterion in plain language. It holds no Gherkin |
| `order_index` | Integer | NOT NULL, default=0 | Sort order within requirement |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_acceptance_criteria_requirement_id`

**Notes:**
- A criterion is written in plain language by a business reader. It never holds Gherkin. Gherkin lives in `gherkin_scenarios`.
- One criterion can have zero, one, or many scenarios. Zero is valid: the criterion is simply not formalized yet.

### Table: `gherkin_scenarios`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `acceptance_criteria_id` | Integer | FK → `acceptance_criteria.id`, NOT NULL, indexed | The criterion this scenario formalizes |
| `title` | String(500) | NOT NULL | Scenario name — the text after the `Scenario:` keyword |
| `gherkin_text` | Text | NOT NULL | Full Gherkin scenario text |
| `origin` | Enum(`human`, `ai`) | NOT NULL, default=`human` | Who produced the first version |
| `state` | Enum(`proposed`, `draft`, `accepted`) | NOT NULL, default=`draft` | Authoring state. NOT test coverage |
| `status` | Enum(`not_covered`, `covered`, `test_passed`, `test_failed`) | NOT NULL, default=`not_covered` | Test coverage state |
| `source_text_hash` | String(64) | nullable | SHA-256 of `acceptance_criteria.text` at the moment of acceptance |
| `order_index` | Integer | NOT NULL, default=0 | Sort order within the criterion |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_gherkin_scenarios_acceptance_criteria_id`, `ix_gherkin_scenarios_state`, `ix_gherkin_scenarios_status`

**The two enums describe two different things. Do not merge them.**
- `state` answers "has a person agreed to this text?"
- `status` answers "does a test exist for it, and does that test pass?"

**Authoring state rules:**
- `proposed` — the AI produced it. It waits in the inspector. No person agreed yet.
- `draft` — a person accepted it. That person now owns it and can edit it.
- `accepted` — a person confirmed the final text. An edit returns it to `draft`.
- A dismissed proposal is soft-deleted, never hard-deleted. The audit trail must show what the AI offered and what the person refused.

**Origin rules:**
- `origin` records the producer of the FIRST version. A later human edit does not change `ai` to `human`. Read `updated_by` to see who edited.
- `created_by` stays a foreign key to `users.id`. It records the person who ran the AI action, never the AI. There is no AI row in the `users` table.

**The stale rule (derived, never stored):**
- On acceptance the service writes `source_text_hash` = SHA-256 of the parent criterion's `text`, encoded UTF-8.
- A scenario is **stale** when `source_text_hash` is not NULL and does not match the SHA-256 of the parent criterion's current `text`.
- Stale is computed on read. A stored flag goes out of date the moment the criterion changes.
- A scenario with `source_text_hash` = NULL is never stale — it was never accepted.
- Only `text` is hashed. A change to `title` alone does not make a scenario stale.

### Table: `labels`

A label groups requirements for navigation and filtering. It is a view axis. It is NOT structure, and it never affects the object chain.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `project_id` | Integer | FK → `projects.id`, NOT NULL, indexed | Owning project |
| `namespace` | Enum(`group`) | NOT NULL, default=`group` | The axis this label belongs to |
| `value` | String(100) | NOT NULL | The label text, for example `Registration` |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_labels_project_id`
**Constraints:** UNIQUE(`project_id`, `namespace`, `value`)

**Rules:**
- A label is displayed as `namespace:value`, for example `group:Registration`.
- The namespace set is closed and controlled by the schema. A user creates values, never namespaces. Adding a namespace is an enum migration and a governance decision.
- `value` MUST NOT contain `/`, `\`, or `:`. Without this rule a user encodes a folder path inside the string and rebuilds an unvalidated hierarchy.
- Labels are scoped to a project. Two projects never share a label row.

### Table: `requirement_labels`

Association table linking requirements to labels.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `requirement_id` | Integer | FK → `requirements.id`, NOT NULL, indexed | |
| `label_id` | Integer | FK → `labels.id`, NOT NULL, indexed | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |

**Constraints:** UNIQUE(`requirement_id`, `label_id`)

**Note:** A requirement can carry at most one label per namespace. The service enforces this, not the database, because the namespace lives on `labels`.

---

## Module 3: Documents — `app/documents/models.py`

### Table: `documents`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `project_id` | Integer | FK → `projects.id`, NOT NULL, indexed | Owning project |
| `filename` | String(500) | NOT NULL | Original filename as uploaded |
| `file_path` | String(1000) | NOT NULL | Relative path on filesystem (under UPLOAD_DIR) |
| `file_type` | String(50) | NOT NULL | File extension (`.txt`, `.md`, `.docx`, `.doc`) |
| `file_size_bytes` | Integer | NOT NULL | File size in bytes |
| `parse_status` | Enum(`pending`, `processing`, `complete`, `failed`) | NOT NULL, default=`pending` | Parsing pipeline status |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_documents_project_id`, `ix_documents_parse_status`

**Note:** File contents are NEVER stored in the database. Only metadata and the relative file path. The actual file lives on the Docker volume at `UPLOAD_DIR/<file_path>`.

### Table: `requirement_documents`

Association table linking requirements to their attached documents.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `requirement_id` | Integer | FK → `requirements.id`, NOT NULL | |
| `document_id` | Integer | FK → `documents.id`, NOT NULL | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |

**Constraints:** UNIQUE(`requirement_id`, `document_id`)

---

## Module 8: Intake — `app/intake/models.py`

Intake is the funnel. Nothing the AI produces enters `requirements` without a person accepting it here. See ADR-0043 and ADR-0045.

### Table: `raw_inputs`

One unit of unstructured source material inside a project.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `project_id` | Integer | FK → `projects.id`, NOT NULL, indexed | Owning project |
| `source_type` | Enum(`paste`, `document`) | NOT NULL | Where the material came from |
| `document_id` | Integer | FK → `documents.id`, nullable, indexed | The parsed document. NOT NULL when `source_type` = `document` |
| `title` | String(500) | nullable | User label, e.g. "Kickoff call 2026-08-28" |
| `content` | Text | nullable | The pasted text. NOT NULL when `source_type` = `paste`. Always NULL when `source_type` = `document` |
| `status` | Enum(`pending`, `processing`, `structured`, `failed`) | NOT NULL, default=`pending` | Decomposition pipeline state |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_raw_inputs_project_id`, `ix_raw_inputs_status`, `ix_raw_inputs_document_id`

**Constraint:**

```
CHECK (
  (source_type = 'paste'    AND content IS NOT NULL AND document_id IS NULL) OR
  (source_type = 'document' AND content IS NULL     AND document_id IS NOT NULL)
)
```

**Rules:**
- A `document` raw input stores no text. The text is read from the file at decomposition time, through `documents.file_path`. This keeps the rule that document content never lives in the database.
- Consequence you must accept: a decomposition is not reproducible from the database alone. If the file leaves the volume, the candidates remain but the text they came from is gone.
- `status` describes the decomposition run, not agreement. Agreement lives on `candidate_requirements.state`.
- A raw input is never edited after creation. To correct a paste, delete it and create a new one. This keeps the provenance of an accepted requirement honest.

### Table: `candidate_requirements`

A proposed requirement waiting for a person. It is NOT a requirement.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `raw_input_id` | Integer | FK → `raw_inputs.id`, NOT NULL, indexed | The material this candidate came from |
| `title` | String(500) | NOT NULL | Proposed short title |
| `description` | Text | nullable | Proposed description |
| `origin` | Enum(`human`, `ai`) | NOT NULL, default=`ai` | Who produced the first version |
| `state` | Enum(`proposed`, `accepted`) | NOT NULL, default=`proposed` | Agreement state |
| `requirement_id` | Integer | FK → `requirements.id`, nullable, indexed | The requirement it became. NULL until accepted |
| `order_index` | Integer | NOT NULL, default=0 | Sort order within the raw input |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_candidate_requirements_raw_input_id`, `ix_candidate_requirements_state`, `ix_candidate_requirements_requirement_id`

**Agreement rules.** A candidate has two states, not the three of `gherkin_scenarios`. A scenario needs a `draft` state because a person edits the text after acceptance. A candidate stops existing as a candidate at the moment of acceptance, so it needs no `draft`. The two enums also differ in their default: a scenario defaults to `human`, a candidate to `ai`.
- `proposed` — the AI produced it, or a person typed it and has not accepted it. No requirement exists yet.
- `accepted` — a person accepted it. The service creates the `requirements` row, writes `requirements.raw_input_id`, and writes `requirement_id` back here.
- A dismissed candidate is soft-deleted, never hard-deleted. The audit trail must show what the AI offered and what the person refused. There is no `dismissed` enum value — `is_deleted` carries that fact, exactly as for a scenario.
- `origin` records the producer of the FIRST version. A person who edits an AI candidate before accepting it does not change `ai` to `human`.
- `created_by` is always a person. There is no AI row in the `users` table.
- Accept is one-way. To undo, soft-delete the requirement. The candidate keeps its `accepted` state and its `requirement_id` as history.

**The project is reached through the raw input.** `candidate_requirements` holds no `project_id`. One truth, one join.

---

## Module 4: NLP — `app/nlp/models.py`

### Table: `analysis_results`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `requirement_id` | Integer | FK → `requirements.id`, nullable, indexed | Analyzed requirement (if applicable) |
| `document_id` | Integer | FK → `documents.id`, nullable, indexed | Analyzed document (if applicable) |
| `analysis_type` | Enum(`quality`, `similarity`, `classification`, `ner`, `completeness`, `ambiguity`) | NOT NULL | What type of analysis was run |
| `result_data` | JSON | NOT NULL | Analysis output (structure varies by type — see NLP module README) |
| `score` | Float | nullable | Numeric score (e.g., quality score 0.0–1.0) |
| `created_at` | DateTime | NOT NULL, default=now | |

**Indexes:** `ix_analysis_results_requirement_id`, `ix_analysis_results_document_id`

**Constraint:** Either `requirement_id` OR `document_id` must be set (not both NULL).

### Table: `embeddings`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `requirement_id` | Integer | FK → `requirements.id`, nullable, indexed | Source requirement |
| `document_id` | Integer | FK → `documents.id`, nullable, indexed | Source document |
| `text_chunk` | Text | NOT NULL | The text that was embedded |
| `embedding_vector` | Vector(384) | NOT NULL | Vector embedding (pgvector, 384 dimensions) |
| `model_name` | String(100) | NOT NULL, default=`all-MiniLM-L6-v2` | Which model generated this embedding |
| `created_at` | DateTime | NOT NULL, default=now | |

**Notes:**
- Requires PostgreSQL `pgvector` extension.
- 384 dimensions corresponds to `all-MiniLM-L6-v2`.
- If the embedding model changes, all existing embeddings must be regenerated.
- Consider HNSW or IVFFlat index for similarity search performance as the table grows.

---

## Module 5: Gherkin — `app/gherkin/models.py`

### Table: `validation_results`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `gherkin_scenario_id` | Integer | FK → `gherkin_scenarios.id`, NOT NULL, indexed | Which scenario was validated |
| `is_valid_syntax` | Boolean | NOT NULL | Whether Gherkin syntax is correct |
| `syntax_errors` | JSON | nullable | List of syntax error details |
| `is_testable` | Boolean | nullable | Whether the AC is considered testable |
| `complexity_flag` | Boolean | NOT NULL, default=False | True if AC is too complex for a single test |
| `suggestions` | JSON | nullable | AI-generated suggestions for improvement |
| `created_at` | DateTime | NOT NULL, default=now | |

**Indexes:** `ix_validation_results_gherkin_scenario_id`

---

## Module 6: Traceability — `app/traceability/models.py`

### Table: `traceability_links`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `source_requirement_id` | Integer | FK → `requirements.id`, NOT NULL, indexed | Source of the link |
| `target_requirement_id` | Integer | FK → `requirements.id`, nullable, indexed | Target requirement |
| `link_type` | Enum(`depends_on`, `blocks`, `relates_to`, `duplicates`, `tested_by`) | NOT NULL | Nature of the link |
| `description` | Text | nullable | User-provided context for the link |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_traceability_links_source_requirement_id`, `ix_traceability_links_target_requirement_id`
**Constraints:** UNIQUE(`source_requirement_id`, `target_requirement_id`, `link_type`)

**Notes:**
- In MVP, all links are created manually. Automated link detection is post-MVP.
- `parent_of` is deliberately absent. Requirements have no containment relation. A link table that carries `parent_of` rebuilds the hierarchy with no depth cap, no cycle guard, and no validation. Do not add it back.

---

## Module 7: Admin & Audit — `app/admin/models.py`

### Table: `audit_logs`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `table_name` | String(100) | NOT NULL, indexed | Which table was modified |
| `record_id` | Integer | NOT NULL | ID of the modified record |
| `action_type` | Enum(`CREATE`, `UPDATE`, `DELETE`) | NOT NULL, indexed | What happened |
| `old_values` | JSON | nullable | Previous field values (NULL for CREATE) |
| `new_values` | JSON | nullable | New field values (NULL for DELETE) |
| `correlation_id` | UUID | NOT NULL, indexed | Request correlation ID |
| `user_id` | Integer | FK → `users.id`, NOT NULL, indexed | Who made the change |
| `timestamp` | DateTime | NOT NULL, default=now | When the change occurred |
| `additional_info` | JSON | nullable | Extra context (e.g., IP address, user agent) |

**Indexes:** `ix_audit_logs_table_name`, `ix_audit_logs_action_type`, `ix_audit_logs_user_id`, `ix_audit_logs_correlation_id`, `ix_audit_logs_timestamp`

**Notes:**
- Audit logs are APPEND-ONLY. Never updated or deleted.
- No soft delete on this table — audit records are permanent.
- No `updated_at`/`updated_by` fields — records are immutable.
- Do NOT modify this table's structure without explicit developer instruction.

---

## Entity Relationship Summary

```
users ──────────┬─── refresh_tokens
                ├─── project_members ──── projects
                │                            ├─── labels ─────────── requirement_labels
                │                            ├─── documents ──┬─── embeddings
                │                            │                └─── analysis_results
                │                            ├─── raw_inputs ─── candidate_requirements
                │                            └─── requirements ──┬─── acceptance_criteria ─── gherkin_scenarios ─── validation_results
                │                                                ├─── requirement_labels
                │                                                ├─── requirement_documents ─── documents
                │                                                ├─── analysis_results
                │                                                ├─── traceability_links (source)
                │                                                └─── traceability_links (target)
                └─── audit_logs

requirements.raw_input_id             ──→ raw_inputs.id     (provenance: exactly one, nullable)
raw_inputs.document_id                ──→ documents.id      (set only when source_type='document')
candidate_requirements.requirement_id ──→ requirements.id   (set on accept)
requirement_documents                 ──→ documents.id      (attachment: many)
```

---

## Migration Order

When creating the schema from scratch, tables must be created in this order (respecting foreign key dependencies):

1. `users`
2. `refresh_tokens`
3. `projects`
4. `project_members`
5. `documents`
6. `raw_inputs`
7. `requirements`
8. `candidate_requirements`
9. `acceptance_criteria`
10. `gherkin_scenarios`
11. `requirement_documents`
12. `labels`
13. `requirement_labels`
14. `analysis_results`
15. `embeddings`
16. `validation_results`
17. `traceability_links`
18. `audit_logs`

---

## PostgreSQL Extensions Required

| Extension | Purpose | Install |
|-----------|---------|---------|
| `pgvector` | Vector storage for embeddings | `CREATE EXTENSION IF NOT EXISTS vector;` |
| `uuid-ossp` | UUID generation (for correlation IDs) | `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";` |
