---
id: ADR-0007
title: pgvector in PostgreSQL over a dedicated vector database
status: accepted
date: 2026-03-25
backfilled: true
deciders: [mihai]
tags: [database, ai, architecture]

supersedes: []
superseded_by: null
depends_on: [ADR-0006]
related_to: [ADR-0001]
affects_modules: [app/nlp]
governed_by: [docs/DATA_MODELS.md, docs/ARCHITECTURE.md]
rejected_alternatives: [dedicated-vector-db]
---

# ADR-0007: pgvector in PostgreSQL over a dedicated vector database

## Context

Semantic search over requirements needs vector storage and similarity queries.
PostgreSQL 16 is already the system database; adding a second datastore just
for vectors would mean another Docker service, another backup target, and
another failure mode.

## Decision

Embeddings are stored in PostgreSQL using the `pgvector` extension — an
`embeddings` table with a `Vector(384)` column matching `all-MiniLM-L6-v2`
output. The image is `pgvector/pgvector:pg16`.

## Rationale

"Avoids a separate vector database service for MVP scale"
(`docs/ARCHITECTURE.md`, Decision Log). Vectors live next to the rows they
describe, share transactions and backups, and MVP volumes are far below where
a specialised store pays off.

## Consequences

### Positive

- One database to run, back up, and migrate (Alembic covers the schema).
- Joins between vectors and domain rows are ordinary SQL.

### Negative

- Similarity-search performance needs attention as the table grows —
  HNSW/IVFFlat indexing is the noted follow-up (`docs/DATA_MODELS.md`).
- The vector dimension is coupled to the embedding model; changing models
  forces regeneration of all embeddings.

## Alternatives considered

### dedicated-vector-db

A separate vector database (e.g. Qdrant, Milvus, Weaviate) was rejected for
MVP: an extra service and operational surface with no benefit at this scale.
