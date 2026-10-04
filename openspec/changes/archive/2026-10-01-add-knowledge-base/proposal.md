# Proposal: add-knowledge-base

## Summary
Add the runbook knowledge base capability to the Autonomous Incident Triage Agent using Supabase Postgres with pgvector and Gemini embeddings.

## Why
The agent needs semantic search over historical incident runbooks to recommend remediation steps to on-call engineers.

## What
- SQL migration file `db/migrations/001_incident_docs.sql` defining `incident_docs` table with 768-dimension embeddings and `match_incident_docs` RPC function.
- `requirements.txt` listing all necessary project dependencies.
- `seed_rag.py` to embed sample runbooks (auth, database, payments) using Gemini embeddings (`output_dimensionality=768`) and insert them idempotently (`ON CONFLICT (md5(content)) DO NOTHING`).
- Isolated unit tests in `tests/test_rag.py`.

## Affected Capabilities
- `knowledge-base` (ADDED)

## Rollback
Drop the `incident_docs` table and `match_incident_docs` function in PostgreSQL; remove `seed_rag.py`.
