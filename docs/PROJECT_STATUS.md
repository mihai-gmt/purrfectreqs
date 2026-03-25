# PurrfectReqs — Project Status

> **Purpose:** Tracks implementation progress across all modules. Agents MUST update this file after completing any feature. Humans use this file to understand what is built and what is next.

---

## Overall Status

**Phase:** Initial setup
**Last updated:** 2026-03-23

---

## Infrastructure

| Item | Status | Notes |
|------|--------|-------|
| Docker Compose stack | ⬜ Not started | |
| Dockerfile | ⬜ Not started | |
| `scripts/start.sh` | ⬜ Not started | |
| Makefile | ⬜ Not started | |
| `app/core/config.py` | ⬜ Not started | |
| `app/core/database.py` | ⬜ Not started | |
| `app/core/logging.py` | ⬜ Not started | |
| `app/core/exceptions.py` | ⬜ Not started | |
| `.env.example` | ⬜ Not started | |
| `pyproject.toml` | ⬜ Not started | |
| Base Alembic setup | ⬜ Not started | |
| Base Jinja2 template (`base.html`) | ⬜ Not started | |

---

## Module 1: Auth

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| User login | ⬜ | ⬜ | ⬜ | Not started |
| User logout | ⬜ | ⬜ | ⬜ | Not started |
| Token refresh | ⬜ | ⬜ | ⬜ | Not started |
| RBAC dependencies | ⬜ | ⬜ | ⬜ | Not started |
| Admin: create user | ⬜ | ⬜ | ⬜ | Not started |
| Admin: list users | ⬜ | ⬜ | ⬜ | Not started |
| Admin: edit user | ⬜ | ⬜ | ⬜ | Not started |
| Admin: password reset | ⬜ | ⬜ | ⬜ | Not started |
| Account lockout | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 2: Projects & Requirements

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| Create project | ⬜ | ⬜ | ⬜ | Not started |
| List / search projects | ⬜ | ⬜ | ⬜ | Not started |
| Edit / delete project | ⬜ | ⬜ | ⬜ | Not started |
| Manage project members | ⬜ | ⬜ | ⬜ | Not started |
| Create requirement | ⬜ | ⬜ | ⬜ | Not started |
| Edit / delete requirement | ⬜ | ⬜ | ⬜ | Not started |
| Requirement hierarchy (epic/story/subtask) | ⬜ | ⬜ | ⬜ | Not started |
| Add / edit acceptance criteria | ⬜ | ⬜ | ⬜ | Not started |
| Update AC status | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 3: Document Ingestion

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| Upload document | ⬜ | ⬜ | ⬜ | Not started |
| Parse document | ⬜ | ⬜ | ⬜ | Not started |
| Extract candidate requirements | ⬜ | ⬜ | ⬜ | Not started |
| List / delete documents | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 4: NLP & AI Analysis

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| Ollama client (`llm_client.py`) | ⬜ | ⬜ | ⬜ | Not started |
| spaCy processor | ⬜ | ⬜ | ⬜ | Not started |
| Embeddings service | ⬜ | ⬜ | ⬜ | Not started |
| Requirement quality analysis | ⬜ | ⬜ | ⬜ | Not started |
| NER analysis | ⬜ | ⬜ | ⬜ | Not started |
| Semantic similarity | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 5: Gherkin Validation

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| Syntax validation | ⬜ | ⬜ | ⬜ | Not started |
| Testability analysis | ⬜ | ⬜ | ⬜ | Not started |
| Complexity flag + split suggestions | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 6: Traceability

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| Create / edit / delete links | ⬜ | ⬜ | ⬜ | Not started |
| View linked requirements | ⬜ | ⬜ | ⬜ | Not started |

---

## Module 7: Admin & Audit

| Feature | Feature File | Tests | Implementation | Status |
|---------|-------------|-------|----------------|--------|
| Audit log (append on all changes) | ⬜ | ⬜ | ⬜ | Not started |
| Admin: view / search audit logs | ⬜ | ⬜ | ⬜ | Not started |
| Admin: export audit logs | ⬜ | ⬜ | ⬜ | Not started |

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ⬜ | Not started |
| 🔄 | In progress |
| 🔴 | Feature file written, tests written (RED state) |
| 🟢 | Tests passing (GREEN state) |
| ✅ | Committed |
