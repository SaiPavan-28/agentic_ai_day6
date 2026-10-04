# Design: add-knowledge-base

## Context
The incident triage agent performs Retrieval-Augmented Generation (RAG) against runbooks to suggest remediation actions.

## Key Decisions
1. **Embedding Dimension (768)**: Configured `GoogleGenerativeAIEmbeddings` with `output_dimensionality=768` to align with `VECTOR(768)` in PostgreSQL schema.
2. **Idempotency**: Use `ON CONFLICT (md5(content)) DO NOTHING` backed by a unique index on `md5(content)` to prevent duplicate runbooks when re-running seed scripts.
3. **RPC Match Function**: Implement `match_incident_docs` PostgreSQL function using cosine similarity (`1 - (embedding <=> query_embedding)`) and JSONB metadata filtering (`metadata @> filter`).

## Alternatives Considered
- Direct vector queries in Python app: Rejected in favor of SQL RPC function for performance and cleaner metadata filtering.
