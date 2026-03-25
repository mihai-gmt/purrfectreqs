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
| `created_at` | DateTime, default=now, NOT NULL | When the record was created |
| `updated_at` | DateTime, default=now, onupdate=now, NOT NULL | When the record was last modified |
| `created_by` | Integer, FK → `users.id`, nullable | Who created the record |
| `updated_by` | Integer, FK → `users.id`, nullable | Who last modified the record |

### Soft Delete Convention

Tables that store user-created content use soft deletes:

| Field | Type | Description |
|-------|------|-------------|
| `is_deleted` | Boolean, default=False | Soft delete flag |
| `deleted_at` | DateTime, nullable | When the record was soft-deleted |
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
| `locked_until` | DateTime | nullable | Lockout expiry (NULL = not locked) |
| `last_password_change` | DateTime | nullable | For password age tracking |
| `last_activity_at` | DateTime | nullable | For session timeout (30-min inactivity) |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_users_email`, `ix_users_username`, `ix_users_status`

**Notes:**
- `super_user` uses underscore in the database enum (Python convention), displayed as "super-user" in the UI.
- First admin user is created via seed script. Subsequent users may self-register via the registration form (default role: `user`, default status: `pending`) or be created directly by an admin.

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
| `parent_id` | Integer | FK → `requirements.id`, nullable, indexed | Parent requirement (for hierarchy) |
| `type` | Enum(`epic`, `story`, `subtask`) | NOT NULL | Requirement type in hierarchy |
| `title` | String(500) | NOT NULL | Short title |
| `description` | Text | nullable | Full requirement description |
| `status` | Enum(`draft`, `in_review`, `approved`, `in_progress`, `done`, `rejected`) | NOT NULL, default=`draft` | Workflow status |
| `priority` | Enum(`critical`, `high`, `medium`, `low`) | nullable | Requirement priority |
| `assigned_to` | Integer | FK → `users.id`, nullable | Assigned user |
| `order_index` | Integer | NOT NULL, default=0 | Sort order within parent |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_requirements_project_id`, `ix_requirements_parent_id`, `ix_requirements_status`, `ix_requirements_assigned_to`

**Hierarchy rules:**
- `epic` → can contain `story` children
- `story` → can contain `subtask` children
- `subtask` → cannot have children
- `parent_id` = NULL means top-level requirement (typically an epic)

### Table: `acceptance_criteria`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `requirement_id` | Integer | FK → `requirements.id`, NOT NULL, indexed | Parent requirement |
| `title` | String(500) | NOT NULL | Short description of the criterion |
| `gherkin_text` | Text | NOT NULL | Full Gherkin scenario text |
| `status` | Enum(`not_covered`, `covered`, `test_passed`, `test_failed`) | NOT NULL, default=`not_covered` | Test coverage state |
| `order_index` | Integer | NOT NULL, default=0 | Sort order within requirement |
| `is_deleted` | Boolean | NOT NULL, default=False | Soft delete |
| `deleted_at` | DateTime | nullable | |
| `deleted_by` | Integer | FK → `users.id`, nullable | |
| `created_at` | DateTime | NOT NULL, default=now | |
| `updated_at` | DateTime | NOT NULL, default=now, onupdate=now | |
| `created_by` | Integer | FK → `users.id`, nullable | |
| `updated_by` | Integer | FK → `users.id`, nullable | |

**Indexes:** `ix_acceptance_criteria_requirement_id`, `ix_acceptance_criteria_status`

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
| `acceptance_criteria_id` | Integer | FK → `acceptance_criteria.id`, NOT NULL, indexed | Which AC was validated |
| `is_valid_syntax` | Boolean | NOT NULL | Whether Gherkin syntax is correct |
| `syntax_errors` | JSON | nullable | List of syntax error details |
| `is_testable` | Boolean | nullable | Whether the AC is considered testable |
| `complexity_flag` | Boolean | NOT NULL, default=False | True if AC is too complex for a single test |
| `suggestions` | JSON | nullable | AI-generated suggestions for improvement |
| `created_at` | DateTime | NOT NULL, default=now | |

**Indexes:** `ix_validation_results_acceptance_criteria_id`

---

## Module 6: Traceability — `app/traceability/models.py`

### Table: `traceability_links`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | PK, auto-increment | |
| `source_requirement_id` | Integer | FK → `requirements.id`, NOT NULL, indexed | Source of the link |
| `target_requirement_id` | Integer | FK → `requirements.id`, nullable, indexed | Target requirement |
| `link_type` | Enum(`depends_on`, `blocks`, `relates_to`, `duplicates`, `parent_of`, `tested_by`) | NOT NULL | Nature of the link |
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

**Note:** In MVP, all links are created manually. Automated link detection is post-MVP.

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
                │                            ├─── requirements ──┬─── acceptance_criteria
                │                            │                   │        └─── validation_results
                │                            │                   ├─── analysis_results
                │                            │                   ├─── requirement_documents ─── documents
                │                            │                   ├─── traceability_links (source)
                │                            │                   └─── traceability_links (target)
                │                            └─── documents ──── analysis_results
                │                                                └─── embeddings
                └─── audit_logs
```

---

## Migration Order

When creating the schema from scratch, tables must be created in this order (respecting foreign key dependencies):

1. `users`
2. `refresh_tokens`
3. `projects`
4. `project_members`
5. `requirements`
6. `acceptance_criteria`
7. `documents`
8. `requirement_documents`
9. `analysis_results`
10. `embeddings`
11. `validation_results`
12. `traceability_links`
13. `audit_logs`

---

## PostgreSQL Extensions Required

| Extension | Purpose | Install |
|-----------|---------|---------|
| `pgvector` | Vector storage for embeddings | `CREATE EXTENSION IF NOT EXISTS vector;` |
| `uuid-ossp` | UUID generation (for correlation IDs) | `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";` |
